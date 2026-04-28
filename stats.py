"""
MongoDB에 저장된 Task 문서 기준 통계 모듈.

현재 통계는 아래 지표를 제공한다.
- 전체 업무 수
- 상태별 수
- 긴급도별 수
- 업무유형별 수
- 말머리별 수
- PDF 첨부 포함 업무 수
- 오늘 마감 업무 수
- 이번 주 마감 업무 수
- 기한 초과 업무 수
"""

from __future__ import annotations

from datetime import date, datetime, timedelta

from todo_manager import load_tasks


def print_stats():
    """MongoDB 기반 업무 통계를 보기 좋게 출력한다."""
    stats = get_stats()

    if stats["total"] == 0:
        print("저장된 업무가 없습니다.")
        return

    print("=" * 40)
    print("         Task-Harvester 업무 통계")
    print("=" * 40)
    print(f"전체 업무 수: {stats['total']}건")
    print(f"PDF 첨부 포함: {stats['with_pdf_count']}건")
    print(f"오늘 마감: {stats['due_today_count']}건")
    print(f"이번 주 마감: {stats['due_this_week_count']}건")
    print(f"기한 초과: {stats['overdue_count']}건")

    print("\n[상태별]")
    _print_count_block(stats["by_status"])

    print("\n[긴급도별]")
    _print_count_block(stats["by_urgency"])

    print("\n[업무유형별]")
    _print_count_block(stats["by_type"])

    print("\n[말머리별]")
    _print_count_block(stats["by_category"])
    print("=" * 40)


def get_stats():
    """MongoDB tasks 컬렉션을 읽어 통계를 dict 형태로 반환한다."""
    todos = load_tasks()

    today = date.today()
    start_of_week = today
    end_of_week = today + timedelta(days=(6 - today.weekday()))
    now = datetime.now()

    due_today_count = 0
    due_this_week_count = 0
    overdue_count = 0
    with_pdf_count = 0

    for todo in todos:
        if todo.get("has_pdf"):
            with_pdf_count += 1

        deadline_date = _parse_date(todo.get("deadline_date") or todo.get("deadline", ""))
        if not deadline_date:
            continue

        if deadline_date == today:
            due_today_count += 1

        if start_of_week <= deadline_date <= end_of_week:
            due_this_week_count += 1

        deadline_at = _parse_datetime(todo.get("deadline_at", ""))
        if deadline_at and deadline_at < now and todo.get("status") != "완료":
            overdue_count += 1
        elif not deadline_at and deadline_date < today and todo.get("status") != "완료":
            overdue_count += 1

    return {
        "total": len(todos),
        "by_status": _count_by(todos, "status"),
        "by_urgency": _count_by(todos, "urgency_level"),
        "by_type": _count_by(todos, "task_type"),
        "by_category": _count_by(todos, "mail_category"),
        "with_pdf_count": with_pdf_count,
        "due_today_count": due_today_count,
        "due_this_week_count": due_this_week_count,
        "overdue_count": overdue_count,
    }


def _count_by(todos, key):
    """지정한 키 값별 개수를 센다."""
    result = {}
    for todo in todos:
        value = todo.get(key) or "미분류"
        result[value] = result.get(value, 0) + 1
    return dict(sorted(result.items(), key=lambda item: (-item[1], item[0])))


def _parse_date(value):
    """YYYY-MM-DD 문자열을 date 객체로 변환한다."""
    if not value:
        return None

    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def _parse_datetime(value):
    """ISO 형태의 마감 시각 문자열을 datetime 객체로 변환한다."""
    if not value:
        return None

    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _print_count_block(counter):
    """카운트 결과를 한 줄씩 출력한다."""
    if not counter:
        print("  없음")
        return

    for key, value in counter.items():
        print(f"  {key}: {value}건")
