# GoogleCal

Google カレンダーへ予定を一括登録するための Python スクリプトです。

## 前提

- Python 3.12 以上
- `uv`
- Google Cloud で有効化した `Google Calendar API`
- OAuth クライアントの `credentials.json`

## セットアップ

1. 依存関係をインストールします。

```bash
uv sync
```

2. スケジュールファイルを用意します。

```powershell
Copy-Item input/schecule.example.yaml input/schecule.yaml
```

3. `credentials.json` をプロジェクト直下に配置します。

4. `input/schecule.yaml` を編集します。

## Google Cloud 設定

1. Google Cloud Console でプロジェクトを作成します。
2. `Google Calendar API` を有効化します。
3. `OAuth 同意画面` を設定します。
4. `認証情報` から `OAuth クライアント ID` を作成します。
5. アプリの種類は `デスクトップ アプリ` を選びます。
6. ダウンロードした JSON を `credentials.json` として配置します。
7. OAuth 同意画面が `テスト中` の場合は、利用する Google アカウントを `テストユーザー` に追加します。

## 実行方法

予定内容だけ確認する場合:

```bash
uv run python main.py --dry-run
```

実際に登録する場合:

```bash
uv run python main.py
```

初回実行時はブラウザで Google ログインと権限許可が求められます。認証完了後、`token.json` が自動生成されます。

## YAML 形式

`input/schecule.yaml` は次の形式です。

```yaml
defaults:
  calendar_name: "登録先カレンダー名"
  title: "通常イベント名"
  timezone: "Asia/Tokyo"
  start_time: "13:00"
  end_time: "17:00"
  location: "会場名"

events:
  - date: "2026-04-04"
  - date: "2026-04-19"
  - date: "2026-06-28"
    location: "別会場"
  - date: "2026-07-25"
    all_day: true
    title: "特別イベント名"
    location: "終日イベント会場"
```

### `defaults`

- `calendar_name`: 登録先カレンダー名
- `title`: 通常時のイベント名
- `timezone`: タイムゾーン
- `start_time`: 通常時の開始時刻
- `end_time`: 通常時の終了時刻
- `location`: 通常時の場所

### `events`

- `date` は必須です
- `title` を指定するとそのイベントだけ件名を上書きできます
- `location` を指定するとそのイベントだけ場所を上書きできます
- `all_day: true` を指定すると終日イベントになります
- 終日イベントでは `start_time` と `end_time` は使いません

## 補足

- 同じ件名、場所、開始、終了の予定が既に存在する場合は登録をスキップします。
- `credentials.json`、`token.json`、`input/schecule.yaml` は `.gitignore` に含めています。
