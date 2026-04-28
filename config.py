import os

# Gmail IMAP/SMTP 서버 설정
IMAP_SERVER = "imap.gmail.com"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# 계정 정보: 환경변수로 관리 (코드에 비밀번호 직접 입력 금지)
EMAIL = os.environ.get("TASK_EMAIL", "")
PASSWORD = os.environ.get("TASK_PASSWORD", "")  # Gmail 앱 비밀번호

# 파일 경로
SAVE_DIR = "./downloads"
TODO_CSV = "todo_list.csv"

# CSV 컬럼 정의 (팀 전체 공유 — 변경 시 팀 협의 필요)
CSV_COLUMNS = [
    "id",             # 고유 ID (중복 감지용 해시)
    "subject",        # 메일 제목
    "sender",         # 발신자 이메일
    "deadline",       # 마감일 (YYYY-MM-DD)
    "task_summary",   # 업무 요약 (LLM or 본문 일부)
    "task_type",      # 업무 유형 (kdh 담당)
    "urgency_score",  # 긴급도 점수 0~100 (차규진 담당)
    "urgency_level",  # 긴급도 등급: 긴급/보통/여유 (차규진 담당)
    "status",         # 상태: 대기/진행중/완료
    "received_at",    # 수신 일시 (YYYY-MM-DD HH:MM)
    "notified",       # 완료 알림 발송 여부: True/False (규진 차 담당)
]

# 메일 필터 키워드
KEYWORD_FILTER = "[업무협조]"

# 긴급도 등급 기준
URGENCY_HIGH = 60    # 이상: 긴급
URGENCY_MID = 30     # 이상: 보통, 미만: 여유
