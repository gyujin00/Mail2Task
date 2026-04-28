"""
담당: kdh
역할: To-do 리스트 관리
"""

import csv
import hashlib
import os
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    pipeline
)
import config


# -----------------------------
# 1. Lazy Loading (모델)
# -----------------------------
_tokenizer = None
_model = None
_ner_pipeline = None


def _load_model():
    global _tokenizer, _model

    if _tokenizer is None:
        if os.path.exists("./todo_model"):
            path = "./todo_model"
            print("[INFO] Fine-tuned model loaded")
        else:
            path = "klue/bert-base"
            print("[WARNING] Using base model")

        _tokenizer = AutoTokenizer.from_pretrained(path)
        _model = AutoModelForSequenceClassification.from_pretrained(path, num_labels=2)
        _model.eval()

    return _tokenizer, _model


def _load_ner():
    global _ner_pipeline

    if _ner_pipeline is None:
        _ner_pipeline = pipeline(
            "ner",
            model="klue/bert-base",
            aggregation_strategy="simple"
        )

    return _ner_pipeline


# -----------------------------
# 2. 룰 기반 필터 (강화)
# -----------------------------
NEGATIVE_PATTERNS = [
    # 감정/상태
    "좋다", "춥다", "덥다", "행복", "피곤", "힘들", "재미", "지루",
    "슬프", "기분", "느낌", "아프", "졸리",

    # 일상 대화
    "점심", "저녁", "아침", "커피", "밥", "식사", "날씨",
    "운동", "게임", "영화", "음악", "쉬", "자다",

    # 위치/이동
    "퇴근", "출근", "집", "귀가", "외출"
]

POSITIVE_PATTERNS = [
    # 명령형/요청형
    "해야", "하자", "할 것", "할게", "합시다",
    "부탁", "요청", "바랍니다", "부탁드립니다", "드립니다",
    "확인", "검토", "리뷰", "점검",

    # 업무 동사
    "진행", "작성", "제출", "준비", "참석", "예약",
    "필요", "처리", "수행", "조치", "공유", "전달",
    "보고", "회신", "답변", "승인", "결재",

    # 시간 표현
    "까지", "이내", "전까지", "내일", "오늘", "이번 주",
    "다음 주", "금요일", "월요일",

    # 업무 명사
    "회의", "보고서", "문서", "자료", "기획", "개발",
    "테스트", "배포", "미팅", "발표"
]

PAST_PATTERNS = [
    "했다", "했어", "했습니다", "했음",
    "완료", "완료했", "완료됨",
    "끝냈", "끝남", "마쳤", "마침",
    "수행함", "수행했", "처리했", "진행했",
    "작성했", "제출했", "참석했"
]


def _rule_filter(text):
    """기존 룰 필터 (하위 호환)"""
    if any(p in text for p in PAST_PATTERNS):
        return False

    if any(p in text for p in NEGATIVE_PATTERNS):
        return False

    if any(p in text for p in POSITIVE_PATTERNS):
        return True

    return None


def _enhanced_rule_filter(text):
    """강화된 룰 필터 (정확도 향상)"""
    if not text or len(text.strip()) < 3:
        return False

    # 1. 과거형 필터 (최우선)
    past_count = sum(1 for p in PAST_PATTERNS if p in text)
    if past_count >= 1:
        return False

    # 2. 물음표로 끝나면 False
    if text.strip().endswith("?"):
        return False

    # 3. 부정 패턴 체크
    neg_count = sum(1 for p in NEGATIVE_PATTERNS if p in text)
    if neg_count >= 2:  # 부정 키워드 2개 이상
        return False

    # 4. 긍정 패턴 체크
    pos_count = sum(1 for p in POSITIVE_PATTERNS if p in text)
    if pos_count >= 2:  # 긍정 키워드 2개 이상
        return True

    # 5. 단일 키워드로 강한 시그널
    if pos_count == 1 and neg_count == 0:
        # 업무 동사가 있으면 True
        task_verbs = ["진행", "작성", "제출", "준비", "참석", "예약",
                      "처리", "수행", "조치", "검토", "확인", "회신"]
        if any(v in text for v in task_verbs):
            return True

    # 6. 애매하면 None (점수 기반으로 위임)
    return None


def _score_based_filter(text):
    """점수 기반 필터 (보조)"""
    score = 0

    # 긍정 점수
    for pattern in POSITIVE_PATTERNS:
        if pattern in text:
            score += 2

    # 부정 점수
    for pattern in NEGATIVE_PATTERNS:
        if pattern in text:
            score -= 3

    # 과거형 감점
    for pattern in PAST_PATTERNS:
        if pattern in text:
            score -= 5

    # 임계값: 3점 이상이면 To-do
    return score >= 3



def is_actual_todo(text):
    """
    텍스트가 실제 To-do인지 판단한다.

    1. 강화된 규칙 필터 (빠르고 정확)
    2. 점수 기반 필터 (보조)

    """
    if not text or len(text.strip()) < 2:
        return False

    # 1. 강화된 규칙 (80% 정확도)
    rule = _enhanced_rule_filter(text)
    if rule is not None:
        return rule

    # 2. 점수 기반 (보조)
    return _score_based_filter(text)


# -----------------------------
# 4. NER 기반 정보 추출
# -----------------------------
def extract_entities(text):
    ner = _load_ner()
    results = ner(text)

    extracted = {
        "time": [],
        "target": [],
        "action": []
    }

    for r in results:
        word = r["word"]
        label = r["entity_group"]

        # KLUE NER 기준
        if label in ["DAT", "TIM"]:
            extracted["time"].append(word)

        elif label in ["ORG", "LOC"]:
            extracted["target"].append(word)

        else:
            extracted["action"].append(word)

    return extracted


# -----------------------------
# 5. CSV 로드
# -----------------------------
def load_todos():
    if not os.path.exists(config.TODO_CSV):
        return []

    with open(config.TODO_CSV, mode='r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        return list(reader)


# -----------------------------
# 6. CSV 저장
# -----------------------------
def save_todo(task, existing_todos):
    task["id"] = _make_id(task["subject"], task["sender"])
    text = task.get("task_summary", task.get("subject", ""))

    if any(todo['id'] == task["id"] for todo in existing_todos):
        return

    if not is_actual_todo(text):
        print(f"[필터링] 비 To-Do: {text}")
        return

    # 🔥 NER 추가
    entities = extract_entities(text)

    task["time"] = ", ".join(entities["time"])
    task["target"] = ", ".join(entities["target"])
    task["action"] = ", ".join(entities["action"])

    task["task_type"] = classify_task_type(text)

    file_exists = os.path.exists(config.TODO_CSV)

    with open(config.TODO_CSV, mode='a', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=config.CSV_COLUMNS)

        if not file_exists:
            writer.writeheader()

        writer.writerow(task)

    print(f"[저장] {text}")


# -----------------------------
# 7. 상태 업데이트
# -----------------------------
def update_status(task_id, notified=False, status=None):
    todos = load_todos()

    for todo in todos:
        if todo['id'] == task_id:
            if status:
                todo['status'] = status
            todo['notified'] = str(notified)
            break

    with open(config.TODO_CSV, mode='w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=config.CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(todos)


# -----------------------------
# 8. 업무 유형 분류
# -----------------------------
def classify_task_type(text):
    if any(x in text for x in ["보고서", "작성", "문서"]):
        return "보고서"
    if any(x in text for x in ["회의", "미팅"]):
        return "회의"
    if any(x in text for x in ["검토", "리뷰"]):
        return "검토"
    if any(x in text for x in ["결재", "승인"]):
        return "결재"
    if any(x in text for x in ["개발", "코드", "패치"]):
        return "개발"

    return "기타"


# -----------------------------
# 10. ID 생성
# -----------------------------
def _make_id(subject, sender):
    raw = f"{subject}_{sender}"
    return hashlib.md5(raw.encode()).hexdigest()[:12]