import unittest
# 같은 디렉토리에 있는 todo_analyzer.py에서 클래스 임포트
from todo_analyzer import TodoAnalyzer

class TestTodoEvaluation(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        """테스트 시작 전 분석기 객체를 한 번만 생성"""
        cls.analyzer = TodoAnalyzer()

    def test_bulk_evaluation(self):
        test_data = [
            # To-Do (정답 = True)
            ("보고서 작성", True),
            ("회의 참석", True),
            ("코드 리뷰 진행", True),
            ("내일까지 기획안 제출", True),
            ("결재 요청 바랍니다", True),
            ("자료 정리 후 공유", True),
            ("서버 점검 작업", True),
            ("메일 확인 후 회신", True),
            ("회의실 예약", True),
            ("피드백 반영하기", True),

            # NOT To-Do (정답 = False)
            ("오늘 날씨가 좋다", False),
            ("점심 뭐 먹지", False),
            ("너무 피곤하다", False),
            ("기분이 좋다", False),
            ("축구 경기 봤다", False),
            ("어제 회의 재미없었다", False),
            ("퇴근하고 싶다", False),
            ("사무실 공기가 안 좋다", False),

            # tricky (애매)
            ("회의 참석 완료", False),
            ("보고서 작성했다", False),
            ("회의 참석하는 게 좋을 듯", False),
            ("자료 정리 필요", True),
            ("확인 부탁드립니다", True),
            ("확인했어요", False),
        ]

        correct = 0
        total = len(test_data)

        print("\n" + "="*50)
        print("신규 TodoAnalyzer 성능 평가 시작")
        print("="*50)

        for text, expected in test_data:
            # 클래스 메서드 호출
            pred = self.analyzer.is_actual_todo(text)

            if pred == expected:
                correct += 1
                result = "✅"
            else:
                result = "❌"

            print(f"{result} | 입력: {text[:15]:<15} | 예측: {str(pred):<5} | 정답: {str(expected):<5}")

        accuracy = correct / total
        print("="*50)
        print(f"최종 정확도: {accuracy:.2f} ({correct}/{total})")
        print("="*50)

        # 최소 기준 (70% 이상)
        self.assertGreaterEqual(accuracy, 0.7)

if __name__ == "__main__":
    unittest.main()