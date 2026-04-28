"""
담당: 승민 홍
역할: LLM API 활용 - 메일 본문을 핵심 액션 아이템 한 줄로 요약
"""

from __future__ import annotations

import re

import config

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover - 의존성 미설치 시 fallback용
    OpenAI = None


_client = None
_MAX_INPUT_CHARS = 4000
_FALLBACK_CHARS = 100


def summarize(text):
    """
    메일 본문을 LLM API로 요약하여 핵심 액션 아이템을 반환한다.

    인자:
        text (str): 메일 본문 + PDF 텍스트

    반환:
        str: 한 줄 요약. API 실패 시 원문 앞 100자 반환.
    """
    cleaned_text = (text or "").strip()
    if not cleaned_text:
        return ""

    client = _get_client()
    if client is None:
        return _fallback_summary(cleaned_text)

    try:
        response = client.responses.create(
            model=config.OPENAI_MODEL,
            reasoning={"effort": "minimal"},
            input=[
                {
                    "role": "system",
                    "content": [
                        {
                            "type": "input_text",
                            "text": (
                                "당신은 업무 메일 요약 도우미다. "
                                "메일과 첨부 텍스트를 보고 실제로 해야 할 핵심 업무를 "
                                "한국어 한 문장으로만 요약하라. "
                                "불필요한 인사말, 배경 설명, 광고 문구는 제외하라."
                            ),
                        }
                    ],
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": (
                                "다음 메일에서 핵심 액션 아이템을 한 문장으로 요약해줘.\n\n"
                                f"{cleaned_text[:_MAX_INPUT_CHARS]}"
                            ),
                        }
                    ],
                },
            ],
        )
    except Exception:
        return _fallback_summary(cleaned_text)

    summary = (response.output_text or "").strip()
    return _normalize_summary(summary) or _fallback_summary(cleaned_text)


def summarize_batch(text_list):
    """여러 메일을 한꺼번에 요약한다."""
    return [summarize(t) for t in text_list]


def _get_client():
    """OpenAI 클라이언트를 필요할 때만 생성한다."""
    global _client

    if not config.OPENAI_API_KEY or OpenAI is None:
        return None

    if _client is None:
        _client = OpenAI(api_key=config.OPENAI_API_KEY)

    return _client


def _fallback_summary(text):
    """API를 쓰지 못할 때는 앞부분만 짧게 정리해 반환한다."""
    normalized = " ".join(text.split())
    return normalized[:_FALLBACK_CHARS]


def _normalize_summary(text):
    """모델 응답을 한 줄 요약 형태로 정리한다."""
    normalized = " ".join((text or "").split())
    normalized = re.sub(r"^[\-*•\d.\s]+", "", normalized)
    return normalized.strip()
