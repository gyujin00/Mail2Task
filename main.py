"""
Task-Harvester: 이메일 기반 지능형 업무 자동 채집 시스템
파이프라인: 메일 수신 → 마감일 해석 → LLM 요약 → 분류 → CSV 저장 → 완료 알림
"""
import config
from mail_reader    import fetch_target_mails        # 규진 차
from pdf_extractor  import extract_text_from_pdf     # 승민 홍
from deadline_parser import parse_deadline           # 승민 홍
from summarizer     import summarize                 # 승민 홍
from stats          import print_stats               # 승민 홍
from classifier     import score_urgency, is_duplicate, group_similar_tasks  # 규진 차
from todo_manager   import load_todos, save_todo, update_status, get_completed_unnotified  # kdh
from notifier       import send_completion_notice    # 규진 차


def run_inbound_pipeline():
    """신규 업무 메일을 수집하여 todo_list.csv에 저장한다."""
    print("=== [1단계] 메일 수신 시작 ===")
    mails = fetch_target_mails()

    if not mails:
        print("새로운 업무 메일 없음.")
        return

    existing_todos = load_todos()

    for mail_info in mails:
        subject    = mail_info["subject"]
        sender     = mail_info["sender"]
        body       = mail_info["body"]
        pdf_paths  = mail_info["pdf_paths"]
        received_at = mail_info["received_at"]

        print(f"\n[처리 중] {subject} | {sender}")

        # PDF 텍스트 추출
        pdf_text = ""
        for path in pdf_paths:
            pdf_text += extract_text_from_pdf(path)

        # 제목의 (~04/30) 같은 표현도 마감일 해석에 쓰이므로 함께 합친다.
        full_text = "\n".join(part for part in [subject, body, pdf_text] if part)

        # 중복 감지
        if is_duplicate(subject, sender, existing_todos):
            print(f"  -> 중복 감지, 건너뜀: {subject}")
            continue

        # 마감일 해석 (승민 홍)
        deadline = parse_deadline(full_text, received_at)

        # LLM 요약 (승민 홍)
        task_summary = summarize(full_text)

        # 긴급도 분류 (규진 차) — deadline은 이미 파싱된 값 사용
        # 마감일은 deadline_parser에서 한 번만 해석하고 classifier는 그 결과만 사용한다.
        urgency_score, urgency_level, _ = score_urgency(
            full_text,
            received_at,
            deadline=deadline,
        )

        task = {
            "subject":       subject,
            "sender":        sender,
            "deadline":      deadline,
            "task_summary":  task_summary,
            "task_type":     "",        # kdh: classify_task_type 내부에서 처리
            "urgency_score": urgency_score,
            "urgency_level": urgency_level,
            "status":        "대기",
            "received_at":   received_at,
        }

        save_todo(task, existing_todos)
        print(f"  -> 저장 완료 | 긴급도: {urgency_level}({urgency_score}점) | 마감: {deadline}")

    # 유사 업무 묶기 (규진 차)
    all_todos = load_todos()
    groups = group_similar_tasks(all_todos)
    similar = [g for g in groups if len(g) > 1]
    if similar:
        print(f"\n[유사 업무 그룹 감지] {len(similar)}개 그룹")
        for g in similar:
            print(f"  - {[t['subject'] for t in g]}")

    print("\n=== 수신 파이프라인 완료 ===")


def run_outbound_pipeline():
    """완료된 태스크 발신자에게 완료 알림을 보낸다."""
    print("=== [2단계] 완료 알림 발송 시작 ===")

    # kdh의 알림 트리거 함수로 완료 미알림 항목 조회
    pending = get_completed_unnotified()

    for todo in pending:
        result = send_completion_notice(todo["sender"], todo["subject"])
        if result:
            update_status(todo["id"], notified=True)
            print(f"  -> 알림 발송 완료: {todo['sender']} | {todo['subject']}")

    print("=== 발송 파이프라인 완료 ===")


if __name__ == "__main__":
    if not config.EMAIL or not config.PASSWORD:
        print("[오류] 환경변수를 설정하세요.")
        print("  set TASK_EMAIL=your@gmail.com")
        print("  set TASK_PASSWORD=앱비밀번호16자리")
        exit(1)

    run_inbound_pipeline()
    run_outbound_pipeline()
    print()
    print_stats()
