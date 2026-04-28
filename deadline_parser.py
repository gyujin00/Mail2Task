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

    # TODO: 아래 패턴들을 구현하세요. (우선순위 순서대로 시도)
    #
    # 패턴 1 [최우선]: 구조화 필드 "마감기한: 2026-04-30 (목) 15:00"
    #   re.search(r"마감기한\s*[:：]\s*(\d{4})-(\d{2})-(\d{2})", text)
    #
    # 패턴 2: 제목의 (~MM/DD) 형식  예) (~05/02)
    #   re.search(r"~(\d{1,2})/(\d{1,2})", text) → base.year 로 연도 보완
    #
    # 패턴 3: 일반 날짜 "YYYY-MM-DD" / "YYYY/MM/DD" / "YYYY.MM.DD"
    #   re.search(r"(\d{4})[.\-/](\d{1,2})[.\-/](\d{1,2})", text)
    #
    # 패턴 4: "MM월 DD일" → base.year 기준으로 연도 보완
    #   re.search(r"(\d{1,2})월\s*(\d{1,2})일", text)
    #
    # 패턴 5: "이번 주 금요일", "다음 주 월요일" 등 상대 표현 (선택 구현)
    # 패턴 6: "D일 후", "D일 이내" 등 상대 표현 (선택 구현)

    return ""


def _parse_base_date(received_at):
    """수신 일시 문자열을 date 객체로 변환한다."""
    try:
        return datetime.strptime(received_at, "%Y-%m-%d %H:%M").date()
    except ValueError:
        return datetime.today().date()
