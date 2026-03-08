from __future__ import annotations

import argparse
from pathlib import Path

from googlecal.calendar_client import build_calendar_service, create_event, event_exists, find_calendar_id
from googlecal.config import (
    DEFAULT_CREDENTIALS_PATH,
    DEFAULT_SCHEDULE_PATH,
    DEFAULT_TOKEN_PATH,
)
from googlecal.schedule import build_event_body, load_schedule


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Googleカレンダーへ予定を一括登録します。")
    parser.add_argument(
        "--schedule-file",
        type=Path,
        default=DEFAULT_SCHEDULE_PATH,
        help="予定を定義した YAML ファイルのパス",
    )
    parser.add_argument(
        "--credentials-file",
        type=Path,
        default=DEFAULT_CREDENTIALS_PATH,
        help="Google OAuth クライアントの credentials.json パス",
    )
    parser.add_argument(
        "--token-file",
        type=Path,
        default=DEFAULT_TOKEN_PATH,
        help="OAuth トークン保存先",
    )
    parser.add_argument(
        "--calendar-name",
        default=None,
        help="登録先カレンダー名。未指定なら YAML の defaults.calendar_name を使用",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Googleカレンダーへ登録せず内容だけ確認",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if not args.schedule_file.exists():
        raise FileNotFoundError(f"スケジュールファイルが見つかりません: {args.schedule_file}")
    if not args.credentials_file.exists():
        raise FileNotFoundError(
            "credentials.json が見つかりません。Google Cloud で OAuth クライアントを作成して配置してください: "
            f"{args.credentials_file}"
        )

    schedule = load_schedule(args.schedule_file)
    service = build_calendar_service(args.credentials_file, args.token_file)
    calendar_name = args.calendar_name or schedule.calendar_name
    calendar_id = find_calendar_id(service, calendar_name)

    created_count = 0
    skipped_count = 0

    for event in schedule.events:
        payload = build_event_body(event)
        if args.dry_run:
            print(f"[DRY RUN] {event.event_date} {payload['summary']}")
            continue

        if event_exists(service, calendar_id, payload):
            skipped_count += 1
            print(f"[SKIP] 既存予定あり: {event.event_date} {payload['summary']}")
            continue

        created = create_event(service, calendar_id, payload)
        created_count += 1
        print(f"[CREATE] {created['htmlLink']}")

    if args.dry_run:
        print(f"確認件数: {len(schedule.events)}")
        return

    print(f"登録完了: {created_count} 件")
    print(f"重複スキップ: {skipped_count} 件")


if __name__ == "__main__":
    main()
