"""
담당: kdh
역할: To-do 리스트 파일 생성(기본) / 업무 유형 분류 / 알림 트리거
"""
import csv
import hashlib
import config


def load_todos():
    """
    todo_list.csv를 읽어 태스크 목록을 반환한다.
    파일이 없으면 빈 리스트를 반환한다.

    반환:
        list[dict]: CSV 행을 dict로 변환한 목록
                    키는 config.CSV_COLUMNS 참고
    """
    # TODO: config.TODO_CSV 파일을 열어 csv.DictReader로 읽기
    # 파일이 없으면 [] 반환

    return []


def save_todo(task, existing_todos):
    """
    새 태스크를 todo_list.csv에 추가한다.

    인자:
        task          (dict): main.py에서 전달하는 태스크 dict
                              키: subject, sender, deadline, task_summary,
                                  task_type, urgency_score, urgency_level,
                                  status, received_at
        existing_todos(list): 중복 체크용 기존 데이터 (load_todos 반환값)
    """
    task["id"] = _make_id(task["subject"], task["sender"])
    task["task_type"] = classify_task_type(task.get("task_summary", ""))

    # TODO: config.TODO_CSV에 task를 한 행으로 추가 (append 모드)
    # 파일이 없으면 헤더(config.CSV_COLUMNS)도 함께 작성


def update_status(task_id, notified=False, status=None):
    """
    특정 id의 태스크 상태를 업데이트한다.

    인자:
        task_id (str): 업데이트할 태스크의 id
        notified(bool): 완료 알림 발송 여부
        status  (str): 변경할 상태값 (예: "완료")
    """
    # TODO: CSV 전체를 읽어 해당 id 행만 수정 후 다시 저장


def classify_task_type(text):
    """
    텍스트를 분석하여 업무 유형을 반환한다.

    반환 예시: "보고서", "회의", "검토", "기타"
    """
    # TODO: 키워드 기반으로 유형 분류
    return "기타"


def get_completed_unnotified():
    """
    상태가 '완료'이고 아직 알림이 발송되지 않은 태스크 목록을 반환한다.
    (알림 트리거 — notifier.py 연동용)

    반환:
        list[dict]: notified 컬럼이 없거나 "" / "False"인 완료 태스크
    """
    todos = load_todos()
    # TODO: status == "완료" and notified != "True" 인 항목 필터링하여 반환
    return []


def _make_id(subject, sender):
    """subject + sender로 고유 ID 생성 (중복 감지용)."""
    raw = f"{subject}_{sender}"
    return hashlib.md5(raw.encode()).hexdigest()[:12]
