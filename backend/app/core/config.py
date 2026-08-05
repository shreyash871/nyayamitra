import os

from dotenv import load_dotenv

# Load the project-root .env (two levels up from this file)
load_dotenv(
    dotenv_path=os.path.join(os.path.dirname(__file__), "..", "..", "..", ".env")
)


class Settings:
    """One place that reads every environment variable.
    The rest of the app imports `settings` from here."""

    DATABASE_URL: str = os.environ["DATABASE_URL"]

    INDIAN_KANOON_API_TOKEN: str = os.getenv("INDIAN_KANOON_API_TOKEN", "")
    INDIAN_KANOON_BASE_URL: str = os.getenv(
        "INDIAN_KANOON_BASE_URL", "https://api.indiankanoon.org"
    )
    INGESTION_MODE: str = os.getenv("INGESTION_MODE", "mock")

    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    CELERY_RESULT_BACKEND: str = os.getenv(
        "CELERY_RESULT_BACKEND", "redis://localhost:6379/1"
    )


settings = Settings()
