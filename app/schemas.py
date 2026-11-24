from pydantic import BaseModel, Field


class RootResponse(BaseModel):
    message: str = Field(examples=["InterviewTrainer AI API is running"])


class GenerateExamRequest(BaseModel):
    topic: str = Field(min_length=1, examples=["Python"])
    difficulty: str = Field(min_length=1, examples=["intermediate"])
    language: str = Field(min_length=1, examples=["es"])


class AnswerOption(BaseModel):
    id: str = Field(min_length=1, examples=["a"])
    text: str = Field(min_length=1, examples=["Una colección ordenada y modificable"])


class QuestionResponse(BaseModel):
    id: str = Field(min_length=1, examples=["q1"])
    statement: str = Field(min_length=1, examples=["¿Qué es una lista en Python?"])
    options: list[AnswerOption] = Field(
        min_length=1,
        examples=[
            [
                {"id": "a", "text": "Una colección ordenada y modificable"},
                {"id": "b", "text": "Un tipo de función"},
            ]
        ],
    )


class GenerateExamResponse(BaseModel):
    exam_id: str = Field(min_length=1, examples=["exam-123"])
    topic: str = Field(min_length=1, examples=["Python"])
    difficulty: str = Field(min_length=1, examples=["intermediate"])
    language: str = Field(min_length=1, examples=["es"])
    questions: list[QuestionResponse] = Field(
        min_length=1,
        examples=[
            [
                {
                    "id": "q1",
                    "statement": "¿Qué es una lista en Python?",
                    "options": [
                        {"id": "a", "text": "Una colección ordenada y modificable"},
                        {"id": "b", "text": "Un tipo de función"},
                    ],
                }
            ]
        ],
    )


class SubmittedAnswer(BaseModel):
    question_id: str = Field(min_length=1, examples=["q1"])
    selected_option_id: str = Field(min_length=1, examples=["a"])


class SubmitExamRequest(BaseModel):
    answers: list[SubmittedAnswer] = Field(
        min_length=1,
        examples=[[{"question_id": "q1", "selected_option_id": "a"}]],
    )


class QuestionResult(BaseModel):
    question_id: str = Field(min_length=1, examples=["q1"])
    selected_option_id: str = Field(min_length=1, examples=["a"])
    correct_option_id: str = Field(min_length=1, examples=["a"])
    is_correct: bool = Field(examples=[True])
    explanation: str = Field(
        min_length=1,
        examples=["Una lista almacena elementos en orden y permite modificarlos."],
    )


class ExamResultResponse(BaseModel):
    exam_id: str = Field(min_length=1, examples=["exam-123"])
    score: float = Field(ge=0, examples=[80.0])
    total_questions: int = Field(ge=0, examples=[5])
    correct_answers: int = Field(ge=0, examples=[4])
    incorrect_answers: int = Field(ge=0, examples=[1])
    results: list[QuestionResult] = Field(
        examples=[
            [
                {
                    "question_id": "q1",
                    "selected_option_id": "a",
                    "correct_option_id": "a",
                    "is_correct": True,
                    "explanation": "Una lista almacena elementos en orden y permite modificarlos.",
                }
            ]
        ],
    )
