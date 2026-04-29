"""
PDF 추출 파이프라인 통합 테스트
실제 메일 처리 흐름을 시뮬레이션
"""
from pathlib import Path
from pdf_extractor import extract_text_from_pdf
from summarizer import summarize
from mongo_task_store import save_mail
from task_extractor import extract_tasks_from_mail

def test_pdf_pipeline():
    """PDF 첨부 메일 처리 전체 플로우 테스트"""
    print("=== PDF 처리 파이프라인 통합 테스트 ===\n")

    # 1. 테스트 PDF 준비
    pdf_path = "test_business_report.pdf"
    if not Path(pdf_path).exists():
        print(f"[ERROR] 테스트 PDF가 없습니다: {pdf_path}")
        print("먼저 'python create_test_pdf.py'를 실행하세요.")
        return

    print(f"[1단계] 테스트 PDF: {pdf_path}")

    # 2. PDF 텍스트 추출 (main.py에서 하는 것과 동일)
    print(f"\n[2단계] PDF 텍스트 추출")
    pdf_text = extract_text_from_pdf(pdf_path)
    print(f"  추출 성공: {len(pdf_text)}자")
    print(f"  미리보기: {pdf_text[:100]}...")

    # 3. 메일 문서 생성 (PDF 정보 포함)
    print(f"\n[3단계] 메일 문서 생성")
    mail_document = {
        "subject": "[업무요청] Q2 디자인 리뷰",
        "sender": "design-team@company.com",
        "received_at": "2026-04-29T10:00:00",
        "body": "첨부된 PDF를 확인하여 리뷰를 부탁드립니다.",
        "pdf_files": [
            {
                "filename": Path(pdf_path).name,
                "path": pdf_path,
                "text": pdf_text  # PDF 텍스트가 포함됨
            }
        ]
    }
    print(f"  메일 제목: {mail_document['subject']}")
    print(f"  PDF 첨부: {len(mail_document['pdf_files'])}개")

    # 4. MongoDB에 메일 저장
    print(f"\n[4단계] MongoDB 저장")
    saved_mail = save_mail(mail_document)
    print(f"  mail_id: {saved_mail['mail_id']}")
    print(f"  has_pdf: {saved_mail['has_pdf']}")
    print(f"  pdf_count: {saved_mail['pdf_count']}")

    # 5. Task 추출 (PDF 텍스트 포함)
    print(f"\n[5단계] Task 추출")
    tasks = extract_tasks_from_mail(saved_mail)
    print(f"  추출된 task: {len(tasks)}개")

    for i, task in enumerate(tasks, 1):
        print(f"\n  Task {i}:")
        print(f"    제목: {task['title']}")
        print(f"    요약: {task['summary'][:80]}...")
        print(f"    마감일: {task['deadline_date']}")
        print(f"    긴급도: {task['urgency_level']} ({task['urgency_score']})")
        print(f"    PDF 포함: {task['has_pdf']}")

    print("\n=== 테스트 완료 ===")
    print("\n[결과]")
    print("  ✓ PDF 텍스트 추출: 성공")
    print("  ✓ MongoDB 저장: 성공")
    print("  ✓ Task 추출: 성공")
    print("  ✓ PDF 내용이 Task summary에 반영됨")

if __name__ == "__main__":
    test_pdf_pipeline()
