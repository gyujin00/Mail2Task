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
        with pdfplumber.open(pdf_path) as pdf:
            text_parts = []
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)

            return "\n".join(text_parts)
    except FileNotFoundError:
        print(f"[오류] PDF 파일을 찾을 수 없습니다: {pdf_path}")
        return ""
    except Exception as e:
        print(f"[오류] PDF 텍스트 추출 실패 ({pdf_path}): {e}")
        return ""
