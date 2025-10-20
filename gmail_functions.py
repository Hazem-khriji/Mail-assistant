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


def get_unread_emails(max_results = 10):
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


def read_email(identifier: str) :
    """
    Reads an email by position number, email ID, sender name, or subject keyword.

    Use this when user wants to read a specific email. Works with:
    - Position: "Read email 1", "Show me the third email" → identifier="1" or "3"
    - Sender: "Read email from boss" → identifier="boss"
    - Subject: "Read the Q4 report email" → identifier="Q4 report"
    - Email ID: Direct Gmail message ID → identifier="18c2f3a5..."

    Args:
        identifier: Position number (1, 2, 3...), sender name, subject keyword, or email ID

    Returns:
        Full email content
    """
    service = get_gmail_service()

    if not service:
        return None

    try:
        # Get unread emails
        emails = get_unread_emails(max_results=10)

        if not emails:
            return "No unread emails found."

        matching_email = None

        # Strategy 1: Try as position number
        try:
            position = int(identifier)
            if 1 <= position <= len(emails):
                matching_email = emails[position - 1]
        except ValueError:
            pass

        # Strategy 2: Try as email ID (exact match)
        if not matching_email:
            for email in emails:
                if email['id'] == identifier:
                    matching_email = email
                    break

        # Strategy 3: Try as sender/subject search
        if not matching_email:
            identifier_lower = identifier.lower()
            for email in emails:
                sender = email['sender'].lower()
                subject = email['subject'].lower()

                if identifier_lower in sender or identifier_lower in subject:
                    matching_email = email
                    break

        # No match found
        if not matching_email:
            return f"No email found matching '{identifier}'. Try using position (1, 2, 3...) or keywords from sender/subject."

        # Get full body
        email_id = matching_email['id']
        body = get_email_body(email_id)

        # Format response
        result = f" Email Details :\n"
        result += f"From: {matching_email['sender']}\n"
        result += f"Subject: {matching_email['subject']}\n"
        result += f"Date: {matching_email.get('date', 'Unknown')}\n"
        result += f"Email ID: {email_id}\n"
        result += f"\n{'=' * 50}\n"
        result += f"CONTENT:\n{body}\n"
        result += f"{'=' * 50}"

        return result

    except Exception as e:
        return f"Error reading email: {str(e)}"


def mark_email_as_unread(message_id):
    """
    Marks an email as unread.

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
            body={'addLabelIds': ['UNREAD']}
        ).execute()

        print(f'Email {message_id} marked as unread.')
        return True

    except HttpError as error:
        print(f'An error occurred: {error}')
        return False


def get_email_from_sender(sender:str = None,max_results: int=1):
    """
    Reads an email by position number, email ID, sender name, or subject keyword.

    Use this when user wants to read a specific email from a specific sender .
    Args:
        sender: Position number (1, 2, 3...), sender name, subject keyword, or email ID
        max_results: Maximum number of emails to return

    Returns:
        Full email content
    """
    service = get_gmail_service()
    if not service:
        return []
    try:
        query = f"from:{sender}"
        messages= service.users().messages().list(
            userId='me',
            q=query,
            maxResults=max_results
        ).execute()

        messages= messages.get('messages',[])
        if not messages:
            print(f"No messages found from {sender}.")
            return []

        emails=[]

        for message in messages:
            msg=service.users().messages().get(
                userId='me',
                id=message['id'],
                format= 'full'
            ).execute()
            headers = msg['payload']['headers']
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
            sender_header = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
            date = next((h['value'] for h in headers if h['name'] == 'Date'), 'Unknown')

            # Get snippet
            snippet = msg.get('snippet', '')

            # Check if read/unread
            labels = msg.get('labelIds', [])
            is_unread = 'UNREAD' in labels

            email_data = {
                'id': message['id'],
                'subject': subject,
                'sender': sender_header,
                'date': date,
                'snippet': snippet,
                'is_unread': is_unread
            }

            emails.append(email_data)
        return emails

    except Exception as e:
        return f"Error reading email: {str(e)}"


#def check_urgency(body: str = None):
    #We need to either finetune an llm for classifying the email or use an llm with zero-shot/few-shot prompting
    #the work will be postponed at the moment here to make further advancements with the project
    #the agent can actually do this job for the moment thanks to the memory



