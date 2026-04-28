"""
업무 분류 보조 모듈.

이 모듈은 아래 역할만 담당한다.
- 긴급도 점수 계산
- 중복 업무 판별
- 제목 기반 유사 업무 묶기

마감일 해석은 deadline_parser.py에서만 수행해
프로젝트 전체가 하나의 기준을 쓰도록 맞춘다.
"""

from __future__ import annotations

import re
from datetime import date, datetime

import config


URGENT_KEYWORDS = [
    "즉시",
    "긴급",
    "오늘",
    "지금 바로",
    "ASAP",
    "asap",
    "급합니다",
    "급히",
]

HIGH_KEYWORDS = [
    "이번 주",
    "금요일까지",
    "주말 전",
    "내일까지",
]

MID_KEYWORDS = [
    "다음 주",
    "이번 달",
]

DEFAULT_PRIORITY_SCORES = {
    "상": 70,
    "중": 40,
    "하": 10,
    "high": 70,
    "medium": 40,
    "low": 10,
}


def score_urgency(text, received_at, deadline=""):
    """
    우선순위 필드, 키워드, 남은 마감일을 기준으로 긴급도를 계산한다.

    Returns:
        tuple[int, str, str]: (점수, 등급, 마감일)
    """
    # 기존 호출부와의 호환성을 위해 인자는 유지한다.
    del received_at

    score = 0

    # 메일 양식에 우선순위가 있으면 그 값을 가장 먼저 사용한다.
    priority_score = _parse_priority(text)
    if priority_score is not None:
        score = priority_score
    else:
        # 구조화된 우선순위가 없을 때만 비정형 키워드로 점수를 보완한다.
        for keyword in URGENT_KEYWORDS:
            if keyword in text:
                score += 80  # "즉시", "긴급" 키워드는 가장 강한 시그널 (자연어 강조)
                break

        for keyword in HIGH_KEYWORDS:
            if keyword in text:
                score += 30
                break

        for keyword in MID_KEYWORDS:
            if keyword in text:
                score += 10
                break

    # 마감일은 deadline_parser.py에서 이미 해석된 값을 전달받아 사용한다.
    if deadline:
        try:
            due_date = datetime.strptime(deadline, "%Y-%m-%d").date()
            days_left = (due_date - date.today()).days
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
        level = "상시"

    return score, level, deadline


def _parse_priority(text):
    """
    '우선순위: 상' 같은 구조화된 필드를 찾아 점수로 변환한다.

    Returns:
        int | None
    """
    match = re.search(
        r"(?:우선순위|priority)\s*[:：]?\s*(상|중|하|high|medium|low)",
        text,
        flags=re.IGNORECASE,
    )
    if not match:
        return None

    label = match.group(1)
    mapping = dict(DEFAULT_PRIORITY_SCORES)
    config_mapping = getattr(config, "PRIORITY_SCORE", None)
    if isinstance(config_mapping, dict):
        mapping.update(config_mapping)

    return mapping.get(label.lower(), mapping.get(label))


def is_duplicate(subject, sender, existing_todos):
    """같은 제목/발신자 조합이 이미 저장되어 있는지 확인한다."""
    for todo in existing_todos:
        if todo.get("subject") == subject and todo.get("sender") == sender:
            return True
    return False


def group_similar_tasks(todos):
    """제목 유사도가 높은 업무끼리 묶어서 반환한다."""
    used = set()
    groups = []

    for index, left in enumerate(todos):
        if index in used:
            continue

        group = [left]
        used.add(index)

        for other_index, right in enumerate(todos):
            if other_index in used:
                continue

            # 제목 단어 집합이 절반 이상 겹치면 같은 그룹으로 본다.
            if _similarity(_task_label(left), _task_label(right)) >= 0.5:
                group.append(right)
                used.add(other_index)

        groups.append(group)

    return groups


def _normalize_subject(subject):
    """제목에서 노이즈 제거 후 정규화하여 유사도 비교 정확도를 높인다."""
    # [말머리] 제거 (예: [업무요청], [기획] 등)
    text = re.sub(r"^\[.+?\]\s*", "", subject)

    # 날짜 패턴 제거
    text = re.sub(r"\(~\d{1,2}/\d{1,2}\)", "", text)  # (~04/30) 형식
    text = re.sub(r"\d{4}[-./]\d{1,2}[-./]\d{1,2}", "", text)  # 2026-05-02 형식

    # 공백 정규화 (여러 공백 → 1개)
    return " ".join(text.split())


def _similarity(left_text, right_text):
    """정규화된 제목의 단어 집합으로 Jaccard 유사도를 계산한다."""
    left_words = set(_normalize_subject(left_text).split())
    right_words = set(_normalize_subject(right_text).split())
    if not left_words or not right_words:
        return 0.0
    return len(left_words & right_words) / len(left_words | right_words)


def _task_label(task):
    """Task 문서가 있으면 title을, 아니면 기존 subject를 비교 기준으로 사용한다."""
    return task.get("title") or task.get("subject", "")
