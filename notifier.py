"""
담당: 규진 차
역할: 작업 완료 알림 자동화 - 완료 상태 태스크 발신자에게 SMTP 메일 발송
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import config


def send_completion_notice(todo):
    """
    업무 완료 알림 메일을 발신자에게 발송한다.

    인자:
        todo (dict): 완료된 업무 정보
            - sender (str): 발신자 이메일
            - subject (str): 메일 제목
            - deadline (str): 마감일 (YYYY-MM-DD)
            - urgency_level (str): 긴급도 등급 (긴급/보통/여유)
            - urgency_score (int): 긴급도 점수 (0~100)
            - received_at (str): 수신 일시 (YYYY-MM-DD HH:MM)

    반환:
        bool: 발송 성공 여부
    """
    to_email = todo["sender"]
    task_subject = todo["subject"]

    msg = MIMEMultipart()
    msg["From"]    = config.EMAIL
    msg["To"]      = to_email
    msg["Subject"] = f"[완료] {task_subject}"
    msg.attach(MIMEText(_build_body(todo), "plain", "utf-8"))

    try:
        with smtplib.SMTP(config.SMTP_SERVER, config.SMTP_PORT) as server:
            server.starttls()
            server.login(config.EMAIL, config.PASSWORD)
            server.sendmail(config.EMAIL, to_email, msg.as_string())
        return True
    except smtplib.SMTPException as e:
        print(f"[알림 발송 실패] {to_email} | {e}")
        return False


def _build_body(todo):
    """완료 알림 메일 본문 생성 (업무 상세 정보 포함)"""
    body = (
        f"안녕하세요,\n\n"
        f"요청하신 업무가 완료되었습니다.\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"  업무 제목: {todo['subject']}\n"
    )

    if todo.get("deadline"):
        body += f"  마감 기한: {todo['deadline']}\n"

    if todo.get("urgency_level"):
        urgency_score = todo.get("urgency_score", 0)
        body += f"  긴급도: {todo['urgency_level']} ({urgency_score}점)\n"

    if todo.get("received_at"):
        body += f"  요청 일시: {todo['received_at']}\n"

    body += (
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"감사합니다.\n"
        f"Task-Harvester 자동 알림"
    )

    return body
