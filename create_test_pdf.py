"""
테스트용 PDF 파일 생성
"""
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

def create_test_pdf():
    """업무 메일 형식의 테스트 PDF 생성"""
    pdf_path = "test_business_report.pdf"

    c = canvas.Canvas(pdf_path, pagesize=A4)
    width, height = A4

    # 페이지 1 - 업무 요청서
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 50, "[Business Request] Q2 Design Review")

    c.setFont("Helvetica", 12)
    c.drawString(50, height - 100, "Date: 2026-04-29")
    c.drawString(50, height - 120, "From: Design Team")
    c.drawString(50, height - 140, "To: Development Team")

    c.setFont("Helvetica", 10)
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
        "Design Team"
    ]

    for line in content:
        c.drawString(50, y_position, line)
        y_position -= 15

    c.showPage()

    # 페이지 2 - 상세 사양
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, height - 50, "Page 2: Detailed Specifications")

    c.setFont("Helvetica", 10)
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
        "Contact: design-team@company.com"
    ]

    for line in specs:
        c.drawString(50, y_position, line)
        y_position -= 15

    c.save()
    print(f"[OK] Test PDF created: {pdf_path}")
    return pdf_path

if __name__ == "__main__":
    create_test_pdf()
