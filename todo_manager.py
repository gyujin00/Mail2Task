"""
담당: kdh
역할: To-do 리스트 관리 + 의도 분류 + 정보 추출
"""

import csv
import hashlib
import os
import torch
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
# 2. 룰 기반 필터
# -----------------------------
NEGATIVE_PATTERNS = ["좋다", "춥다", "덥다", "행복", "피곤", "점심", "날씨"]
POSITIVE_PATTERNS = ["해야", "하자", "할 것", "부탁", "요청", "바랍니다", "확인"]
PAST_PATTERNS = ["했다", "완료", "수행함", "끝냈"]


def _rule_filter(text):
    if any(p in text for p in PAST_PATTERNS):
        return False

    if any(p in text for p in NEGATIVE_PATTERNS):
        return False

    if any(p in text for p in POSITIVE_PATTERNS):
        return True

    return None


# -----------------------------
# 3. BERT 의도 판단
# -----------------------------
def _bert_predict(text):
    tokenizer, model = _load_model()

    inputs = tokenizer(
        text,
        return_tensors="pt",
        truncation=True,
        padding=True,
        max_length=64
    )

    with torch.no_grad():
        outputs = model(**inputs)
        logits = outputs.logits
        pred = torch.argmax(logits, dim=1).item()

    return pred == 1


def is_actual_todo(text):
    if not text or len(text.strip()) < 2:
        return False

    rule = _rule_filter(text)
    if rule is not None:
        return rule

    return _bert_predict(text)


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
# 9. 완료 + 미알림 조회
# -----------------------------
def get_completed_unnotified():
    todos = load_todos()

    return [
        todo for todo in todos
        if todo.get('status') == "완료"
        and (not todo.get('notified') or todo.get('notified') == "False")
    ]


# -----------------------------
# 10. ID 생성
# -----------------------------
def _make_id(subject, sender):
    raw = f"{subject}_{sender}"
    return hashlib.md5(raw.encode()).hexdigest()[:12]
