"""
메일 본문에서 실행 가능한 TO-DO 항목을 문장 단위로 추출한다.

판별 원리 (형태소 분석 기반 규칙):
  한국어는 교착어(agglutinative)이므로 동사 어간 + 어미 조합으로 의미가 결정됨.

  형태소 분석 3단계:
    1. Okt.pos(norm=True, stem=False)로 표면형 태깅
       → 마지막 용언의 어미를 분석하여 의도(Intent) 분류
    2. Okt.pos(norm=True, stem=True)로 어간형 태깅
       → 행동 동사 구조 확인 (명사+경동사 복합 서술어 포함)
    3. REQUEST / COMMAND / OBLIGATION / FUTURE_INTENT + 행동 구조 → TODO

  regex는 fallback(Okt 미설치)과 문장 분리에만 사용.
  의미 판단에 regex 금지 / 단순 명사 포함 여부로 판단 금지.
"""
from __future__ import annotations

import re
from enum import Enum


# ── 의도 분류 ─────────────────────────────────────────────────────────────────

class Intent(str, Enum):
    REQUEST       = "REQUEST"        # 주세요, 바랍니다, 부탁드립니다
    COMMAND       = "COMMAND"        # 하십시오, (으)세요
    OBLIGATION    = "OBLIGATION"     # 해야 합니다, 해야 됩니다
    FUTURE_INTENT = "FUTURE_INTENT"  # 하겠습니다, 예정입니다
    REPORT        = "REPORT"         # 했습니다 (과거 완료)
    NONE          = "NONE"           # 판단 불가


_TODO_INTENTS: frozenset[Intent] = frozenset({
    Intent.REQUEST,
    Intent.COMMAND,
    Intent.OBLIGATION,
    Intent.FUTURE_INTENT,
})


# ── 행동 동사 의미 어간 ────────────────────────────────────────────────────────
# 한국어 행동 동사의 대부분은 [행동명사] + 경동사(하다/드리다) 구조:
#   "검토하다" → Okt: ('검토', Noun) + ('하다', Verb)
# 따라서 이 목록은 행동명사(Noun) 기준으로 정의.
_ACTION_STEMS: frozenset[str] = frozenset({
    # 문서·보고
    "검토", "확인", "제출", "작성", "보고", "정리", "취합", "기안", "발표",
    "발송", "회신", "답변", "공유", "전달",
    # 업무 커뮤니케이션
    "공지", "안내", "연락", "문의", "협의", "논의", "제안",
    # 업무 처리
    "처리", "수행", "진행", "조치", "승인", "결재", "협조",
    "신청", "등록", "준비", "예약", "참석", "지원",
    # 품질·검증
    "리뷰", "검수", "분석", "점검",
    # 개발·운영
    "개발", "배포", "테스트", "수정", "반영", "기획", "설계",
    # 요청·부탁 명사 (부탁드립니다 등에서 행동으로 인정)
    "요청", "부탁",
})

# 요청 의미 명사: 단독으로도 REQUEST 행동 구조 인정
_REQUEST_NOUNS: frozenset[str] = frozenset({"부탁", "요청"})

# 미래·계획 의미 명사: '예정입니다', '계획입니다' 패턴 인식
_FUTURE_NOUNS: frozenset[str] = frozenset({"예정", "계획"})


# ── 어미 패턴 (Okt 반환 용언 토큰의 표면형 끝부분 기준) ───────────────────────
# Okt는 어미를 별도 태그로 분리하지 않으므로, 용언 토큰 전체 표면형의 endswith로 판단.

# REPORT: 과거 완료 어미
_PAST_ENDINGS: tuple[str, ...] = (
    "았습니다", "었습니다", "했습니다", "됐습니다", "하였습니다",
    "았어요",   "었어요",   "했어요",   "됐어요",   "하였어요",
    "았음",     "었음",     "했음",     "됐음",
    "았다",     "었다",     "했다",     "됐다",
    "았는데",   "었는데",   "했는데",
    "였습니다", "였어요",   "였음",     "였다",
    "셨습니다", "셨어요",
    "았",       "었",       "했",       "됐",        # 짧은 형태 (복합문 내 어절)
)

# REQUEST: 요청 어미 (평서형 + 의문형 완곡 요청 포함)
_REQUEST_ENDINGS: tuple[str, ...] = (
    "주세요", "주십시오", "주시기 바랍니다",
    "바랍니다", "드립니다", "드려요",
    "달라", "달라고",
    # 의문형 완곡 요청: "검토해 주시겠어요?", "확인해 주시겠습니까?"
    "주시겠어요", "주시겠습니까", "주시겠습니다",
)

# COMMAND: 명령형 어미 (주세요 계열 제외 — REQUEST에서 먼저 처리됨)
_COMMAND_ENDINGS: tuple[str, ...] = (
    "하십시오", "하세요",
    "으십시오", "으세요",
    "십시오",
    "세요",
    "시오",
)

# OBLIGATION: 의무 어간부 ("해야", "아야" 등)
_OBLIGATION_STEMS: tuple[str, ...] = (
    "해야", "아야", "어야", "여야",
)

# OBLIGATION: 의무 보조 서술어 ("합니다", "됩니다" 등)
_OBLIGATION_AUX: tuple[str, ...] = (
    "합니다", "됩니다", "해요", "돼요", "한다", "된다",
)

# FUTURE_INTENT: 미래/의지 어미
_FUTURE_ENDINGS: tuple[str, ...] = (
    "하겠습니다", "겠습니다", "하겠어요", "겠어요", "하겠다", "겠다",
)

# FUTURE_INTENT: 미래 명사(예정/계획) 뒤 서술 어미
_FUTURE_AUX_ENDINGS: tuple[str, ...] = (
    "입니다", "이에요", "이다", "임",
)

# 요청 보조 서술어: 부탁/요청 명사 뒤에 오는 동사
_REQUEST_AUX_ENDINGS: tuple[str, ...] = (
    "드립니다", "드려요", "드리다", "합니다", "해요",
)


# ── fallback regex (모듈 레벨 1회 컴파일 — Okt 미설치 환경 전용) ───────────────
_FALLBACK_PAST_RE = re.compile(
    r"(았|었|했|됐|하였|셨)(습니다|어요|아요|음|다|는데)"
)
_FALLBACK_REQUEST_RE = re.compile(
    r"[아어해]\s*주\s*세요"           # 해 주세요
    r"|[아어해]\s*주\s*십시오"         # 해 주십시오
    r"|주\s*시\s*겠\s*(어요|습니까)"  # 주시겠어요, 주시겠습니까 (완곡 요청)
    r"|기\s*바랍니다|바랍니다"         # 기 바랍니다, 바랍니다
    r"|부탁\s*(합니다|드립니다|드려요)" # 부탁드립니다 등
    r"|(으)?십시오"                    # (으)십시오
    r"|(으)?세요"                      # (으)세요
    r"|해\s*야\s*(합니다|됩니다)"      # 해야 합니다/됩니다
    r"|겠\s*(습니다|어요)"             # 하겠습니다, 배포하겠습니다, 드리겠습니다 전부 커버
    r"|예정\s*입니다"                  # 예정입니다
)


# ── 구조화 필드 마커 (무조건 TODO) ───────────────────────────────────────────
_STRUCTURED_MARKERS: tuple[str, ...] = (
    "과업명:", "업무명:", "업무유형:", "마감일:", "마감기한:",
    "요청사항:", "대상:", "우선순위:",
)


# ── Okt 지연 로딩 ─────────────────────────────────────────────────────────────
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


# ── 공개 API ──────────────────────────────────────────────────────────────────

def extract_todo_list(text: str, *, subject: str = "", title: str = "") -> list[str]:
    """메일 본문 + 제목에서 실행 가능한 TO-DO 항목을 최대 7개 반환한다."""
    source = "\n".join(p for p in [subject, title, text] if p)
    sentences = _split_sentences(source)
    todos: list[str] = []
    for sent in sentences:
        sent = sent.strip()
        if len(sent) < 6 or len(sent) > 120:
            continue
        if _is_actionable(sent):
            todos.append(sent)
        if len(todos) >= 7:
            break
    return todos


# ── 내부 구현 ─────────────────────────────────────────────────────────────────

def _split_sentences(text: str) -> list[str]:
    """한국어 문장 경계에서 분리한다."""
    text = re.sub(r"\n+", "\n", text or "")
    text = re.sub(r"(?<=[다요죠])\.\s+", ".\n", text)
    text = re.sub(r"(?<=[다요죠])!\s+", "!\n", text)
    lines = []
    for chunk in text.split("\n"):
        chunk = chunk.strip()
        chunk = re.sub(r"^[-*•\d]+[.)\s]+", "", chunk).strip()
        if chunk:
            lines.append(chunk)
    return lines


def _is_actionable(sentence: str) -> bool:
    """
    문장이 실행 가능한 TO-DO인지 형태소 기반 규칙으로 판별한다.

    판별 흐름:
      0. 구조화 필드(과업명: 등) → 즉시 True
      1. 비업무 노이즈 단어 2개 이상 → False
      2. Okt 형태소 분석 (표면형: 어미 분석용, 어간형: 행동 동사 정규화용)
      3. 의도(Intent) 분류 → REPORT / NONE이면 False
      4. TODO 의도 + 행동 동사 구조 확인 → True / False
      5. Okt 미설치 → regex fallback
    """
    # 0. 구조화 필드
    if any(marker in sentence for marker in _STRUCTURED_MARKERS):
        return True

    okt = _get_okt()
    if okt is not None:
        try:
            # 표면형: 용언 어미 분석으로 의도 분류
            pos_surface: list[tuple[str, str]] = okt.pos(sentence, norm=True, stem=False)
            # 어간형: 복합 서술어 정규화로 행동 동사 구조 확인
            pos_stem: list[tuple[str, str]] = okt.pos(sentence, norm=True, stem=True)

            intent = _classify_intent(pos_surface)

            if intent == Intent.REPORT or intent == Intent.NONE:
                return False
            if intent in _TODO_INTENTS:
                return _has_action_structure(pos_surface, pos_stem)
        except Exception:
            # Okt 분석 실패 시 regex fallback으로 복구
            return _fallback_is_actionable(sentence)
        return False

    # Okt 미설치: regex fallback (보조 처리 전용)
    return _fallback_is_actionable(sentence)


def _classify_intent(pos_surface: list[tuple[str, str]]) -> Intent:
    """
    형태소 분석 표면형 결과로 문장의 의도를 분류한다.

    핵심 원칙:
      - 마지막 용언(Verb/Adjective)의 어미가 주 판단 기준
      - 2-용언 구조(해야 + 합니다) 또는 명사+서술어 구조를 보조 기준으로 사용
      - regex 금지 — 모든 판단은 Okt 반환 토큰의 endswith 비교

    분류 우선순위:
      1. REPORT       : 마지막 용언이 과거 어미
      2. FUTURE_INTENT: 마지막 용언이 겠-어미 또는 (예정/계획 명사 + 서술 어미)
      3. REQUEST      : 마지막 용언이 주세요/바랍니다/드립니다 계열
                        또는 (부탁/요청 명사 + 보조 서술어)
      4. COMMAND      : 마지막 용언이 세요/십시오 계열
      5. OBLIGATION   : (의무 어간 + 합니다/됩니다) 2-동사 구조
      6. NONE         : 해당 없음
    """
    verbs: list[tuple[int, str, str]] = [
        (i, w, t)
        for i, (w, t) in enumerate(pos_surface)
        if t in ("Verb", "Adjective")
    ]
    nouns: list[tuple[int, str]] = [
        (i, w)
        for i, (w, t) in enumerate(pos_surface)
        if t == "Noun"
    ]

    if not verbs:
        return Intent.NONE

    _, last_verb, _ = verbs[-1]

    # ── 1. REPORT: 마지막 용언이 과거 어미 ──────────────────────────────────
    if last_verb.endswith(_PAST_ENDINGS):
        return Intent.REPORT

    # ── 2. FUTURE_INTENT: 겠-어미 ───────────────────────────────────────────
    if last_verb.endswith(_FUTURE_ENDINGS):
        return Intent.FUTURE_INTENT

    # ── 2-b. FUTURE_INTENT: 미래 명사(예정/계획) + 서술 어미(입니다/이다) ───
    if last_verb.endswith(_FUTURE_AUX_ENDINGS):
        if any(noun in _FUTURE_NOUNS for _, noun in nouns):
            return Intent.FUTURE_INTENT

    # ── 3. REQUEST: 주세요/바랍니다/드립니다 계열 어미 ─────────────────────
    if last_verb.endswith(_REQUEST_ENDINGS):
        return Intent.REQUEST

    # ── 3-b. REQUEST: 부탁/요청 명사 + 보조 서술어(드립니다/합니다) ─────────
    if last_verb.endswith(_REQUEST_AUX_ENDINGS):
        if any(noun in _REQUEST_NOUNS for _, noun in nouns):
            return Intent.REQUEST

    # ── 4. COMMAND: 세요/십시오 계열 명령형 어미 ────────────────────────────
    if last_verb.endswith(_COMMAND_ENDINGS):
        return Intent.COMMAND

    # ── 5. OBLIGATION: [의무 어간(해야)] + [보조 서술어(합니다)] 2-동사 구조 ─
    if len(verbs) >= 2:
        _, second_last_verb, _ = verbs[-2]
        if (second_last_verb.endswith(_OBLIGATION_STEMS)
                and last_verb.endswith(_OBLIGATION_AUX)):
            return Intent.OBLIGATION

    # ── 5-b. OBLIGATION: 해야 단독 종결 (구어체) ────────────────────────────
    if last_verb.endswith(_OBLIGATION_STEMS):
        return Intent.OBLIGATION

    return Intent.NONE


def _has_action_structure(
    pos_surface: list[tuple[str, str]],
    pos_stem: list[tuple[str, str]],
) -> bool:
    """
    형태소 분석 결과에서 행동 동사 구조가 존재하는지 확인한다.

    인식 패턴:
      Pattern 1 (표면형): [행동명사(ACTION_STEMS)] + [용언] 구조
        Okt는 대부분의 행동 동사를 [명사 + 경동사]로 분리함
        예: '검토해 주세요' → ('검토', Noun) + ('해', Verb) + ('주세요', Verb)
            행동명사 '검토' 뒤에 용언이 따르면 행동 구조 인정

      Pattern 2 (어간형): 어간형 용언 토큰에서 경동사 어미 제거 후 ACTION_STEMS 확인
        예: stem=True → ('검토하다', Verb) → 어간 '검토' 추출 → ACTION_STEMS 포함

    명사 단독 포함 여부로 판단하지 않음:
      반드시 [행동명사 + 용언] 또는 [동사 어간 in ACTION_STEMS] 구조여야 함.
    """
    # Pattern 1: 행동명사 + 용언 구조 (표면형 기준)
    for i, (word, tag) in enumerate(pos_surface):
        if tag == "Noun" and (word in _ACTION_STEMS or word in _REQUEST_NOUNS):
            rest = pos_surface[i + 1:]
            if any(t in ("Verb", "Adjective") for _, t in rest):
                return True

    # Pattern 2: 어간형 용언에서 경동사 어미 제거 후 행동 어간 추출
    for word, tag in pos_stem:
        if tag not in ("Verb", "Adjective"):
            continue
        for suffix in ("하다", "되다", "이다", "드리다"):
            if word.endswith(suffix) and len(word) > len(suffix) + 1:
                stem = word[: -len(suffix)]
                if stem in _ACTION_STEMS or stem in _REQUEST_NOUNS:
                    return True
        # 단순 "다" 제거 후 확인
        if word.endswith("다") and len(word) > 2:
            if word[:-1] in _ACTION_STEMS:
                return True

    return False


def _fallback_is_actionable(sentence: str) -> bool:
    """
    Okt 미설치/예외 환경용 fallback. regex는 이 함수에서만 의미 판단에 사용됨.
    모듈 레벨 상수 _FALLBACK_PAST_RE / _FALLBACK_REQUEST_RE 사용 (1회 컴파일).
    """
    past_match = _FALLBACK_PAST_RE.search(sentence)
    if past_match:
        after_past = sentence[past_match.end():]
        if not _FALLBACK_REQUEST_RE.search(after_past):
            return False

    if not _FALLBACK_REQUEST_RE.search(sentence):
        return False

    return any(stem in sentence for stem in _ACTION_STEMS)


# ── 테스트 ────────────────────────────────────────────────────────────────────

def _run_tests() -> None:
    """
    형태소 기반 의도 분류 + 행동 구조 판별 테스트.

    Okt 설치 환경에서 실행 권장.
    각 케이스: (문장, 기대 결과, 기대 의도)
    """
    cases: list[tuple[str, bool, str]] = [
        # REQUEST 케이스
        ("보고서를 검토해 주시기 바랍니다",        True,  "REQUEST"),
        ("검토 부탁드립니다",                       True,  "REQUEST"),
        ("수정해 주십시오",                         True,  "REQUEST"),
        ("발표 자료를 작성해 주세요",               True,  "REQUEST"),
        ("회의에 참석해 주세요",                    True,  "REQUEST"),
        ("승인을 요청드립니다",                     True,  "REQUEST"),
        ("메일 확인 부탁드립니다",                  True,  "REQUEST"),
        # OBLIGATION 케이스
        ("자료를 취합해야 합니다",                  True,  "OBLIGATION"),
        ("제출해야 됩니다",                         True,  "OBLIGATION"),
        # FUTURE_INTENT 케이스
        ("다음 주 배포 예정입니다",                 True,  "FUTURE_INTENT"),
        ("검토 후 공유 예정입니다",                 True,  "FUTURE_INTENT"),
        ("배포하겠습니다",                          True,  "FUTURE_INTENT"),
        ("답변 드리겠습니다",                       True,  "FUTURE_INTENT"),
        # 복합문: 과거절 + 현재 요청 → True
        ("검토했는데 추가 공유 부탁드립니다",       True,  "REQUEST"),
        # STRUCTURED MARKER → True
        ("업무유형: 개발",                          True,  "STRUCTURED"),
        # REPORT → False
        ("검토했습니다",                            False, "REPORT"),
        ("처리가 완료됐습니다",                     False, "REPORT"),
        ("수행했음",                                False, "REPORT"),
        # NONE → False
        ("내일 회의가 있습니다",                    False, "NONE"),
        ("오늘 날씨가 좋네요",                      False, "NONE"),
    ]

    okt = _get_okt()
    okt_available = okt is not None
    print(f"Okt 사용 가능: {okt_available}\n")

    passed = 0
    failed = 0
    for sentence, expected, intent_hint in cases:
        result = _is_actionable(sentence)
        status = "PASS" if result == expected else "FAIL"
        if result == expected:
            passed += 1
        else:
            failed += 1
        print(f"[{status}] {sentence!r}")
        if result != expected:
            print(f"       기대={expected} 실제={result} (의도힌트={intent_hint})")

    print(f"\n결과: {passed}/{passed + failed} 통과")


if __name__ == "__main__":
    _run_tests()
