import json
import os

EMAIL_FILE = "emails.json"


def load_emails():
    if not os.path.exists(EMAIL_FILE):
        return []
    with open(EMAIL_FILE, "r") as f:
        return json.load(f)


def save_emails(emails):
    with open(EMAIL_FILE, "w") as f:
        json.dump(emails, f, indent=2)


def handle_email(request):
    emails = load_emails()
    emails.append({"text": request, "to": "TBD"})
    save_emails(emails)
    return f"[email_agent] Saved draft: '{request}' (total drafts: {len(emails)})"
