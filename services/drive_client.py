import json
import os
import io
from functools import lru_cache
from typing import Optional

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

_SCOPES = ["https://www.googleapis.com/auth/drive"]


def _build_service():
    sa_json = os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"]
    info = json.loads(sa_json)
    creds = service_account.Credentials.from_service_account_info(info, scopes=_SCOPES)
    return build("drive", "v3", credentials=creds)


@lru_cache(maxsize=1)
def get_drive_service():
    return _build_service()


def ensure_folder(parent_id: str, name: str) -> str:
    svc = get_drive_service()
    q = (
        f"'{parent_id}' in parents and name='{name}' "
        f"and mimeType='application/vnd.google-apps.folder' and trashed=false"
    )
    results = svc.files().list(q=q, fields="files(id)").execute()
    files = results.get("files", [])
    if files:
        return files[0]["id"]
    meta = {
        "name": name,
        "mimeType": "application/vnd.google-apps.folder",
        "parents": [parent_id],
    }
    folder = svc.files().create(body=meta, fields="id").execute()
    return folder["id"]


def upload_file(local_path: str, filename: str, parent_folder_id: str) -> str:
    svc = get_drive_service()
    media = MediaFileUpload(local_path, resumable=True)
    meta = {"name": filename, "parents": [parent_folder_id]}
    f = svc.files().create(body=meta, media_body=media, fields="id").execute()
    return f["id"]


def download_file(file_id: str, local_path: str) -> None:
    svc = get_drive_service()
    request = svc.files().get_media(fileId=file_id)
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    with open(local_path, "wb") as fh:
        downloader = MediaIoBaseDownload(fh, request, chunksize=8 * 1024 * 1024)
        done = False
        while not done:
            _, done = downloader.next_chunk()


def write_json(data: dict, filename: str, parent_folder_id: str) -> str:
    svc = get_drive_service()
    content = json.dumps(data, ensure_ascii=False, default=str).encode("utf-8")
    media = MediaIoBaseDownload.__class__  # placeholder — use MediaInMemoryUpload
    from googleapiclient.http import MediaIoBaseUpload
    buf = io.BytesIO(content)
    media = MediaIoBaseUpload(buf, mimetype="application/json")
    meta = {"name": filename, "parents": [parent_folder_id]}
    f = svc.files().create(body=meta, media_body=media, fields="id").execute()
    return f["id"]


def read_json(file_id: str) -> dict:
    svc = get_drive_service()
    content = svc.files().get_media(fileId=file_id).execute()
    return json.loads(content)


def find_file(filename: str, parent_folder_id: str) -> Optional[str]:
    svc = get_drive_service()
    q = f"'{parent_folder_id}' in parents and name='{filename}' and trashed=false"
    results = svc.files().list(q=q, fields="files(id)", pageSize=1).execute()
    files = results.get("files", [])
    return files[0]["id"] if files else None


def get_web_view_link(file_id: str) -> str:
    svc = get_drive_service()
    f = svc.files().get(fileId=file_id, fields="webViewLink").execute()
    return f.get("webViewLink", "")
