from datetime import datetime
import os
import mimetypes
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle
from app.config import settings

SCOPES = ["https://www.googleapis.com/auth/drive", "https://www.googleapis.com/auth/spreadsheets"]

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CREDENTIALS_PATH = os.path.join(BASE_DIR, settings.google_credentials)
TOKEN_PATH = os.path.join(BASE_DIR, "token.pickle")


def get_services():
    creds = None

    # Загружаем токен, если он есть
    if os.path.exists(TOKEN_PATH):
        with open(TOKEN_PATH, "rb") as token:
            creds = pickle.load(token)

    # Если токен недействителен или отсутствует, делаем OAuth flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        # Сохраняем токен
        with open(TOKEN_PATH, "wb") as token:
            pickle.dump(creds, token)

    drive_service = build("drive", "v3", credentials=creds)
    sheets_service = build("sheets", "v4", credentials=creds)
    return drive_service, sheets_service


def upload_to_drive(file_path: str, filename: str) -> str:
    drive_service, _ = get_services()

    mime_type, _ = mimetypes.guess_type(file_path)
    file_metadata = {"name": filename}
    media = MediaFileUpload(file_path, mimetype=mime_type)

    file = drive_service.files().create(
        body=file_metadata,
        media_body=media,
        fields="id"
    ).execute()
    file_id = file["id"]

    # Делаем доступным по ссылке
    drive_service.permissions().create(
        fileId=file_id, body={"role": "reader", "type": "anyone"}
    ).execute()

    return f"https://drive.google.com/uc?id={file_id}"


def insert_image_and_update_status(rows: list[str], image_url: str):
    _, sheets_service = get_services()

    today = datetime.now().strftime("%d.%m.%Y")

    requests = []
    for row in rows:
        row = row.strip()
        if not row.isdigit():
            continue

        # Фото вставляем в колонку J
        formula = f'=IMAGE("{image_url}")'
        requests.append({
            "range": f"J{row}",
            "values": [[formula]]
        })

        # Статус в колонку K
        requests.append({
            "range": f"L{row}",
            "values": [["На складе в Китае"]]
        })

        # Дата в колонку L
        requests.append({
            "range": f"M{row}",
            "values": [[today]]
        })

    body = {
        "valueInputOption": "USER_ENTERED",
        "data": requests
    }

    sheets_service.spreadsheets().values().batchUpdate(
        spreadsheetId=settings.spreadsheet_id,
        body=body
    ).execute()