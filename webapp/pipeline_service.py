from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import config
from mail_reader import fetch_target_mails
from pdf_extractor import extract_text_from_pdf
from task_extractor import extract_tasks_from_mail
from todo_manager_adapter import load_tasks, mail_exists, save_mail, save_tasks


@dataclass(frozen=True)
class SyncResult:
    """동기화 결과를 화면에 표시하기 위한 요약 값."""
    fetched_mails: int
    new_mails: int
    new_tasks: int
    failed: int


def sync_inbound() -> SyncResult:
    """
    기존 `main.run_inbound_pipeline()`과 동일한 파이프라인을 웹에서 재사용한다.
    - 메일 수집
    - PDF 텍스트 추출
    - mails/tasks 저장 (중복 방지)
    - 메일 1건 → task N건 구조 유지

    설계 포인트:
    - “기존 핵심 로직”을 바꾸지 않고 웹에서 호출할 수 있도록,
      main.py의 흐름을 함수 형태로 옮겨 담았다.
    - 중복 방지는 `todo_manager_adapter.mail_exists()`의 mail_id 기반 로직을 그대로 사용한다.
    """
    if not config.EMAIL or not config.PASSWORD:
        raise RuntimeError("메일 계정 정보가 설정되지 않았습니다. 설정 페이지에서 먼저 저장하세요.")

    mails = fetch_target_mails()
    fetched = len(mails)
    new_mails = 0
    new_tasks = 0
    failed = 0

    for mail_info in mails:
        try:
            subject = mail_info.get("subject", "")
            sender = mail_info.get("sender", "")
            body = mail_info.get("body", "")
            pdf_paths = mail_info.get("pdf_paths", [])
            received_at = mail_info.get("received_at", "")

            if mail_exists(subject, sender, received_at):
                continue

            # 기존 파이프라인과 동일하게:
            # 다운로드된 pdf_paths를 pdf_files(텍스트 포함)로 변환해 mails 문서에 저장한다.
            pdf_files = []
            for path in pdf_paths:
                pdf_files.append(
                    {
                        "filename": Path(path).name,
                        "path": path,
                        "text": extract_text_from_pdf(path),
                    }
                )

            mail_document = save_mail(
                {
                    "subject": subject,
                    "sender": sender,
                    "received_at": received_at,
                    "body": body,
                    "pdf_files": pdf_files,
                }
            )
            new_mails += 1

            # 메일 1건에서 Task가 여러 개 나올 수 있으므로 리스트로 저장한다.
            tasks = extract_tasks_from_mail(mail_document)
            saved_tasks = save_tasks(tasks)
            new_tasks += len(saved_tasks)
        except Exception:
            # 웹에서는 “전체 동기화가 멈추는 것”보다 “부분 성공 + 실패 카운트”가 유용하다.
            failed += 1

    # 유사 업무 그룹 계산은 콘솔 출력용이어서 웹 동기화 결과에서는 제외한다.
    _ = load_tasks()

    return SyncResult(
        fetched_mails=fetched,
        new_mails=new_mails,
        new_tasks=new_tasks,
        failed=failed,
    )

