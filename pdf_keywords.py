from __future__ import annotations

import re
from collections import Counter


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
    "page",
    "pages",
    "업무",
    "요청",
    "첨부",
    "파일",
    "문서",
    "관련",
    "확인",
    "검토",
}

KOREAN_SUFFIXES = (
    "합니다",
    "합니다만",
    "드립니다",
    "바랍니다",
    "해주세요",
    "입니다",
    "있습니다",
    "됩니다",
    "대한",
    "에서",
    "으로",
    "까지",
    "부터",
    "에게",
    "하고",
    "하며",
    "했다",
    "예정",
)


def extract_pdf_keywords(
    text: str,
    filename: str = "",
    limit: int = 20,
) -> list[str]:
    """PDF 원문에서 명사형에 가까운 핵심 키워드를 규칙 기반으로 추출한다."""
    if not any(part.strip() for part in [filename, text] if part):
        return []

    counts = Counter()
    _add_weighted_tokens(counts, text, weight=3)
    _add_weighted_tokens(counts, filename, weight=1)

    ranked = sorted(
        counts.items(),
        key=lambda item: (item[1], _is_korean_token(item[0]), item[0]),
        reverse=True,
    )
    return [token for token, _ in ranked[:limit]]


def _normalize_keyword(token: str) -> str:
    normalized = token.strip().lower()
    for suffix in KOREAN_SUFFIXES:
        if normalized.endswith(suffix) and len(normalized) > len(suffix) + 1:
            normalized = normalized[: -len(suffix)]
            break
    return normalized


def _add_weighted_tokens(counter: Counter, raw_text: str, weight: int) -> None:
    for token in re.findall(r"[A-Za-z0-9가-힣]{2,}", raw_text or ""):
        normalized = _normalize_keyword(token)
        if not normalized or normalized in STOPWORDS:
            continue
        if len(normalized) < 2:
            continue
        counter[normalized] += weight


def _is_korean_token(token: str) -> int:
    return 1 if re.search(r"[가-힣]", token) else 0
