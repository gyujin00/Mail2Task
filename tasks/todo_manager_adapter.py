"""
todo_manager.py 원본을 보존한 채 실제 런타임과 연결하는 어댑터 모듈.

역할:
- 팀원의 의도 분류 / 엔티티 추출 / 유형 분류 로직 호출
- 실패 시 현재 프로젝트가 멈추지 않도록 안전한 fallback 제공
- 실제 저장/조회는 mongo_task_store로 위임
"""

from __future__ import annotations

import hashlib
import importlib
import re

from storage import mongo_task_store


_todo_manager_module = None
_todo_manager_import_error = None


def load_todos():
    """기존 호출부 호환용 별칭."""
    return load_tasks()


def load_tasks():
    """MongoDB에 저장된 Task 목록을 반환한다."""
    return mongo_task_store.load_tasks()


def save_mail(mail):
    """메일 원문을 MongoDB mails 컬렉션에 저장한다."""
    return mongo_task_store.save_mail(mail)


def save_todo(task, existing_todos):
    """
    todo_manager 원본 로직을 최대한 거쳐 단일 Task를 저장한다.
    """
    prepared_task = dict(task)
    prepared_task["id"] = prepared_task.get("id") or _make_id(
        prepared_task.get("subject", ""),
        prepared_task.get("sender", ""),
    )

    analysis_text = prepared_task.get("source_text") or prepared_task.get(
        "task_summary",
        prepared_task.get("subject", ""),
    )
    if not is_actual_todo(analysis_text):
        print(f"[필터링] 비 To-Do: {analysis_text}")
        return None

    entities = extract_entities(analysis_text)
    prepared_task["time"] = ", ".join(entities["time"])
    prepared_task["target"] = ", ".join(entities["target"])
    prepared_task["action"] = ", ".join(entities["action"])
    prepared_task["time_entities"] = entities["time"]
    prepared_task["target_entities"] = entities["target"]
    prepared_task["action_entities"] = entities["action"]

    if not prepared_task.get("task_type"):
        prepared_task["task_type"] = classify_task_type(analysis_text)

    if any(todo.get("id") == prepared_task["id"] for todo in existing_todos):
        return None

    saved_documents = mongo_task_store.save_tasks([prepared_task])
    if saved_documents:
        print(f"[저장] {analysis_text}")
        return saved_documents[0]
    return None


def save_tasks(tasks):
    """
    추출된 Task 목록을 todo_manager 원본 로직을 거쳐 MongoDB에 저장한다.
    """
    existing_todos = load_tasks()
    saved = []
    for task in tasks:
        saved_task = save_todo(task, existing_todos)
        if saved_task is None:
            continue
        existing_todos.append(saved_task)
        saved.append(saved_task)
    return saved


def update_status(task_id, notified=False, status=None):
    """특정 업무(Task)의 상태/알림 여부를 갱신한다."""
    return mongo_task_store.update_status(task_id, notified=notified, status=status)


def get_completed_unnotified():
    """완료되었지만 아직 완료 알림을 보내지 않은 업무를 조회한다."""
    return mongo_task_store.get_completed_unnotified()


def mail_exists(subject, sender, received_at):
    """같은 메일이 이미 저장되었는지 확인한다."""
    return mongo_task_store.mail_exists(subject, sender, received_at)


def classify_task_type(text):
    """
    todo_manager 원본 분류기를 우선 사용하고, 부족한 경우 현재 규칙으로 보완한다.
    """
    manager = _get_todo_manager_module()
    if manager is not None:
        try:
            result = manager.classify_task_type(text)
            if result and result != "기타":
                return result
        except Exception:
            pass

    return mongo_task_store.classify_task_type(text)


def is_actual_todo(text):
    """
    todo_manager 원본의 의도 분류를 우선 사용한다.
    모델/의존성이 없으면 보수적 fallback을 사용한다.
    """
    if not text or len(text.strip()) < 2:
        return False

    manager = _get_todo_manager_module()
    if manager is not None:
        try:
            return bool(manager.is_actual_todo(text))
        except Exception:
            pass

    if _rule_filter(text) is not None:
        return _rule_filter(text)
    return True


def extract_entities(text):
    """
    todo_manager 원본의 NER 추출을 우선 사용한다.
    실패 시 구조화 필드/날짜 패턴 기반 fallback을 사용한다.
    """
    manager = _get_todo_manager_module()
    if manager is not None:
        try:
            entities = manager.extract_entities(text)
            if isinstance(entities, dict):
                normalized = {
                    "time": list(entities.get("time", [])),
                    "target": list(entities.get("target", [])),
                    "action": list(entities.get("action", [])),
                }
                return _deduplicate_entities(normalized)
        except Exception:
            pass

    extracted = {"time": [], "target": [], "action": []}
    extracted["time"].extend(_find_time_entities(text))

    action_value = _extract_structured_value(text, ("과업명", "업무명", "action", "task"))
    if action_value:
        extracted["action"].append(action_value)

    target_value = _extract_structured_value(text, ("대상", "target"))
    if target_value:
        extracted["target"].append(target_value)

    return _deduplicate_entities(extracted)


def _get_todo_manager_module():
    """todo_manager 모듈을 지연 로드한다."""
    global _todo_manager_module, _todo_manager_import_error

    if _todo_manager_module is not None:
        return _todo_manager_module
    if _todo_manager_import_error is not None:
        return None

    try:
        _todo_manager_module = importlib.import_module("tasks.todo_manager")
        return _todo_manager_module
    except Exception as error:  # pragma: no cover - 환경 의존 fallback
        _todo_manager_import_error = error
        return None


def _rule_filter(text):
    """todo_manager와 비슷한 규칙 기반 fallback."""
    negative_patterns = ["좋다", "춥다", "덥다", "행복", "피곤", "점심", "날씨"]
    positive_patterns = ["해야", "하자", "할 것", "부탁", "요청", "바랍니다", "확인"]
    past_patterns = ["했다", "완료", "수행함", "끝냈"]

    if any(pattern in text for pattern in past_patterns):
        return False
    if any(pattern in text for pattern in negative_patterns):
        return False
    if any(pattern in text for pattern in positive_patterns):
        return True
    return None


def _extract_structured_value(text, field_names):
    """'필드명: 값' 형식에서 값을 추출한다."""
    for raw_line in (text or "").splitlines():
        line = raw_line.strip().replace("*", "")
        lowered = line.lower()
        for field_name in field_names:
            name = field_name.lower()
            if lowered.startswith(name + ":") or lowered.startswith(name + "："):
                return line.split(":", 1)[-1].split("：", 1)[-1].strip()
    return ""


def _find_time_entities(text):
    """모델이 없을 때 날짜/시간 패턴을 간단히 추출한다."""
    patterns = [
        r"\d{4}[.\-/]\d{1,2}[.\-/]\d{1,2}(?:\s+\d{1,2}:\d{2})?",
        r"\d{1,2}/\d{1,2}(?:\s+\d{1,2}:\d{2})?",
        r"\d{1,2}\s*월\s*\d{1,2}\s*일(?:\s+\d{1,2}:\d{2})?",
        r"이번\s*주\s*[월화수목금토일]요일?",
        r"다음\s*주\s*[월화수목금토일]요일?",
        r"내일(?:까지)?",
    ]
    results = []
    for pattern in patterns:
        results.extend(re.findall(pattern, text))
    return results


def _deduplicate_entities(extracted):
    """중복 엔티티를 제거하면서 순서를 유지한다."""
    result = {}
    for key, values in extracted.items():
        seen = set()
        result[key] = []
        for value in values:
            normalized = (value or "").strip()
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            result[key].append(normalized)
    return result


def _make_id(subject, sender):
    """기존 todo_manager와 동일한 방식으로 ID를 만든다."""
    raw = f"{subject}_{sender}"
    return hashlib.md5(raw.encode()).hexdigest()[:12]
