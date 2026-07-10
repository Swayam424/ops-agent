import json
import os
from config import client

EMAIL_FILE = "emails.json"

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
    return f"[email_agent] Saved draft: '{request}' (to: {to})"
