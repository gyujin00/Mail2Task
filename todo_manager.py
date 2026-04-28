"""
통합 Todo 매니저 (정확도 복구 버전)
- 저장소: MongoDB (dev)
- 로직: 사용자 지정 강화 필터 + NER (local)
"""

from __future__ import annotations
import hashlib
import os
import re
from datetime import datetime
from pymongo import DESCENDING, MongoClient
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline

import config

# ---------------------------------------------------------
# 1. AI 모델 & NER 로직 (Lazy Loading)
# ---------------------------------------------------------
_tokenizer = None
_model = None
_ner_pipeline = None

def _load_ner():
    global _ner_pipeline
    if _ner_pipeline is None:
        _ner_pipeline = pipeline("ner", model="klue/bert-base", aggregation_strategy="simple")
    return _ner_pipeline

# [정확도 복구] 사용자님의 원본 키워드 리스트 그대로 유지
NEGATIVE_PATTERNS = [
    "좋다", "춥다", "덥다", "행복", "피곤", "힘들", "재미", "지루", "슬프", "기분", "느낌", "아프", "졸리",
    "점심", "저녁", "아침", "커피", "밥", "식사", "날씨", "운동", "게임", "영화", "음악", "쉬", "자다",
    "퇴근", "출근", "집", "귀가", "외출"
]

POSITIVE_PATTERNS = [
    "해야", "하자", "할 것", "할게", "합시다", "부탁", "요청", "바랍니다", "부탁드립니다", "드립니다",
    "확인", "검토", "리뷰", "점검", "진행", "작성", "제출", "준비", "참석", "예약", "필요", "처리", 
    "수행", "조치", "공유", "전달", "보고", "회신", "답변", "승인", "결재", "까지", "이내", "전까지", 
    "내일", "오늘", "이번 주", "다음 주", "금요일", "월요일", "회의", "보고서", "문서", "자료", 
    "기획", "개발", "테스트", "배포", "미팅", "발표"
]

PAST_PATTERNS = [
    "했다", "했어", "했습니다", "했음", "완료", "완료했", "완료됨", "끝냈", "끝남", "마쳤", "마침",
    "수행함", "수행했", "처리했", "진행했", "작성했", "제출했", "참석했"
]

# [정확도 핵심] 사용자님의 강화된 필터 로직 복구
def _enhanced_rule_filter(text):
    if not text or len(text.strip()) < 3:
        return False
    # 1. 과거형 필터 (최우선)
    if any(p in text for p in PAST_PATTERNS):
        return False
    # 2. 물음표 종료
    if text.strip().endswith("?"):
        return False
    # 3. 부정 패턴 체크 (2개 이상)
    if sum(1 for p in NEGATIVE_PATTERNS if p in text) >= 2:
        return False
    # 4. 긍정 패턴 체크 (2개 이상)
    if sum(1 for p in POSITIVE_PATTERNS if p in text) >= 2:
        return True
    # 5. 단일 키워드 + 업무 동사 강한 시그널
    if sum(1 for p in POSITIVE_PATTERNS if p in text) == 1 and sum(1 for p in NEGATIVE_PATTERNS if p in text) == 0:
        task_verbs = ["진행", "작성", "제출", "준비", "참석", "예약", "처리", "수행", "조치", "검토", "확인", "회신"]
        if any(v in text for v in task_verbs):
            return True
    return None

def _score_based_filter(text):
    score = 0
    for p in POSITIVE_PATTERNS:
        if p in text: score += 2
    for p in NEGATIVE_PATTERNS:
        if p in text: score -= 3
    for p in PAST_PATTERNS:
        if p in text: score -= 5
    return score >= 3  # 사용자님의 원본 임계값 3 유지

def is_actual_todo(text):
    if not text or len(text.strip()) < 2:
        return False
    rule_result = _enhanced_rule_filter(text)
    if rule_result is not None:
        return rule_result
    return _score_based_filter(text)

def extract_entities(text):
    try:
        ner = _load_ner()
        results = ner(text)
        extracted = {"time": [], "target": [], "action": []}
        for r in results:
            label, word = r["entity_group"], r["word"]
            if label in ["DAT", "TIM"]: extracted["time"].append(word)
            elif label in ["ORG", "LOC"]: extracted["target"].append(word)
            else: extracted["action"].append(word)
        return extracted
    except:
        return {"time": [], "target": [], "action": []}

# ---------------------------------------------------------
# 2. MongoDB 연결 (dev 유지)
# ---------------------------------------------------------
_client = None

def _get_client():
    global _client
    if _client is None:
        _client = MongoClient(config.MONGODB_URI, serverSelectionTimeoutMS=5000)
    return _client

def _get_mail_collection():
    client = _get_client()
    col = client[config.MONGODB_DB][config.MONGODB_MAILS_COLLECTION]
    col.create_index("mail_id", unique=True)
    return col

def _get_task_collection():
    client = _get_client()
    col = client[config.MONGODB_DB][config.MONGODB_TASKS_COLLECTION]
    col.create_index("task_id", unique=True)
    col.create_index("id", unique=True)
    return col

# ---------------------------------------------------------
# 3. 데이터 저장 및 조회
# ---------------------------------------------------------
def save_mail(mail):
    collection = _get_mail_collection()
    mail_id = mail.get("mail_id") or _make_mail_id(mail.get("subject", ""), mail.get("sender", ""), mail.get("received_at", ""))
    document = {
        "mail_id": mail_id,
        "subject": mail.get("subject", ""),
        "sender": mail.get("sender", ""),
        "received_at": mail.get("received_at", ""),
        "body": mail.get("body", ""),
        "created_at": _now_iso(),
        "updated_at": _now_iso(),
    }
    collection.replace_one({"mail_id": mail_id}, document, upsert=True)
    return document

def save_tasks(tasks):
    if not tasks: return []
    collection = _get_task_collection()
    saved_documents = []

    for task in tasks:
        title = task.get("title") or task.get("subject", "")
        
        # 복구된 정확도 로직 적용
        if not is_actual_todo(title):
            continue

        entities = extract_entities(title)
        task_id = task.get("task_id") or _make_task_id(task.get("mail_id", ""), title, task.get("task_order", 1))

        document = {
            "task_id": task_id,
            "id": task_id,
            "mail_id": task.get("mail_id", ""),
            "title": title,
            "status": task.get("status", "대기"),
            "task_type": classify_task_type(title),
            "time": ", ".join(entities["time"]),
            "target": ", ".join(entities["target"]),
            "action": ", ".join(entities["action"]),
            "received_at": task.get("received_at", ""),
            "created_at": _now_iso(),
            "updated_at": _now_iso(),
        }
        collection.replace_one({"task_id": task_id}, document, upsert=True)
        saved_documents.append(document)
    return saved_documents

def load_tasks():
    collection = _get_task_collection()
    return list(collection.find({}, {"_id": 0}).sort("received_at", DESCENDING))

def update_status(task_id, notified=None, status=None):
    updates = {"updated_at": _now_iso()}
    if notified is not None: updates["notified"] = bool(notified)
    if status is not None: updates["status"] = status
    collection = _get_task_collection()
    collection.update_one({"$or": [{"task_id": task_id}, {"id": task_id}]}, {"$set": updates})

def classify_task_type(text):
    # 사용자님의 원본 분류 로직 유지
    if any(x in text for x in ["보고서", "작성", "문서"]): return "보고서"
    if any(x in text for x in ["회의", "미팅"]): return "회의"
    if any(x in text for x in ["검토", "리뷰"]): return "검토"
    if any(x in text for x in ["결재", "승인"]): return "결재"
    if any(x in text for x in ["개발", "코드", "패치"]): return "개발"
    return "기타"

def _make_mail_id(subject, sender, received_at):
    raw = f"{subject}_{sender}_{received_at}"
    return hashlib.md5(raw.encode()).hexdigest()[:16]

def _make_task_id(mail_id, title, task_order):
    raw = f"{mail_id}_{task_order}_{title}"
    return hashlib.md5(raw.encode()).hexdigest()[:16]

def _now_iso():
    return datetime.utcnow().isoformat(timespec="seconds")