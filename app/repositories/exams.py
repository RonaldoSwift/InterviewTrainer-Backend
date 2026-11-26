from copy import deepcopy
from dataclasses import dataclass, field
from enum import Enum
from threading import Lock
from typing import Protocol
from uuid import UUID

from app.schemas import (
    AnswerResult,
    Difficulty,
    GeneratedExam,
    Language,
    SubmitAnswerResponse,
    Topic,
)


ExamParameters = tuple[Topic, Difficulty, Language]


class ReservationStatus(Enum):
    RESERVED = "reserved"
    EXISTING = "existing"
    PARAMETER_CONFLICT = "parameter_conflict"
    GENERATION_IN_PROGRESS = "generation_in_progress"


class AnswerSaveStatus(Enum):
    SAVED = "saved"
    SAME_ANSWER = "same_answer"
    ANSWER_CONFLICT = "answer_conflict"
    EXAM_NOT_FOUND = "exam_not_found"


@dataclass
class ExamRecord:
    parameters: ExamParameters
    exam: GeneratedExam | None = None
    answers: dict[str, AnswerResult] = field(default_factory=dict)
    answer_responses: dict[str, SubmitAnswerResponse] = field(default_factory=dict)


@dataclass(frozen=True)
class ExamReservation:
    status: ReservationStatus
    record: ExamRecord | None = None


@dataclass(frozen=True)
class AnswerSaveResult:
    status: AnswerSaveStatus
    response: SubmitAnswerResponse | None = None


class ExamRepository(Protocol):
    def reserve_exam(
        self,
        exam_id: UUID,
        parameters: ExamParameters,
    ) -> ExamReservation:
        ...

    def complete_generation(self, exam: GeneratedExam) -> None:
        ...

    def cancel_generation(self, exam_id: UUID) -> None:
        ...

    def get_exam(self, exam_id: UUID) -> ExamRecord | None:
        ...

    def save_answer(
        self,
        exam_id: UUID,
        answer: AnswerResult,
    ) -> AnswerSaveResult:
        ...


class InMemoryExamRepository:
    def __init__(self) -> None:
        self._exams: dict[UUID, ExamRecord] = {}
        self._lock = Lock()

    def reserve_exam(
        self,
        exam_id: UUID,
        parameters: ExamParameters,
    ) -> ExamReservation:
        with self._lock:
            record = self._exams.get(exam_id)
            if record is None:
                self._exams[exam_id] = ExamRecord(parameters=parameters)
                return ExamReservation(ReservationStatus.RESERVED)

            if record.parameters != parameters:
                return ExamReservation(ReservationStatus.PARAMETER_CONFLICT)
            if record.exam is None:
                return ExamReservation(ReservationStatus.GENERATION_IN_PROGRESS)
            return ExamReservation(
                ReservationStatus.EXISTING,
                deepcopy(record),
            )

    def complete_generation(self, exam: GeneratedExam) -> None:
        with self._lock:
            record = self._exams.get(exam.exam_id)
            if record is None or record.exam is not None:
                raise RuntimeError("Exam generation reservation is not available")
            record.exam = exam

    def cancel_generation(self, exam_id: UUID) -> None:
        with self._lock:
            record = self._exams.get(exam_id)
            if record is not None and record.exam is None:
                del self._exams[exam_id]

    def get_exam(self, exam_id: UUID) -> ExamRecord | None:
        with self._lock:
            record = self._exams.get(exam_id)
            return deepcopy(record) if record is not None else None

    def save_answer(
        self,
        exam_id: UUID,
        answer: AnswerResult,
    ) -> AnswerSaveResult:
        with self._lock:
            record = self._exams.get(exam_id)
            if record is None or record.exam is None:
                return AnswerSaveResult(AnswerSaveStatus.EXAM_NOT_FOUND)

            existing = record.answers.get(answer.question_id)
            if existing is not None:
                if existing.option_id == answer.option_id:
                    return AnswerSaveResult(
                        AnswerSaveStatus.SAME_ANSWER,
                        deepcopy(record.answer_responses[answer.question_id]),
                    )
                return AnswerSaveResult(AnswerSaveStatus.ANSWER_CONFLICT)

            record.answers[answer.question_id] = answer
            answered_count = len(record.answers)
            total_questions = len(record.exam.questions)
            response = SubmitAnswerResponse(
                **answer.model_dump(),
                status=(
                    "completed"
                    if answered_count == total_questions
                    else "in_progress"
                ),
                answered_questions=answered_count,
                total_questions=total_questions,
                progress_percentage=round(
                    answered_count / total_questions * 100,
                    2,
                ),
            )
            record.answer_responses[answer.question_id] = response
            return AnswerSaveResult(AnswerSaveStatus.SAVED, deepcopy(response))
