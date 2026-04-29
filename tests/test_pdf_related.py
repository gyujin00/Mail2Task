from __future__ import annotations

import importlib.util

from core.pdf_related import find_related_pdfs


def test_related_pdf_recommendation():
    if importlib.util.find_spec("apyori") is None:
        print("apyori not installed; skipping test")
        return

    source = {
        "pdf_id": "pdf-1",
        "filename": "design_review_q2.pdf",
        "text": "Q2 design review dashboard usability navigation component feedback",
    }
    candidates = [
        {
            "pdf_id": "pdf-2",
            "filename": "design_guideline_dashboard.pdf",
            "text": "dashboard component usability guideline and design system review",
        },
        {
            "pdf_id": "pdf-3",
            "filename": "security_policy.pdf",
            "text": "oauth jwt reverse proxy redis security policy",
        },
    ]

    related = find_related_pdfs(source, candidates, limit=5)

    assert len(related) == 1
    assert related[0]["pdf_id"] == "pdf-2"
    assert related[0]["related_score"] > 0
