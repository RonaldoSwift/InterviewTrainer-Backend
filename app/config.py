import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    app_title: str = "InterviewTrainer AI"
    app_description: str = "Backend API for InterviewTrainer AI."
    app_version: str = "0.1.0"

    @classmethod
    def from_environment(cls) -> "Settings":
        return cls(
            app_title=os.getenv("APP_TITLE", "InterviewTrainer AI"),
            app_description=os.getenv(
                "APP_DESCRIPTION",
                "Backend API for InterviewTrainer AI.",
            ),
            app_version=os.getenv("APP_VERSION", "0.1.0"),
        )


settings = Settings.from_environment()
