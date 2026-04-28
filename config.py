import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent


def _load_dotenv():
    """프로젝트 루트의 .env 파일을 읽어 환경변수로 등록한다."""
    env_path = BASE_DIR / ".env"
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'").strip('"')
        os.environ.setdefault(key, value)


_load_dotenv()


# Gmail IMAP/SMTP 서버 설정
IMAP_SERVER = "imap.gmail.com"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# 계정 정보: .env 또는 환경변수에서 읽는다.
EMAIL = os.environ.get("TASK_EMAIL", "")
PASSWORD = os.environ.get("TASK_PASSWORD", "")  # Gmail 앱 비밀번호

# MongoDB 설정
MONGODB_URI = os.environ.get(
    "MONGODB_URI",
    "mongodb://admin:admin1234@localhost:27017/mail2task?authSource=admin",
)
MONGODB_DB = os.environ.get("MONGODB_DB", "mail2task")
MONGODB_MAILS_COLLECTION = os.environ.get("MONGODB_MAILS_COLLECTION", "mails")
MONGODB_TASKS_COLLECTION = os.environ.get(
    "MONGODB_TASKS_COLLECTION",
    os.environ.get("MONGODB_COLLECTION", "tasks"),
)
# 기존 코드 호환용 별칭
MONGODB_COLLECTION = MONGODB_TASKS_COLLECTION

# OpenAI API 설정
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-5.4-mini")

# 파일 경로
SAVE_DIR = str(BASE_DIR / "downloads")
TODO_CSV = str(BASE_DIR / "todo_list.csv")

# CSV 컬럼 정의
CSV_COLUMNS = [
    "id",
    "subject",
    "sender",
    "deadline",
    "task_summary",
    "task_type",
    "urgency_score",
    "urgency_level",
    "status",
    "received_at",
    "notified",
]

# 메일 필터: 제목이 [카테고리] 형태로 시작하는 메일만 수집
SUBJECT_PATTERN = r"^\[.+\]"

# 업무 유형 후보
TASK_TYPES = ["프로젝트", "루틴", "행정", "기타"]

# 우선순위별 긴급도 기본 점수
PRIORITY_SCORE = {
    "상": 70,
    "중": 40,
    "하": 10,
    "high": 70,
    "medium": 40,
    "low": 10,
}

# 긴급도 등급 기준
URGENCY_HIGH = 60
URGENCY_MID = 30
