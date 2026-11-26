from typing import Literal
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)


Topic = Literal["Swift", "Concurrency", "SwiftUI", "Arquitectura", "Testing"]
Difficulty = Literal["basic", "intermediate"]
Language = Literal["es", "en"]
ExamStatus = Literal["in_progress", "completed"]


class APIModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CreateExamRequest(APIModel):
    exam_id: UUID
    topic: Topic
    difficulty: Difficulty
    language: Language


class AnswerRequest(APIModel):
    question_id: str = Field(min_length=1)
    option_id: str = Field(min_length=1)

    @field_validator("question_id", "option_id")
    @classmethod
    def values_must_not_be_whitespace(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("value must not be blank")
        return value


class OptionResponse(APIModel):
    option_id: str = Field(min_length=1)
    text: str = Field(min_length=1)

    @field_validator("option_id", "text")
    @classmethod
    def values_must_not_be_whitespace(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("value must not be blank")
        return value


class QuestionResponse(APIModel):
    question_id: str = Field(min_length=1)
    text: str = Field(min_length=1)
    options: list[OptionResponse] = Field(min_length=4, max_length=4)

    @field_validator("question_id", "text")
    @classmethod
    def values_must_not_be_whitespace(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("value must not be blank")
        return value


class GeneratedQuestion(QuestionResponse):
    correct_option_id: str
    explanation: str = Field(min_length=1)

    @model_validator(mode="after")
    def correct_option_is_available(self) -> "GeneratedQuestion":
        option_ids = [option.option_id for option in self.options]
        if self.correct_option_id not in option_ids:
            raise ValueError("correct_option_id must match one of the question options")
        if len(set(option_ids)) != len(option_ids):
            raise ValueError("question option IDs must be unique")
        option_texts = [option.text.strip().casefold() for option in self.options]
        if len(set(option_texts)) != len(option_texts):
            raise ValueError("question option texts must be unique")
        return self


class GeneratedExam(APIModel):
    exam_id: UUID
    topic: Topic
    difficulty: Difficulty
    language: Language
    questions: list[GeneratedQuestion] = Field(min_length=5, max_length=5)

    @model_validator(mode="after")
    def question_ids_are_unique(self) -> "GeneratedExam":
        question_ids = [question.question_id for question in self.questions]
        if len(set(question_ids)) != len(question_ids):
            raise ValueError("question IDs must be unique")
        question_texts = [question.text.strip().casefold() for question in self.questions]
        if len(set(question_texts)) != len(question_texts):
            raise ValueError("question texts must be unique")
        return self


class ExamCreateResponse(APIModel):
    exam_id: UUID
    topic: Topic
    difficulty: Difficulty
    language: Language
    questions: list[QuestionResponse] = Field(min_length=5, max_length=5)


class AnswerResult(APIModel):
    question_id: str
    option_id: str
    is_correct: bool
    correct_option_id: str
    explanation: str = Field(min_length=1)


class SubmitAnswerResponse(AnswerResult):
    status: ExamStatus
    answered_questions: int = Field(ge=0)
    total_questions: int = Field(ge=1)
    progress_percentage: float = Field(ge=0, le=100)


class ExamReadResponse(APIModel):
    exam_id: UUID
    topic: Topic
    difficulty: Difficulty
    language: Language
    status: ExamStatus
    questions: list[QuestionResponse] = Field(min_length=5, max_length=5)
    answers: list[AnswerResult]


class ExamSummaryResponse(APIModel):
    exam_id: UUID
    status: ExamStatus
    total_questions: int = Field(ge=1)
    answered_questions: int = Field(ge=0)
    correct_answers: int = Field(ge=0)
    percentage: float = Field(ge=0, le=100)


class HealthResponse(APIModel):
    status: Literal["ok"] = "ok"
