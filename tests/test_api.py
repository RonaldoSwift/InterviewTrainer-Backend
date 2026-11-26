import unittest
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from app.main import app
from app.repositories.exams import (
    InMemoryExamRepository,
    ReservationStatus,
)
from app.routers.exams import get_exam_repository, get_question_generator
from app.schemas import CreateExamRequest, GeneratedExam
from app.services.question_generator import TemplateQuestionGenerator


class CountingQuestionGenerator(TemplateQuestionGenerator):
    def __init__(self) -> None:
        self.calls = 0

    def generate_exam(self, request: CreateExamRequest) -> GeneratedExam:
        self.calls += 1
        return super().generate_exam(request)


class FailingQuestionGenerator:
    def generate_exam(self, request: CreateExamRequest) -> GeneratedExam:
        raise RuntimeError("test-only internal error")


class ExamAPITests(unittest.TestCase):
    def setUp(self) -> None:
        self.repository = InMemoryExamRepository()
        self.generator = CountingQuestionGenerator()
        app.dependency_overrides[get_exam_repository] = lambda: self.repository
        app.dependency_overrides[get_question_generator] = lambda: self.generator
        self.client = TestClient(app)

    def tearDown(self) -> None:
        self.client.close()
        app.dependency_overrides.clear()

    def create_payload(self, exam_id: str | None = None) -> dict[str, str]:
        return {
            "exam_id": exam_id or str(uuid4()),
            "topic": "Swift",
            "difficulty": "basic",
            "language": "es",
        }

    def create_exam(self, exam_id: str | None = None) -> dict:
        response = self.client.post("/exams", json=self.create_payload(exam_id))
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def test_exactly_five_api_endpoints_are_in_openapi(self) -> None:
        expected = {
            ("GET", "/health"),
            ("POST", "/exams"),
            ("GET", "/exams/{exam_id}"),
            ("POST", "/exams/{exam_id}/answers"),
            ("GET", "/exams/{exam_id}/summary"),
        }
        openapi = self.client.get("/openapi.json").json()
        actual = {
            (method.upper(), path)
            for path, operations in openapi["paths"].items()
            for method in operations
        }

        self.assertEqual(actual, expected)
        self.assertEqual(self.client.get("/health").json(), {"status": "ok"})
        self.assertEqual(self.client.get("/docs").status_code, 200)
        self.assertEqual(self.generator.calls, 0)
        self.assertEqual(self.client.get("/").status_code, 404)

    def test_create_and_get_exam_do_not_reveal_unanswered_solutions(self) -> None:
        created = self.create_exam()
        exam_id = created["exam_id"]

        self.assertEqual(UUID(exam_id).version, 4)
        self.assertEqual(len(created["questions"]), 5)
        self.assertEqual(len(created["questions"][0]["options"]), 4)
        self.assertEqual(
            set(created["questions"][0]),
            {"question_id", "text", "options"},
        )

        response = self.client.get(f"/exams/{exam_id}")
        self.assertEqual(response.status_code, 200)
        exam = response.json()
        self.assertEqual(exam["status"], "in_progress")
        self.assertEqual(exam["answers"], [])
        self.assertTrue(
            all(
                "correct_option_id" not in question
                and "explanation" not in question
                for question in exam["questions"]
            )
        )

    def test_recreating_exam_with_same_parameters_is_idempotent(self) -> None:
        payload = self.create_payload()
        first = self.client.post("/exams", json=payload)
        second = self.client.post("/exams", json=payload)

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(second.json(), first.json())
        self.assertEqual(self.generator.calls, 1)

    def test_reusing_exam_id_with_different_parameters_conflicts(self) -> None:
        payload = self.create_payload()
        self.assertEqual(self.client.post("/exams", json=payload).status_code, 200)

        payload["topic"] = "SwiftUI"
        response = self.client.post("/exams", json=payload)

        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["code"], "conflict")
        self.assertEqual(self.generator.calls, 1)

    def test_creation_conflicts_while_generation_is_in_progress(self) -> None:
        payload = self.create_payload()
        exam_id = UUID(payload["exam_id"])
        reservation = self.repository.reserve_exam(
            exam_id,
            ("Swift", "basic", "es"),
        )
        self.assertEqual(reservation.status, ReservationStatus.RESERVED)

        response = self.client.post("/exams", json=payload)

        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["code"], "conflict")
        self.assertEqual(self.generator.calls, 0)

    def test_answer_is_returned_and_repeating_it_is_idempotent(self) -> None:
        exam = self.create_exam()
        exam_id = exam["exam_id"]
        payload = {
            "question_id": exam["questions"][0]["question_id"],
            "option_id": "a",
        }

        first = self.client.post(f"/exams/{exam_id}/answers", json=payload)
        next_question = exam["questions"][1]
        self.client.post(
            f"/exams/{exam_id}/answers",
            json={
                "question_id": next_question["question_id"],
                "option_id": "b",
            },
        )
        second = self.client.post(f"/exams/{exam_id}/answers", json=payload)

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(second.json(), first.json())
        self.assertEqual(first.json()["is_correct"], True)
        self.assertEqual(first.json()["correct_option_id"], "a")
        self.assertTrue(first.json()["explanation"])
        self.assertEqual(first.json()["answered_questions"], 1)
        self.assertEqual(first.json()["progress_percentage"], 20)

        exam_after_answer = self.client.get(f"/exams/{exam_id}").json()
        self.assertEqual(len(exam_after_answer["answers"]), 2)
        self.assertEqual(
            exam_after_answer["answers"][0]["question_id"],
            payload["question_id"],
        )

    def test_changing_a_submitted_answer_conflicts(self) -> None:
        exam = self.create_exam()
        exam_id = exam["exam_id"]
        question_id = exam["questions"][0]["question_id"]
        self.client.post(
            f"/exams/{exam_id}/answers",
            json={"question_id": question_id, "option_id": "a"},
        )

        response = self.client.post(
            f"/exams/{exam_id}/answers",
            json={"question_id": question_id, "option_id": "b"},
        )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["code"], "conflict")

    def test_summary_is_in_progress_then_completed(self) -> None:
        exam = self.create_exam()
        exam_id = exam["exam_id"]

        self.client.post(
            f"/exams/{exam_id}/answers",
            json={
                "question_id": exam["questions"][0]["question_id"],
                "option_id": "a",
            },
        )
        incomplete = self.client.get(f"/exams/{exam_id}/summary")
        self.assertEqual(incomplete.status_code, 200)
        self.assertEqual(incomplete.json()["status"], "in_progress")
        self.assertEqual(incomplete.json()["answered_questions"], 1)
        self.assertEqual(incomplete.json()["correct_answers"], 1)
        self.assertEqual(incomplete.json()["percentage"], 20)

        for question in exam["questions"][1:]:
            response = self.client.post(
                f"/exams/{exam_id}/answers",
                json={
                    "question_id": question["question_id"],
                    "option_id": "b",
                },
            )
            self.assertEqual(response.status_code, 200)

        complete = self.client.get(f"/exams/{exam_id}/summary")
        self.assertEqual(complete.status_code, 200)
        self.assertEqual(complete.json()["status"], "completed")
        self.assertEqual(complete.json()["answered_questions"], 5)
        self.assertEqual(complete.json()["correct_answers"], 1)
        self.assertEqual(complete.json()["percentage"], 20)

    def test_unknown_exam_and_question_return_uniform_404_errors(self) -> None:
        unknown_exam_id = str(uuid4())

        for response in (
            self.client.get(f"/exams/{unknown_exam_id}"),
            self.client.get(f"/exams/{unknown_exam_id}/summary"),
            self.client.post(
                f"/exams/{unknown_exam_id}/answers",
                json={"question_id": "q1", "option_id": "a"},
            ),
        ):
            self.assertEqual(response.status_code, 404)
            self.assertEqual(set(response.json()), {"code", "message"})
            self.assertEqual(response.json()["code"], "not_found")

        exam = self.create_exam()
        response = self.client.post(
            f"/exams/{exam['exam_id']}/answers",
            json={"question_id": "missing", "option_id": "a"},
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["code"], "not_found")

    def test_invalid_option_and_request_use_uniform_422_errors(self) -> None:
        exam = self.create_exam()
        response = self.client.post(
            f"/exams/{exam['exam_id']}/answers",
            json={
                "question_id": exam["questions"][0]["question_id"],
                "option_id": "missing",
            },
        )
        self.assertEqual(response.status_code, 422)
        self.assertEqual(set(response.json()), {"code", "message"})
        self.assertEqual(response.json()["code"], "invalid_input")

        invalid_request = self.client.post(
            "/exams",
            json={
                **self.create_payload(),
                "topic": "Python",
            },
        )
        self.assertEqual(invalid_request.status_code, 422)
        self.assertEqual(invalid_request.json()["code"], "invalid_input")

    def test_internal_generation_errors_are_not_exposed_and_reservation_is_released(
        self,
    ) -> None:
        payload = self.create_payload()
        app.dependency_overrides[get_question_generator] = (
            lambda: FailingQuestionGenerator()
        )

        with self.assertLogs("app.main", level="ERROR"):
            with TestClient(app, raise_server_exceptions=False) as client:
                response = client.post("/exams", json=payload)

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json()["code"], "internal_error")
        self.assertNotIn("test-only internal error", response.text)

        app.dependency_overrides[get_question_generator] = lambda: self.generator
        retry = self.client.post("/exams", json=payload)
        self.assertEqual(retry.status_code, 200)
