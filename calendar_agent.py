import json
import os

from dotenv import load_dotenv
from groq import Groq

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

CALENDAR_FILE = "calendar.json"


def load_events():
    if not os.path.exists(CALENDAR_FILE):
        return []
    with open(CALENDAR_FILE, "r") as f:
        return json.load(f)


def save_events(events):
    with open(CALENDAR_FILE, "w") as f:
        json.dump(events, f, indent=2)


def extract_date(request):
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": "Extract only the date/time mentioned in this request. Respond with ONLY the date/time phrase (e.g. 'tomorrow', 'friday', 'next monday 5pm'). If none mentioned, respond 'unspecified'.",
            },
            {"role": "user", "content": request},
        ],
    )
    return response.choices[0].message.content.strip()


def handle_calendar(request):
    events = load_events()
    date = extract_date(request)
    events.append({"text": request, "date": date})
    save_events(events)
    return f"[calendar_agent] Saved event: '{request}' (date: {date})"
