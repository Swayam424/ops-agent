import json
import os

CALENDAR_FILE = "calendar.json"


def load_events():
    if not os.path.exists(CALENDAR_FILE):
        return []
    with open(CALENDAR_FILE, "r") as f:
        return json.load(f)


def save_events(events):
    with open(CALENDAR_FILE, "w") as f:
        json.dump(events, f, indent=2)


def handle_calendar(request):
    events = load_events()
    events.append({"text": request, "date": "TBD"})
    save_events(events)
    return f"[calendar_agent] Saved event: '{request}' (total events: {len(events)})"
