import json
import os
from typing import Any

from google.oauth2 import service_account
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def _service():
    raw = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON") or os.environ.get("GSC_SERVICE_ACCOUNT_JSON")
    if not raw:
        raise RuntimeError(
            "Set GOOGLE_SERVICE_ACCOUNT_JSON to the JSON string or a path to the service-account key file."
        )
    info = json.loads(raw) if raw.strip().startswith("{") else json.load(open(raw))
    creds = service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
    return build("sheets", "v4", credentials=creds, cache_discovery=False)


def read_range(spreadsheet_id: str, a1_range: str) -> list[list[Any]]:
    svc = _service()
    resp = svc.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=a1_range).execute()
    return resp.get("values", [])


def write_range(spreadsheet_id: str, a1_range: str, values: list[list[Any]]) -> dict:
    svc = _service()
    return (
        svc.spreadsheets()
        .values()
        .update(
            spreadsheetId=spreadsheet_id,
            range=a1_range,
            valueInputOption="RAW",
            body={"values": values},
        )
        .execute()
    )


def sheet_metadata(spreadsheet_id: str) -> dict:
    svc = _service()
    return (
        svc.spreadsheets()
        .get(spreadsheetId=spreadsheet_id, fields="properties.title,sheets.properties")
        .execute()
    )


def service_account_email() -> str | None:
    raw = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON") or os.environ.get("GSC_SERVICE_ACCOUNT_JSON")
    if not raw:
        return None
    info = json.loads(raw) if raw.strip().startswith("{") else json.load(open(raw))
    return info.get("client_email")
