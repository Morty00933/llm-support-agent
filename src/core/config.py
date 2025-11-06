from __future__ import annotations
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    # App
    ENV: str = Field(default="dev")
    LOG_LEVEL: str = Field(default="INFO")
    APP_NAME: str = "llm-support-agent"
    APP_VERSION: str = "0.2.0"

    # HTTP
    CORS_ORIGINS: str = Field(default="*")  # comma-separated
    TRUSTED_HOSTS: str = Field(default="*")  # comma-separated

    # DB
    DB_HOST: str = "db"
    DB_PORT: int = 5432
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "postgres"
    DB_NAME: str = "app"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20

    # Redis / Celery
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    CELERY_BROKER_URL: str | None = None
    CELERY_RESULT_BACKEND: str | None = None

    # JWT
    JWT_SECRET: str = "change-me"
    JWT_ALG: str = "HS256"
    JWT_ISS: str = "llm-agent"
    JWT_AUD: str = "llm-ui"
    JWT_EXPIRE_MIN: int = 60 * 24

    # Ollama
    OLLAMA_HOST: str = "http://ollama:11434"
    OLLAMA_MODEL_CHAT: str = "llama3.1:8b"
    OLLAMA_MODEL_EMBED: str = "nomic-embed-text"

    # Observability
    PROMETHEUS_ENABLED: bool = True
    SENTRY_DSN: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        return (
            f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    @property
    def REDIS_DSN(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"

    @property
    def BROKER_URL(self) -> str:
        return self.CELERY_BROKER_URL or self.REDIS_DSN

    @property
    def RESULT_BACKEND(self) -> str:
        return self.CELERY_RESULT_BACKEND or self.REDIS_DSN


settings = Settings()
