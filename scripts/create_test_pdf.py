from __future__ import annotations

import sys
from pathlib import Path

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
except ModuleNotFoundError:
    A4 = None
    canvas = None


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


def create_test_pdf(output_path: Path | None = None) -> Path:
    """Create a sample business PDF used by the manual PDF pipeline tests."""
    if canvas is None or A4 is None:
        raise RuntimeError("reportlab is not installed. Install it first to create sample PDFs.")

    pdf_path = output_path or (ROOT_DIR / "test_business_report.pdf")

    pdf = canvas.Canvas(str(pdf_path), pagesize=A4)
    width, height = A4
    del width

    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(50, height - 50, "[Business Request] Q2 Design Review")

    pdf.setFont("Helvetica", 12)
    pdf.drawString(50, height - 100, "Date: 2026-04-29")
    pdf.drawString(50, height - 120, "From: Design Team")
    pdf.drawString(50, height - 140, "To: Development Team")

    pdf.setFont("Helvetica", 10)
    y_position = height - 180
    content = [
        "",
        "Subject: Design Mockup Review Request",
        "",
        "Dear Team,",
        "",
        "We need your review on the new UI design mockups for the Q2 release.",
        "",
        "Key Points:",
        "- Review all mockup files in the attachment",
        "- Provide feedback by May 2nd, 2026 (Friday) 4PM",
        "- Focus on usability and technical feasibility",
        "- Priority: HIGH",
        "",
        "Deliverables:",
        "1. Technical feasibility assessment",
        "2. Implementation timeline estimate",
        "3. Resource requirements",
        "",
        "Please confirm receipt of this document.",
        "",
        "Best regards,",
        "Design Team",
    ]

    for line in content:
        pdf.drawString(50, y_position, line)
        y_position -= 15

    pdf.showPage()

    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(50, height - 50, "Page 2: Detailed Specifications")

    pdf.setFont("Helvetica", 10)
    y_position = height - 100
    specs = [
        "",
        "Design Components:",
        "- Navigation Bar (responsive)",
        "- Dashboard Layout (grid system)",
        "- Form Elements (accessibility compliant)",
        "- Data Visualization Charts",
        "",
        "Technical Requirements:",
        "- React 18+",
        "- TypeScript",
        "- Tailwind CSS",
        "- Mobile-first approach",
        "",
        "Timeline:",
        "- Review: May 2, 2026",
        "- Implementation Start: May 5, 2026",
        "- Testing: May 15-20, 2026",
        "- Release: May 25, 2026",
        "",
        "Contact: design-team@company.com",
    ]

    for line in specs:
        pdf.drawString(50, y_position, line)
        y_position -= 15

    pdf.save()
    print(f"[OK] Test PDF created: {pdf_path}")
    return pdf_path


if __name__ == "__main__":
    try:
        create_test_pdf()
    except RuntimeError as exc:
        print(f"[INFO] {exc}")
