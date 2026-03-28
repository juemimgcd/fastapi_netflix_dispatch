from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", ".venv/.env"),
        env_ignore_empty=True,
        extra="ignore",
    )

    ASYNC_DATABASE_URL: str = Field(
        validation_alias=AliasChoices("ASYNC_DATABASE_URL", "DATABASE_URL")
    )
    REDIS_URL: str = "redis://localhost:6379/0"
    # jwt settings
    JWT_SECRET: str
    JWT_ALG: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    cors_origins: str = ""

    # mail settings
    MAIL_HOST: str = "localhost"
    MAIL_PORT: int = 25
    MAIL_USER: str = ""
    MAIL_PASS: str = ""
    MAIL_FROM: str = "noreply@example.com"
    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"


settings = Settings()
