import os
import base64
import re
from email.utils import parseaddr

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from config import GMAIL_SCOPES, CREDENTIALS_FILE, TOKEN_FILE, BODY_SNIPPET_LENGTH


def get_gmail_service():
    """Authenticate and return a Gmail API service instance."""
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, GMAIL_SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, GMAIL_SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())
    return build("gmail", "v1", credentials=creds)


def list_messages(service, query, max_results=100):
    """Fetch message IDs matching the query, with pagination."""
    messages = []
    result = service.users().messages().list(
        userId="me", q=query, maxResults=min(max_results, 500)
    ).execute()
    messages.extend(result.get("messages", []))

    while "nextPageToken" in result and len(messages) < max_results:
        result = service.users().messages().list(
            userId="me",
            q=query,
            maxResults=min(max_results - len(messages), 500),
            pageToken=result["nextPageToken"],
        ).execute()
        messages.extend(result.get("messages", []))

    return messages[:max_results]


def _get_header(headers, name):
    """Extract a header value by name."""
    for h in headers:
        if h["name"].lower() == name.lower():
            return h["value"]
    return ""


def _decode_body(payload):
    """Extract plain text body from message payload."""
    # Direct body
    if payload.get("mimeType") == "text/plain" and payload.get("body", {}).get("data"):
        return base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="replace")

    # Multipart — search parts recursively
    for part in payload.get("parts", []):
        if part.get("mimeType") == "text/plain" and part.get("body", {}).get("data"):
            return base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="replace")
        # Nested multipart
        for subpart in part.get("parts", []):
            if subpart.get("mimeType") == "text/plain" and subpart.get("body", {}).get("data"):
                return base64.urlsafe_b64decode(subpart["body"]["data"]).decode("utf-8", errors="replace")

    return None


def get_message_details(service, msg_id):
    """Fetch a single message and extract from, subject, and body snippet."""
    msg = service.users().messages().get(
        userId="me", id=msg_id, format="full"
    ).execute()

    headers = msg.get("payload", {}).get("headers", [])
    sender = _get_header(headers, "From")
    subject = _get_header(headers, "Subject")

    # Try to get plain text body, fall back to Gmail snippet
    body = _decode_body(msg.get("payload", {}))
    if body:
        # Strip excessive whitespace
        body = re.sub(r"\s+", " ", body).strip()[:BODY_SNIPPET_LENGTH]
    else:
        body = msg.get("snippet", "")

    return {
        "id": msg_id,
        "from": sender,
        "subject": subject,
        "body_snippet": body,
    }


def ensure_label(service, label_name):
    """Get or create a Gmail label, return its ID."""
    results = service.users().labels().list(userId="me").execute()
    for label in results.get("labels", []):
        if label["name"] == label_name:
            return label["id"]

    # Create the label
    label_body = {
        "name": label_name,
        "labelListVisibility": "labelShow",
        "messageListVisibility": "show",
    }
    created = service.users().labels().create(userId="me", body=label_body).execute()
    print(f"Created Gmail label: {label_name}")
    return created["id"]


def trash_messages(service, msg_ids):
    """Move messages to trash."""
    for msg_id in msg_ids:
        service.users().messages().trash(userId="me", id=msg_id).execute()


def label_messages(service, msg_ids, label_id):
    """Apply a label to messages using batch modify."""
    if not msg_ids:
        return
    service.users().messages().batchModify(
        userId="me",
        body={"ids": msg_ids, "addLabelIds": [label_id]},
    ).execute()
