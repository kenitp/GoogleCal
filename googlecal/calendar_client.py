from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import Resource, build

SCOPES = ["https://www.googleapis.com/auth/calendar"]


def build_calendar_service(credentials_path: Path, token_path: Path) -> Resource:
    creds: Credentials | None = None

    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    elif creds is None or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(str(credentials_path), SCOPES)
        creds = flow.run_local_server(port=0)

    token_path.write_text(creds.to_json(), encoding="utf-8")
    return build("calendar", "v3", credentials=creds)


def find_calendar_id(service: Resource, calendar_name: str) -> str:
    page_token: str | None = None
    while True:
        response = service.calendarList().list(pageToken=page_token).execute()
        for item in response.get("items", []):
            if item.get("summary") == calendar_name:
                return str(item["id"])
        page_token = response.get("nextPageToken")
        if not page_token:
            break

    raise ValueError(f"カレンダー '{calendar_name}' が見つかりません。")


def get_calendar_summary(service: Resource, calendar_id: str) -> str:
    calendar = service.calendars().get(calendarId=calendar_id).execute()
    summary = calendar.get("summary")
    if not summary:
        raise ValueError(f"カレンダー '{calendar_id}' の名前を取得できません。")
    return str(summary)


def event_exists(service: Resource, calendar_id: str, payload: dict[str, Any]) -> bool:
    time_min, time_max = _event_range(payload)
    response = (
        service.events()
        .list(
            calendarId=calendar_id,
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )

    for item in response.get("items", []):
        if _same_event(item, payload):
            return True
    return False


def create_event(service: Resource, calendar_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    return service.events().insert(calendarId=calendar_id, body=payload).execute()


def _event_range(payload: dict[str, Any]) -> tuple[str, str]:
    if "date" in payload["start"]:
        start_date = date.fromisoformat(payload["start"]["date"])
        end_date = date.fromisoformat(payload["end"]["date"])
        start_at = datetime.combine(start_date, datetime.min.time(), tzinfo=timezone.utc)
        end_at = datetime.combine(end_date, datetime.min.time(), tzinfo=timezone.utc)
        return _as_utc_z(start_at), _as_utc_z(end_at)

    start_at = _normalize_datetime(payload["start"])
    end_at = _normalize_datetime(payload["end"])
    return _as_utc_z(start_at - timedelta(minutes=1)), _as_utc_z(end_at + timedelta(minutes=1))


def _same_event(existing: dict[str, Any], payload: dict[str, Any]) -> bool:
    return _event_signature(existing) == _event_signature(payload)


def _as_utc_z(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _event_signature(event: dict[str, Any]) -> tuple[Any, ...]:
    return (
        event.get("summary"),
        event.get("location", ""),
        _normalize_event_boundary(event.get("start", {})),
        _normalize_event_boundary(event.get("end", {})),
    )


def _normalize_event_boundary(boundary: dict[str, Any]) -> tuple[str, Any]:
    if "date" in boundary:
        return ("date", date.fromisoformat(boundary["date"]))
    return ("dateTime", _normalize_datetime(boundary))


def _normalize_datetime(boundary: dict[str, Any]) -> datetime:
    value = datetime.fromisoformat(boundary["dateTime"])
    if value.tzinfo is not None:
        return value.astimezone(timezone.utc)

    timezone_name = boundary.get("timeZone", "UTC")
    return value.replace(tzinfo=ZoneInfo(timezone_name)).astimezone(timezone.utc)
