"""
담당: 규진 차
역할: 업무 긴급도 분류 / 중복 업무 감지 / 비슷한 업무끼리 묶기
"""
import re
from datetime import datetime, date
import config


# ─────────────────────────────────────────
# 1. 업무 긴급도 분류
# ─────────────────────────────────────────

URGENT_KEYWORDS = ["즉시", "긴급", "오늘", "지금 바로", "ASAP", "asap", "급합니다", "급히"]
HIGH_KEYWORDS   = ["이번 주", "금요일까지", "주말 전", "내일까지"]
MID_KEYWORDS    = ["다음 주", "이번 달"]

def score_urgency(text, received_at):
    """
    메일 본문을 분석하여 긴급도 점수, 등급, 마감일을 반환한다.

    인자:
        text        (str): 메일 본문 + PDF 텍스트
        received_at (str): 수신 일시 "YYYY-MM-DD HH:MM"

    반환:
        tuple(int, str, str): (긴급도 점수 0~100, 등급, 마감일 "YYYY-MM-DD")
        등급: "긴급" | "보통" | "여유"
        마감일: 파싱 실패 시 ""
    """
    score = 0

    for kw in URGENT_KEYWORDS:
        if kw in text:
            score += 50
            break

    for kw in HIGH_KEYWORDS:
        if kw in text:
            score += 30
            break

    for kw in MID_KEYWORDS:
        if kw in text:
            score += 10
            break

    deadline = _parse_deadline(text, received_at)
    if deadline:
        try:
            dl = datetime.strptime(deadline, "%Y-%m-%d").date()
            days_left = (dl - date.today()).days
            if days_left <= 1:
                score += 30
            elif days_left <= 3:
                score += 20
            elif days_left <= 7:
                score += 10
        except ValueError:
            pass

    score = min(score, 100)

    if score >= config.URGENCY_HIGH:
        level = "긴급"
    elif score >= config.URGENCY_MID:
        level = "보통"
    else:
        level = "여유"

    return score, level, deadline


def _parse_deadline(text, received_at):
    """텍스트에서 마감일을 추출한다. 실패 시 빈 문자열 반환."""
    # "YYYY-MM-DD" 또는 "YYYY/MM/DD" 형식
    m = re.search(r"(\d{4})[.\-/](\d{1,2})[.\-/](\d{1,2})", text)
    if m:
        return f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"

    # "MM월 DD일" 형식 → 수신 연도 기준으로 보완
    m = re.search(r"(\d{1,2})월\s*(\d{1,2})일", text)
    if m:
        try:
            year = datetime.strptime(received_at, "%Y-%m-%d %H:%M").year
            return f"{year}-{int(m.group(1)):02d}-{int(m.group(2)):02d}"
        except ValueError:
            pass

    return ""


# ─────────────────────────────────────────
# 2. 중복 업무 감지
# ─────────────────────────────────────────

def is_duplicate(subject, sender, existing_todos):
    """
    동일한 subject + sender 조합이 CSV에 이미 존재하는지 확인한다.

    인자:
        subject        (str): 메일 제목
        sender         (str): 발신자 이메일
        existing_todos (list[dict]): load_todos() 반환값

    반환:
        bool: True면 중복
    """
    for todo in existing_todos:
        if todo.get("subject") == subject and todo.get("sender") == sender:
            return True
    return False


# ─────────────────────────────────────────
# 3. 비슷한 업무끼리 묶기
# ─────────────────────────────────────────

def group_similar_tasks(todos):
    """
    업무 목록에서 제목이 유사한 태스크를 그룹으로 묶어 반환한다.

    인자:
        todos (list[dict]): load_todos() 반환값

    반환:
        list[list[dict]]: 유사한 태스크끼리 묶인 그룹 목록
                          단독 태스크는 원소가 1개인 리스트로 포함됨

    예시:
        [
            [{"subject": "보고서 제출 요청"}, {"subject": "보고서 작성 요청"}],
            [{"subject": "회의 일정 확인"}],
        ]
    """
    used = set()
    groups = []

    for i, t1 in enumerate(todos):
        if i in used:
            continue
        group = [t1]
        used.add(i)
        for j, t2 in enumerate(todos):
            if j in used:
                continue
            if _similarity(t1["subject"], t2["subject"]) >= 0.5:
                group.append(t2)
                used.add(j)
        groups.append(group)

    return groups


def _similarity(s1, s2):
    """두 문자열의 단어 집합 기반 유사도를 반환한다 (Jaccard)."""
    w1 = set(s1.split())
    w2 = set(s2.split())
    if not w1 or not w2:
        return 0.0
    return len(w1 & w2) / len(w1 | w2)
