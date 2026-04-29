# ============================================================
# mail_reader.py 테스트 스크립트
# ============================================================
# 사전 준비
#   1. Gmail 앱 비밀번호 발급
#      Google 계정 → 보안 → "앱 비밀번호" 검색 → 생성 (16자리 복사)
#
#   2. .env 파일 설정
#      .env.example 파일을 복사하여 .env 파일 생성 후
#      TASK_EMAIL과 TASK_PASSWORD에 본인의 Gmail 계정 정보 입력
#
#   3. 테스트 메일 발송 (본인에게)
#      제목: [업무요청] 브랜드 리뉴얼 건 (~05/02)
#      본문 예시:
#        - 과업명: 로고 시안 확정
#        - 마감기한: 2026-05-02 (토) 16:00
#        - 업무유형: 프로젝트
#        - 우선순위: 상
#
#   4. 실행
#      python test_mail_reader.py
#
# 정상 출력 예시
#   수신된 업무 메일: 1건
#   제목:     [업무요청] 브랜드 리뉴얼 건 (~05/02)
#   발신자:   your@gmail.com
#   긴급도:   긴급(80점) | 마감: 2026-05-02
# ============================================================

import shutil
from email.message import EmailMessage
from pathlib import Path

import config
from classifier import score_urgency
from deadline_parser import parse_deadline
from mail_reader import _download_pdfs, fetch_target_mails


def main():
    print(f"EMAIL 설정 여부: {'O' if config.EMAIL else 'X'}")
    print(f"PASSWORD 설정 여부: {'O' if config.PASSWORD else 'X'}")

    if not config.EMAIL or not config.PASSWORD:
        print("\n[ERROR] .env 파일에 TASK_EMAIL, TASK_PASSWORD를 먼저 설정하세요.")
        return 1

    mails = fetch_target_mails()
    print(f"\n조회된 대상 메일 수: {len(mails)}")

    if not mails:
        print("조건에 맞는 메일이 없습니다.")
        return 0

    for mail in mails:
        # 제목에도 마감일 힌트가 들어갈 수 있어 제목과 본문을 함께 본다.
        full_text = "\n".join(
            part for part in [mail["subject"], mail["body"]] if part
        )
        deadline = parse_deadline(full_text, mail["received_at"])
        score, level, deadline = score_urgency(
            full_text,
            mail["received_at"],
            deadline=deadline,
        )

        print("-" * 40)
        print(f"제목:          {mail['subject']}")
        print(f"발신자:        {mail['sender']}")
        print(f"수신 시각:     {mail['received_at']}")
        print(f"본문 미리보기: {mail['body'][:80]}")
        print(f"PDF 파일:      {mail['pdf_paths']}")
        print(f"긴급도:        {level} ({score}) | 마감일: {deadline}")

    return 0


def test_pdf_filename_collision():
    """동일한 PDF 첨부파일명이 들어와도 덮어쓰지 않고 저장되는지 확인한다."""
    temp_dir = Path("downloads") / "_mail_reader_collision_test"
    original_save_dir = config.SAVE_DIR

    try:
        shutil.rmtree(temp_dir, ignore_errors=True)
        temp_dir.mkdir(parents=True, exist_ok=True)
        config.SAVE_DIR = str(temp_dir)

        paths = []
        for content in (b"first", b"second", b"third"):
            msg = EmailMessage()
            msg.add_attachment(
                content,
                maintype="application",
                subtype="pdf",
                filename="report.pdf",
            )
            paths.extend(_download_pdfs(msg))

        names = [Path(path).name for path in paths]
        expected = ["report.pdf", "report (2).pdf", "report (3).pdf"]

        print("\n[Collision Test]")
        print(f"saved:    {names}")
        print(f"expected: {expected}")

        return 0 if names == expected else 1
    finally:
        config.SAVE_DIR = original_save_dir
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
