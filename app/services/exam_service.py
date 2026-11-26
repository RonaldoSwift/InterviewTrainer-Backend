from uuid import UUID

from fastapi import HTTPException

from app.repositories.exams import (
    AnswerSaveStatus,
    ExamParameters,
    ExamRecord,
    ExamRepository,
    ReservationStatus,
)
from app.schemas import (
    AnswerRequest,
    AnswerResult,
    CreateExamRequest,
    ExamCreateResponse,
    ExamReadResponse,
    ExamStatus,
    ExamSummaryResponse,
    GeneratedExam,
    QuestionResponse,
    SubmitAnswerResponse,
)
from app.services.question_generator import QuestionGenerator


class ExamService:
    def __init__(
        self,
        question_generator: QuestionGenerator,
        exam_repository: ExamRepository,
    ) -> None:
        self._question_generator = question_generator
        self._exam_repository = exam_repository

    def create_exam(self, request: CreateExamRequest) -> ExamCreateResponse:
        parameters: ExamParameters = (
            request.topic,
            request.difficulty,
            request.language,
        )
        reservation = self._exam_repository.reserve_exam(
            request.exam_id,
            parameters,
        )

        if reservation.status is ReservationStatus.PARAMETER_CONFLICT:
            raise HTTPException(
                status_code=409,
                detail="Este exam_id ya está asociado a otros parámetros.",
            )
        if reservation.status is ReservationStatus.GENERATION_IN_PROGRESS:
            raise HTTPException(
                status_code=409,
                detail="La generación de este examen está en curso.",
            )
        if reservation.status is ReservationStatus.EXISTING:
            if reservation.record is None or reservation.record.exam is None:
                raise RuntimeError("Existing exam reservation has no generated exam")
            return self._to_create_response(reservation.record.exam)

        try:
            exam = self._question_generator.generate_exam(request)
            self._exam_repository.complete_generation(exam)
        except Exception:
            self._exam_repository.cancel_generation(request.exam_id)
            raise

        return self._to_create_response(exam)

    def get_exam(self, exam_id: UUID) -> ExamReadResponse:
        record, exam = self._get_completed_exam(exam_id)
        status = self._status(record, exam)
        answers = [
            record.answers[question.question_id]
            for question in exam.questions
            if question.question_id in record.answers
        ]
        return ExamReadResponse(
            exam_id=exam.exam_id,
            topic=exam.topic,
            difficulty=exam.difficulty,
            language=exam.language,
            status=status,
            questions=self._public_questions(exam),
            answers=answers,
        )

    def submit_answer(
        self,
        exam_id: UUID,
        request: AnswerRequest,
    ) -> SubmitAnswerResponse:
        record, exam = self._get_completed_exam(exam_id)
        question = next(
            (
                question
                for question in exam.questions
                if question.question_id == request.question_id
            ),
            None,
        )
        if question is None:
            raise HTTPException(status_code=404, detail="No se encontró la pregunta.")

        option_ids = {option.option_id for option in question.options}
        if request.option_id not in option_ids:
            raise HTTPException(
                status_code=422,
                detail="La opción seleccionada no pertenece a la pregunta.",
            )

        answer = AnswerResult(
            question_id=question.question_id,
            option_id=request.option_id,
            is_correct=request.option_id == question.correct_option_id,
            correct_option_id=question.correct_option_id,
            explanation=question.explanation,
        )
        saved = self._exam_repository.save_answer(exam_id, answer)
        if saved.status is AnswerSaveStatus.ANSWER_CONFLICT:
            raise HTTPException(
                status_code=409,
                detail="La pregunta ya fue respondida con otra opción.",
            )
        if (
            saved.status is AnswerSaveStatus.EXAM_NOT_FOUND
            or saved.response is None
        ):
            raise HTTPException(status_code=404, detail="No se encontró el examen.")
        return saved.response

    def get_summary(self, exam_id: UUID) -> ExamSummaryResponse:
        record, exam = self._get_completed_exam(exam_id)
        total_questions = len(exam.questions)
        answered_count = len(record.answers)
        correct_count = sum(answer.is_correct for answer in record.answers.values())
        return ExamSummaryResponse(
            exam_id=exam.exam_id,
            status=self._status(record, exam),
            total_questions=total_questions,
            answered_questions=answered_count,
            correct_answers=correct_count,
            percentage=round(correct_count / total_questions * 100, 2),
        )

    def _get_completed_exam(self, exam_id: UUID) -> tuple[ExamRecord, GeneratedExam]:
        record = self._exam_repository.get_exam(exam_id)
        if record is None:
            raise HTTPException(status_code=404, detail="No se encontró el examen.")
        if record.exam is None:
            raise HTTPException(
                status_code=409,
                detail="La generación de este examen está en curso.",
            )
        return record, record.exam

    @staticmethod
    def _status(record: ExamRecord, exam: GeneratedExam) -> ExamStatus:
        if len(record.answers) == len(exam.questions):
            return "completed"
        return "in_progress"

    @staticmethod
    def _public_questions(exam: GeneratedExam) -> list[QuestionResponse]:
        return [
            QuestionResponse(
                question_id=question.question_id,
                text=question.text,
                options=question.options,
            )
            for question in exam.questions
        ]

    @classmethod
    def _to_create_response(cls, exam: GeneratedExam) -> ExamCreateResponse:
        return ExamCreateResponse(
            exam_id=exam.exam_id,
            topic=exam.topic,
            difficulty=exam.difficulty,
            language=exam.language,
            questions=cls._public_questions(exam),
        )
