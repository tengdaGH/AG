
import os.path
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/calendar.readonly", "https://www.googleapis.com/auth/userinfo.email"]

def main():
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    service = build("oauth2", "v2", credentials=creds)
    user_info = service.userinfo().get().execute()
    print(f"Authenticated as: {user_info.get('email')}")

if __name__ == "__main__":
    main()
