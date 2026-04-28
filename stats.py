"""
담당: 승민 홍
역할: 업무 통계 - todo_list.csv 기반 현황 집계 및 출력
"""
from todo_manager import load_todos


def print_stats():
    """todo_list.csv 기반 업무 현황 통계를 출력한다."""
    todos = load_todos()

    if not todos:
        print("저장된 업무가 없습니다.")
        return

    total     = len(todos)
    by_status = _count_by(todos, "status")
    by_level  = _count_by(todos, "urgency_level")
    by_type   = _count_by(todos, "task_type")

    print("=" * 35)
    print("        Task-Harvester 업무 통계")
    print("=" * 35)
    print(f"전체 업무 수: {total}건\n")

    print("[상태별]")
    for k, v in by_status.items():
        print(f"  {k}: {v}건")

    print("\n[긴급도별]")
    for k, v in by_level.items():
        print(f"  {k}: {v}건")

    print("\n[유형별]")
    for k, v in by_type.items():
        print(f"  {k}: {v}건")
    print("=" * 35)


def get_stats():
    """
    통계를 dict로 반환한다.

    반환:
        dict: {
            "total": int,
            "by_status": dict,
            "by_urgency": dict,
            "by_type": dict,
        }
    """
    # TODO: print_stats와 동일한 집계를 dict로 반환
    return {}


def _count_by(todos, key):
    result = {}
    for todo in todos:
        val = todo.get(key, "미분류")
        result[val] = result.get(val, 0) + 1
    return result
