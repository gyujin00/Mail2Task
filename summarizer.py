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
    summary_hints = _collect_summary_hints(source_text)

    try:
        response = client.responses.create(
            model=config.OPENAI_MODEL,
            reasoning={"effort": "low"},
            input=[
                {
                    "role": "system",
                    "content": [
                        {
                            "type": "input_text",
                            "text": (
                                "당신은 업무 메일 상세 화면용 요약 도우미다. "
                                "제목, 본문, 첨부 내용을 전체적으로 읽고 "
                                "사람이 바로 이해할 수 있게 자연스럽고 읽기 좋은 한국어 1~2줄로 요약하라. "
                                "억지로 형식을 맞추기보다, 메일에서 중요한 내용을 빠뜨리지 않고 "
                                "핵심만 매끄럽게 정리하는 데 집중하라. "
                                "배경 상황, 해야 할 작업, 마감, 추가 요청이 있으면 중요도에 따라 자연스럽게 포함하라. "
                                "특히 본문 뒤쪽에 붙은 보조 요청이나 조건도 중요한 내용이면 빼먹지 마라. "
                                "다만 원문에 없는 내용은 보태지 말고, 해석을 과하게 늘리지도 마라. "
                                "문장을 기계적으로 끊지 말고, 팀원이 메모하듯 자연스럽게 써라. "
                                "좋은 예: '체크리스트가 예전 기준이라 최신 운영 환경과 맞지 않고 Redis 점검 항목도 빠져 있습니다.' "
                                "'이번 달 마지막 주 금요일까지 점검 항목을 정리해 형식을 통일하고, 가능하면 자동화 가능한 부분도 메모로 남겨주세요.' "
                                "나쁜 예: '문제나 특이사항이 있으면 바로 공유해 달라는 요청입니다.' "
                                "'추가 문의 후 후속 조치를 이어가야 합니다.' "
                                "뭉뚱그린 표현, 원문 복붙, 라벨명 나열, 인삿말은 제외하라."
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
                                "출력 규칙:\n"
                                "- 1~2줄만 작성\n"
                                "- 자연스럽고 읽기 좋은 한국어 문장으로 작성\n"
                                "- 중요한 배경, 해야 할 일, 마감, 추가 요청이 있으면 빠뜨리지 말 것\n"
                                "- 원문에 없는 요청이나 행동을 새로 만들지 말 것\n"
                                "- '관련 내용', '필요한 조치', '해당 업무'처럼 모호한 표현은 피할 것\n"
                                "- 제목과 본문에 나온 핵심 명사는 가능한 한 유지할 것\n\n"
                                "놓치기 쉬운 단서:\n"
                                f"{summary_hints or '- 없음'}\n\n"
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
    """API를 쓰지 못할 때도 화면용 짧고 자연스러운 1~2줄 요약을 만든다."""
    headline = (title or _strip_category(subject) or "").strip()
    if not headline:
        headline = " ".join((text or "").split())[:_FALLBACK_CHARS]

    details = []
    if deadline_date:
        details.append(f"마감은 {deadline_date}")
    if urgency_level:
        details.append(f"긴급도는 {urgency_level}")
    if task_type:
        details.append(f"{task_type} 관련 요청")

    normalized_headline = " ".join(headline.split())[:_FALLBACK_CHARS]
    if not details:
        return f"{normalized_headline} 요청입니다."
    return f"{normalized_headline} 요청입니다.\n{' · '.join(details)}."


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


def _collect_summary_hints(text):
    """원문에서 마감/보조 요청/배경 문장을 골라 요약 프롬프트에 보조 힌트로 넣는다."""
    raw_sentences = [
        sentence.strip()
        for sentence in re.split(r"(?<=[\.\?!])\s+|\n+", text or "")
        if sentence.strip()
    ]
    if not raw_sentences:
        return ""

    hint_markers = (
        "마감",
        "까지",
        "현재",
        "특히",
        "추가로",
        "가능하면",
        "시간 남으면",
        "메모",
        "통일",
        "자동화",
        "누락",
        "반영 안",
        "어려웠",
    )

    hints = []
    seen = set()
    for sentence in raw_sentences:
        normalized = " ".join(sentence.split())
        if not normalized or normalized in seen:
            continue
        if any(marker in normalized for marker in hint_markers):
            seen.add(normalized)
            hints.append(f"- {normalized}")

    return "\n".join(hints[:5])
