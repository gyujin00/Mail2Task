from __future__ import annotations

import re
from collections import Counter


STOPWORDS = {
    # English
    "the", "and", "for", "with", "from", "that", "this", "into", "have",
    "will", "your", "please", "pdf", "file", "files", "document", "attachment",
    "page", "pages",
    # Korean — 업무 메일 공통 보일러플레이트
    "업무", "요청", "첨부", "파일", "문서", "관련", "확인", "검토",
    # Korean — Okt가 명사로 추출하는 기능어
    "것", "수", "등", "및", "이", "그", "저", "위해", "통해", "대해",
    "경우", "내용",
    # Korean — Okt stem=True 결과에서 단독으로 나오는 보조동사/경어 어간
    "하다", "되다", "이다", "있다", "없다", "드리",
}

# Okt 미설치 환경을 위한 규칙 기반 suffix 목록 (fallback 전용)
_KOREAN_SUFFIXES = (
    "합니다", "합니다만", "드립니다", "바랍니다", "해주세요",
    "입니다", "있습니다", "됩니다", "대로", "에서", "으로",
    "까지", "부터", "하게", "하고", "하며", "이다", "예정",
)

# Okt 지연 로딩 (JVM 초기화 비용을 최초 호출 시로 미룸)
_okt = None


def _get_okt():
    global _okt
    if _okt is None:
        try:
            from konlpy.tag import Okt  # noqa: PLC0415
            _okt = Okt()
        except Exception:
            _okt = False
    return _okt if _okt is not False else None


def extract_pdf_keywords(
    text: str,
    filename: str = "",
    limit: int = 20,
) -> list[str]:
    """형태소 분석(Okt) 또는 규칙 기반으로 PDF 대표 키워드를 추출한다."""
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


def _extract_stems_with_okt(text: str) -> list[str]:
    """Okt 형태소 분석으로 명사 어근과 동사/형용사 어간을 추출한다.

    - Noun: 원형 그대로 사용
    - Verb/Adjective: stem=True 결과에서 '하다/되다/이다' 제거 → 어간만 유지
    """
    okt = _get_okt()
    if okt is None:
        return []
    try:
        pos_result = okt.pos(text, norm=True, stem=True)
        tokens: list[str] = []
        for word, tag in pos_result:
            if tag == "Noun":
                stem = word.strip().lower()
            elif tag in ("Verb", "Adjective"):
                stem = word.strip().lower()
                # "검토하다" → "검토", "배포되다" → "배포", "명확이다" → "명확"
                for suffix in ("하다", "되다", "이다"):
                    if stem.endswith(suffix) and len(stem) > len(suffix) + 1:
                        stem = stem[: -len(suffix)]
                        break
                else:
                    # 위 세 가지가 아닌 경우 "다" 하나만 제거 ("먹다" → "먹")
                    if stem.endswith("다") and len(stem) > 2:
                        stem = stem[:-1]
            else:
                continue
            if len(stem) >= 2 and stem not in STOPWORDS:
                tokens.append(stem)
        return tokens
    except Exception:
        return []


def _normalize_keyword(token: str) -> str:
    """Okt 없는 환경용: 규칙 기반 suffix 제거로 어근을 근사 추출한다."""
    normalized = token.strip().lower()
    for suffix in _KOREAN_SUFFIXES:
        if normalized.endswith(suffix) and len(normalized) > len(suffix) + 1:
            normalized = normalized[: -len(suffix)]
            break
    return normalized


def _add_weighted_tokens(counter: Counter, raw_text: str, weight: int) -> None:
    """토큰을 추출해 가중치와 함께 counter에 누적한다.

    한국어가 포함된 경우 Okt 형태소 분석을 우선 사용하고,
    Okt 미설치 시 규칙 기반 suffix 제거로 fallback한다.
    """
    if not raw_text:
        return

    has_korean = bool(re.search(r"[가-힣]", raw_text))
    if has_korean:
        stems = _extract_stems_with_okt(raw_text)
        if stems:
            # Okt 성공: 어간/어근 토큰 집계
            for stem in stems:
                counter[stem] += weight
            # 영문/숫자 토큰은 별도로 추가 (Okt는 한글만 처리)
            for token in re.findall(r"[A-Za-z0-9]{2,}", raw_text):
                normalized = token.lower()
                if normalized and normalized not in STOPWORDS and len(normalized) >= 2:
                    counter[normalized] += weight
            return

    # fallback: regex 토크나이징 + 규칙 기반 suffix 제거
    for token in re.findall(r"[A-Za-z0-9가-힣]{2,}", raw_text):
        normalized = _normalize_keyword(token)
        if not normalized or normalized in STOPWORDS or len(normalized) < 2:
            continue
        counter[normalized] += weight


def _is_korean_token(token: str) -> int:
    return 1 if re.search(r"[가-힣]", token) else 0
