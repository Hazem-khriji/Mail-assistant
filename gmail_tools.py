
"""
LangChain tools for the email agent.
Each tool wraps a Gmail function and formats output for the agent.
"""

from langchain.tools import tool
from gmail_functions import get_unread_emails, get_email_body, mark_email_as_read

@tool()
def get_unread_mail_tool(max_results :int =10):
    """
    Fetches unread emails from Gmail inbox.

    Use this tool when the user asks about:
    - Unread emails
    - New messages
    - Checking their inbox
    - Recent emails that haven't been read

    Args:
        max_results: Maximum number of emails to return (default: 10, max: 100)

    Returns:
        A formatted string listing unread emails with sender, subject, preview, and email ID
    """
    try:
        # Validate input
        if max_results < 1:
            return "Error: max_results must be at least 1"

        if max_results > 20:
            max_results = 20
            print("Limiting to 20 emails")

        emails = get_unread_emails(max_results)
        if not emails :
            return "No unread emails found. Your inbox is clear"
        else:
            result = f"found {len(emails)} unread emails"
            for i, email in enumerate(emails, 1):
                result += f"{i}. From: {email['sender']}\n"
                result += f"   Subject: {email['subject']}\n"
                result += f"   Preview: {email['snippet'][:100]}...\n"
                result += f"   Email ID: {email['id']}\n\n"

            return result
    except Exception as e:
        return "Error fetching emails : " + str(e)



@tool()
def get_email_body_tool(message_id: str):
    """
    Gets the full body content of a specific email.

    Use this tool when the user wants to:
    - Read the full content of an email
    - See the complete message (not just preview)
    - Get details about a specific email

    Args:
        message_id: The Gmail message ID (obtained from get_unread_emails_tool)

    Returns:
        The full text content of the email
    """
    try:
        if not message_id:
            return "Error: message_id must be provided"
        else:
            body = get_email_body(message_id)
            if not body:
                return f"Error: couldn't retrieve body of email ID:  {message_id}"
            else:
                return f"email body: \n\n{body}"

    except Exception as e:
        return "Error reading email : " + str(e)



@tool()
def mark_email_as_read_tool(message_id: str):
    """
    Marks an email as read in Gmail.
    Use this tool when the user wants to:
    - Mark an email as read
    - Mark as seen
    - Remove the unread status
    - Clear the unread indicator

    Args
        message_id: The Gmail message ID to mark as read
    Returns:
        Confirmation message indicating success or failure
    """

    try :
        if not message_id:
            return "Error: message_id must be provided"
        else:
            result=mark_email_as_read(message_id)
            if not result:
                return "Error: couldn't mark email as read."
            else:
                return f"Email has been marked as read."
    except Exception as e:
        return "Error marking email as read : " + str(e)

gmail_tools =[get_unread_mail_tool, get_email_body_tool, mark_email_as_read_tool]