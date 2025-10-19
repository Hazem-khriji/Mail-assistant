import os.path
import base64
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly',
          'https://www.googleapis.com/auth/gmail.send',
          'https://www.googleapis.com/auth/gmail.modify']

def get_gmail_service():
    """
    Authenticates and returns the Gmail API service.
    This handles the OAuth flow and token management.
    """
    creds = None

    # The file token.json stores the user's access and refresh tokens
    # It's created automatically when the authorization flow completes for the first time
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    # If there are no (valid) credentials available, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)

        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        # Build the Gmail API service
        service = build('gmail', 'v1', credentials=creds)
        return service
    except HttpError as error:
        print(f'An error occurred: {error}')
        return None


def get_unread_emails(max_results = 10) -> object:
    """
    Fetches unread emails from Gmail inbox.

    Args:
        max_results: Maximum number of emails to fetch (default: 10)

    Returns:
        List of email dictionaries containing id, subject, sender, snippet, and date
    """
    service = get_gmail_service()

    if not service:
        return []

    try:
        # Call the Gmail API to fetch unread messages
        results = service.users().messages().list(
            userId='me',
            labelIds=['INBOX', 'UNREAD'],
            maxResults=max_results
        ).execute()

        messages = results.get('messages', [])

        if not messages:
            print('No unread messages found.')
            return []

        emails = []

        # Fetch full details for each message
        for message in messages:
            msg = service.users().messages().get(
                userId='me',
                id=message['id'],
                format='full'
            ).execute()

            # Extract email headers
            headers = msg['payload']['headers']
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
            date = next((h['value'] for h in headers if h['name'] == 'Date'), 'Unknown')

            # Get email body/snippet
            snippet = msg.get('snippet', '')

            email_data = {
                'id': message['id'],
                'subject': subject,
                'sender': sender,
                'date': date,
                'snippet': snippet
            }

            emails.append(email_data)

        return emails

    except HttpError as error:
        print(f'An error occurred: {error}')
        return []


def get_email_body(message_id):
    """
    Gets the full body of an email by its ID.

    Args:
        message_id: The Gmail message ID

    Returns:
        String containing the email body
    """
    service = get_gmail_service()

    if not service:
        return None

    try:
        message = service.users().messages().get(
            userId='me',
            id=message_id,
            format='full'
        ).execute()

        # Function to decode email body
        def get_body(payload):
            if 'parts' in payload:
                for part in payload['parts']:
                    if part['mimeType'] == 'text/plain':
                        data = part['body'].get('data', '')
                        if data:
                            return base64.urlsafe_b64decode(data).decode('utf-8')
                    elif 'parts' in part:
                        return get_body(part)
            else:
                data = payload['body'].get('data', '')
                if data:
                    return base64.urlsafe_b64decode(data).decode('utf-8')
            return ''

        body = get_body(message['payload'])
        return body

    except HttpError as error:
        print(f'An error occurred: {error}')
        return None


def mark_email_as_read(message_id):
    """
    Marks an email as read.

    Args:
        message_id: The Gmail message ID

    Returns:
        True if successful, False otherwise
    """
    service = get_gmail_service()

    if not service:
        return False

    try:
        service.users().messages().modify(
            userId='me',
            id=message_id,
            body={'removeLabelIds': ['UNREAD']}
        ).execute()

        print(f'Email {message_id} marked as read.')
        return True

    except HttpError as error:
        print(f'An error occurred: {error}')
        return False



