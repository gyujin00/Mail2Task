"""
담당: 승민 홍
역할: LLM API 활용 - 메일 본문을 핵심 액션 아이템 한 줄로 요약
"""


def summarize(text):
    """
    메일 본문을 LLM API로 요약하여 핵심 액션 아이템을 반환한다.

    인자:
        text (str): 메일 본문 + PDF 텍스트

    반환:
        str: 한 줄 요약. API 실패 시 원문 앞 100자 반환.
    """
    # TODO: LLM API 연동
    # 추천: OpenAI API 또는 Anthropic Claude API
    #
    # 예시 프롬프트:
    # "다음 업무 메일에서 핵심 할 일을 한 문장으로 요약해줘:\n\n{text}"
    #
    # import anthropic
    # client = anthropic.Anthropic(api_key="...")
    # response = client.messages.create(
    #     model="claude-haiku-4-5-20251001",
    #     max_tokens=100,
    #     messages=[{"role": "user", "content": f"...{text}"}]
    # )
    # return response.content[0].text

    return text[:100]  # API 구현 전 임시 반환


def summarize_batch(text_list):
    """여러 메일을 한꺼번에 요약한다."""
    return [summarize(t) for t in text_list]
