from __future__ import annotations

from pathlib import Path

try:
    from tests._bootstrap import ROOT_DIR
except ModuleNotFoundError:
    from _bootstrap import ROOT_DIR

from mail.pdf_extractor import extract_text_from_pdf
from storage.mongo_task_store import save_mail
from tasks.task_extractor import extract_tasks_from_mail


def test_pdf_pipeline() -> None:
    """Run the mail -> PDF text -> task extraction flow with a sample file."""
    print("=== PDF pipeline integration test ===\n")

    pdf_path = ROOT_DIR / "test_business_report.pdf"
    if not pdf_path.exists():
        downloads_dir = ROOT_DIR / "downloads"
        fallback_pdfs = list(downloads_dir.glob("*.pdf")) if downloads_dir.exists() else []
        if not fallback_pdfs:
            print(f"[ERROR] Missing test PDF: {pdf_path}")
            print("Run 'python -m scripts.create_test_pdf' first.")
            return
        pdf_path = fallback_pdfs[0]
        print(f"[INFO] Falling back to existing PDF: {pdf_path.name}")

    print(f"[1/5] Using PDF: {pdf_path.name}")

    print("\n[2/5] Extracting text")
    pdf_text = extract_text_from_pdf(str(pdf_path))
    print(f"  Extracted chars: {len(pdf_text)}")
    print(f"  Preview: {pdf_text[:100]}...")

    print("\n[3/5] Building mail document")
    mail_document = {
        "subject": "[업무요청] Q2 디자인 리뷰",
        "sender": "design-team@company.com",
        "received_at": "2026-04-29T10:00:00",
        "body": "첨부된 PDF를 확인하고 리뷰를 부탁드립니다.",
        "pdf_files": [
            {
                "filename": pdf_path.name,
                "path": str(pdf_path),
                "text": pdf_text,
            }
        ],
    }

    print("\n[4/5] Saving mail")
    saved_mail = save_mail(mail_document)
    print(f"  mail_id: {saved_mail['mail_id']}")
    print(f"  has_pdf: {saved_mail['has_pdf']}")
    print(f"  pdf_count: {saved_mail['pdf_count']}")

    print("\n[5/5] Extracting tasks")
    tasks = extract_tasks_from_mail(saved_mail)
    print(f"  tasks: {len(tasks)}")
    for index, task in enumerate(tasks, start=1):
        print(f"\n  Task {index}")
        print(f"    title: {task['title']}")
        print(f"    summary: {task['summary'][:80]}...")
        print(f"    deadline: {task['deadline_date']}")
        print(f"    urgency: {task['urgency_level']} ({task['urgency_score']})")
        print(f"    has_pdf: {task['has_pdf']}")


if __name__ == "__main__":
    test_pdf_pipeline()
