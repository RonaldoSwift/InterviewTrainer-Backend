# InterviewTrainer AI Backend

Backend API for InterviewTrainer AI, built with Python, FastAPI, Pydantic and Poetry.

## Requirements

- Python 3.11 or higher
- Poetry

## Installation

```bash
poetry install
```

## Run the server

```bash
poetry run uvicorn app.main:app --reload
```

The API will be available at <http://127.0.0.1:8000>.

## Check the server

Open <http://127.0.0.1:8000/> or run:

```bash
curl http://127.0.0.1:8000/
```

Expected response:

```json
{"message":"InterviewTrainer AI API is running"}
```

## Run locally

```bash
poetry install
poetry run uvicorn app.main:app --reload
```

Swagger UI is available at <http://127.0.0.1:8000/docs>.
