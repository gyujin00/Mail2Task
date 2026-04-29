from __future__ import annotations

from typing import Any

import database
from summarizer import summarize


def list_tasks() -> list[dict[str, Any]]:
    """Return the task documents shown in the web list view."""
    return database.fetch_tasks()


def get_task(task_id: str) -> dict[str, Any] | None:
    """Fetch a task by either its legacy `id` or current `task_id`."""
    return database.fetch_task(task_id)


def get_mail(mail_id: str) -> dict[str, Any] | None:
    """Fetch the source mail document for the detail page."""
    return database.fetch_mail(mail_id)


def refresh_task_summary(
    task: dict[str, Any],
    mail: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Regenerate older verbose summaries into the short detail-view format."""
    if not task or not _needs_summary_refresh(task.get("summary", "")):
        return task

    body = (mail or {}).get("body") or task.get("raw_body") or ""
    pdf_text = "\n".join(
        file.get("text", "")
        for file in ((mail or {}).get("pdf_files") or [])
        if file.get("text")
    )
    source_text = "\n".join(part for part in (body, pdf_text) if part)
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


def _needs_summary_refresh(summary: str) -> bool:
    """Detect summaries that still use the old single-line verbose format."""
    normalized = " ".join((summary or "").split())
    if not normalized:
        return True
    if "\n" in (summary or ""):
        return False
    if len(normalized) > 90:
        return True

    legacy_markers = ("업무유형", "우선순위", "파일명", "마감기한", "상세")
    return any(marker in normalized for marker in legacy_markers)
