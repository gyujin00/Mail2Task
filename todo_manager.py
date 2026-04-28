from __future__ import annotations

import hashlib
import re
from datetime import datetime

import config
import database

try:
    from todo_analyzer import TodoAnalyzer
except Exception:  # pragma: no cover - 선택 의존성/모델 미설치 fallback
    TodoAnalyzer = None


analyzer = TodoAnalyzer() if TodoAnalyzer is not None else None


def save_mail(mail: dict):
    mail_id = _make_mail_id(
        mail.get("subject", ""),
        mail.get("sender", ""),
        mail.get("received_at", ""),
    )
    pdf_files = mail.get("pdf_files", [])
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
        "pdf_paths": [file.get("path", "") for file in pdf_files if file.get("path")],
        "has_pdf": bool(pdf_files),
        "pdf_count": len(pdf_files),
        "created_at": _now_iso(),
        "updated_at": _now_iso(),
    }
    database.upsert_mail(mail_id, document)
    return document


def save_tasks(tasks: list[dict]):
    if not tasks:
        return []

    saved_docs = []

    for task in tasks:
        title = task.get("title") or task.get("subject", "")
        analysis_text = task.get("source_text") or title

        analysis = _analyze_task(analysis_text)
        if not analysis:
            continue

        task_id = task.get("task_id") or task.get("id") or _make_task_id(
            task.get("mail_id", ""),
            title,
            task.get("task_order", 1),
        )

        deadline_date = task.get("deadline_date") or task.get("deadline", "")
        deadline_time = task.get("deadline_time", "")
        document = {
            "task_id": task_id,
            "id": task_id,
            "mail_id": task.get("mail_id", ""),
            "task_order": task.get("task_order", 1),
            "title": title,
            "subject": task.get("subject", ""),
            "sender": task.get("sender", ""),
            "status": task.get("status", "대기"),
            "task_type": task.get("task_type")
            or analysis["task_type"]
            or classify_task_type(analysis_text),
            "time": ", ".join(analysis["entities"]["time"]),
            "target": ", ".join(analysis["entities"]["target"]),
            "action": ", ".join(analysis["entities"]["action"]),
            "time_entities": analysis["entities"]["time"],
            "target_entities": analysis["entities"]["target"],
            "action_entities": analysis["entities"]["action"],
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
            "notified": bool(task.get("notified", False)),
            "created_at": task.get("created_at") or _now_iso(),
            "updated_at": _now_iso(),
        }

        database.upsert_task(task_id, document)
        saved_docs.append(document)

    return saved_docs


def load_tasks():
    return database.fetch_tasks()


def load_todos():
    return load_tasks()


def save_todo(task, existing_todos):
    del existing_todos
    saved = save_tasks([task])
    if saved:
        return saved[0]
    return None


def update_status(task_id, notified=None, status=None):
    updates = {"updated_at": _now_iso()}
    if notified is not None:
        updates["notified"] = bool(notified)
    if status is not None:
        updates["status"] = status
    database.update_task(task_id, updates)


def get_completed_unnotified():
    col = database.get_task_collection()
    return list(
        col.find(
            {
                "status": "완료",
                "$or": [
                    {"notified": False},
                    {"notified": {"$exists": False}},
                ],
            },
            {"_id": 0},
        )
    )


def mail_exists(subject, sender, received_at):
    mail_id = _make_mail_id(subject, sender, received_at)
    return database.mail_exists(mail_id)


def classify_task_type(text: str) -> str:
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

    if analyzer is not None:
        try:
            analyzed_type = analyzer.classify_task_type(text)
            if analyzed_type and analyzed_type != "기타":
                return analyzed_type
        except Exception:
            pass

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
    for label, keywords in keyword_rules.items():
        if any(keyword in text for keyword in keywords):
            return label
    return "기타"


def _analyze_task(text: str):
    if not text or len(text.strip()) < 2:
        return None

    if analyzer is not None:
        try:
            result = analyzer.analyze(text)
            if result:
                return {
                    "task_type": result.get("task_type", "기타"),
                    "entities": _normalize_entities(result.get("entities", {})),
                }
        except Exception:
            pass

    if not _rule_filter(text):
        return None

    return {
        "task_type": classify_task_type(text),
        "entities": _fallback_entities(text),
    }


def _rule_filter(text: str) -> bool:
    negative_patterns = [
        "좋다", "춥다", "덥다", "행복", "피곤", "점심", "날씨",
        "힘들", "재미", "지루", "슬프", "기분", "느낌", "아프",
    ]
    positive_patterns = [
        "해야", "하자", "할 것", "부탁", "요청", "바랍니다", "확인",
        "검토", "리뷰", "점검", "진행", "작성", "제출", "준비", "처리",
        "공유", "전달", "보고", "회신", "답변", "승인", "결재", "까지",
        "이내", "전까지", "내일", "오늘", "이번 주", "다음 주", "회의",
    ]
    past_patterns = [
        "했다", "완료", "수행함", "끝냈", "끝남", "마쳤", "진행했", "제출했"
    ]

    if any(pattern in text for pattern in past_patterns):
        return False
    if text.strip().endswith("?"):
        return False
    if sum(1 for pattern in negative_patterns if pattern in text) >= 2:
        return False
    if sum(1 for pattern in positive_patterns if pattern in text) >= 1:
        return True
    return True


def _fallback_entities(text: str):
    entities = {"time": [], "target": [], "action": []}
    entities["time"].extend(_find_time_entities(text))

    action_value = _extract_structured_value(text, ("과업명", "업무명", "action", "task"))
    if action_value:
        entities["action"].append(action_value)

    target_value = _extract_structured_value(text, ("대상", "target"))
    if target_value:
        entities["target"].append(target_value)

    return _normalize_entities(entities)


def _find_time_entities(text: str):
    patterns = [
        r"\d{4}[.\-/]\d{1,2}[.\-/]\d{1,2}(?:\s+\d{1,2}:\d{2})?",
        r"\d{1,2}/\d{1,2}(?:\s+\d{1,2}:\d{2})?",
        r"\d{1,2}\s*월\s*\d{1,2}\s*일(?:\s+\d{1,2}:\d{2})?",
        r"이번\s*주\s*[월화수목금토일]요일?",
        r"다음\s*주\s*[월화수목금토일]요일?",
        r"오늘(?:\s*\d{1,2}:\d{2})?까지?",
        r"내일(?:\s*\d{1,2}:\d{2})?까지?",
    ]
    results = []
    for pattern in patterns:
        results.extend(re.findall(pattern, text))
    return results


def _extract_structured_value(text: str, field_names: tuple[str, ...]):
    for raw_line in (text or "").splitlines():
        line = raw_line.strip().replace("*", "")
        lowered = line.lower()
        for field_name in field_names:
            name = field_name.lower()
            if lowered.startswith(name + ":") or lowered.startswith(name + "："):
                parts = re.split(r"[:：]", line, maxsplit=1)
                if len(parts) == 2:
                    return parts[1].strip()
    return ""


def _normalize_entities(entities: dict):
    normalized = {"time": [], "target": [], "action": []}
    for key in normalized:
        seen = set()
        for value in entities.get(key, []):
            item = (value or "").strip()
            if not item or item in seen:
                continue
            seen.add(item)
            normalized[key].append(item)
    return normalized


def _make_mail_id(subject, sender, received_at):
    return hashlib.md5(f"{subject}_{sender}_{received_at}".encode()).hexdigest()[:16]


def _make_task_id(mail_id, title, task_order):
    return hashlib.md5(f"{mail_id}_{task_order}_{title}".encode()).hexdigest()[:16]


def _extract_mail_category(subject: str):
    match = re.match(r"^\[([^\]]+)\]", subject or "")
    if match:
        return match.group(1).strip()
    return ""


def _build_deadline_at(deadline_date: str, deadline_time: str):
    if not deadline_date:
        return ""
    if deadline_time:
        return f"{deadline_date}T{deadline_time}:00"
    return f"{deadline_date}T23:59:59"


def _now_iso():
    return datetime.utcnow().isoformat(timespec="seconds")
