import unittest
from todo_manager import is_actual_todo


class TestTodoEvaluation(unittest.TestCase):

    def test_bulk_evaluation(self):
        test_data = [
            # -----------------------------
            # To-Do (정답 = True)
            # -----------------------------
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

            # -----------------------------
            # NOT To-Do (정답 = False)
            # -----------------------------
            ("오늘 날씨가 좋다", False),
            ("점심 뭐 먹지", False),
            ("너무 피곤하다", False),
            ("기분이 좋다", False),
            ("축구 경기 봤다", False),
            ("어제 회의 재미없었다", False),
            ("퇴근하고 싶다", False),
            ("사무실 공기가 안 좋다", False),

            # -----------------------------
            # tricky (애매)
            # -----------------------------
            ("회의 참석 완료", False),
            ("보고서 작성했다", False),
            ("회의 참석하는 게 좋을 듯", False),
            ("자료 정리 필요", True),
            ("확인 부탁드립니다", True),
            ("확인했어요", False),
        ]

        correct = 0
        total = len(test_data)

        print("\n--- Bulk Evaluation ---")

        for text, expected in test_data:
            pred = is_actual_todo(text)

            if pred == expected:
                correct += 1
                result = "✅"
            else:
                result = "❌"

            print(f"{result} | 입력: {text} | 예측: {pred} | 정답: {expected}")

        accuracy = correct / total

        print(f"\n정확도: {accuracy:.2f} ({correct}/{total})")

        # 최소 기준 (70% 이상)
        self.assertGreaterEqual(accuracy, 0.7)
        
        
if __name__ == "__main__": 
    unittest.main()