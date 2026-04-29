"""
PDF 텍스트 추출 기능 테스트
"""
import os
from pathlib import Path
from pdf_extractor import extract_text_from_pdf

def create_sample_pdf():
    """테스트용 샘플 PDF 생성 (reportlab 사용)"""
    try:
        from reportlab.pdfgen import canvas
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont

        # 한글 폰트 등록 시도 (없으면 영어로만)
        try:
            pdfmetrics.registerFont(TTFont('NanumGothic', 'NanumGothic.ttf'))
            font_name = 'NanumGothic'
        except:
            font_name = 'Helvetica'

        pdf_path = "test_sample.pdf"
        c = canvas.Canvas(pdf_path)
        c.setFont(font_name, 12)

        # 페이지 1
        c.drawString(100, 750, "Task-Harvester Test Document")
        c.drawString(100, 700, "Page 1: Project Overview")
        c.drawString(100, 650, "This is a test PDF for text extraction.")
        c.drawString(100, 600, "Action Item: Review design mockups by 2026-05-02")
        c.showPage()

        # 페이지 2
        c.setFont(font_name, 12)
        c.drawString(100, 750, "Page 2: Details")
        c.drawString(100, 700, "Deadline: Friday 4PM")
        c.drawString(100, 650, "Priority: High")
        c.showPage()

        c.save()
        return pdf_path
    except ImportError:
        print("[INFO] reportlab이 없어 샘플 PDF를 생성할 수 없습니다.")
        return None

def test_extraction():
    """PDF 텍스트 추출 테스트"""
    print("=== PDF 텍스트 추출 기능 테스트 ===\n")

    # 1. 샘플 PDF 생성
    print("[1단계] 샘플 PDF 생성")
    sample_pdf = create_sample_pdf()

    if not sample_pdf:
        print("  샘플 PDF 생성 실패 - downloads 폴더의 기존 PDF로 테스트합니다.")
        downloads_dir = Path("downloads")
        if downloads_dir.exists():
            pdf_files = list(downloads_dir.glob("*.pdf"))
            if pdf_files:
                sample_pdf = str(pdf_files[0])
                print(f"  테스트 PDF: {sample_pdf}")
            else:
                print("  [FAIL] 테스트할 PDF 파일이 없습니다.")
                return
        else:
            print("  [FAIL] downloads 폴더가 없습니다.")
            return
    else:
        print(f"  [OK] 샘플 PDF 생성 완료: {sample_pdf}")

    # 2. 텍스트 추출
    print(f"\n[2단계] PDF 텍스트 추출")
    text = extract_text_from_pdf(sample_pdf)

    if text:
        print(f"  [OK] 텍스트 추출 성공")
        print(f"  추출된 텍스트 길이: {len(text)} 자")
        print(f"\n--- 추출된 내용 미리보기 ---")
        preview = text[:500]
        print(preview)
        if len(text) > 500:
            print("...")
        print("--- 미리보기 끝 ---\n")
    else:
        print(f"  [FAIL] 텍스트 추출 실패 또는 빈 내용")

    # 3. 에러 케이스 테스트
    print("[3단계] 에러 케이스 테스트")

    # 존재하지 않는 파일
    result = extract_text_from_pdf("nonexistent.pdf")
    if result == "":
        print("  [OK] 존재하지 않는 파일 처리: 빈 문자열 반환")
    else:
        print("  [FAIL] 존재하지 않는 파일 처리 실패")

    # 빈 경로
    result = extract_text_from_pdf("")
    if result == "":
        print("  [OK] 빈 경로 처리: 빈 문자열 반환")
    else:
        print("  [FAIL] 빈 경로 처리 실패")

    # 4. 정리
    if sample_pdf and sample_pdf == "test_sample.pdf" and os.path.exists(sample_pdf):
        os.remove(sample_pdf)
        print(f"\n[정리] 테스트 PDF 삭제: {sample_pdf}")

    print("\n=== 테스트 완료 ===")

if __name__ == "__main__":
    test_extraction()
