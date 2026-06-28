import os
import json
import gspread
from google.oauth2.service_account import Credentials

scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

if os.path.exists("service_account.json"):

    creds = Credentials.from_service_account_file(
        "service_account.json",
        scopes=scope
    )

else:

    service_account_info = json.loads(
            os.environ["GOOGLE_SERVICE_ACCOUNT"]
    )

    creds = Credentials.from_service_account_info(
        service_account_info,
        scopes=scope
    )

client = gspread.authorize(creds)

# スプレッドシートのキーを指定して開く
spreadsheet = client.open_by_key("1QndFPPD7_-0iFRQe_37oALHeDlJz_kvfvzrZZ1rSlAU")