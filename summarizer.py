"""
담당: 승민 홍
역할: LLM API 사용 - 메일 내용을 상세 화면용 짧은 요약으로 정리
"""

from __future__ import annotations

import re

import config

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover - optional dependency fallback
    OpenAI = None


_client = None
_MAX_INPUT_CHARS = 4000
_FALLBACK_CHARS = 140


def summarize(
    text,
    *,
    subject="",
    title="",
    deadline_date="",
    urgency_level="",
    task_type="",
):
    """
    메일 본문과 첨부 내용을 상세 화면용 1~2줄 요약으로 반환한다.

    인자:
        text (str): 메일 본문 + PDF 텍스트
        subject (str): 메일 제목
        title (str): 추출된 업무 제목
        deadline_date (str): 마감일
        urgency_level (str): 긴급도
        task_type (str): 업무 유형

    반환:
        str: 화면에 바로 보여줄 짧은 요약. API 실패 시 fallback 요약 반환.
    """
    cleaned_text = (text or "").strip()
    cleaned_subject = (subject or "").strip()
    cleaned_title = (title or "").strip()
    if not cleaned_text and not cleaned_subject and not cleaned_title:
        return ""

    client = _get_client()
    if client is None:
        return _fallback_summary(
            cleaned_text,
            subject=cleaned_subject,
            title=cleaned_title,
            deadline_date=deadline_date,
            urgency_level=urgency_level,
            task_type=task_type,
        )

    source_text = cleaned_text or cleaned_subject or cleaned_title

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
                                "당신은 업무 메일 상세 화면용 요약 도우미다. "
                                "제목, 본문, 첨부 내용을 보고 사용자가 바로 이해할 수 있게 "
                                "핵심만 한국어 1~2줄로 요약하라. "
                                "첫 줄은 해야 할 일의 핵심, 둘째 줄은 마감/우선순위/참고사항만 정리하라. "
                                "불필요한 수식어, 원문 복붙, 라벨명 나열, 인삿말은 제외하라."
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
                                "업무 메일 정보:\n"
                                f"- 제목: {cleaned_subject or '(없음)'}\n"
                                f"- 업무명: {cleaned_title or '(없음)'}\n"
                                f"- 업무유형: {task_type or '(없음)'}\n"
                                f"- 마감일: {deadline_date or '(없음)'}\n"
                                f"- 긴급도: {urgency_level or '(없음)'}\n\n"
                                "원문:\n"
                                f"{source_text[:_MAX_INPUT_CHARS]}"
                            ),
                        }
                    ],
                },
            ],
        )
    except Exception:
        return _fallback_summary(
            source_text,
            subject=cleaned_subject,
            title=cleaned_title,
            deadline_date=deadline_date,
            urgency_level=urgency_level,
            task_type=task_type,
        )

    summary = (response.output_text or "").strip()
    return _normalize_summary(summary) or _fallback_summary(
        source_text,
        subject=cleaned_subject,
        title=cleaned_title,
        deadline_date=deadline_date,
        urgency_level=urgency_level,
        task_type=task_type,
    )


def summarize_batch(text_list):
    """여러 메일을 순서대로 요약한다."""
    return [summarize(t) for t in text_list]


def _get_client():
    """OpenAI 클라이언트를 필요할 때만 생성한다."""
    global _client

    if not config.OPENAI_API_KEY or OpenAI is None:
        return None

    if _client is None:
        _client = OpenAI(api_key=config.OPENAI_API_KEY)

    return _client


def _fallback_summary(
    text,
    *,
    subject="",
    title="",
    deadline_date="",
    urgency_level="",
    task_type="",
):
    """API를 쓰지 못할 때도 화면용 짧은 1~2줄 요약을 만든다."""
    headline = (title or _strip_category(subject) or "").strip()
    if not headline:
        headline = " ".join((text or "").split())[:_FALLBACK_CHARS]

    details = []
    if deadline_date:
        details.append(f"마감 {deadline_date}")
    if urgency_level:
        details.append(f"긴급도 {urgency_level}")
    if task_type:
        details.append(task_type)

    normalized_headline = " ".join(headline.split())[:_FALLBACK_CHARS]
    if not details:
        return normalized_headline
    return f"{normalized_headline}\n{' · '.join(details)}"


def _normalize_summary(text):
    """모델 응답을 1~2줄 화면 요약 형태로 정리한다."""
    raw_lines = str(text or "").replace("\r\n", "\n").split("\n")
    cleaned_lines = []
    for raw_line in raw_lines:
        normalized = " ".join(raw_line.split())
        normalized = re.sub(r"^[\-\*\d\.\s]+", "", normalized)
        normalized = normalized.strip()
        if normalized:
            cleaned_lines.append(normalized)

    if not cleaned_lines:
        return ""

    return "\n".join(cleaned_lines[:2])


def _strip_category(subject):
    """메일 제목 앞의 [카테고리]를 제거해 화면용 요약 제목으로 쓴다."""
    return re.sub(r"^\[[^\]]+\]\s*", "", subject or "").strip()
