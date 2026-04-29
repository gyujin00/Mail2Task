from __future__ import annotations

from core.pdf_keywords import extract_pdf_keywords


def test_extract_pdf_keywords():
    text = """
    프로모션 랜딩 페이지 디자인 검토 요청입니다.
    대시보드 컴포넌트와 버튼 색상, 사용자 피드백 반영 여부를 확인해주세요.
    """
    keywords = extract_pdf_keywords(text, filename="design_review.pdf")

    assert "디자인" in keywords
    assert "랜딩" in keywords
    assert "대시보드" in keywords
