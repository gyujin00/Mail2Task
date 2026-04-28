"""
Task-Harvester 메인 실행 파일.

흐름:
1. 메일 수집
2. PDF 텍스트 추출
3. 마감일 해석
4. 요약 생성
5. 긴급도 계산
6. MongoDB 저장
7. 완료 알림 발송
8. 통계 출력
"""

from pathlib import Path

import config
from classifier import group_similar_tasks
from mail_reader import fetch_target_mails
from mongo_task_store import (
    get_completed_unnotified,
    load_tasks,
    mail_exists,
    save_mail,
    save_tasks,
    update_status,
)
from notifier import send_completion_notice
from pdf_extractor import extract_text_from_pdf
from stats import print_stats
from task_extractor import extract_tasks_from_mail


def run_inbound_pipeline():
    """신규 업무 메일을 수집해 저장소에 적재한다."""
    print("=== [1단계] 메일 수신 시작 ===")
    mails = fetch_target_mails()

    if not mails:
        print("새로 수집된 업무 메일이 없습니다.")
        return

    for mail_info in mails:
        subject = mail_info["subject"]
        sender = mail_info["sender"]
        body = mail_info["body"]
        pdf_paths = mail_info["pdf_paths"]
        received_at = mail_info["received_at"]

        print(f"\n[처리 중] {subject} | {sender}")

        if mail_exists(subject, sender, received_at):
            print(f"  -> 이미 저장된 메일이라 건너뜀: {subject}")
            continue

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
        tasks = extract_tasks_from_mail(mail_document)
        saved_tasks = save_tasks(tasks)

        print(f"  -> 메일 저장 완료 | 추출 업무 {len(saved_tasks)}건")
        for task in saved_tasks:
            deadline_text = task.get("deadline_date") or "미정"
            print(
                f"     - {task['title']} | 긴급도 {task['urgency_level']}({task['urgency_score']}) | 마감: {deadline_text}"
            )

    all_todos = load_tasks()
    groups = group_similar_tasks(all_todos)
    similar = [group for group in groups if len(group) > 1]
    if similar:
        print(f"\n[유사 업무 그룹 감지] {len(similar)}개 그룹")
        for group in similar:
            print(f"  - {[task.get('title') or task['subject'] for task in group]}")

    print("\n=== 수신 파이프라인 완료 ===")


def run_outbound_pipeline():
    """완료되었지만 알림이 안 간 업무에 대해 완료 메일을 발송한다."""
    print("=== [2단계] 완료 알림 발송 시작 ===")

    pending = get_completed_unnotified()

    for todo in pending:
        result = send_completion_notice(todo)
        if result:
            update_status(todo["task_id"], notified=True)
            task_title = todo.get("title") or todo["subject"]
            print(f"  -> 알림 발송 완료: {todo['sender']} | {task_title}")

    print("=== 발송 파이프라인 완료 ===")


if __name__ == "__main__":
    if not config.EMAIL or not config.PASSWORD:
        print("[오류] 메일 계정 정보를 먼저 설정하세요.")
        print("  .env 파일에 TASK_EMAIL, TASK_PASSWORD를 입력하세요.")
        raise SystemExit(1)

    run_inbound_pipeline()
    run_outbound_pipeline()
    print()
    print_stats()
