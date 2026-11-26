from typing import Protocol

from app.schemas import (
    CreateExamRequest,
    GeneratedExam,
    GeneratedQuestion,
    OptionResponse,
)


class QuestionGenerator(Protocol):
    def generate_exam(self, request: CreateExamRequest) -> GeneratedExam:
        ...


class TemplateQuestionGenerator:
    def generate_exam(self, request: CreateExamRequest) -> GeneratedExam:
        if request.language == "es":
            templates = [
                (
                    f"Al resolver un problema de {request.topic}, ¿qué conviene hacer primero?",
                    "Aclarar los requisitos y descomponer el problema",
                    "Empezar sin entender el objetivo",
                    "Ignorar las restricciones",
                    "Asumir los requisitos sin confirmarlos",
                    "Aclarar los requisitos ayuda a resolver el problema correcto.",
                ),
                (
                    f"¿Cómo demostrarías que una solución de {request.topic} funciona?",
                    "Validarla con pruebas representativas",
                    "Asumir que funciona sin comprobarla",
                    "Evitar revisar los casos límite",
                    "Probar únicamente el caso más sencillo",
                    "Las pruebas representativas ayudan a verificar el comportamiento esperado.",
                ),
                (
                    f"En una entrevista sobre {request.topic}, ¿cómo explicarías una decisión?",
                    "Describir el razonamiento y sus ventajas y desventajas",
                    "Dar solo la respuesta sin explicar el razonamiento",
                    "Evitar mencionar alternativas",
                    "Afirmar que la decisión no tiene desventajas",
                    "Explicar el razonamiento y las alternativas permite evaluar la decisión.",
                ),
                (
                    f"¿Qué harías si encuentras un caso límite al trabajar con {request.topic}?",
                    "Analizarlo, ajustar la solución y probarlo",
                    "Ignorarlo porque es poco común",
                    "Eliminar las pruebas relacionadas",
                    "Devolver siempre un resultado fijo",
                    "Analizar y probar los casos límite hace la solución más confiable.",
                ),
                (
                    f"Si hay varias soluciones para un problema de {request.topic}, ¿cómo eliges?",
                    "Comparar sus ventajas según los requisitos",
                    "Elegir la primera sin analizarla",
                    "Preferir la más compleja",
                    "Ignorar las restricciones del problema",
                    "Comparar alternativas con respecto a los requisitos justifica la elección.",
                ),
            ]
        else:
            templates = [
                (
                    f"When solving a {request.topic} problem, what should you do first?",
                    "Clarify the requirements and break down the problem",
                    "Start without understanding the goal",
                    "Ignore the constraints",
                    "Assume the requirements without confirming them",
                    "Clarifying requirements helps solve the right problem.",
                ),
                (
                    f"How would you show that a {request.topic} solution works?",
                    "Validate it with representative tests",
                    "Assume it works without checking",
                    "Avoid checking edge cases",
                    "Test only the simplest case",
                    "Representative tests help verify expected behavior.",
                ),
                (
                    f"In an interview about {request.topic}, how should you explain a decision?",
                    "Describe the reasoning and its trade-offs",
                    "Give only the answer without explaining it",
                    "Avoid mentioning alternatives",
                    "Claim the decision has no drawbacks",
                    "Explaining reasoning and alternatives makes the decision clear.",
                ),
                (
                    f"What would you do after finding an edge case in {request.topic}?",
                    "Analyze it, adjust the solution, and test it",
                    "Ignore it because it is uncommon",
                    "Remove the related tests",
                    "Always return a fixed result",
                    "Analyzing and testing edge cases makes a solution more reliable.",
                ),
                (
                    f"If several solutions fit a {request.topic} problem, how would you choose?",
                    "Compare their trade-offs against the requirements",
                    "Choose the first one without analysis",
                    "Prefer the most complex one",
                    "Ignore the problem constraints",
                    "Comparing alternatives against requirements justifies the choice.",
                ),
            ]

        questions = [
            GeneratedQuestion(
                question_id=f"q{index}",
                text=text,
                options=[
                    OptionResponse(option_id=option_id, text=option_text)
                    for option_id, option_text in zip(
                        ("a", "b", "c", "d"),
                        option_texts,
                    )
                ],
                correct_option_id="a",
                explanation=explanation,
            )
            for index, (text, *option_texts, explanation) in enumerate(
                templates,
                start=1,
            )
        ]

        return GeneratedExam(
            exam_id=request.exam_id,
            topic=request.topic,
            difficulty=request.difficulty,
            language=request.language,
            questions=questions,
        )
