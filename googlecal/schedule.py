from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class EventInput:
    title: str
    event_date: date
    location: str | None
    all_day: bool
    start_time: time | None
    end_time: time | None
    timezone: str


@dataclass(frozen=True)
class ScheduleInput:
    calendar_name: str
    events: list[EventInput]


def load_schedule(schedule_path: Path) -> ScheduleInput:
    raw = yaml.safe_load(schedule_path.read_text(encoding="utf-8")) or {}
    defaults = raw.get("defaults", {})
    events = raw.get("events", [])

    calendar_name = _parse_required_text(defaults.get("calendar_name"), "defaults.calendar_name")
    default_title = _parse_required_text(defaults.get("title"), "defaults.title")
    default_location = defaults.get("location")
    default_timezone = _parse_required_text(defaults.get("timezone"), "defaults.timezone")
    default_all_day = bool(defaults.get("all_day", False))
    default_start_time = _parse_optional_time(defaults.get("start_time"))
    default_end_time = _parse_optional_time(defaults.get("end_time"))

    normalized_events: list[EventInput] = []
    for event in events:
        if not isinstance(event, dict):
            raise ValueError("events には辞書形式の要素を指定してください。")

        event_date = _parse_date(event.get("date"))
        all_day = bool(event.get("all_day", default_all_day))
        start_time = None if all_day else _parse_optional_time(event.get("start_time"), default_start_time)
        end_time = None if all_day else _parse_optional_time(event.get("end_time"), default_end_time)

        if not all_day and (start_time is None or end_time is None):
            raise ValueError(f"{event_date} の開始時刻または終了時刻が不足しています。")

        normalized_events.append(
            EventInput(
                title=str(event.get("title", default_title)),
                event_date=event_date,
                location=event.get("location", default_location),
                all_day=all_day,
                start_time=start_time,
                end_time=end_time,
                timezone=str(event.get("timezone", default_timezone)),
            )
        )

    return ScheduleInput(calendar_name=calendar_name, events=normalized_events)


def build_event_body(event: EventInput) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "summary": event.title,
    }

    if event.location:
        payload["location"] = event.location

    if event.all_day:
        next_day = event.event_date.fromordinal(event.event_date.toordinal() + 1)
        payload["start"] = {"date": event.event_date.isoformat()}
        payload["end"] = {"date": next_day.isoformat()}
        return payload

    start_at = datetime.combine(event.event_date, event.start_time)
    end_at = datetime.combine(event.event_date, event.end_time)
    payload["start"] = {
        "dateTime": start_at.isoformat(),
        "timeZone": event.timezone,
    }
    payload["end"] = {
        "dateTime": end_at.isoformat(),
        "timeZone": event.timezone,
    }
    return payload


def _parse_date(value: Any) -> date:
    if isinstance(value, date):
        return value
    if not value:
        raise ValueError("各イベントに date を指定してください。")
    return date.fromisoformat(str(value))


def _parse_optional_time(value: Any, fallback: time | None = None) -> time | None:
    if value is None:
        return fallback
    if isinstance(value, time):
        return value
    return time.fromisoformat(str(value))


def _parse_required_text(value: Any, field_name: str) -> str:
    if value is None:
        raise ValueError(f"{field_name} を指定してください。")

    text = str(value).strip()
    if not text:
        raise ValueError(f"{field_name} を空にできません。")
    return text
