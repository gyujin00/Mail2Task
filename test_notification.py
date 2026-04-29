"""
작업 완료 알림 자동화 테스트 스크립트
"""
from datetime import datetime
from mongo_task_store import save_tasks, get_completed_unnotified, update_status
from notifier import send_completion_notice

def create_test_tasks():
    """테스트용 완료 task 생성"""
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
    print(f"[OK] 테스트 task {len(saved)}개 생성 완료")
    return saved

def test_notification_system():
    """알림 시스템 테스트"""
    print("\n=== 작업 완료 알림 자동화 테스트 ===\n")

    # 1. 테스트 데이터 생성
    print("[1단계] 테스트 데이터 생성")
    create_test_tasks()

    # 2. 완료되었지만 미알림 task 조회
    print("\n[2단계] 완료 & 미알림 task 조회")
    pending = get_completed_unnotified()
    print(f"[OK] 알림 대기 중인 task: {len(pending)}개")
    for task in pending:
        print(f"  - {task['title']} (발신자: {task['sender']})")

    if not pending:
        print("\n[FAIL] 알림 대기 중인 task가 없습니다.")
        return

    # 3. 알림 발송 테스트
    print("\n[3단계] 알림 발송 테스트")
    for task in pending:
        print(f"\n처리 중: {task['title']}")
        try:
            # 실제 메일 발송
            result = send_completion_notice(task)

            if result:
                update_status(task["task_id"], notified=True)
                print(f"  [OK] 알림 발송 완료: {task['sender']}")
                print(f"    - 제목: {task['title']}")
                print(f"    - 마감일: {task.get('deadline_date', '미정')}")
                print(f"    - 긁급도: {task.get('urgency_level', '')} ({task.get('urgency_score', 0)}점)")
            else:
                print(f"  [FAIL] 알림 발송 실패")
        except Exception as e:
            print(f"  [ERROR] 오류 발생: {e}")

    # 4. 결과 확인
    print("\n[4단계] 결과 확인")
    remaining = get_completed_unnotified()
    print(f"[OK] 남은 미알림 task: {len(remaining)}개")

    print("\n=== 테스트 완료 ===")
    print("\n[INFO] 실제 메일 발송 테스트:")
    print("   1. test_notification.py에서 'result = True' 주석 해제")
    print("   2. 'result = send_completion_notice(task)' 주석 제거")
    print("   3. .env 파일의 TASK_EMAIL, TASK_PASSWORD 확인")

if __name__ == "__main__":
    test_notification_system()
