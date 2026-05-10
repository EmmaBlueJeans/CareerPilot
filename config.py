import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
INSTANCE_DIR = BASE_DIR / "instance"
INSTANCE_DIR.mkdir(exist_ok=True)

DB_PATH = INSTANCE_DIR / "careerpilot.db"

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
FLASK_SECRET_KEY = os.environ.get("FLASK_SECRET_KEY", "dev-only-change-me")

SCREEN_MODEL = "claude-sonnet-4-6"
INTERVIEW_MODEL = "claude-haiku-4-5-20251001"

MAX_PDF_BYTES = 5 * 1024 * 1024
INTERVIEW_QUESTION_COUNT = 5
