from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from .models import (
    NCLEXCategory,
    NCLEXQuestion,
    NCLEXSubtopic,
    NCLEXTopic,
    NCLEXExam,
    NCLEXExamResult,
    Exam_question_result,
    PracticeQuestionResult,
    PracticeSession,
    QuestionOption,
)


def extract_data(response):
    """Helper to extract payload regardless of response wrapper middleware."""
    if isinstance(response.data, dict) and "data" in response.data:
        return response.data["data"]
    return response.data


class PracticeFinishAPIViewTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="learner@example.com", password="password123"
        )
        self.client.force_authenticate(self.user)
        category = NCLEXCategory.objects.create(title="Care")
        topic = NCLEXTopic.objects.create(category=category, title="Safety")
        subtopic = NCLEXSubtopic.objects.create(
            topic=topic, title="Medication", description="Medication safety"
        )
        self.answered_question = NCLEXQuestion.objects.create(
            category=category,
            topic=topic,
            subtopic=subtopic,
            question="Which action is safest?",
            level="Beginner",
            type="radio",
        )
        self.correct_option = QuestionOption.objects.create(
            question=self.answered_question, text="Verify the order", is_correct=True
        )
        QuestionOption.objects.create(
            question=self.answered_question, text="Guess", is_correct=False
        )
        self.skipped_question = NCLEXQuestion.objects.create(
            category=category,
            topic=topic,
            subtopic=subtopic,
            question="Which action is skipped?",
            level="Beginner",
            type="radio",
        )
        QuestionOption.objects.create(
            question=self.skipped_question, text="Correct", is_correct=True
        )
        self.session = PracticeSession.objects.create(
            user=self.user, practice_mode="test", total_question=2, topic=topic
        )
        self.session.question_set.set([self.answered_question, self.skipped_question])
        PracticeQuestionResult.objects.create(
            session=self.session,
            question=self.answered_question,
            answer=self.correct_option,
            is_correct=True,
            extra_data={"selected_option_id": self.correct_option.id},
        )

    def test_finish_returns_summary_and_review_including_skipped_questions(self):
        response = self.client.post(f"/api/nclex/practice/finish/{self.session.id}/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payload = extract_data(response)
        result = payload["result"]
        self.assertEqual(result["total_correct_answer"], 1)
        self.assertEqual(result["total_incorrect_answer"], 0)
        self.assertEqual(result["total_skipped_answer"], 1)
        self.assertEqual(result["total_percentage"], 50.0)
        self.assertEqual(len(result["results"]), 2)

        skipped = next(
            item for item in result["results"]
            if item["question_id"] == self.skipped_question.id
        )
        self.assertIsNone(skipped["user_answer"])
        self.assertTrue(skipped["is_skipped"])
        self.assertFalse(skipped["is_correct"])
        self.assertIsNotNone(skipped["correct_answer"])

        self.session.refresh_from_db()
        self.assertTrue(self.session.is_finished)
        self.assertIsNotNone(self.session.finished_at)

    def test_finished_session_rejects_new_answers(self):
        self.client.post(f"/api/nclex/practice/finish/{self.session.id}/")

        response = self.client.post(
            "/api/nclex/practice/answer/",
            {
                "session_id": self.session.id,
                "question_id": self.skipped_question.id,
                "answer": [],
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class NCLEXFinalExamAPITests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="nclex_student@example.com", password="password123"
        )
        self.client.force_authenticate(self.user)

        category = NCLEXCategory.objects.create(title="Physiological Adaptation")
        topic = NCLEXTopic.objects.create(category=category, title="Cardiology")
        subtopic = NCLEXSubtopic.objects.create(topic=topic, title="Heart Failure", description="Heart failure care")

        # Question 1: Radio
        self.q1 = NCLEXQuestion.objects.create(
            category=category, topic=topic, subtopic=subtopic,
            question="What is the primary intervention for MAP < 65?",
            level="Foundational", type="radio"
        )
        self.q1_opt1 = QuestionOption.objects.create(question=self.q1, text="Vasopressor/fluid resuscitation", is_correct=True, order=1)
        self.q1_opt2 = QuestionOption.objects.create(question=self.q1, text="Administer oral pain medication", is_correct=False, order=2)

        # Question 2: Multiple
        self.q2 = NCLEXQuestion.objects.create(
            category=category, topic=topic, subtopic=subtopic,
            question="Select all interventions for acute pulmonary edema.",
            level="Foundational", type="multiple"
        )
        self.q2_opt1 = QuestionOption.objects.create(question=self.q2, text="High Fowler position", is_correct=True, order=1)
        self.q2_opt2 = QuestionOption.objects.create(question=self.q2, text="Oxygen therapy", is_correct=True, order=2)
        self.q2_opt3 = QuestionOption.objects.create(question=self.q2, text="Supine position", is_correct=False, order=3)

        # Create the 5 sequential exams
        self.exam1 = NCLEXExam.objects.create(
            order=1, title="NCLEX Practice Exam 1", subtitle="Diagnostic Assessment",
            tag="Start Here", level="Foundational", total_question=2, time_limit_mins=150
        )
        self.exam1.questions.set([self.q1, self.q2])

        self.exam2 = NCLEXExam.objects.create(
            order=2, title="NCLEX Practice Exam 2", subtitle="Targeted Review",
            tag="", level="Progressive", total_question=2, time_limit_mins=150
        )
        self.exam2.questions.set([self.q1, self.q2])

        self.exam3 = NCLEXExam.objects.create(
            order=3, title="NCLEX Practice Exam 3", subtitle="Advanced Application",
            tag="Up next", level="Progressive", total_question=2, time_limit_mins=150
        )
        self.exam3.questions.set([self.q1, self.q2])

        self.exam4 = NCLEXExam.objects.create(
            order=4, title="NCLEX Practice Exam 4", subtitle="Comprehensive",
            tag="", level="Advanced", total_question=2, time_limit_mins=150
        )
        self.exam4.questions.set([self.q1, self.q2])

        self.exam5 = NCLEXExam.objects.create(
            order=5, title="NCLEX Practice Exam 5", subtitle="Pass Prediction",
            tag="Pass Predictor", level="Expert", total_question=2, time_limit_mins=150
        )
        self.exam5.questions.set([self.q1, self.q2])

    def test_exam_list_initial_unlock_state(self):
        """Initially, Exam 1 is available/unlocked and Exams 2..5 are locked."""
        response = self.client.get("/api/nclex/exams/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payload = extract_data(response)
        exams = payload["exams"]
        self.assertEqual(len(exams), 5)

        # Exam 1 is available
        self.assertEqual(exams[0]["order"], 1)
        self.assertEqual(exams[0]["status"], "available")
        self.assertTrue(exams[0]["is_unlocked"])
        self.assertTrue(exams[0]["can_start"])
        self.assertEqual(exams[0]["tag"], "Start Here")

        # Exam 2 is locked
        self.assertEqual(exams[1]["order"], 2)
        self.assertEqual(exams[1]["status"], "locked")
        self.assertFalse(exams[1]["is_unlocked"])
        self.assertFalse(exams[1]["can_start"])

    def test_cannot_start_locked_exam(self):
        """User cannot start Exam 2 while Exam 1 is locked/incomplete."""
        response = self.client.post(f"/api/nclex/exams/{self.exam2.id}/start/")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        msg = str(response.data)
        self.assertIn("locked", msg.lower())

    def test_start_exam_and_answer_submission(self):
        """User starts Exam 1, answers questions in test mode, and finishes."""
        # 1. Start Exam 1
        start_res = self.client.post(f"/api/nclex/exams/{self.exam1.id}/start/")
        self.assertEqual(start_res.status_code, status.HTTP_201_CREATED)
        start_payload = extract_data(start_res)
        session_id = start_payload["session_id"]
        self.assertEqual(len(start_payload["questions"]), 2)

        # 2. Cannot start another exam while Exam 1 is in progress
        start_other = self.client.post(f"/api/nclex/exams/{self.exam2.id}/start/")
        self.assertEqual(start_other.status_code, status.HTTP_400_BAD_REQUEST)

        # 3. Submit answer for Question 1 (radio)
        ans1_res = self.client.post(
            "/api/nclex/exams/answer/",
            {
                "session_id": session_id,
                "question_id": self.q1.id,
                "answer": [self.q1_opt1.id],
            },
            format="json",
        )
        self.assertEqual(ans1_res.status_code, status.HTTP_200_OK)
        ans1_payload = extract_data(ans1_res)
        self.assertEqual(ans1_payload["answered_count"], 1)
        self.assertEqual(ans1_payload["remaining_count"], 1)
        # Test mode should NOT leak is_correct or explanation in the answer submission response
        self.assertNotIn("explanation", ans1_payload)

        # 4. Submit answer for Question 2 (multiple)
        ans2_res = self.client.post(
            "/api/nclex/exams/answer/",
            {
                "session_id": session_id,
                "question_id": self.q2.id,
                "answer": [self.q2_opt1.id, self.q2_opt2.id],
            },
            format="json",
        )
        self.assertEqual(ans2_res.status_code, status.HTTP_200_OK)
        ans2_payload = extract_data(ans2_res)
        self.assertEqual(ans2_payload["answered_count"], 2)
        self.assertTrue(ans2_payload["is_all_answered"])

        # 5. Finish Exam 1
        finish_res = self.client.post(f"/api/nclex/exams/finish/{session_id}/")
        self.assertEqual(finish_res.status_code, status.HTTP_200_OK)
        finish_payload = extract_data(finish_res)
        self.assertEqual(finish_payload["score"], 100.0)
        self.assertTrue(finish_payload["is_completed"])
        self.assertTrue(finish_payload["next_exam_unlocked"])
        self.assertEqual(finish_payload["next_exam_id"], self.exam2.id)

        # 6. Verify Exam 1 results and progressive unlock of Exam 2 in list API
        list_res = self.client.get("/api/nclex/exams/")
        exams = extract_data(list_res)["exams"]

        # Exam 1 is now completed with 100% score
        self.assertEqual(exams[0]["status"], "completed")
        self.assertEqual(exams[0]["score"], 100.0)
        self.assertIsNotNone(exams[0]["completed_date"])
        self.assertTrue(exams[0]["can_review"])
        self.assertFalse(exams[0]["can_start"])

        # Exam 2 is now unlocked/available with "Up next" tag
        self.assertEqual(exams[1]["status"], "available")
        self.assertTrue(exams[1]["is_unlocked"])
        self.assertTrue(exams[1]["can_start"])
        self.assertEqual(exams[1]["tag"], "Up next")

        # Exam 3 remains locked
        self.assertEqual(exams[2]["status"], "locked")
        self.assertFalse(exams[2]["is_unlocked"])

        # 7. Verify single attempt rule: User CANNOT retake or start Exam 1 again
        retake_res = self.client.post(f"/api/nclex/exams/{self.exam1.id}/start/")
        self.assertEqual(retake_res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("already completed", str(retake_res.data).lower())

        # 8. Verify Review endpoint for completed Exam 1
        review_res = self.client.get(f"/api/nclex/exams/review/{session_id}/")
        self.assertEqual(review_res.status_code, status.HTTP_200_OK)
        review_payload = extract_data(review_res)
        self.assertEqual(review_payload["score"], 100.0)
        self.assertEqual(review_payload["readiness_level"], "Strong Readiness")
        self.assertEqual(len(review_payload["result"]["review"]), 2)
        self.assertTrue(review_payload["result"]["review"][0]["is_correct"])
        self.assertTrue(review_payload["result"]["review"][1]["is_correct"])
        # Verify multi-dimensional analytics fields
        self.assertIn("client_needs_performance", review_payload["result"])
        self.assertIn("clinical_judgment_performance", review_payload["result"])
        self.assertIn("body_system_performance", review_payload["result"])
        self.assertIn("strengths", review_payload["result"])
        self.assertIn("areas_to_improve", review_payload["result"])

    def test_flagging_and_pre_submit_summary(self):
        """Test question flagging and pre-submission review summary."""
        start_res = self.client.post(f"/api/nclex/exams/{self.exam1.id}/start/")
        session_id = extract_data(start_res)["session_id"]

        # Flag question 1
        flag_res = self.client.post(
            f"/api/nclex/exams/session/{session_id}/flag/",
            {"session_id": session_id, "question_id": self.q1.id, "is_flagged": True},
            format="json",
        )
        self.assertEqual(flag_res.status_code, status.HTTP_200_OK)
        flag_payload = extract_data(flag_res)
        self.assertEqual(flag_payload["flagged_count"], 1)
        self.assertIn(self.q1.id, flag_payload["flagged_question_ids"])

        # Answer question 1
        self.client.post(
            "/api/nclex/exams/answer/",
            {
                "session_id": session_id,
                "question_id": self.q1.id,
                "answer": [self.q1_opt1.id],
                "current_index": 1,
            },
            format="json",
        )

        # Fetch pre-submission summary
        summary_res = self.client.get(f"/api/nclex/exams/session/{session_id}/summary/")
        self.assertEqual(summary_res.status_code, status.HTTP_200_OK)
        summary_payload = extract_data(summary_res)
        self.assertEqual(summary_payload["total_questions"], 2)
        self.assertEqual(summary_payload["answered_count"], 1)
        self.assertEqual(summary_payload["unanswered_count"], 1)
        self.assertEqual(summary_payload["flagged_count"], 1)

    def test_attempt_assigned_questions_immutability(self):
        """Assigned question IDs must remain fixed and identical across reloads."""
        start_res = self.client.post(f"/api/nclex/exams/{self.exam1.id}/start/")
        session_id = extract_data(start_res)["session_id"]
        questions1 = [q["id"] for q in extract_data(start_res)["questions"]]

        # Fetch session questions
        questions_res = self.client.get(f"/api/nclex/exams/session/{session_id}/questions/")
        questions2 = [q["id"] for q in extract_data(questions_res)["questions"]]

        self.assertEqual(questions1, questions2)

