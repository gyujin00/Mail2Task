from __future__ import annotations
import hashlib
from datetime import datetime
import database
from todo_analyzer import TodoAnalyzer  # 분리한 AI 클래스 임포트

# 분석기 인스턴스 생성
analyzer = TodoAnalyzer()

# ---------------------------------------------------------
# 가공 및 실행 로직 (비즈니스 로직만 남김)
# ---------------------------------------------------------

def save_mail(mail: dict):
    mail_id = _make_mail_id(mail.get("subject", ""), mail.get("sender", ""), mail.get("received_at", ""))
    document = {
        "mail_id": mail_id,
        "subject": mail.get("subject", ""),
        "sender": mail.get("sender", ""),
        "received_at": mail.get("received_at", ""),
        "body": mail.get("body", ""),
        "created_at": _now_iso(),
        "updated_at": _now_iso(),
    }
    database.upsert_mail(mail_id, document)
    return document

def save_tasks(tasks: list[dict]):
    if not tasks: return []
    saved_docs = []
    
    for task in tasks:
        title = task.get("title") or task.get("subject", "")
        
        # 1. AI 분석기 사용 (To-do 여부 및 데이터 추출)
        analysis = analyzer.analyze(title)
        if not analysis: continue  # To-do가 아니면 패스

        # 2. 메타데이터 처리
        task_id = _make_task_id(task.get("mail_id", ""), title, task.get("task_order", 1))

        # 3. 문서 조립
        document = {
            "task_id": task_id, 
            "id": task_id, 
            "mail_id": task.get("mail_id", ""),
            "title": title, 
            "status": task.get("status", "대기"),
            "task_type": analysis["task_type"],
            "time": ", ".join(analysis["entities"]["time"]),
            "target": ", ".join(analysis["entities"]["target"]),
            "action": ", ".join(analysis["entities"]["action"]),
            "received_at": task.get("received_at", ""),
            "created_at": _now_iso(), 
            "updated_at": _now_iso(),
        }
        
        database.upsert_task(task_id, document)
        saved_docs.append(document)
        
    return saved_docs

def load_tasks():
    return database.fetch_tasks()

def update_status(task_id, notified=None, status=None):
    updates = {"updated_at": _now_iso()}
    if notified is not None: updates["notified"] = bool(notified)
    if status is not None: updates["status"] = status
    database.update_task(task_id, updates)

# ---------------------------------------------------------
# 유틸리티 함수 (내부 로직)
# ---------------------------------------------------------

def _make_mail_id(subject, sender, received_at):
    return hashlib.md5(f"{subject}_{sender}_{received_at}".encode()).hexdigest()[:16]

def _make_task_id(mail_id, title, task_order):
    return hashlib.md5(f"{mail_id}_{task_order}_{title}".encode()).hexdigest()[:16]

def _now_iso():
    return datetime.utcnow().isoformat(timespec="seconds")