from __future__ import annotations

try:
    from tests._bootstrap import ROOT_DIR
except ModuleNotFoundError:
    from _bootstrap import ROOT_DIR

del ROOT_DIR

from classifier import group_similar_tasks, is_duplicate, score_urgency


def test_group_similar_tasks() -> None:
    print("=" * 60)
    print("TEST 1: group similar tasks")
    print("=" * 60)

    todos = [
        {"subject": "[업무요청] 로고 수정 검토"},
        {"subject": "[기획] 로고 수정 검토"},
        {"subject": "[업무요청] 서버 점검"},
    ]

    groups = group_similar_tasks(todos)
    similar = [group for group in groups if len(group) > 1]
    print(f"similar groups: {similar}")
    print(f"PASS: {len(similar) == 1 and len(similar[0]) == 2}")


def test_is_duplicate() -> None:
    print("\n" + "=" * 60)
    print("TEST 2: duplicate detection")
    print("=" * 60)

    existing_todos = [
        {"subject": "[업무요청] 로고 수정", "sender": "user1@example.com"},
        {"subject": "[업무요청] 서버 점검", "sender": "user2@example.com"},
    ]

    print(is_duplicate("[업무요청] 로고 수정", "user1@example.com", existing_todos))
    print(is_duplicate("[업무요청] 로고 수정", "user3@example.com", existing_todos))
    print(is_duplicate("[업무요청] 사이트 개편", "user1@example.com", existing_todos))


def test_score_urgency() -> None:
    print("\n" + "=" * 60)
    print("TEST 3: urgency scoring")
    print("=" * 60)

    test_cases = [
        {
            "text": "우선순위: 상\n로고 수정 검토 부탁드립니다.",
            "deadline": "2026-04-29",
            "expected_level": "긴급",
        },
        {
            "text": "우선순위: 중\n서버 점검 요청드립니다.",
            "deadline": "2026-05-10",
            "expected_level": "보통",
        },
        {
            "text": "우선순위: 하\n일반 업무입니다.",
            "deadline": "",
            "expected_level": "상시",
        },
    ]

    received_at = "2026-04-28 10:00"
    for case in test_cases:
        score, level, deadline = score_urgency(case["text"], received_at, deadline=case["deadline"])
        print(level, score, deadline, level == case["expected_level"])


def main() -> None:
    test_group_similar_tasks()
    test_is_duplicate()
    test_score_urgency()


if __name__ == "__main__":
    main()
