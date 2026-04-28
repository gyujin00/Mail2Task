# ============================================================
# classifier.py 테스트 스크립트
# ============================================================
# 테스트 항목:
#   1. group_similar_tasks - 정규화 기능 (말머리/날짜 제거)
#   2. is_duplicate - 중복 감지
#   3. score_urgency - 긴급도 계산
#
# 실행: python test_classifier.py
# ============================================================

from classifier import group_similar_tasks, is_duplicate, score_urgency


def test_group_similar_tasks():
    """유사 업무 그룹핑 테스트 (정규화 기능 검증)"""
    print("=" * 60)
    print("TEST 1: 유사 업무 그룹핑 (정규화 기능)")
    print("=" * 60)

    # 테스트 케이스: 말머리가 다르지만 내용이 같은 경우
    todos = [
        {"subject": "[업무요청] 로고 디자인 검토"},
        {"subject": "[기획] 로고 디자인 검토"},
        {"subject": "[업무요청] 서버 점검"},
    ]

    groups = group_similar_tasks(todos)
    similar = [g for g in groups if len(g) > 1]

    print(f"\n입력 업무 {len(todos)}건:")
    for t in todos:
        print(f"  - {t['subject']}")

    print(f"\n유사 그룹 {len(similar)}개:")
    for i, g in enumerate(similar, 1):
        print(f"  그룹 {i}: {[t['subject'] for t in g]}")

    print("\n[OK] 예상: '로고 디자인 검토' 2건이 같은 그룹으로 묶여야 함")
    print(f"[OK] 결과: {'PASS' if len(similar) == 1 and len(similar[0]) == 2 else 'FAIL'}")

    # 테스트 케이스 2: 날짜만 다른 경우
    print("\n" + "-" * 60)
    todos2 = [
        {"subject": "[업무요청] 브랜드 리뉴얼 건 (~04/30)"},
        {"subject": "[업무요청] 브랜드 리뉴얼 건 (~05/01)"},
        {"subject": "[업무요청] 웹사이트 개편 (~05/02)"},
    ]

    groups2 = group_similar_tasks(todos2)
    similar2 = [g for g in groups2 if len(g) > 1]

    print(f"\n입력 업무 {len(todos2)}건:")
    for t in todos2:
        print(f"  - {t['subject']}")

    print(f"\n유사 그룹 {len(similar2)}개:")
    for i, g in enumerate(similar2, 1):
        print(f"  그룹 {i}: {[t['subject'] for t in g]}")

    print("\n[OK] 예상: '브랜드 리뉴얼 건' 2건이 같은 그룹으로 묶여야 함")
    print(f"[OK] 결과: {'PASS' if len(similar2) == 1 and len(similar2[0]) == 2 else 'FAIL'}")


def test_is_duplicate():
    """중복 업무 감지 테스트"""
    print("\n" + "=" * 60)
    print("TEST 2: 중복 업무 감지")
    print("=" * 60)

    existing_todos = [
        {"subject": "[업무요청] 로고 디자인", "sender": "user1@example.com"},
        {"subject": "[업무요청] 서버 점검", "sender": "user2@example.com"},
    ]

    # 케이스 1: 완전 중복
    result1 = is_duplicate("[업무요청] 로고 디자인", "user1@example.com", existing_todos)
    print(f"\n케이스 1 - 같은 제목 + 같은 발신자")
    print(f"  입력: [업무요청] 로고 디자인 from user1@example.com")
    print(f"  예상: True (중복)")
    print(f"  결과: {result1} - {'PASS' if result1 else 'FAIL'}")

    # 케이스 2: 같은 제목, 다른 발신자
    result2 = is_duplicate("[업무요청] 로고 디자인", "user3@example.com", existing_todos)
    print(f"\n케이스 2 - 같은 제목 + 다른 발신자")
    print(f"  입력: [업무요청] 로고 디자인 from user3@example.com")
    print(f"  예상: False (중복 아님)")
    print(f"  결과: {result2} - {'PASS' if not result2 else 'FAIL'}")

    # 케이스 3: 다른 제목, 같은 발신자
    result3 = is_duplicate("[업무요청] 웹사이트 개편", "user1@example.com", existing_todos)
    print(f"\n케이스 3 - 다른 제목 + 같은 발신자")
    print(f"  입력: [업무요청] 웹사이트 개편 from user1@example.com")
    print(f"  예상: False (중복 아님)")
    print(f"  결과: {result3} - {'PASS' if not result3 else 'FAIL'}")


def test_score_urgency():
    """긴급도 계산 테스트"""
    print("\n" + "=" * 60)
    print("TEST 3: 긴급도 계산")
    print("=" * 60)

    test_cases = [
        {
            "text": "우선순위: 상\n로고 디자인 검토 부탁드립니다.",
            "deadline": "2026-04-29",
            "expected_level": "긴급",
            "desc": "우선순위: 상 + D-1",
        },
        {
            "text": "우선순위: 중\n서버 점검 요청드립니다.",
            "deadline": "2026-05-10",
            "expected_level": "보통",
            "desc": "우선순위: 중",
        },
        {
            "text": "우선순위: 하\n일반 업무입니다.",
            "deadline": "",
            "expected_level": "상시",
            "desc": "우선순위: 하",
        },
        {
            "text": "즉시 처리 부탁드립니다. 긴급합니다.",
            "deadline": "",
            "expected_level": "긴급",
            "desc": "긴급 키워드",
        },
    ]

    received_at = "2026-04-28 10:00"

    for i, case in enumerate(test_cases, 1):
        score, level, _ = score_urgency(case["text"], received_at, deadline=case["deadline"])
        is_pass = level == case["expected_level"]

        print(f"\n케이스 {i} - {case['desc']}")
        print(f"  결과: {level} ({score}점)")
        print(f"  예상: {case['expected_level']}")
        print(f"  {'[OK] PASS' if is_pass else '[FAIL] FAIL'}")


def main():
    print("\n")
    print("=" * 60)
    print(" " * 15 + "classifier.py 테스트")
    print("=" * 60)

    test_group_similar_tasks()
    test_is_duplicate()
    test_score_urgency()

    print("\n" + "=" * 60)
    print("테스트 완료")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
