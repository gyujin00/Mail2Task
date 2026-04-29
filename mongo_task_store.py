"""
MongoDB 기반 메일/업무 저장소 모듈.

todo_manager.py는 팀원의 CSV/분류 구현을 보존하고,
실제 런타임 저장/조회는 이 모듈이 담당한다.
"""

from __future__ import annotations

import hashlib
import re
from datetime import datetime

from pymongo import DESCENDING, MongoClient

import config
from pdf_keywords import extract_pdf_keywords


_client = None


def load_tasks():
    """저장된 업무(Task) 문서를 최신 수신일 기준으로 불러온다."""
    collection = _get_task_collection()
    return list(collection.find({}, {"_id": 0}).sort("received_at", DESCENDING))


def save_mail(mail):
    """메일 원문 문서를 mails 컬렉션에 저장하고 저장 결과를 반환한다."""
    collection = _get_mail_collection()

    mail_id = mail.get("mail_id") or _make_mail_id(
        mail.get("subject", ""),
        mail.get("sender", ""),
        mail.get("received_at", ""),
    )
    pdf_files = mail.get("pdf_files", [])
    pdf_ids = [_make_pdf_id(mail_id, file.get("filename", ""), index) for index, file in enumerate(pdf_files, start=1)]
    document = {
        "mail_id": mail_id,
        "subject": mail.get("subject", ""),
        "mail_category": mail.get("mail_category") or _extract_mail_category(
            mail.get("subject", "")
        ),
        "sender": mail.get("sender", ""),
        "received_at": mail.get("received_at", ""),
        "body": mail.get("body", ""),
        "pdf_files": pdf_files,
        "pdf_ids": pdf_ids,
        "pdf_paths": [file.get("path", "") for file in pdf_files if file.get("path")],
        "has_pdf": bool(pdf_files),
        "pdf_count": len(pdf_files),
        "created_at": mail.get("created_at") or _now_iso(),
        "updated_at": _now_iso(),
    }

    collection.replace_one({"mail_id": mail_id}, document, upsert=True)
    return document


def save_pdf_documents(mail):
    """메일에 포함된 PDF 원문을 pdf_documents 컬렉션에 저장한다."""
    pdf_files = mail.get("pdf_files", [])
    if not pdf_files:
        return []

    collection = _get_pdf_collection()
    mail_id = mail.get("mail_id", "")
    task_ids = mail.get("task_ids", [])
    now_text = _now_iso()
    saved_documents = []

    for index, pdf_file in enumerate(pdf_files, start=1):
        filename = pdf_file.get("filename", "")
        path = pdf_file.get("path", "")
        text = pdf_file.get("text", "")
        keywords = pdf_file.get("keywords") or extract_pdf_keywords(text, filename=filename)
        pdf_id = pdf_file.get("pdf_id") or _make_pdf_id(mail_id, filename, index)

        document = {
            "pdf_id": pdf_id,
            "mail_id": mail_id,
            "task_ids": list(task_ids),
            "filename": filename,
            "path": path,
            "text": text,
            "keywords": keywords,
            "keyword_count": len(keywords),
            "created_at": pdf_file.get("created_at") or now_text,
            "updated_at": now_text,
        }

        collection.replace_one({"pdf_id": pdf_id}, document, upsert=True)
        saved_documents.append(document)

    return saved_documents


def save_tasks(tasks):
    """추출된 업무(Task) 목록을 tasks 컬렉션에 저장한다."""
    if not tasks:
        return []

    collection = _get_task_collection()
    now_text = _now_iso()
    saved_documents = []

    for task in tasks:
        task_id = task.get("task_id") or task.get("id")
        if not task_id:
            task_id = _make_task_id(
                task.get("mail_id", ""),
                task.get("title") or task.get("subject", ""),
                task.get("task_order", 1),
            )

        deadline_date = task.get("deadline_date") or task.get("deadline", "")
        deadline_time = task.get("deadline_time", "")
        document = {
            "task_id": task_id,
            "id": task_id,
            "mail_id": task.get("mail_id", ""),
            "task_order": task.get("task_order", 1),
            "title": task.get("title") or task.get("subject", ""),
            "subject": task.get("subject", ""),
            "sender": task.get("sender", ""),
            "status": task.get("status", "대기"),
            "task_type": task.get("task_type")
            or classify_task_type(task.get("source_text") or task.get("raw_body", "")),
            "priority_raw": task.get("priority_raw", ""),
            "urgency_score": task.get("urgency_score", 0),
            "urgency_level": task.get("urgency_level", ""),
            "deadline_date": deadline_date,
            "deadline": deadline_date,
            "deadline_time": deadline_time,
            "deadline_at": task.get("deadline_at")
            or _build_deadline_at(deadline_date, deadline_time),
            "deadline_source": task.get("deadline_source", ""),
            "deadline_raw_text": task.get("deadline_raw_text", ""),
            "mail_category": task.get("mail_category")
            or _extract_mail_category(task.get("subject", "")),
            "received_at": task.get("received_at", ""),
            "has_pdf": bool(task.get("has_pdf", False)),
            "pdf_count": int(task.get("pdf_count", 0)),
            "pdf_paths": task.get("pdf_paths", []),
            "summary": task.get("summary") or task.get("task_summary", ""),
            "task_summary": task.get("summary") or task.get("task_summary", ""),
            "source_text": task.get("source_text", ""),
            "raw_body": task.get("raw_body", ""),
            "time": task.get("time", ""),
            "target": task.get("target", ""),
            "action": task.get("action", ""),
            "time_entities": task.get("time_entities", []),
            "target_entities": task.get("target_entities", []),
            "action_entities": task.get("action_entities", []),
            "notified": bool(task.get("notified", False)),
            "created_at": task.get("created_at") or now_text,
            "updated_at": now_text,
        }

        collection.replace_one({"task_id": task_id}, document, upsert=True)
        saved_documents.append(document)

    return saved_documents


def update_status(task_id, notified=None, status=None):
    """특정 업무(Task)의 상태나 알림 여부를 갱신한다."""
    updates = {"updated_at": _now_iso()}

    if notified is not None:
        updates["notified"] = bool(notified)

    if status is not None:
        updates["status"] = status

    collection = _get_task_collection()
    collection.update_one(
        {"$or": [{"task_id": task_id}, {"id": task_id}]},
        {"$set": updates},
    )


def get_completed_unnotified():
    """완료되었지만 아직 완료 알림을 보내지 않은 업무를 조회한다."""
    collection = _get_task_collection()
    return list(
        collection.find(
            {
                "status": "완료",
                "$or": [
                    {"notified": False},
                    {"notified": {"$exists": False}},
                ],
            },
            {"_id": 0},
        ).sort("received_at", DESCENDING)
    )


def mail_exists(subject, sender, received_at):
    """같은 메일이 이미 저장되어 있는지 확인한다."""
    collection = _get_mail_collection()
    mail_id = _make_mail_id(subject, sender, received_at)
    return collection.count_documents({"mail_id": mail_id}, limit=1) > 0


def classify_task_type(text):
    """현재 task 추출/통계용 업무 유형 분류 규칙."""
    if not text:
        return "기타"

    structured_match = re.search(
        r"(?:업무유형|task\s*type)\s*[:：]?\s*([^\n\r]+)",
        text,
        flags=re.IGNORECASE,
    )
    if structured_match:
        raw_value = structured_match.group(1).strip()
        normalized_value = raw_value.lower()
        if "프로젝트" in raw_value or "project" in normalized_value:
            return "프로젝트"
        if "루틴" in raw_value or "routine" in normalized_value:
            return "루틴"
        if "행정" in raw_value or "admin" in normalized_value:
            return "행정"
        return "기타"

    keyword_rules = {
        "보고서": ["보고서", "작성", "문서"],
        "회의": ["회의", "미팅"],
        "검토": ["검토", "리뷰"],
        "결재": ["결재", "승인"],
        "개발": ["개발", "코드", "패치"],
        "프로젝트": ["프로젝트", "시안", "구축", "런칭"],
        "루틴": ["정기", "매일", "매주", "반복", "월간"],
        "행정": ["행정", "정산", "결산", "비품", "증빙", "보고"],
    }

    for task_type, keywords in keyword_rules.items():
        if any(keyword in text for keyword in keywords):
            return task_type

    return "기타"


def _get_mail_collection():
    """MongoDB mails 컬렉션을 반환하고 필요한 인덱스를 보장한다."""
    client = _get_client()
    collection = client[config.MONGODB_DB][config.MONGODB_MAILS_COLLECTION]
    collection.create_index("mail_id", unique=True)
    collection.create_index("received_at")
    collection.create_index("mail_category")
    return collection


def _get_task_collection():
    """MongoDB tasks 컬렉션을 반환하고 필요한 인덱스를 보장한다."""
    client = _get_client()
    collection = client[config.MONGODB_DB][config.MONGODB_TASKS_COLLECTION]
    collection.create_index("task_id", unique=True)
    collection.create_index("id", unique=True)
    collection.create_index("mail_id")
    collection.create_index("status")
    collection.create_index("deadline_date")
    collection.create_index("task_type")
    collection.create_index("urgency_level")
    collection.create_index("mail_category")
    return collection


def _get_pdf_collection():
    """MongoDB pdf_documents 컬렉션을 반환하고 필요한 인덱스를 보장한다."""
    client = _get_client()
    collection = client[config.MONGODB_DB][config.MONGODB_PDFS_COLLECTION]
    collection.create_index("pdf_id", unique=True)
    collection.create_index("mail_id")
    collection.create_index("filename")
    return collection


def _get_client():
    """MongoDB 클라이언트를 재사용한다."""
    global _client
    if _client is None:
        _client = MongoClient(config.MONGODB_URI, serverSelectionTimeoutMS=5000)
        _client.admin.command("ping")
    return _client


def _extract_mail_category(subject):
    """제목 앞의 [운영], [업무요청] 같은 말머리를 추출한다."""
    match = re.match(r"^\[([^\]]+)\]", subject or "")
    if match:
        return match.group(1).strip()
    return ""


def _make_mail_id(subject, sender, received_at):
    """제목, 발신자, 수신시각을 기준으로 안정적인 메일 ID를 만든다."""
    raw = f"{subject}_{sender}_{received_at}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()[:16]


def _make_task_id(mail_id, title, task_order):
    """메일 ID와 업무 순서를 기준으로 안정적인 Task ID를 만든다."""
    raw = f"{mail_id}_{task_order}_{title}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()[:16]


def _make_pdf_id(mail_id, filename, pdf_order):
    """메일 ID와 첨부 순서를 기준으로 안정적인 PDF ID를 만든다."""
    raw = f"{mail_id}_{pdf_order}_{filename}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()[:16]


def _build_deadline_at(deadline_date, deadline_time):
    """날짜/시간 필드를 하나의 ISO 문자열로 합친다."""
    if not deadline_date:
        return ""

    if deadline_time:
        return f"{deadline_date}T{deadline_time}:00"
    return f"{deadline_date}T23:59:59"


def _now_iso():
    """현재 시각을 ISO 문자열로 반환한다."""
    return datetime.utcnow().isoformat(timespec="seconds")
