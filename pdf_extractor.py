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
    if not pdf_path:
        return ""

    try:
        texts = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                page_text = page_text.strip()
                if page_text:
                    texts.append(page_text)
        return "\n\n".join(texts).strip()
    except Exception:
        return ""
