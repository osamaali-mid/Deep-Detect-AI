from __future__ import annotations

import unittest
from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

from examples.auth.models import Group
from examples.db_management.services import group_services


class TestGroupServices(unittest.IsolatedAsyncioTestCase):
    """
    Unit tests for group_services module using asynchronous mocks.
    """

    def setUp(self) -> None:
        """Set up common mock objects for each test.

        This method initialises mock database and group objects for use
        in each test case.
        """
        self.db: AsyncMock = AsyncMock()
        self.grp = MagicMock(spec=Group)
        self.grp.id = 1
        self.grp.name = 'Test Group'
        self.grp.uniform_number = '12345678'

    async def test_list_groups(self) -> None:
        """Test retrieving a list of all groups.

        Ensures that all groups are returned as expected from the
        database query.
        """
        mock_result: MagicMock = MagicMock()
        mock_unique: MagicMock = mock_result.unique.return_value
        mock_scalars: MagicMock = mock_unique.scalars.return_value
        mock_scalars.all.return_value = ['group1', 'group2']

        self.db.execute = AsyncMock(return_value=mock_result)

        groups: list = await group_services.list_groups(db=self.db)

        self.assertEqual(groups, ['group1', 'group2'])

    async def test_create_group_success(self) -> None:
        """Test successful creation of a new group.

        Verifies that a new group is created and committed to the
        database without error.
        """
        self.db.commit = AsyncMock()
        self.db.refresh = AsyncMock()
        self.db.add = MagicMock()

        with patch(
            'examples.db_management.services.group_services.Group',
        ) as MockGroup:
            mock_group: MagicMock = MagicMock()
            MockGroup.return_value = mock_group

            result: MagicMock = await group_services.create_group(
                name='New Group',
                uniform_number='87654321',
                db=self.db,
            )

            self.assertEqual(result, mock_group)
            self.db.add.assert_called_with(mock_group)
            self.db.commit.assert_awaited()
            self.db.refresh.assert_awaited_with(mock_group)

    async def test_create_group_integrity_error(self) -> None:
        """
        Test group creation raises HTTPException for duplicate uniform number.

        Ensures that an HTTPException with status 400 is raised if a
        duplicate uniform number is used during group creation.
        """
        self.db.commit = AsyncMock(
            side_effect=IntegrityError('Integrity error', {}, None),
        )
        self.db.rollback = AsyncMock()
        self.db.add = MagicMock()

        with self.assertRaises(HTTPException) as context:
            await group_services.create_group(
                name='Duplicate Group',
                uniform_number='12345678',
                db=self.db,
            )

        self.assertEqual(context.exception.status_code, 400)
        self.db.rollback.assert_awaited()

    async def test_update_group_success(self) -> None:
        """Test successful update of group details.

        Verifies that the group details are updated and committed to the
        database.
        """
        self.db.commit = AsyncMock()

        await group_services.update_group(
            grp=self.grp,
            new_name='Updated Group',
            new_uniform_number='11112222',
            db=self.db,
        )

        self.db.commit.assert_awaited()
        self.assertEqual(self.grp.name, 'Updated Group')
        self.assertEqual(self.grp.uniform_number, '11112222')

    async def test_update_group_invalid_uniform_number(self) -> None:
        """
        Test updating group raises HTTPException for invalid uniform number.

        Ensures that an HTTPException with status 400 is raised if an
        invalid uniform number is provided during update.
        """
        with self.assertRaises(HTTPException) as context:
            await group_services.update_group(
                grp=self.grp,
                new_name=None,
                new_uniform_number='123',  # invalid uniform number
                db=self.db,
            )

        self.assertEqual(context.exception.status_code, 400)

    async def test_update_group_no_fields_provided(self) -> None:
        """Test updating group raises HTTPException when no fields provided.

        Ensures that an HTTPException with status 400 is raised if no
        update fields are provided.
        """
        with self.assertRaises(HTTPException) as context:
            await group_services.update_group(
                grp=self.grp,
                new_name=None,
                new_uniform_number=None,
                db=self.db,
            )

        self.assertEqual(context.exception.status_code, 400)

    async def test_delete_group_success(self) -> None:
        """Test successful deletion of a group.

        Verifies that the group is deleted and the transaction is
        committed.
        """
        self.db.delete = AsyncMock()
        self.db.commit = AsyncMock()

        await group_services.delete_group(grp=self.grp, db=self.db)

        self.db.delete.assert_awaited_with(self.grp)
        self.db.commit.assert_awaited()

    async def test_delete_group_exception(self) -> None:
        """Test group deletion raises HTTPException on database error.

        Ensures that an HTTPException with status 500 is raised if the
        database commit fails during group deletion.
        """
        self.db.delete = AsyncMock()
        self.db.commit = AsyncMock(side_effect=Exception('DB error'))
        self.db.rollback = AsyncMock()

        with self.assertRaises(HTTPException) as context:
            await group_services.delete_group(grp=self.grp, db=self.db)

        self.assertEqual(context.exception.status_code, 500)
        self.db.rollback.assert_awaited()

    async def test_create_group_general_exception(self) -> None:
        """
        Test creating a group raises HTTPException on general database error.

        Ensures that an HTTPException with status 500 is raised if a
        general database error occurs during group creation.
        """
        self.db.commit = AsyncMock(side_effect=Exception('Unexpected error'))
        self.db.rollback = AsyncMock()
        self.db.add = MagicMock()

        with self.assertRaises(HTTPException) as context:
            await group_services.create_group(
                name='General Exception Group',
                uniform_number='99998888',
                db=self.db,
            )

        self.assertEqual(context.exception.status_code, 500)
        self.assertIn(
            'Database error: Unexpected error',
            context.exception.detail,
        )
        self.db.rollback.assert_awaited()

    async def test_update_group_general_exception(self) -> None:
        """
        Test updating a group raises HTTPException on general database error.

        Ensures that an HTTPException with status 500 is raised if a
        general database error occurs during group update.
        """
        self.db.commit = AsyncMock(side_effect=Exception('Unexpected error'))
        self.db.rollback = AsyncMock()

        with self.assertRaises(HTTPException) as context:
            await group_services.update_group(
                grp=self.grp,
                new_name='Updated Group',
                new_uniform_number='88889999',
                db=self.db,
            )

        self.assertEqual(context.exception.status_code, 500)
        self.assertIn(
            'Database error: Unexpected error',
            context.exception.detail,
        )
        self.db.rollback.assert_awaited()


if __name__ == '__main__':
    unittest.main()

'''
pytest --cov=examples.db_management.services.group_services\
    --cov-report=term-missing\
        tests/examples/db_management/services/group_services_test.py
'''
