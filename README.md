# InterviewTrainer AI Backend

Backend API for InterviewTrainer AI, built with Python, FastAPI, Pydantic and Poetry. Question generation currently uses the existing local templates; Gemini is not integrated yet.

## Requirements

- Python 3.11 or higher
- Poetry

## Installation and execution

```bash
poetry install
poetry run uvicorn app.main:app --reload
```

The API is available at <http://127.0.0.1:8000>. Swagger UI is available at <http://127.0.0.1:8000/docs>.

Optional application metadata can be set with `APP_TITLE`, `APP_DESCRIPTION` and `APP_VERSION`.

## API

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/health` | Check service health without generating questions |
| POST | `/exams` | Create an exam using a client-generated UUID |
| GET | `/exams/{exam_id}` | Get public questions and submitted answers |
| POST | `/exams/{exam_id}/answers` | Submit one answer and receive its result |
| GET | `/exams/{exam_id}/summary` | Get current progress and score |

`POST /exams` request:

```json
{
  "exam_id": "d290f1ee-6c54-4b01-90e6-d701748f0851",
  "topic": "Swift",
  "difficulty": "basic",
  "language": "es"
}
```

Allowed topics are `Swift`, `Concurrency`, `SwiftUI`, `Arquitectura` and `Testing`. Allowed difficulties are `basic` and `intermediate`; allowed languages are `es` and `en`.

The response contains the same ID and parameters plus five questions. Each question contains `question_id`, `text` and four `options` with `option_id` and `text`. Solutions and explanations are not included in this response or for unanswered questions in `GET /exams/{exam_id}`.

`POST /exams/{exam_id}/answers` request:

```json
{
  "question_id": "q1",
  "option_id": "a"
}
```

The response includes `is_correct`, `correct_option_id`, `explanation`, `status`, `answered_questions`, `total_questions` and `progress_percentage`. Repeating the same answer returns the same result; changing an answer already recorded returns `409 Conflict`.

`GET /exams/{exam_id}/summary` returns `status`, `total_questions`, `answered_questions`, `correct_answers` and `percentage`. The status is `in_progress` until every question has an answer, then becomes `completed`.

Errors use this format:

```json
{
  "code": "not_found",
  "message": "No se encontró el examen."
}
```

Invalid input or options return `422`, missing exams/questions return `404`, and conflicting exam IDs or changed answers return `409`.

Exam data is stored in memory and is lost when the process restarts. Idempotency guarantees apply only within a single running process.

## Tests

```bash
poetry run python -m unittest discover -s tests -v
```
