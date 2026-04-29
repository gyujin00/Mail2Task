from __future__ import annotations

import os
from pathlib import Path

try:
    from tests._bootstrap import ROOT_DIR
except ModuleNotFoundError:
    from _bootstrap import ROOT_DIR

from pdf_extractor import extract_text_from_pdf


def create_sample_pdf() -> Path | None:
    """Create a small sample PDF locally when reportlab is available."""
    try:
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.pdfgen import canvas
    except ImportError:
        print("[INFO] reportlab is not installed, skipping sample PDF creation.")
        return None

    try:
        pdfmetrics.registerFont(TTFont("NanumGothic", "NanumGothic.ttf"))
        font_name = "NanumGothic"
    except Exception:
        font_name = "Helvetica"

    pdf_path = ROOT_DIR / "test_sample.pdf"
    pdf = canvas.Canvas(str(pdf_path))
    pdf.setFont(font_name, 12)

    pdf.drawString(100, 750, "Task-Harvester Test Document")
    pdf.drawString(100, 700, "Page 1: Project Overview")
    pdf.drawString(100, 650, "This is a test PDF for text extraction.")
    pdf.drawString(100, 600, "Action Item: Review design mockups by 2026-05-02")
    pdf.showPage()

    pdf.setFont(font_name, 12)
    pdf.drawString(100, 750, "Page 2: Details")
    pdf.drawString(100, 700, "Deadline: Friday 4PM")
    pdf.drawString(100, 650, "Priority: High")
    pdf.showPage()
    pdf.save()
    return pdf_path


def test_extraction() -> None:
    print("=== PDF text extraction test ===\n")

    sample_pdf = create_sample_pdf()
    if not sample_pdf:
        downloads_dir = ROOT_DIR / "downloads"
        pdf_files = list(downloads_dir.glob("*.pdf")) if downloads_dir.exists() else []
        if not pdf_files:
            print("[FAIL] No PDF file available for testing.")
            return
        sample_pdf = pdf_files[0]
    else:
        print(f"[OK] Created sample PDF: {sample_pdf}")

    print("\n[1/3] Extracting text")
    text = extract_text_from_pdf(str(sample_pdf))
    if text:
        print(f"[OK] Extracted {len(text)} characters")
        preview = text[:500]
        print(preview)
        if len(text) > 500:
            print("...")
    else:
        print("[FAIL] Text extraction returned empty output")

    print("\n[2/3] Error case checks")
    print("[OK] Missing file returns empty string" if extract_text_from_pdf("nonexistent.pdf") == "" else "[FAIL] Missing file case failed")
    print("[OK] Empty path returns empty string" if extract_text_from_pdf("") == "" else "[FAIL] Empty path case failed")

    print("\n[3/3] Cleanup")
    if sample_pdf.name == "test_sample.pdf" and os.path.exists(sample_pdf):
        os.remove(sample_pdf)
        print(f"[OK] Removed {sample_pdf}")


if __name__ == "__main__":
    test_extraction()
