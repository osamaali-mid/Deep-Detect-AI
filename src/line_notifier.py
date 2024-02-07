import requests
from datetime import datetime

def send_line_notification(token: str, message: str) -> int:
    """
    Send a notification message to a LINE user using LINE Notify API.

    Args:
        token (str): The authorisation token for LINE Notify.
        message (str): The message to be sent to the user.

    Returns:
        int: The HTTP status code returned by the LINE Notify API.

    Note:
        You must obtain a valid LINE Notify token by registering a LINE Notify service.
        The token must be kept confidential and not hardcoded in production code.

    Example:
        >>> line_token = 'your_line_notify_token'
        >>> message = 'Hello, this is a test message.'
        >>> status = send_line_notification(line_token, message)
        >>> print(status)
        200
    """
    # Define the headers for the HTTP request to LINE Notify API
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    # Define the payload for the POST request, including the message
    payload = {'message': message}
    
    # Send the POST request to the LINE Notify API and capture the response
    response = requests.post(
        'https://notify-api.line.me/api/notify',
        headers=headers,
        data=payload
    )
    
    # Return the HTTP status code from the response
    return response.status_code

# This block is executed when the script is run directly, not when imported
if __name__ == '__main__':
    # Example usage of the send_line_notification function:
    
    # Replace 'YOUR_LINE_NOTIFY_TOKEN' with your actual LINE Notify token
    line_token = 'YOUR_LINE_NOTIFY_TOKEN'
    
    # Get the current time and format it as a string
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Create a message string with the current time and a warning message
    message = f'[{current_time}] Warning: Someone is not wearing a helmet!'
    
    # Send the notification message using the LINE Notify API
    status = send_line_notification(line_token, message)
    
    # Print the status code to the console to confirm the message was sent
    print(f'Notification sent, status code: {status}')