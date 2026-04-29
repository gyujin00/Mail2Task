from __future__ import annotations

import re
from collections import Counter
from itertools import islice


STOPWORDS = {
    "the",
    "and",
    "for",
    "with",
    "from",
    "that",
    "this",
    "into",
    "have",
    "will",
    "your",
    "please",
    "pdf",
    "file",
    "files",
    "document",
    "attachment",
    "review",
    "업무",
    "요청",
    "첨부",
    "파일",
    "문서",
}


def find_related_pdfs(
    source_pdf: dict,
    candidate_pdfs: list[dict],
    limit: int = 5,
) -> list[dict]:
    """`apyori` 기반 연관 규칙으로 source PDF와 연관된 PDF를 추천한다."""
    try:
        from apyori import apriori
    except ImportError:
        return []

    pdfs = [source_pdf, *candidate_pdfs]
    pdf_tokens = {
        pdf.get("pdf_id", ""): _extract_tokens(pdf)
        for pdf in pdfs
        if pdf.get("pdf_id")
    }

    source_id = source_pdf.get("pdf_id", "")
    source_tokens = pdf_tokens.get(source_id, [])
    if not source_tokens:
        return []

    transactions = [tokens for tokens in pdf_tokens.values() if len(tokens) >= 2]
    if len(transactions) < 2:
        return []

    results = list(
        apriori(
            transactions,
            min_support=0.1,
            min_confidence=0.1,
            min_lift=1.0,
            min_length=2,
            max_length=4,
        )
    )

    source_token_set = set(source_tokens)

    ranked = []
    for candidate in candidate_pdfs:
        candidate_id = candidate.get("pdf_id", "")
        candidate_tokens = set(pdf_tokens.get(candidate_id, []))
        if not candidate_id or not candidate_tokens:
            continue

        rule_matches = []
        for relation in results:
            relation_items = set(relation.items)
            if not (relation_items & source_token_set and relation_items & candidate_tokens):
                continue

            base_score = float(relation.support or 0)

            for ordered in relation.ordered_statistics:
                base = set(ordered.items_base)
                add = set(ordered.items_add)
                if not base or not add:
                    continue
                if not (
                    (base & source_token_set and add & candidate_tokens)
                    or (base & candidate_tokens and add & source_token_set)
                ):
                    continue

                confidence = float(ordered.confidence or 0)
                lift = float(ordered.lift or 0)
                rule_score = base_score * confidence * min(max(lift, 1.0), 3.0)
                rule_matches.append(
                    {
                        "score": rule_score,
                        "support": base_score,
                        "confidence": confidence,
                        "lift": lift,
                        "items": sorted(relation_items),
                    }
                )

        if not rule_matches:
            continue

        rule_matches.sort(key=lambda item: item["score"], reverse=True)
        top_rules = rule_matches[:3]

        overlap_score = _token_overlap_score(source_token_set, candidate_tokens)
        rules_score = sum(item["score"] for item in top_rules)
        total_score = min(1.0, (rules_score * 2.5) + overlap_score)
        if total_score <= 0:
            continue

        shared_keywords = sorted(source_token_set & candidate_tokens)[:5]
        reasons = []
        if shared_keywords:
            reasons.append("공통 토큰: " + ", ".join(shared_keywords))
        for item in top_rules:
            reasons.append(
                "연관 규칙: "
                f"support={item['support']:.3f}, "
                f"confidence={item['confidence']:.3f}, "
                f"lift={item['lift']:.3f}"
            )

        enriched = dict(candidate)
        enriched["related_score"] = round(total_score, 3)
        enriched["related_reasons"] = _dedupe_preserve_order(reasons)[:4]
        ranked.append(enriched)

    ranked.sort(
        key=lambda item: (
            float(item.get("related_score") or 0),
            item.get("updated_at") or "",
        ),
        reverse=True,
    )
    return ranked[:limit]


def find_related_pdfs_for_text(
    source_text: str,
    candidate_pdfs: list[dict],
    limit: int = 5,
    source_name: str = "mail-body",
) -> list[dict]:
    """메일 본문 같은 자유 텍스트를 기준으로 연관 PDF를 추천한다."""
    source_document = {
        "pdf_id": f"virtual-{source_name}",
        "filename": source_name,
        "text": source_text or "",
    }
    return find_related_pdfs(source_document, candidate_pdfs, limit=limit)


def _extract_tokens(pdf_document: dict) -> list[str]:
    if pdf_document.get("keywords"):
        return [
            str(token).lower()
            for token in pdf_document.get("keywords", [])
            if str(token).strip()
        ][:20]

    text = " ".join(
        part
        for part in [
            pdf_document.get("filename", ""),
            pdf_document.get("text", ""),
        ]
        if part
    )
    tokens = [
        token.lower()
        for token in re.findall(r"[A-Za-z0-9가-힣]{2,}", text)
        if token.lower() not in STOPWORDS
    ]
    counter = Counter(tokens)
    # transaction 크기를 제한해 지나치게 긴 PDF가 규칙 생성을 오염시키지 않게 한다.
    return [token for token, _ in islice(counter.most_common(20), 20)]


def _token_overlap_score(source_tokens: set[str], candidate_tokens: set[str]) -> float:
    overlap = source_tokens & candidate_tokens
    if not overlap:
        return 0.0
    return len(overlap) / max(1, len(source_tokens | candidate_tokens))


def _dedupe_preserve_order(values: list[str]) -> list[str]:
    seen = set()
    result = []
    for value in values:
        if not value or value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result
