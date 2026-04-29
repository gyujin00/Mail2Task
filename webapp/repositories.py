from __future__ import annotations

from typing import Any

import database
from summarizer import summarize


def list_tasks() -> list[dict[str, Any]]:
    """tasks 컬렉션에서 화면 표시용 문서를 조회한다."""
    return database.fetch_tasks()


def get_task(task_id: str) -> dict[str, Any] | None:
    """task_id(id 포함)로 단건 조회."""
    return database.fetch_task(task_id)


def get_mail(mail_id: str) -> dict[str, Any] | None:
    """mail_id로 mails 컬렉션 단건 조회."""
    return database.fetch_mail(mail_id)


def list_pdfs_by_mail(mail_id: str) -> list[dict[str, Any]]:
    """mail_id에 연결된 PDF 문서 목록 조회."""
    return database.fetch_pdfs_by_mail(mail_id)


def list_pdfs(
    exclude_pdf_ids: list[str] | None = None,
    limit: int = 200,
) -> list[dict[str, Any]]:
    """PDF 문서 목록 조회."""
    return database.fetch_pdfs(exclude_pdf_ids=exclude_pdf_ids, limit=limit)


def refresh_task_summary(
    task: dict[str, Any],
    mail: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Regenerate old verbose summaries into a short detail-view summary."""
    if not task or not _needs_summary_refresh(task.get("summary", "")):
        return task

    body = (mail or {}).get("body") or task.get("raw_body") or ""
    pdf_text = "\n".join(
        file.get("text", "")
        for file in ((mail or {}).get("pdf_files") or [])
        if file.get("text")
    )
    source_text = "\n".join(part for part in [body, pdf_text] if part)
    source_text = source_text or task.get("source_text") or task.get("subject", "")

    refreshed = summarize(
        source_text,
        subject=task.get("subject", ""),
        title=task.get("title", ""),
        deadline_date=task.get("deadline_date", ""),
        urgency_level=task.get("urgency_level", ""),
        task_type=task.get("task_type", ""),
    )
    if not refreshed:
        return task

    database.update_task(
        task.get("task_id") or task.get("id"),
        {"summary": refreshed, "task_summary": refreshed},
    )

    updated = dict(task)
    updated["summary"] = refreshed
    updated["task_summary"] = refreshed
    return updated


def set_task_status_completed(task_id: str) -> None:
    """업무 완료 처리."""
    database.update_task(task_id, {"status": "완료"})


def _needs_summary_refresh(summary: str) -> bool:
    """Refresh summaries that are empty or still stored in the old verbose format."""
    normalized = " ".join((summary or "").split())
    if not normalized:
        return True
    if "\n" in (summary or ""):
        return False
    if len(normalized) > 90:
        return True

    legacy_markers = ("업무유형", "우선순위", "파일명", "마감기한", "상세")
    return any(marker in normalized for marker in legacy_markers)
