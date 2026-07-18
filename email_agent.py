import json
import os
import base64
from email.mime.text import MIMEText
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from config import client

EMAIL_FILE = "emails.json"
CONTACTS_FILE = "contacts.json"
SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/gmail.send"
]

def get_gmail_service():
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
        creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    return build("gmail", "v1", credentials=creds)

def load_contacts():
    if not os.path.exists(CONTACTS_FILE):
        return {}
    with open(CONTACTS_FILE, "r") as f:
        return json.load(f)

def resolve_email(name):
    contacts = load_contacts()
    return contacts.get(name.lower().strip())

def send_gmail(to_email, subject, body_text):
    try:
        service = get_gmail_service()
        message = MIMEText(body_text)
        message["to"] = to_email
        message["subject"] = subject
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

        sent = service.users().messages().send(
            userId="me",
            body={"raw": raw}
        ).execute()
        return sent.get("id")
    except Exception as e:
        print(f"[error] Gmail send failed: {e}")
        return None

def create_gmail_draft(to_email, subject, body_text):
    try:
        service = get_gmail_service()
        message = MIMEText(body_text)
        message["to"] = to_email or ""
        message["subject"] = subject
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

        draft = service.users().drafts().create(
            userId="me",
            body={"message": {"raw": raw}}
        ).execute()
        return draft.get("id")
    except Exception as e:
        print(f"[error] Gmail draft creation failed: {e}")
        return None

def update_gmail_draft(draft_id, subject, body_text):
    try:
        service = get_gmail_service()
        message = MIMEText(body_text)
        message["to"] = ""
        message["subject"] = subject
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

        updated = service.users().drafts().update(
            userId="me",
            id=draft_id,
            body={"message": {"raw": raw}}
        ).execute()
        return updated.get("id")
    except Exception as e:
        print(f"[error] Gmail draft update failed: {e}")
        return None

def load_emails():
    if not os.path.exists(EMAIL_FILE):
        return []
    with open(EMAIL_FILE, "r") as f:
        return json.load(f)

def save_emails(emails):
    with open(EMAIL_FILE, "w") as f:
        json.dump(emails, f, indent=2)

def extract_recipient(request):
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "Extract only the recipient (who this message is for/to) from this request. Respond with ONLY the recipient name/role (e.g. 'mom', 'professor', 'team'). If none mentioned, respond 'unspecified'."},
            {"role": "user", "content": request}
        ]
    )
    return response.choices[0].message.content.strip()

def handle_email(request, update_draft_id=None):
    emails = load_emails()
    to = extract_recipient(request)
    real_email = resolve_email(to)

    if update_draft_id:
        draft_id = update_gmail_draft(update_draft_id, subject=f"Message for {to}", body_text=request)
        for e in emails:
            if e.get("gmail_draft_id") == update_draft_id:
                e["text"] = request
                e["to"] = to
        save_emails(emails)
        if draft_id:
            return f"[email_agent] Updated draft: '{request}' (to: {to})"
        else:
            return f"[email_agent] Tried to update draft but failed."

    emails.append({"text": request, "to": to})

    if real_email:
        msg_id = send_gmail(real_email, subject=f"Message from ops-agent", body_text=request)
        if msg_id:
            emails[-1]["sent"] = True
            save_emails(emails)
            return f"[email_agent] Real email SENT to {to} ({real_email})"
        else:
            save_emails(emails)
            return f"[email_agent] Tried to send to {to} but failed."
    else:
        draft_id = create_gmail_draft(None, subject=f"Message for {to}", body_text=request)
        if draft_id:
            emails[-1]["gmail_draft_id"] = draft_id
            save_emails(emails)
            return f"[email_agent] No known email for '{to}' — saved as draft instead (id: {draft_id})"
        else:
            save_emails(emails)
            return f"[email_agent] Saved locally: '{request}' (to: {to}) — no email on file, and draft creation failed"
