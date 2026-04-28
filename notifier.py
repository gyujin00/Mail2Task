"""
담당: 규진 차
역할: 작업 완료 알림 자동화 - 완료 상태 태스크 발신자에게 SMTP 메일 발송
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import config


def send_completion_notice(to_email, task_subject):
    """
    업무 완료 알림 메일을 발신자에게 발송한다.

    인자:
        to_email     (str): 수신자 이메일 (원래 업무 발신자)
        task_subject (str): 완료된 업무의 메일 제목

    반환:
        bool: 발송 성공 여부
    """
    msg = MIMEMultipart()
    msg["From"]    = config.EMAIL
    msg["To"]      = to_email
    msg["Subject"] = f"[완료] {task_subject}"
    msg.attach(MIMEText(_build_body(task_subject), "plain", "utf-8"))

    try:
        with smtplib.SMTP(config.SMTP_SERVER, config.SMTP_PORT) as server:
            server.starttls()
            server.login(config.EMAIL, config.PASSWORD)
            server.sendmail(config.EMAIL, to_email, msg.as_string())
        return True
    except smtplib.SMTPException as e:
        print(f"[알림 발송 실패] {to_email} | {e}")
        return False


def _build_body(task_subject):
    return (
        f"안녕하세요,\n\n"
        f"요청하신 업무가 완료되었습니다.\n\n"
        f"  업무: {task_subject}\n\n"
        f"감사합니다.\n"
        f"Task-Harvester 자동 알림"
    )
