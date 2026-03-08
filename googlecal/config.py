from pathlib import Path

APP_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SCHEDULE_PATH = APP_ROOT / "input" / "schecule.yaml"
DEFAULT_CREDENTIALS_PATH = APP_ROOT / "credentials.json"
DEFAULT_TOKEN_PATH = APP_ROOT / "token.json"
