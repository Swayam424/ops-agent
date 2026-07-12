import json
import os
import base64
from email.mime.text import MIMEText
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from config import client

EMAIL_FILE = "emails.json"
SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/gmail.compose"
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

def create_gmail_draft(to_name, subject, body_text):
    try:
        service = get_gmail_service()
        message = MIMEText(body_text)
        message["to"] = ""  # left blank since we don't have a real email yet
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

def handle_email(request):
    emails = load_emails()
    to = extract_recipient(request)
    emails.append({"text": request, "to": to})
    save_emails(emails)

    draft_id = create_gmail_draft(to, subject=f"Message for {to}", body_text=request)
    if draft_id:
        return f"[email_agent] Saved draft: '{request}' (to: {to})\nReal Gmail draft created (id: {draft_id}) — open Gmail Drafts to review/send"
    else:
        return f"[email_agent] Saved draft: '{request}' (to: {to}) — but Gmail draft creation failed"
