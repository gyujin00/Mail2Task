from __future__ import annotations

try:
    from tests._bootstrap import ROOT_DIR
except ModuleNotFoundError:
    from _bootstrap import ROOT_DIR

del ROOT_DIR

from mail.notifier import send_completion_notice
from storage.mongo_task_store import get_completed_unnotified, save_tasks, update_status


def create_test_tasks():
    """Create a couple of completed but unnotified tasks for manual mail checks."""
    test_tasks = [
        {
            "task_id": "test_001",
            "mail_id": "mail_001",
            "title": "보고서 작성",
            "subject": "[업무요청] 보고서 작성",
            "sender": "ckrbwls1214@gmail.com",
            "status": "완료",
            "task_type": "보고서",
            "urgency_score": 70,
            "urgency_level": "긴급",
            "deadline_date": "2026-04-30",
            "deadline": "2026-04-30",
            "received_at": "2026-04-28T10:00:00",
            "notified": False,
            "task_order": 1,
        },
        {
            "task_id": "test_002",
            "mail_id": "mail_002",
            "title": "회의 참석",
            "subject": "[알림] 회의 참석",
            "sender": "ckrbwls1214@gmail.com",
            "status": "완료",
            "task_type": "회의",
            "urgency_score": 50,
            "urgency_level": "보통",
            "deadline_date": "2026-04-29",
            "deadline": "2026-04-29",
            "received_at": "2026-04-27T15:00:00",
            "notified": False,
            "task_order": 1,
        },
    ]

    saved = save_tasks(test_tasks)
    print(f"[OK] Created {len(saved)} test tasks")
    return saved


def test_notification_system() -> None:
    print("\n=== Completion notification test ===\n")

    print("[1/4] Creating sample tasks")
    create_test_tasks()

    print("\n[2/4] Fetching pending notification tasks")
    pending = get_completed_unnotified()
    print(f"[OK] Pending tasks: {len(pending)}")
    for task in pending:
        print(f"  - {task['title']} ({task['sender']})")

    if not pending:
        print("[FAIL] No pending tasks found.")
        return

    print("\n[3/4] Sending notifications")
    for task in pending:
        print(f"\nSending: {task['title']}")
        try:
            result = send_completion_notice(task)
            if result:
                update_status(task["task_id"], notified=True)
                print(f"  [OK] Sent to {task['sender']}")
            else:
                print("  [FAIL] Notification send failed")
        except Exception as exc:
            print(f"  [ERROR] {exc}")

    print("\n[4/4] Remaining pending tasks")
    remaining = get_completed_unnotified()
    print(f"[OK] Remaining pending tasks: {len(remaining)}")


if __name__ == "__main__":
    test_notification_system()
