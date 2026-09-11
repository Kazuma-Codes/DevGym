import json
from django.test import TestCase, Client
from api.models import CandidateProfile, InterviewSession, InterviewTurn


class ApiEndpointTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_health_check(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_create_profile(self):
        payload = {
            "name": "Jane Doe",
            "resume_text": "Software Engineer with 3 years experience in Python and React.",
            "job_description": "Looking for Python backend engineer.",
        }
        response = self.client.post(
            "/api/profile",
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("profile_id", data)
        self.assertTrue(CandidateProfile.objects.filter(id=data["profile_id"]).exists())

    def test_start_interview_subject_mode(self):
        payload = {
            "mode": "SUBJECT",
            "subject": "OOP",
            "difficulty": "easy",
            "max_questions": 3,
        }
        response = self.client.post(
            "/api/start",
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("session_id", data)
        self.assertEqual(data["mode"], "SUBJECT")
        self.assertEqual(data["question_number"], 1)
        self.assertTrue(len(data["question"]) > 0)

    def test_submit_text_answer_and_finish_session(self):
        start_payload = {
            "mode": "SUBJECT",
            "subject": "OOP",
            "difficulty": "easy",
            "max_questions": 2,
        }
        start_res = self.client.post(
            "/api/start",
            data=json.dumps(start_payload),
            content_type="application/json",
        )
        session_id = start_res.json()["session_id"]

        # Submit answer to question 1
        answer_payload = {
            "text": "The four main pillars of OOP are encapsulation, abstraction, inheritance, and polymorphism.",
        }
        ans_res = self.client.post(
            f"/api/answer/{session_id}",
            data=answer_payload,
        )
        self.assertEqual(ans_res.status_code, 200)
        ans_data = ans_res.json()
        self.assertIn("score", ans_data)
        self.assertIn("feedback", ans_data)
        self.assertGreaterEqual(ans_data["score"], 1)

        # Check turn recorded in DB
        turns = InterviewTurn.objects.filter(session_id=session_id)
        self.assertEqual(turns.count(), 1)

        # Finish session
        finish_res = self.client.post(f"/api/session/{session_id}/finish")
        self.assertEqual(finish_res.status_code, 200)
        summary_data = finish_res.json()
        self.assertEqual(summary_data["session_id"], session_id)
        self.assertEqual(summary_data["status"], "completed")

    def test_tts_status(self):
        response = self.client.get("/api/tts/status")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("engine", data)
        self.assertIn("configured", data)

    def test_root_index(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
