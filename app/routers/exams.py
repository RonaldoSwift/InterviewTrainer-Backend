from uuid import UUID

from fastapi import APIRouter, Depends

from app.repositories.exams import ExamRepository, InMemoryExamRepository
from app.schemas import (
    AnswerRequest,
    CreateExamRequest,
    ExamCreateResponse,
    ExamReadResponse,
    ExamSummaryResponse,
    HealthResponse,
    SubmitAnswerResponse,
)
from app.services.exam_service import ExamService
from app.services.question_generator import (
    QuestionGenerator,
    TemplateQuestionGenerator,
)


router = APIRouter()

_question_generator = TemplateQuestionGenerator()
_exam_repository = InMemoryExamRepository()


def get_question_generator() -> QuestionGenerator:
    return _question_generator


def get_exam_repository() -> ExamRepository:
    return _exam_repository


def get_exam_service(
    question_generator: QuestionGenerator = Depends(get_question_generator),
    exam_repository: ExamRepository = Depends(get_exam_repository),
) -> ExamService:
    return ExamService(question_generator, exam_repository)


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    return HealthResponse()


@router.post("/exams", response_model=ExamCreateResponse)
def create_exam(
    request: CreateExamRequest,
    exam_service: ExamService = Depends(get_exam_service),
) -> ExamCreateResponse:
    return exam_service.create_exam(request)


@router.get("/exams/{exam_id}", response_model=ExamReadResponse)
def get_exam(
    exam_id: UUID,
    exam_service: ExamService = Depends(get_exam_service),
) -> ExamReadResponse:
    return exam_service.get_exam(exam_id)


@router.post(
    "/exams/{exam_id}/answers",
    response_model=SubmitAnswerResponse,
)
def submit_answer(
    exam_id: UUID,
    request: AnswerRequest,
    exam_service: ExamService = Depends(get_exam_service),
) -> SubmitAnswerResponse:
    return exam_service.submit_answer(exam_id, request)


@router.get(
    "/exams/{exam_id}/summary",
    response_model=ExamSummaryResponse,
)
def get_exam_summary(
    exam_id: UUID,
    exam_service: ExamService = Depends(get_exam_service),
) -> ExamSummaryResponse:
    return exam_service.get_summary(exam_id)
