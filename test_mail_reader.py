# ============================================================
# mail_reader.py 테스트 스크립트
# ============================================================
# 사전 준비
#   1. Gmail 앱 비밀번호 발급
#      Google 계정 → 보안 → "앱 비밀번호" 검색 → 생성 (16자리 복사)
#
#   2. .env 파일 설정
#      프로젝트 루트의 .env 파일에 아래 값 입력
#      TASK_EMAIL=본인Gmail@gmail.com
#      TASK_PASSWORD=앱비밀번호16자리
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

import config
from classifier import score_urgency
from deadline_parser import parse_deadline
from mail_reader import fetch_target_mails


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


if __name__ == "__main__":
    raise SystemExit(main())
