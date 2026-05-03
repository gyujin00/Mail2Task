from __future__ import annotations

import hashlib
import re
from datetime import datetime

from core import config
from storage import database

# ── 업무 유형 분류 ─────────────────────────────────────────────────────────────
# 업무 유형은 명사 어근(名詞 語根) 기반 분류 문제:
# 동사 어미가 TODO 여부를 결정하는 것과 달리, 업무 도메인은 문장에 등장하는
# 대표 명사 어근("회의", "결재", "배포")이 결정한다.
#
# 설계 원칙:
#   1. 겹치는 어근은 더 좁은(특수한) 카테고리에만 배치
#   2. 우선순위: 특수 도메인(개발·결재) → 업무 방식(회의·검토) → 산출물(보고서) →
#               프로젝트 관리 → 반복 패턴(루틴) → 총무·행정(포괄)
_TASK_TYPE_STEMS: dict[str, list[str]] = {
    "개발":     ["개발", "코드", "배포", "빌드", "디버깅", "버그", "api", "서버", "장애", "패치"],
    "결재":     ["결재", "승인", "품의", "상신", "전결", "재가"],
    "회의":     ["회의", "미팅", "협의", "안건", "브리핑", "킥오프", "인터뷰"],
    "검토":     ["검토", "리뷰", "피드백", "의견", "코멘트", "검수"],
    "보고서":   ["보고서", "초안", "최종안", "발표자료", "취합"],
    "프로젝트": ["프로젝트", "구축", "런칭", "마일스톤", "산출물", "착수", "제안서"],
    "루틴":     ["정기", "반복", "월간", "주간", "분기", "데일리", "정례"],
    "행정":     ["행정", "정산", "출장", "휴가", "근태", "예산", "계약", "발주", "지출"],
}
# 특수→일반 순 (앞에 올수록 변별력 높은 범주)
_TASK_TYPE_ORDER = ["개발", "결재", "회의", "검토", "보고서", "프로젝트", "루틴", "행정"]

_okt = None


def _get_okt():
    global _okt
    if _okt is None:
        try:
            from konlpy.tag import Okt  # noqa: PLC0415
            _okt = Okt()
        except Exception:
            _okt = False
    return _okt if _okt is not False else None


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
    """
    텍스트에서 업무 유형을 분류한다.

    업무 유형은 명사 어근 기반 분류 문제: 문장의 동사 어미가 TODO 여부를
    결정하는 것과 달리, 업무 도메인은 문장에 등장하는 대표 명사 어근이 결정한다.

    분류 순서:
      1. 구조화 필드(업무유형:) → 명시값 우선
      2. Okt 어근 추출 후 _TASK_TYPE_STEMS 교차 (특수→일반 순)
      3. Okt 미설치: 원문 substring fallback
    """
    # 1. 구조화 필드 명시값 우선
    structured_match = re.search(
        r"(?:업무유형|task\s*type)\s*[:：]\s*([^\n\r]+)",
        text,
        flags=re.IGNORECASE,
    )
    if structured_match:
        raw = structured_match.group(1).strip()
        for label in _TASK_TYPE_ORDER:
            if label in raw:
                return label

    # 2. Okt 어근 추출 후 카테고리 매칭
    stems = _extract_content_stems(text)
    if stems:
        for label in _TASK_TYPE_ORDER:
            if any(s in stems for s in _TASK_TYPE_STEMS[label]):
                return label
        return "기타"

    # 3. fallback: Okt 미설치 환경, 원문 substring 검사
    for label in _TASK_TYPE_ORDER:
        if any(kw in text for kw in _TASK_TYPE_STEMS[label]):
            return label
    return "기타"


def _extract_content_stems(text: str) -> set[str]:
    """Okt stem=True로 명사·동사 어근 집합을 반환한다 (유형 분류용)."""
    okt = _get_okt()
    if okt is None:
        return set()
    try:
        stems: set[str] = set()
        for word, tag in okt.pos(text, norm=True, stem=True):
            w = word.strip().lower()
            if tag == "Noun" and len(w) >= 2:
                stems.add(w)
            elif tag in ("Verb", "Adjective"):
                for suffix in ("하다", "되다", "이다"):
                    if w.endswith(suffix) and len(w) > len(suffix) + 1:
                        stems.add(w[: -len(suffix)])
                        break
        return stems
    except Exception:
        return set()


def _analyze_task(text: str):
    if not text or len(text.strip()) < 2:
        return None

    from core.todo_extractor import _is_actionable
    if not _is_actionable(text):
        return None

    return {
        "task_type": classify_task_type(text),
        "entities": _fallback_entities(text),
    }


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
