from fastapi import FastAPI

from app.schemas import RootResponse


app = FastAPI(
    title="InterviewTrainer AI",
    description="Backend API for InterviewTrainer AI.",
    version="0.1.0",
)


@app.get("/", response_model=RootResponse)
def read_root() -> RootResponse:
    return RootResponse(message="InterviewTrainer AI API is running")
