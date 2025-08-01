from __future__ import annotations

import base64

import redis.asyncio as redis
from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from examples.auth.database import get_db
from examples.auth.models import Site
from examples.auth.models import User
from examples.auth.redis_pool import get_redis_pool
from examples.db_management.deps import _site_permission
from examples.db_management.deps import get_current_user
from examples.db_management.deps import is_super_admin
from examples.db_management.deps import require_admin
from examples.db_management.deps import SUPER_ADMIN_NAME
from examples.db_management.schemas.site import SiteCreate
from examples.db_management.schemas.site import SiteDelete
from examples.db_management.schemas.site import SiteRead
from examples.db_management.schemas.site import SiteUpdate
from examples.db_management.schemas.site import SiteUserOp
from examples.db_management.services.site_services import add_user_to_site
from examples.db_management.services.site_services import create_site
from examples.db_management.services.site_services import delete_site
from examples.db_management.services.site_services import list_sites
from examples.db_management.services.site_services import remove_user_from_site
from examples.db_management.services.site_services import update_site

router: APIRouter = APIRouter(tags=['site-mgmt'])


@router.get('/list_sites', response_model=list[SiteRead])
async def endpoint_list_sites(
    db: AsyncSession = Depends(get_db),
    me: User = Depends(get_current_user),
) -> list[SiteRead]:
    """Retrieve a list of sites accessible to the user.

    Args:
        db (AsyncSession): Database session.
        me (User): Current authenticated user.

    Returns:
        list[SiteRead]: List of accessible sites.

    Raises:
        HTTPException: If the user lacks admin privileges.
    """
    # Super admin retrieves all sites; admin retrieves group-specific sites
    if is_super_admin(me):
        sites = await list_sites(db)
    elif me.role == 'admin':
        sites = await list_sites(db, group_id=me.group_id)
    else:
        raise HTTPException(status_code=403, detail='Admin role required.')

    # Convert Site objects to SiteRead schemas for response
    return [
        SiteRead(
            id=site.id,
            name=site.name,
            group_id=site.group_id,
            group_name=site.group.name if site.group else None,
            user_ids=[user.id for user in site.users],
        )
        for site in sites
    ]


@router.post(
    '/create_site',
    response_model=SiteRead,
    dependencies=[Depends(require_admin)],
)
async def endpoint_create_site(
    payload: SiteCreate,
    db: AsyncSession = Depends(get_db),
    me: User = Depends(get_current_user),
) -> SiteRead:
    """Create a new site.

    Args:
        payload (SiteCreate): Data required to create a site.
        db (AsyncSession): Database session.
        me (User): Current authenticated user.

    Returns:
        SiteRead: Details of the created site.

    Raises:
        HTTPException: If permission check fails.
    """
    group_id: int | None = payload.group_id or me.group_id

    # Perform permission checks (admins restricted to their group)
    _site_permission(me, group_id=group_id)

    site: Site = await create_site(payload.name, group_id, db)

    return SiteRead(
        id=site.id,
        name=site.name,
        group_id=site.group_id,
        group_name=site.group.name if site.group else None,
        user_ids=[user.id for user in site.users],
    )


@router.put(
    '/update_site',
    dependencies=[Depends(require_admin)],
)
async def endpoint_update_site(
    payload: SiteUpdate,
    db: AsyncSession = Depends(get_db),
    me: User = Depends(get_current_user),
) -> dict[str, str]:
    """Update an existing site's name.

    Args:
        payload (SiteUpdate): Contains site ID and the new site name.
        db (AsyncSession): Database session.
        me (User): Current authenticated user.

    Returns:
        dict[str, str]: Confirmation message.

    Raises:
        HTTPException: If the site is not found or permission fails.
    """
    # Retrieve the site to update
    site: Site | None = (
        await db.execute(
            select(Site).where(Site.id == payload.site_id),
        )
    ).scalar_one_or_none()

    if not site:
        raise HTTPException(status_code=404, detail='Site not found.')

    # Permission check before updating the site
    _site_permission(me, site=site)

    await update_site(site, payload.new_name, db)
    return {'message': 'Site updated successfully.'}


@router.delete(
    '/delete_site',
    dependencies=[Depends(require_admin)],
)
async def endpoint_delete_site(
    payload: SiteDelete,
    db: AsyncSession = Depends(get_db),
    me: User = Depends(get_current_user),
    rds: redis.Redis = Depends(get_redis_pool),
) -> dict[str, str]:
    """Delete an existing site and related data, and remove related redis keys.

    Args:
        payload (SiteDelete): Contains site ID to delete.
        db (AsyncSession): Database session.
        me (User): Current authenticated user.
        rds (redis.Redis): Redis connection pool.

    Returns:
        dict[str, str]: Confirmation message.

    Raises:
        HTTPException: If the site is not found or permission fails.
    """
    # Retrieve the site to delete
    site: Site | None = (
        await db.execute(
            select(Site).where(Site.id == payload.site_id),
        )
    ).unique().scalar_one_or_none()

    if not site:
        raise HTTPException(status_code=404, detail='Site not found.')

    # Check permissions for deletion
    _site_permission(me, site=site)

    # Delete redis streaming keys (site.name must be base64 encoded)
    def encode_site_name(site_name: str) -> str:
        """Encode the site name using URL-safe base64 encoding.

        Args:
            site_name (str): The site name to encode.

        Returns:
            str: The base64-encoded site name.
        """
        return base64.urlsafe_b64encode(
            site_name.encode('utf-8'),
        ).decode('ascii')
    encoded_name: str = encode_site_name(site.name)
    key_pattern: str = f'stream_frame:{encoded_name}*'
    keys: list[bytes] = await rds.keys(key_pattern)
    if keys:
        await rds.delete(*keys)

    await delete_site(site, db)
    return {'message': 'Site and related data deleted successfully.'}


@router.post(
    '/add_user_to_site',
    dependencies=[Depends(require_admin)],
)
async def endpoint_add_user_to_site(
    payload: SiteUserOp,
    db: AsyncSession = Depends(get_db),
    me: User = Depends(get_current_user),
) -> dict[str, str]:
    """Associate a user with a specific site.

    Args:
        payload (SiteUserOp): Contains user ID and site ID.
        db (AsyncSession): Database session.
        me (User): Current authenticated user.

    Returns:
        dict[str, str]: Confirmation message.

    Raises:
        HTTPException: If site or user is not found, or permission fails.
    """
    # Retrieve the site to which the user will be added
    site: Site | None = (
        await db.execute(
            select(Site).where(Site.id == payload.site_id),
        )
    ).unique().scalar_one_or_none()

    if not site:
        raise HTTPException(status_code=404, detail='Site not found.')

    # Permission check
    _site_permission(me, site=site)

    # Retrieve the user to add
    user: User | None = (
        await db.execute(
            select(User).where(User.id == payload.user_id),
        )
    ).unique().scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail='User not found.')

    if user.username == SUPER_ADMIN_NAME:
        raise HTTPException(
            status_code=403,
            detail="Cannot modify super admin's site membership.",
        )

    if user.group_id != site.group_id:
        raise HTTPException(
            status_code=403,
            detail='User and site must belong to the same group.',
        )

    await add_user_to_site(user.id, site.id, db)
    return {'message': 'User linked to site successfully.'}


@router.post(
    '/remove_user_from_site',
    dependencies=[Depends(require_admin)],
)
async def endpoint_remove_user_from_site(
    payload: SiteUserOp,
    db: AsyncSession = Depends(get_db),
    me: User = Depends(get_current_user),
) -> dict[str, str]:
    """Dissociate a user from a specific site.

    Args:
        payload (SiteUserOp): Contains user ID and site ID.
        db (AsyncSession): Database session.
        me (User): Current authenticated user.

    Returns:
        dict[str, str]: Confirmation message.

    Raises:
        HTTPException: If site or user is not found, or permission fails.
    """
    # Retrieve the site from which the user will be removed
    site: Site | None = (
        await db.execute(
            select(Site).where(Site.id == payload.site_id),
        )
    ).unique().scalar_one_or_none()

    if not site:
        raise HTTPException(status_code=404, detail='Site not found.')

    _site_permission(me, site=site)

    # Retrieve the user to remove
    user: User | None = (
        await db.execute(
            select(User).where(User.id == payload.user_id),
        )
    ).unique().scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail='User not found.')

    if user.username == SUPER_ADMIN_NAME:
        raise HTTPException(
            status_code=403, detail='Cannot remove super admin from site.',
        )

    await remove_user_from_site(user.id, site.id, db)
    return {'message': 'User unlinked from site successfully.'}
