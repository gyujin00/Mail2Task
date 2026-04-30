"""
메일 본문에서 실행 가능한 TO-DO 항목을 문장 단위로 추출한다.

전략:
  1. 문장 분리
  2. 기존 규칙 기반 필터링(is_actual_todo 유사 로직) 1차 적용
  3. Okt 형태소 분석으로 시제 판단 보완 (설치된 경우에만)
  4. 통과한 문장을 TO-DO 목록으로 반환
"""
from __future__ import annotations

import re

# ── 행동 동사 키워드 ─────────────────────────────────────────────────────────
_ACTION_VERBS = [
    "검토", "확인", "제출", "작성", "준비", "참석", "공유", "전달", "보고",
    "회신", "답변", "승인", "결재", "요청", "처리", "수행", "조치", "정리",
    "배포", "개발", "테스트", "진행", "협조", "신청", "등록", "발주",
    "수정", "반영", "검수", "점검", "취합", "제안", "발표", "기획",
    "부탁", "바랍니다", "해주세요", "해야", "드립니다", "부탁드립니다",
]

# 기존 규칙 기반과 동일한 negative 패턴
_NEGATIVE_PATTERNS = [
    "좋다", "춥다", "덥다", "행복", "피곤", "힘들", "재미", "지루",
    "슬프", "기분", "느낌", "아프", "졸리", "점심", "저녁", "아침",
    "커피", "밥", "식사", "날씨", "운동", "게임", "영화", "음악",
]

# 문자열 기반 과거 시제 suffix (규칙 기반 1차)
_PAST_SUFFIXES = [
    "했습니다", "했어요", "했음", "했다", "했는데",
    "됐습니다", "됐어요", "됐음", "됐다",
    "었습니다", "았습니다", "었어요", "았어요",
    # "하였-" 계열 — norm=True 없는 환경에서 Okt가 놓치는 패턴
    "하였습니다", "하였음", "하였다",
    # "였-" 계열 ("이었습니다" 축약형)
    "였습니다", "였어요", "였음", "였다",
    "수행했", "완료했", "처리했", "제출했", "작성했",
    "끝냈", "끝났", "마쳤", "마감됐",
]

# Okt 형태소 분석기 (lazy load)
_okt = None


def _get_okt():
    global _okt
    if _okt is None:
        try:
            from konlpy.tag import Okt
            _okt = Okt()
        except Exception:
            _okt = False  # 설치 안 됐으면 False로 고정
    return _okt if _okt is not False else None


# ── 공개 API ─────────────────────────────────────────────────────────────────

def extract_todo_list(text, *, subject="", title=""):
    """
    메일 본문 + 제목에서 실행 가능한 TO-DO 항목을 최대 7개 반환한다.

    Returns:
        list[str]
    """
    source = "\n".join(p for p in [subject, title, text] if p)
    sentences = _split_sentences(source)
    todos = []
    for sent in sentences:
        sent = sent.strip()
        if len(sent) < 6 or len(sent) > 100:
            continue
        if _is_actionable(sent):
            todos.append(sent)
        if len(todos) >= 7:
            break
    return todos


# ── 내부 구현 ──────────────────────────────────────────────────────────────

def _split_sentences(text):
    """한국어 문장 경계에서 분리한다."""
    # 불릿/번호 목록 → 줄 단위로 분리
    text = re.sub(r'\n+', '\n', text or "")
    # 문장 부호 뒤 공백 기준 분리 (다., 요., 니다. 등)
    text = re.sub(r'(?<=[다요죠])\.\s+', '.\n', text)
    text = re.sub(r'(?<=[다요죠])!\s+', '!\n', text)
    lines = []
    for chunk in text.split('\n'):
        chunk = chunk.strip()
        chunk = re.sub(r'^[-*•\d]+[.)\s]+', '', chunk).strip()
        if chunk:
            lines.append(chunk)
    return lines


def _is_actionable(sentence):
    """
    문장이 실행 가능한 TO-DO인지 판단한다.
    규칙 기반을 기본으로 하고, Okt 형태소 분석으로 시제·어간 판단을 보완한다.
    """
    # 1. negative 패턴 → 즉시 제외
    if sum(1 for p in _NEGATIVE_PATTERNS if p in sentence) >= 2:
        return False

    # 2. 과거 시제 판단 (문자열 규칙 먼저, 형태소로 보완)
    if _is_past_tense(sentence):
        return False

    # 3. 행동 동사 존재 여부 (substring + Okt 어간 매칭)
    if not _has_action_verb(sentence):
        return False

    return True


def _has_action_verb(sentence: str) -> bool:
    """행동 동사가 포함되어 있는지 판단한다.

    1단계: substring 매칭 (빠름, 한국어 어간은 어미 앞에 나타나므로 대부분 커버)
    2단계: Okt stem=True 로 어간 추출 후 집합 교차 (1단계에서 놓친 변형 커버)
    """
    # 1단계: 빠른 substring 매칭
    if any(verb in sentence for verb in _ACTION_VERBS):
        return True

    # 2단계: Okt 어간 매칭
    okt = _get_okt()
    if okt is not None:
        try:
            pos_result = okt.pos(sentence, norm=True, stem=True)
            stems: set[str] = set()
            for word, tag in pos_result:
                w = word.lower()
                if tag == "Noun":
                    stems.add(w)
                elif tag in ("Verb", "Adjective"):
                    # "검토하다" → "검토", "배포하다" → "배포"
                    for suffix in ("하다", "되다", "이다"):
                        if w.endswith(suffix) and len(w) > len(suffix) + 1:
                            stems.add(w[: -len(suffix)])
                            break
                    else:
                        if w.endswith("다") and len(w) > 2:
                            stems.add(w[:-1])
                    stems.add(w)
            return bool(stems & set(_ACTION_VERBS))
        except Exception:
            pass

    return False


def _is_past_tense(sentence):
    """
    과거 시제 여부를 판단한다.

    1단계: 문자열 suffix 매칭 (빠름)
    2단계: Okt 형태소로 마지막 술어 동사 시제 확인 (보완)
    """
    # 1단계: 규칙 기반
    for suffix in _PAST_SUFFIXES:
        if suffix in sentence:
            # 과거형이 있어도 뒤에 현재형 요청이 이어지면 허용
            # 예: "검토했는데 추가 공유 부탁드립니다"
            if _has_trailing_request(sentence, suffix):
                continue
            return True

    # 2단계: Okt 형태소 보완 (위에서 못 잡은 과거형 커버)
    return _is_past_tense_morph(sentence)


def _has_trailing_request(sentence, past_suffix):
    """
    과거형 suffix 이후에 현재 요청 표현이 이어지는지 확인한다.
    예: "검토했는데 추가 공유 부탁드립니다" → True (허용)
    """
    idx = sentence.find(past_suffix)
    if idx == -1:
        return False
    remainder = sentence[idx + len(past_suffix):]
    request_markers = ["부탁", "요청", "바랍니다", "해주세요", "해야", "드립니다", "주시기"]
    return any(m in remainder for m in request_markers)


def _is_past_tense_morph(sentence):
    """
    Okt 형태소 분석으로 마지막 술어 동사/형용사가 과거 시제인지 판단한다.
    Okt가 없으면 False 반환 (규칙 기반만으로 동작).
    """
    okt = _get_okt()
    if okt is None:
        return False

    try:
        pos_result = okt.pos(sentence, norm=True, stem=False)
        # 마지막 Verb / Adjective 토큰이 메인 술어
        verbs = [w for w, t in pos_result if t in ("Verb", "Adjective")]
        if not verbs:
            return False
        last_verb = verbs[-1]
        past_markers = ("었", "았", "했", "됐", "셨", "이었", "였")
        return any(marker in last_verb for marker in past_markers)
    except Exception:
        return False
