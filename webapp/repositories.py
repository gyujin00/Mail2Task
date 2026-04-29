from __future__ import annotations

from typing import Any

import database


def list_tasks() -> list[dict[str, Any]]:
    """tasks 컬렉션에서 화면 표시에 필요한 문서를 조회한다(현재는 전체)."""
    return database.fetch_tasks()


def get_task(task_id: str) -> dict[str, Any] | None:
    """task_id(id 포함)로 단건 조회."""
    return database.fetch_task(task_id)


def get_mail(mail_id: str) -> dict[str, Any] | None:
    """mail_id로 mails 컬렉션 단건 조회(상세 화면에서 원본 메일 표시용)."""
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


def set_task_status_completed(task_id: str) -> None:
    """업무 완료 처리(상태 변경). 알림 발송은 notifier가 담당."""
    database.update_task(task_id, {"status": "완료"})

