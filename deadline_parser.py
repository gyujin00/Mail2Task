"""
담당: 승민 홍
역할: 마감일 자동 해석 - 메일 본문/PDF 텍스트에서 날짜 표현 파싱
"""
import re
from datetime import datetime, timedelta


def parse_deadline(text, received_at):
    """
    텍스트에서 마감일을 추출하여 반환한다.

    인자:
        text        (str): 메일 본문 또는 PDF 텍스트
        received_at (str): 수신 일시 "YYYY-MM-DD HH:MM" (상대 날짜 계산 기준)

    반환:
        str: 마감일 "YYYY-MM-DD". 추출 실패 시 빈 문자열.
    """
    base = _parse_base_date(received_at)

    # TODO: 아래 패턴들을 구현하세요.
    # 패턴 1: "YYYY-MM-DD" / "YYYY/MM/DD" / "YYYY.MM.DD"
    # 패턴 2: "MM월 DD일" → base.year 기준으로 연도 보완
    # 패턴 3: "이번 주 금요일", "다음 주 월요일" 등 상대 표현
    # 패턴 4: "D일 후", "D일 이내" 등 상대 표현
    #
    # 힌트: re.search(r"(\d{4})[.\-/](\d{1,2})[.\-/](\d{1,2})", text)

    return ""


def _parse_base_date(received_at):
    """수신 일시 문자열을 date 객체로 변환한다."""
    try:
        return datetime.strptime(received_at, "%Y-%m-%d %H:%M").date()
    except ValueError:
        return datetime.today().date()
