from pymongo import DESCENDING, MongoClient
import config

_client = None

def _get_client():
    """MongoClient를 싱글톤으로 재사용(웹/CLI 모두 동일)."""
    global _client
    if _client is None:
        _client = MongoClient(config.MONGODB_URI, serverSelectionTimeoutMS=5000)
    return _client

def get_mail_collection():
    """메일 원문 저장용 컬렉션(mails)."""
    client = _get_client()
    col = client[config.MONGODB_DB][config.MONGODB_MAILS_COLLECTION]
    col.create_index("mail_id", unique=True)
    return col

def get_pdf_collection():
    """PDF 원문/메타데이터 저장용 컬렉션(pdf_documents)."""
    client = _get_client()
    col = client[config.MONGODB_DB][config.MONGODB_PDFS_COLLECTION]
    col.create_index("pdf_id", unique=True)
    col.create_index("mail_id")
    return col

def get_task_collection():
    """To-do(Task) 저장용 컬렉션(tasks). 통계/대시보드는 이 컬렉션 기준으로 계산한다."""
    client = _get_client()
    col = client[config.MONGODB_DB][config.MONGODB_TASKS_COLLECTION]
    col.create_index("task_id", unique=True)
    col.create_index("id", unique=True)
    return col

def upsert_mail(mail_id, document):
    """mail_id를 키로 메일 문서를 upsert한다(중복 저장 방지)."""
    col = get_mail_collection()
    col.replace_one({"mail_id": mail_id}, document, upsert=True)

def upsert_task(task_id, document):
    """task_id를 키로 Task 문서를 upsert한다(메일 1건 → Task N건 구조 지원)."""
    col = get_task_collection()
    col.replace_one({"task_id": task_id}, document, upsert=True)

def upsert_pdf(pdf_id, document):
    """pdf_id를 키로 PDF 문서를 upsert한다."""
    col = get_pdf_collection()
    col.replace_one({"pdf_id": pdf_id}, document, upsert=True)

def fetch_tasks():
    """Task 목록 조회(기본: 최신 수신일 순)."""
    col = get_task_collection()
    return list(col.find({}, {"_id": 0}).sort("received_at", DESCENDING))

def fetch_task(task_id: str):
    """Task 단건 조회(task_id와 id 필드를 모두 허용)."""
    col = get_task_collection()
    return col.find_one({"$or": [{"task_id": task_id}, {"id": task_id}]}, {"_id": 0})

def fetch_mail(mail_id: str):
    """메일 원문 단건 조회(상세 화면에서 본문/첨부 목록 표시용)."""
    col = get_mail_collection()
    return col.find_one({"mail_id": mail_id}, {"_id": 0})

def fetch_pdf(pdf_id: str):
    """PDF 문서 단건 조회."""
    col = get_pdf_collection()
    return col.find_one({"pdf_id": pdf_id}, {"_id": 0})

def fetch_pdfs_by_mail(mail_id: str):
    """메일에 연결된 PDF 문서 목록 조회."""
    col = get_pdf_collection()
    return list(col.find({"mail_id": mail_id}, {"_id": 0}))


def fetch_pdfs(exclude_pdf_ids=None, limit: int = 200):
    """PDF 문서 목록 조회. 필요 시 특정 PDF ID들을 제외한다."""
    col = get_pdf_collection()
    query = {}
    if exclude_pdf_ids:
        query["pdf_id"] = {"$nin": list(exclude_pdf_ids)}
    return list(col.find(query, {"_id": 0}).limit(limit))

def update_task(task_id, updates):
    """Task 상태/알림 여부 등의 부분 업데이트."""
    col = get_task_collection()
    col.update_one(
        {"$or": [{"task_id": task_id}, {"id": task_id}]},
        {"$set": updates}
    )

def mail_exists(mail_id):
    """mail_id 기준 중복 저장 여부 확인."""
    col = get_mail_collection()
    return col.count_documents({"mail_id": mail_id}, limit=1) > 0
