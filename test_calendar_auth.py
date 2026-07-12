from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/calendar"]

def main():
    flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
    creds = flow.run_local_server(port=0)

    service = build("calendar", "v3", credentials=creds)
    calendar_list = service.calendarList().list().execute()

    print("Connected! Your calendars:")
    for cal in calendar_list.get("items", []):
        print(" -", cal["summary"])

    with open("token.json", "w") as token:
        token.write(creds.to_json())

if __name__ == "__main__":
    main()
