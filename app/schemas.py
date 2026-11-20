from pydantic import BaseModel, Field


class RootResponse(BaseModel):
    message: str = Field(examples=["InterviewTrainer AI API is running"])
