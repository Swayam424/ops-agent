import datetime
from datetime import datetime as dt, timedelta, timezone
import json
import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from config import client

CALENDAR_FILE = "calendar.json"
SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/gmail.compose"
]

IST = timezone(timedelta(hours=5, minutes=30))

def get_calendar_service():
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
        creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    return build("calendar", "v3", credentials=creds)

def create_google_event(text, start_dt):
    try:
        service = get_calendar_service()
        end_dt = start_dt + datetime.timedelta(hours=1)
        event = {
            "summary": text,
            "start": {"dateTime": start_dt.isoformat(), "timeZone": "Asia/Kolkata"},
            "end": {"dateTime": end_dt.isoformat(), "timeZone": "Asia/Kolkata"},
        }
        created = service.events().insert(calendarId="primary", body=event).execute()
        return created.get("id"), created.get("htmlLink")
    except Exception as e:
        print(f"[error] Google Calendar event creation failed: {e}")
        return None, None

def update_google_event(event_id, text=None, start_dt=None):
    try:
        service = get_calendar_service()
        event = service.events().get(calendarId="primary", eventId=event_id).execute()

        if text:
            event["summary"] = text
        if start_dt:
            end_dt = start_dt + datetime.timedelta(hours=1)
            event["start"] = {"dateTime": start_dt.isoformat(), "timeZone": "Asia/Kolkata"}
            event["end"] = {"dateTime": end_dt.isoformat(), "timeZone": "Asia/Kolkata"}

        updated = service.events().update(calendarId="primary", eventId=event_id, body=event).execute()
        return updated.get("htmlLink")
    except Exception as e:
        print(f"[error] Google Calendar event update failed: {e}")
        return None

def find_free_slot(duration_minutes=60, search_days=7, work_start_hour=9, work_end_hour=20):
    try:
        service = get_calendar_service()
        now = dt.now(IST)
        time_min = now.isoformat()
        time_max = (now + timedelta(days=search_days)).isoformat()

        body = {
            "timeMin": time_min,
            "timeMax": time_max,
            "timeZone": "Asia/Kolkata",
            "items": [{"id": "primary"}]
        }
        result = service.freebusy().query(body=body).execute()
        busy_periods = result["calendars"]["primary"]["busy"]

        busy_ranges = [
            (dt.fromisoformat(b["start"]), dt.fromisoformat(b["end"]))
            for b in busy_periods
        ]

        candidate = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        end_search = now + timedelta(days=search_days)

        while candidate < end_search:
            if candidate.hour < work_start_hour:
                candidate = candidate.replace(hour=work_start_hour)
            if candidate.hour >= work_end_hour:
                candidate = (candidate + timedelta(days=1)).replace(hour=work_start_hour)
                continue

            slot_end = candidate + timedelta(minutes=duration_minutes)
            overlaps = any(
                candidate < b_end and slot_end > b_start
                for b_start, b_end in busy_ranges
            )
            if not overlaps:
                return candidate

            candidate += timedelta(minutes=30)

        return None
    except Exception as e:
        print(f"[error] Freebusy lookup failed: {e}")
        return None

def load_events():
    if not os.path.exists(CALENDAR_FILE):
        return []
    with open(CALENDAR_FILE, "r") as f:
        return json.load(f)

def save_events(events):
    with open(CALENDAR_FILE, "w") as f:
        json.dump(events, f, indent=2)

def extract_datetime(request):
    now = dt.now()
    today_str = now.strftime("%A, %Y-%m-%d %H:%M")
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": (
                f"Current date/time: {today_str}. "
                "The user will describe an event. Figure out what real calendar date/time they mean, "
                "even if they use relative words like 'tomorrow', 'friday', 'next week', or a specific time like '3pm'. "
                "IMPORTANT: when the user names a weekday (e.g. 'monday', 'friday') without saying 'next', "
                "always interpret it as the UPCOMING occurrence of that weekday — if today IS that weekday, "
                "assume next week's occurrence, not today. Never resolve a named weekday to a date earlier than "
                "or equal to today unless the user explicitly says 'today'. "
                "Respond with ONLY an ISO 8601 datetime in this exact format: YYYY-MM-DDTHH:MM:SS — nothing else. "
                "If no date is mentioned in the request at all, respond with exactly: unspecified\n\n"
                "Example: if today is Monday 2026-07-13, and the user says 'friday at 3pm', "
                "respond: 2026-07-17T15:00:00\n"
                "Example: if today is Monday 2026-07-13, and the user says 'monday at 10am', "
                "respond: 2026-07-20T10:00:00 (next Monday, since today is already Monday)\n"
                "Example: if the user says 'buy milk', respond: unspecified"
            )},
            {"role": "user", "content": request}
        ]
    )
    return response.choices[0].message.content.strip()

def handle_calendar(request, update_event_id=None, auto_find_slot=False):
    events = load_events()

    if auto_find_slot:
        start_dt = find_free_slot()
        if not start_dt:
            return f"[calendar_agent] Couldn't find a free slot for: '{request}'"
        iso_datetime = start_dt.isoformat()
    else:
        iso_datetime = extract_datetime(request)
        if iso_datetime == "unspecified":
            start_dt = dt.now() + timedelta(hours=1)
        else:
            try:
                start_dt = dt.fromisoformat(iso_datetime)
            except ValueError:
                start_dt = dt.now() + timedelta(hours=1)

    if update_event_id:
        link = update_google_event(update_event_id, text=request, start_dt=start_dt)
        for e in events:
            if e.get("google_event_id") == update_event_id:
                e["text"] = request
                e["date"] = iso_datetime
        save_events(events)
        if link:
            return f"[calendar_agent] Updated event: '{request}' (when: {start_dt.strftime('%A %b %d, %I:%M %p')})\nUpdated: {link}"
        else:
            return f"[calendar_agent] Tried to update event but failed."

    event_id, link = create_google_event(request, start_dt)
    events.append({"text": request, "date": iso_datetime, "google_event_id": event_id})
    save_events(events)

    if link:
        return f"[calendar_agent] Saved event: '{request}' (when: {start_dt.strftime('%A %b %d, %I:%M %p')})\nReal event created: {link}"
    else:
        return f"[calendar_agent] Saved event: '{request}' (when: {start_dt.strftime('%A %b %d, %I:%M %p')}) — but Google Calendar sync failed"
