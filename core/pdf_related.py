"""
PDF 연관 추천 — TF-IDF 코사인 유사도 기반

문서 유사도 추천의 학술 표준인 TF-IDF 코사인 유사도를 사용한다.
외부 라이브러리 없이 순수 Python(math, collections)으로 구현됨.

  TF(t, d)  = 문서 d에서 단어 t의 출현 횟수
  IDF(t)    = log((N+1) / (df(t)+1)) + 1   ← sklearn 스무딩 공식
              전 문서에 고르게 분포 → 낮은 가중치 / 특정 문서에만 집중 → 높은 가중치
  코사인 유사도 = 두 벡터의 내적 / (각 벡터 크기의 곱)
"""
from __future__ import annotations

import re
from collections import Counter
from itertools import islice
from math import log, sqrt


STOPWORDS: frozenset[str] = frozenset({
    "the", "and", "for", "with", "from", "that", "this",
    "into", "have", "will", "your", "please",
    "pdf", "file", "files", "document", "attachment", "review",
    "업무", "요청", "첨부", "파일", "문서",
})


def find_related_pdfs(
    source_pdf: dict,
    candidate_pdfs: list[dict],
    limit: int = 5,
) -> list[dict]:
    """source_pdf와 TF-IDF 코사인 유사도가 높은 PDF를 최대 limit개 반환한다."""
    all_pdfs = [source_pdf, *candidate_pdfs]

    token_map: dict[str, list[str]] = {
        pdf["pdf_id"]: _extract_tokens(pdf)
        for pdf in all_pdfs
        if pdf.get("pdf_id")
    }

    source_id = source_pdf.get("pdf_id", "")
    if not token_map.get(source_id):
        return []

    tfidf = _build_tfidf_vectors(token_map)
    source_vec = tfidf.get(source_id, {})
    if not source_vec:
        return []

    ranked = []
    for candidate in candidate_pdfs:
        cid = candidate.get("pdf_id", "")
        if not cid:
            continue
        candidate_vec = tfidf.get(cid, {})
        if not candidate_vec:
            continue

        score = _cosine_similarity(source_vec, candidate_vec)
        if score <= 0:
            continue

        top_terms = _top_shared_terms(source_vec, candidate_vec, n=5)

        enriched = dict(candidate)
        enriched["related_score"] = round(score, 3)
        enriched["related_reasons"] = (
            ["핵심 공통 키워드: " + ", ".join(top_terms)]
            if top_terms
            else ["TF-IDF 코사인 유사도 기반 추천"]
        )
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
    """메일 본문 등 자유 텍스트로 관련 PDF를 추천한다."""
    source_document = {
        "pdf_id": f"virtual-{source_name}",
        "filename": source_name,
        "text": source_text or "",
    }
    return find_related_pdfs(source_document, candidate_pdfs, limit=limit)


def _build_tfidf_vectors(token_map: dict[str, list[str]]) -> dict[str, dict[str, float]]:
    """
    TF-IDF 벡터를 계산한다.

    IDF 공식: log((N+1) / (df(t)+1)) + 1   (sklearn TfidfTransformer, smooth_idf=True)
    스무딩(+1)을 적용해 N이 작을 때 IDF=0으로 인한 제로 벡터 문제를 방지한다.
    모든 단어에 IDF >= 1.0 이 보장되므로 소규모 문서셋에서도 유사도가 계산된다.
    """
    N = len(token_map)
    if N == 0:
        return {}

    # 단어별 문서 빈도(df): 해당 단어가 등장하는 문서 수
    df: Counter[str] = Counter()
    for tokens in token_map.values():
        for term in set(tokens):
            df[term] += 1

    vectors: dict[str, dict[str, float]] = {}
    for doc_id, tokens in token_map.items():
        tf = Counter(tokens)
        vectors[doc_id] = {
            term: count * (log((N + 1) / (df[term] + 1)) + 1.0)
            for term, count in tf.items()
        }
    return vectors


def _cosine_similarity(vec_a: dict[str, float], vec_b: dict[str, float]) -> float:
    """두 TF-IDF 벡터의 코사인 유사도 [0, 1] 를 반환한다."""
    if not vec_a or not vec_b:
        return 0.0

    dot = sum(vec_a.get(term, 0.0) * val for term, val in vec_b.items())
    if dot <= 0:
        return 0.0

    mag_a = sqrt(sum(v * v for v in vec_a.values()))
    mag_b = sqrt(sum(v * v for v in vec_b.values()))
    if mag_a == 0.0 or mag_b == 0.0:
        return 0.0

    return dot / (mag_a * mag_b)


def _top_shared_terms(
    vec_a: dict[str, float],
    vec_b: dict[str, float],
    n: int = 5,
) -> list[str]:
    """두 벡터 모두에 존재하며 내적 기여(vec_a[t] × vec_b[t])가 큰 단어를 반환한다."""
    shared = set(vec_a) & set(vec_b)
    return sorted(shared, key=lambda t: vec_a[t] * vec_b[t], reverse=True)[:n]


def _extract_tokens(pdf_document: dict) -> list[str]:
    # 1순위: MongoDB에 저장된 사전 계산 키워드 (Okt 어간 포함)
    if pdf_document.get("keywords"):
        return [
            str(token).lower()
            for token in pdf_document.get("keywords", [])
            if str(token).strip()
        ][:20]

    # 2순위: keywords 미저장 → pdf_keywords 경로 (Okt 어근 추출)
    filename = pdf_document.get("filename", "")
    text = pdf_document.get("text", "")
    from core.pdf_keywords import extract_pdf_keywords  # noqa: PLC0415
    keywords = extract_pdf_keywords(text, filename=filename, limit=20)
    if keywords:
        return keywords

    # fallback: regex 토크나이징
    combined = " ".join(part for part in [filename, text] if part)
    tokens = [
        token.lower()
        for token in re.findall(r"[A-Za-z0-9가-힣]{2,}", combined)
        if token.lower() not in STOPWORDS
    ]
    counter = Counter(tokens)
    return [token for token, _ in islice(counter.most_common(20), 20)]


# ── 기존 Apriori 방식이 부적절했던 이유 ──────────────────────────────────────────
#
# 1. 문제 도메인 불일치
#    Apriori는 수백~수천 건의 독립 거래에서 {A,B} → {C} 공동 구매 패턴을 찾는
#    장바구니 분석 알고리즘이다. "이 PDF와 비슷한 PDF 찾기"는 문서 유사도 문제이며,
#    Apriori가 전제하는 독립 트랜잭션 구조와 근본적으로 맞지 않는다.
#
# 2. 소규모 데이터에서 통계적 무의미성
#    min_support=0.1 + 문서 10개 → 규칙 통과 기준이 단 1개 문서.
#    실질적으로 모든 공동 출현 토큰이 규칙을 통과해 필터 역할을 하지 못한다.
#
# 3. 문서 내 공동 출현의 자명성
#    같은 문서 안의 토큰들은 당연히 함께 나온다. 이 공동 출현이 "연관 규칙"으로
#    잡혀도 문서 간 유사도를 나타내는 신호가 아니다.
#
# 4. 점수 공식의 임의성
#    rule_score = support × confidence × capped_lift(상한 3.0)
#    total_score = rules_score × 2.5 + overlap_score
#    2.5, 3.0 등은 문헌 근거 없는 magic number이며 결과 신뢰도를 검증할 수 없다.
#
# 5. fallback이 오히려 더 적합했던 아이러니
#    apyori 미설치 시 Jaccard overlap만 사용하는 경로가 있었는데,
#    복잡한 Apriori를 우회한 이 단순한 집합 유사도가 실제로는 더 적절한 접근이었다.
