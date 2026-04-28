"""
메일 1건에서 업무(Task) 여러 개를 추출하는 모듈.

1차 구현은 팀 메일 양식의 구조화 필드를 규칙 기반으로 읽는다.
LLM은 나중에 비정형 문장에서 추가 업무를 보강할 때 붙일 수 있도록
입력/출력 구조를 먼저 분리해 둔다.
"""

from __future__ import annotations

import hashlib
import re

from classifier import score_urgency
from deadline_parser import parse_deadline_info
from mongo_task_store import classify_task_type
from summarizer import summarize


TITLE_FIELD_NAMES = ("과업명", "업무명", "task name", "task")
TYPE_FIELD_NAMES = ("업무유형", "task type")
PRIORITY_FIELD_NAMES = ("우선순위", "priority")


def extract_tasks_from_mail(mail_document):
    """
    메일 문서에서 업무(Task) 목록을 추출한다.

    현재는 구조화된 '과업명:' 블록을 중심으로 자르고,
    없으면 메일 전체를 대표 업무 1건으로 저장한다.
    """
    subject = mail_document.get("subject", "")
    body = mail_document.get("body", "")
    received_at = mail_document.get("received_at", "")
    mail_id = mail_document.get("mail_id", "")
    pdf_files = mail_document.get("pdf_files", [])
    pdf_text = "\n".join(file.get("text", "") for file in pdf_files if file.get("text"))
    full_text = "\n".join(part for part in [subject, body, pdf_text] if part)

    source_text = "\n".join(part for part in [body, pdf_text] if part)
    blocks = _extract_task_blocks(source_text)
    if not blocks:
        blocks = [source_text or full_text]

    tasks = []
    for index, block in enumerate(blocks, start=1):
        task_scope_text = "\n".join(part for part in [subject, block] if part)
        title = _extract_field_value(block, TITLE_FIELD_NAMES) or _fallback_task_title(
            subject
        )
        # 개별 업무 블록의 마감 정보를 먼저 읽고, 없을 때만 제목/전체 문맥으로 보완한다.
        deadline_info = parse_deadline_info(block, received_at)
        if not deadline_info["date"]:
            deadline_info = parse_deadline_info(task_scope_text or full_text, received_at)
        task_type = _extract_task_type(block, task_scope_text)
        priority_raw = _extract_field_value(block, PRIORITY_FIELD_NAMES)
        summary = summarize(task_scope_text or full_text)
        urgency_score, urgency_level, _ = score_urgency(
            task_scope_text or full_text,
            received_at,
            deadline=deadline_info["date"],
        )

        task_id = _make_task_id(mail_id, index, title)
        tasks.append(
            {
                "task_id": task_id,
                "id": task_id,
                "mail_id": mail_id,
                "task_order": index,
                "title": title,
                "subject": subject,
                "sender": mail_document.get("sender", ""),
                "status": "대기",
                "task_type": task_type,
                "priority_raw": priority_raw,
                "urgency_score": urgency_score,
                "urgency_level": urgency_level,
                "deadline_date": deadline_info["date"],
                "deadline": deadline_info["date"],
                "deadline_time": deadline_info["time"],
                "deadline_source": deadline_info["source"],
                "deadline_raw_text": deadline_info["raw_text"],
                "mail_category": mail_document.get("mail_category", ""),
                "received_at": received_at,
                "has_pdf": bool(pdf_files),
                "pdf_count": len(pdf_files),
                "pdf_paths": [file.get("path", "") for file in pdf_files if file.get("path")],
                "summary": summary,
                "task_summary": summary,
                "source_text": block.strip() or task_scope_text,
                "raw_body": body,
                "notified": False,
            }
        )

    return tasks


def _extract_task_blocks(text):
    """'과업명:'이 반복되는 메일 본문을 업무 단위 블록으로 자른다."""
    lines = [_normalize_line(line) for line in (text or "").splitlines()]
    blocks = []
    current = []

    for line in lines:
        if not line:
            if current:
                current.append("")
            continue

        if _is_title_line(line):
            if current:
                blocks.append(_finalize_block(current))
            current = [line]
            continue

        if current:
            current.append(line)

    if current:
        blocks.append(_finalize_block(current))

    return [block for block in blocks if block.strip()]


def _normalize_line(line):
    """마크다운 볼드나 불릿을 제거해 필드 파싱 정확도를 높인다."""
    text = (line or "").strip()
    text = text.replace("*", "")
    text = re.sub(r"^[-*•]\s*", "", text)
    return text.strip()


def _finalize_block(lines):
    """업무 블록 끝의 불필요한 빈 줄을 제거한다."""
    cleaned = list(lines)
    while cleaned and cleaned[-1] == "":
        cleaned.pop()
    return "\n".join(cleaned).strip()


def _is_title_line(line):
    """'과업명:'이 시작되는 줄을 새 업무 블록의 시작으로 본다."""
    lowered = line.lower()
    return any(
        lowered.startswith(field.lower() + ":")
        or lowered.startswith(field.lower() + " :")
        or lowered.startswith(field.lower() + "：")
        for field in TITLE_FIELD_NAMES
    )


def _extract_field_value(text, field_names):
    """구조화된 '필드명: 값' 형식에서 값만 꺼낸다."""
    for raw_line in (text or "").splitlines():
        line = _normalize_line(raw_line)
        lowered = line.lower()
        for field_name in field_names:
            field_name_lower = field_name.lower()
            if lowered.startswith(field_name_lower + ":") or lowered.startswith(
                field_name_lower + "："
            ):
                _, value = re.split(r"[:：]", line, maxsplit=1)
                return value.strip()
    return ""


def _extract_task_type(block_text, fallback_text):
    """구조화된 업무유형을 우선 사용하고, 없으면 키워드 분류로 보완한다."""
    structured_value = _extract_field_value(block_text, TYPE_FIELD_NAMES)
    if structured_value:
        return classify_task_type(f"업무유형: {structured_value}")
    return classify_task_type(fallback_text)


def _fallback_task_title(subject):
    """구조화된 과업명이 없을 때는 메일 제목을 대표 업무명으로 사용한다."""
    title = re.sub(r"^\[[^\]]+\]\s*", "", subject or "")
    title = re.sub(r"\(\s*~\s*\d{1,2}/\d{1,2}(?:\s+\d{1,2}:\d{2})?\s*\)", "", title)
    title = re.sub(r"\s+", " ", title).strip()
    return title or "제목 미상 업무"


def _make_task_id(mail_id, task_order, title):
    """메일 ID와 블록 순서를 기준으로 안정적인 Task ID를 만든다."""
    raw = f"{mail_id}:{task_order}:{title}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()[:16]
