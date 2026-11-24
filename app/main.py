from uuid import uuid4

from fastapi import FastAPI, HTTPException

from app.schemas import (
    AnswerOption,
    ExamResultResponse,
    GenerateExamRequest,
    GenerateExamResponse,
    QuestionResponse,
    QuestionResult,
    RootResponse,
    SubmitExamRequest,
)


app = FastAPI(
    title="InterviewTrainer AI",
    description="Backend API for InterviewTrainer AI.",
    version="0.1.0",
)

_exam_answer_keys: dict[str, dict[str, tuple[set[str], str, str]]] = {}
_exam_results: dict[str, ExamResultResponse] = {}


@app.get("/", response_model=RootResponse)
def read_root() -> RootResponse:
    return RootResponse(message="InterviewTrainer AI API is running")


@app.post("/api/v1/exams/generate", response_model=GenerateExamResponse)
def generate_exam(request: GenerateExamRequest) -> GenerateExamResponse:
    language = request.language.strip().lower().split("-")[0]
    if language in {"es", "español", "spanish"}:
        templates = [
            (
                f"Al resolver un problema de {request.topic}, ¿qué conviene hacer primero?",
                [
                    ("a", "Aclarar los requisitos y descomponer el problema"),
                    ("b", "Empezar sin entender el objetivo"),
                    ("c", "Ignorar las restricciones"),
                    ("d", "Asumir los requisitos sin confirmarlos"),
                ],
                "a",
                "Aclarar los requisitos ayuda a resolver el problema correcto.",
            ),
            (
                f"¿Cómo demostrarías que una solución de {request.topic} funciona?",
                [
                    ("a", "Validarla con pruebas representativas"),
                    ("b", "Asumir que funciona sin comprobarla"),
                    ("c", "Evitar revisar los casos límite"),
                    ("d", "Probar únicamente el caso más sencillo"),
                ],
                "a",
                "Las pruebas representativas ayudan a verificar el comportamiento esperado.",
            ),
            (
                f"En una entrevista sobre {request.topic}, ¿cómo explicarías una decisión?",
                [
                    ("a", "Describir el razonamiento y sus ventajas y desventajas"),
                    ("b", "Dar solo la respuesta sin explicar el razonamiento"),
                    ("c", "Evitar mencionar alternativas"),
                    ("d", "Afirmar que la decisión no tiene desventajas"),
                ],
                "a",
                "Explicar el razonamiento y las alternativas permite evaluar la decisión.",
            ),
            (
                f"¿Qué harías si encuentras un caso límite al trabajar con {request.topic}?",
                [
                    ("a", "Analizarlo, ajustar la solución y probarlo"),
                    ("b", "Ignorarlo porque es poco común"),
                    ("c", "Eliminar las pruebas relacionadas"),
                    ("d", "Devolver siempre un resultado fijo"),
                ],
                "a",
                "Analizar y probar los casos límite hace la solución más confiable.",
            ),
            (
                f"Si hay varias soluciones para un problema de {request.topic}, ¿cómo eliges?",
                [
                    ("a", "Comparar sus ventajas según los requisitos"),
                    ("b", "Elegir la primera sin analizarla"),
                    ("c", "Preferir la más compleja"),
                    ("d", "Ignorar las restricciones del problema"),
                ],
                "a",
                "Comparar alternativas con respecto a los requisitos justifica la elección.",
            ),
        ]
    elif language in {"en", "english", "inglés"}:
        templates = [
            (
                f"When solving a {request.topic} problem, what should you do first?",
                [
                    ("a", "Clarify the requirements and break down the problem"),
                    ("b", "Start without understanding the goal"),
                    ("c", "Ignore the constraints"),
                    ("d", "Assume the requirements without confirming them"),
                ],
                "a",
                "Clarifying requirements helps solve the right problem.",
            ),
            (
                f"How would you show that a {request.topic} solution works?",
                [
                    ("a", "Validate it with representative tests"),
                    ("b", "Assume it works without checking"),
                    ("c", "Avoid checking edge cases"),
                    ("d", "Test only the simplest case"),
                ],
                "a",
                "Representative tests help verify expected behavior.",
            ),
            (
                f"In an interview about {request.topic}, how should you explain a decision?",
                [
                    ("a", "Describe the reasoning and its trade-offs"),
                    ("b", "Give only the answer without explaining it"),
                    ("c", "Avoid mentioning alternatives"),
                    ("d", "Claim the decision has no drawbacks"),
                ],
                "a",
                "Explaining reasoning and alternatives makes the decision clear.",
            ),
            (
                f"What would you do after finding an edge case in {request.topic}?",
                [
                    ("a", "Analyze it, adjust the solution, and test it"),
                    ("b", "Ignore it because it is uncommon"),
                    ("c", "Remove the related tests"),
                    ("d", "Always return a fixed result"),
                ],
                "a",
                "Analyzing and testing edge cases makes a solution more reliable.",
            ),
            (
                f"If several solutions fit a {request.topic} problem, how would you choose?",
                [
                    ("a", "Compare their trade-offs against the requirements"),
                    ("b", "Choose the first one without analysis"),
                    ("c", "Prefer the most complex one"),
                    ("d", "Ignore the problem constraints"),
                ],
                "a",
                "Comparing alternatives against requirements justifies the choice.",
            ),
        ]
    else:
        raise HTTPException(
            status_code=422,
            detail="El idioma debe ser español (es) o inglés (en).",
        )

    exam_id = str(uuid4())
    questions = [
        QuestionResponse(
            id=f"q{index}",
            statement=statement,
            options=[AnswerOption(id=option_id, text=text) for option_id, text in options],
        )
        for index, (statement, options, _, _) in enumerate(templates, start=1)
    ]
    _exam_answer_keys[exam_id] = {
        question.id: (
            {option.id for option in question.options},
            correct_option_id,
            explanation,
        )
        for question, (_, _, correct_option_id, explanation) in zip(questions, templates)
    }

    return GenerateExamResponse(
        exam_id=exam_id,
        topic=request.topic,
        difficulty=request.difficulty,
        language=request.language,
        questions=questions,
    )


@app.post(
    "/api/v1/exams/{exam_id}/submit",
    response_model=ExamResultResponse,
)
def submit_exam(exam_id: str, request: SubmitExamRequest) -> ExamResultResponse:
    answer_key = _exam_answer_keys.get(exam_id)
    if answer_key is None:
        raise HTTPException(status_code=404, detail="No se encontró el examen.")

    answers_by_question = {answer.question_id: answer for answer in request.answers}
    if len(answers_by_question) != len(request.answers):
        raise HTTPException(status_code=422, detail="Hay respuestas duplicadas.")
    if set(answers_by_question) != set(answer_key):
        raise HTTPException(
            status_code=422,
            detail="Debes enviar una respuesta para cada pregunta del examen.",
        )

    results = []
    for question_id, answer in answers_by_question.items():
        valid_option_ids, correct_option_id, explanation = answer_key[question_id]
        if answer.selected_option_id not in valid_option_ids:
            raise HTTPException(
                status_code=422,
                detail=f"La alternativa seleccionada no existe para {question_id}.",
            )
        results.append(
            QuestionResult(
                question_id=question_id,
                selected_option_id=answer.selected_option_id,
                correct_option_id=correct_option_id,
                is_correct=answer.selected_option_id == correct_option_id,
                explanation=explanation,
            )
        )

    correct_answers = sum(result.is_correct for result in results)
    total_questions = len(results)
    exam_result = ExamResultResponse(
        exam_id=exam_id,
        score=round(correct_answers / total_questions * 100, 2),
        total_questions=total_questions,
        correct_answers=correct_answers,
        incorrect_answers=total_questions - correct_answers,
        results=results,
    )
    _exam_results[exam_id] = exam_result
    return exam_result


@app.get(
    "/api/v1/exams/{exam_id}/result",
    response_model=ExamResultResponse,
)
def get_exam_result(exam_id: str) -> ExamResultResponse:
    if exam_id not in _exam_answer_keys:
        raise HTTPException(status_code=404, detail="No se encontró el examen.")

    exam_result = _exam_results.get(exam_id)
    if exam_result is None:
        raise HTTPException(
            status_code=409,
            detail="El examen todavía no ha sido calificado.",
        )
    return exam_result
