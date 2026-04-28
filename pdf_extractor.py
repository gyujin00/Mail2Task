"""
담당: 승민 홍
역할: pdfplumber로 PDF 파일에서 텍스트 추출
"""
import pdfplumber


def extract_text_from_pdf(pdf_path):
    """
    PDF 파일에서 전체 텍스트를 추출하여 반환한다.

    인자:
        pdf_path (str): PDF 파일 경로

    반환:
        str: 추출된 전체 텍스트. 실패 시 빈 문자열 반환.
    """
    # TODO: pdfplumber로 pdf_path를 열어 각 페이지 텍스트를 합쳐서 반환
    # 강의안 4/4 슬라이드 코드 참고
    #
    # with pdfplumber.open(pdf_path) as pdf:
    #     ...

    return ""
