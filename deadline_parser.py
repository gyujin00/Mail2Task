"""
마감일 해석 전담 모듈.

마감일은 여기서만 해석하고, 다른 모듈은 이 결과만 사용한다.
우선순위는 팀 메일 양식의 구조화 필드를 먼저 보고,
없으면 제목/본문의 일반적인 날짜 표현으로 내려가며 해석한다.
"""

from __future__ import annotations

import re
from datetime import date, datetime, timedelta


WEEKDAY_MAP = {
    "월": 0,
    "화": 1,
    "수": 2,
    "목": 3,
    "금": 4,
    "토": 5,
    "일": 6,
}


def parse_deadline(text, received_at):
    """마감일만 간단히 필요할 때 YYYY-MM-DD 문자열로 반환한다."""
    return parse_deadline_info(text, received_at)["date"]


def parse_deadline_info(text, received_at):
    """
    메일 텍스트에서 마감일 상세 정보를 추출한다.

    Returns:
        dict: {
            "date": "YYYY-MM-DD" or "",
            "time": "HH:MM" or "",
            "source": 추출 규칙 이름 또는 "",
            "raw_text": 실제로 매칭된 원문 또는 "",
        }
    """
    normalized_text = text or ""
    base_date = _parse_base_date(received_at)

    # 구조화된 필드를 가장 먼저 시도하고, 실패하면 점점 느슨한 패턴으로 내려간다.
    parsers = [
        _parse_structured_deadline_field,
        _parse_title_tilde_date,
        _parse_general_ymd_date,
        _parse_month_day_slash,
        _parse_korean_month_day,
        _parse_relative_weekday,
        _parse_relative_day,
    ]

    for parser in parsers:
        info = parser(normalized_text, base_date)
        if info:
            return info

    return {"date": "", "time": "", "source": "", "raw_text": ""}


def _parse_structured_deadline_field(text, base_date):
    """본문의 '마감기한: 2026-04-30 15:00' 같은 구조화된 형식을 우선 처리한다."""
    del base_date
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        if not any(keyword in line.lower() for keyword in ["deadline"]) and not any(
            keyword in line for keyword in ["마감기한", "마감"]
        ):
            continue

        date_match = re.search(
            r"(\d{4})[.\-/](\d{1,2})[.\-/](\d{1,2})",
            line,
        )
        if not date_match:
            continue

        time_match = re.search(r"(\d{1,2}):(\d{2})", line)
        return _build_info(
            year=int(date_match.group(1)),
            month=int(date_match.group(2)),
            day=int(date_match.group(3)),
            hour_text=time_match.group(1) if time_match else None,
            minute_text=time_match.group(2) if time_match else None,
            source="body_field",
            raw_text=line,
        )

    return None


def _parse_title_tilde_date(text, base_date):
    """제목에 자주 들어가는 '(~04/30)' 형태를 처리한다."""
    pattern = re.compile(r"(~\s*(\d{1,2})/(\d{1,2})(?:\s+(\d{1,2}):(\d{2}))?)")
    match = pattern.search(text)
    if not match:
        return None
    return _build_info(
        year=base_date.year,
        month=int(match.group(2)),
        day=int(match.group(3)),
        hour_text=match.group(4),
        minute_text=match.group(5),
        source="title_tilde",
        raw_text=match.group(1),
    )


def _parse_general_ymd_date(text, base_date):
    """본문 어디에 있든 YYYY-MM-DD, YYYY/MM/DD, YYYY.MM.DD를 처리한다."""
    del base_date
    pattern = re.compile(
        r"((\d{4})[.\-/](\d{1,2})[.\-/](\d{1,2})(?:\s+(\d{1,2}):(\d{2}))?)"
    )
    match = pattern.search(text)
    if not match:
        return None
    return _build_info(
        year=int(match.group(2)),
        month=int(match.group(3)),
        day=int(match.group(4)),
        hour_text=match.group(5),
        minute_text=match.group(6),
        source="general_ymd",
        raw_text=match.group(1),
    )


def _parse_month_day_slash(text, base_date):
    """연도가 없는 04/30 같은 표현은 수신 연도를 기준으로 보완한다."""
    pattern = re.compile(r"((?<!\d)(\d{1,2})/(\d{1,2})(?:\s+(\d{1,2}):(\d{2}))?)")
    match = pattern.search(text)
    if not match:
        return None
    return _build_info(
        year=base_date.year,
        month=int(match.group(2)),
        day=int(match.group(3)),
        hour_text=match.group(4),
        minute_text=match.group(5),
        source="month_day_slash",
        raw_text=match.group(1),
    )


def _parse_korean_month_day(text, base_date):
    """'4월 30일' 같은 한글 날짜 표현을 처리한다."""
    pattern = re.compile(
        r"((\d{1,2})\s*월\s*(\d{1,2})\s*일(?:\s+(\d{1,2}):(\d{2}))?)"
    )
    match = pattern.search(text)
    if not match:
        return None
    return _build_info(
        year=base_date.year,
        month=int(match.group(2)),
        day=int(match.group(3)),
        hour_text=match.group(4),
        minute_text=match.group(5),
        source="korean_month_day",
        raw_text=match.group(1),
    )


def _parse_relative_weekday(text, base_date):
    """'이번 주 금요일', '다음 주 월요일' 같은 상대 요일 표현을 처리한다."""
    pattern = re.compile(
        r"((이번|다음)\s*주\s*"
        r"([월화수목금토일])요일?"
        r"(?:\s*(\d{1,2}):(\d{2}))?)"
    )
    match = pattern.search(text)
    if not match:
        return None

    week_token = match.group(2)
    weekday_token = match.group(3)
    target_weekday = WEEKDAY_MAP[weekday_token]

    days_until = target_weekday - base_date.weekday()
    if week_token == "다음":
        # 다음 주는 최소 1주 이후가 되도록 보정한다.
        days_until += 7 if days_until >= 0 else 14
    elif days_until < 0:
        # 이번 주인데 이미 지난 요일이면 다음 주 같은 요일로 넘긴다.
        days_until += 7

    target_date = base_date + timedelta(days=days_until)
    return _build_info(
        year=target_date.year,
        month=target_date.month,
        day=target_date.day,
        hour_text=match.group(4),
        minute_text=match.group(5),
        source="relative_weekday",
        raw_text=match.group(1),
    )


def _parse_relative_day(text, base_date):
    """'내일까지', '3일 이내' 같은 상대 일수 표현을 처리한다."""
    tomorrow_match = re.search(
        r"(내일(?:까지)?(?:\s*(\d{1,2}):(\d{2}))?)",
        text,
    )
    if tomorrow_match:
        target_date = base_date + timedelta(days=1)
        return _build_info(
            year=target_date.year,
            month=target_date.month,
            day=target_date.day,
            hour_text=tomorrow_match.group(2),
            minute_text=tomorrow_match.group(3),
            source="relative_tomorrow",
            raw_text=tomorrow_match.group(1),
        )

    within_days_match = re.search(
        r"((\d+)\s*일\s*(?:이내|후|뒤)(?:\s*(\d{1,2}):(\d{2}))?)",
        text,
    )
    if not within_days_match:
        return None

    target_date = base_date + timedelta(days=int(within_days_match.group(2)))
    return _build_info(
        year=target_date.year,
        month=target_date.month,
        day=target_date.day,
        hour_text=within_days_match.group(3),
        minute_text=within_days_match.group(4),
        source="relative_days",
        raw_text=within_days_match.group(1),
    )


def _build_info(year, month, day, hour_text, minute_text, source, raw_text):
    """검증된 날짜/시간 정보를 공통 포맷으로 묶어 반환한다."""
    try:
        due_date = date(year, month, day)
    except ValueError:
        return None

    time_text = ""
    if hour_text is not None and minute_text is not None:
        try:
            hour = int(hour_text)
            minute = int(minute_text)
            # 잘못된 시간값은 마감 정보 전체를 버리도록 처리한다.
            if not (0 <= hour <= 23 and 0 <= minute <= 59):
                return None
            time_text = f"{hour:02d}:{minute:02d}"
        except ValueError:
            return None

    return {
        "date": due_date.strftime("%Y-%m-%d"),
        "time": time_text,
        "source": source,
        "raw_text": raw_text,
    }


def _parse_base_date(received_at):
    """수신 시각 문자열을 상대 날짜 계산용 기준 날짜로 변환한다."""
    try:
        return datetime.strptime(received_at, "%Y-%m-%d %H:%M").date()
    except ValueError:
        return datetime.today().date()
