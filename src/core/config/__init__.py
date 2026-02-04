from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseConfig(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")
    
    host: str = Field(default="postgres", alias="DB_HOST")
    port: int = Field(default=5432, alias="DB_PORT")
    user: str = Field(default="postgres", alias="DB_USER")
    password: str = Field(default="postgres", alias="DB_PASSWORD")
    name: str = Field(default="llm_agent", alias="DB_NAME")
    pool_size: int = Field(default=10, alias="DB_POOL_SIZE")
    max_overflow: int = Field(default=20, alias="DB_MAX_OVERFLOW")
    pool_timeout: int = Field(default=30, alias="DB_POOL_TIMEOUT")
    pool_recycle: int = Field(default=1800, alias="DB_POOL_RECYCLE")
    echo: bool = Field(default=False, alias="DB_ECHO")
    
    @property
    def async_url(self) -> str:
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"
    
    @property
    def sync_url(self) -> str:
        return f"postgresql+psycopg://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"


class RedisConfig(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")
    
    host: str = Field(default="redis", alias="REDIS_HOST")
    port: int = Field(default=6379, alias="REDIS_PORT")
    password: str = Field(default="", alias="REDIS_PASSWORD")
    db: int = Field(default=0, alias="REDIS_DB")
    ssl: bool = Field(default=False, alias="REDIS_SSL")
    
    @property
    def dsn(self) -> str:
        scheme = "rediss" if self.ssl else "redis"
        if self.password:
            return f"{scheme}://:{self.password}@{self.host}:{self.port}/{self.db}"
        return f"{scheme}://{self.host}:{self.port}/{self.db}"
    
    @property
    def broker_url(self) -> str:
        return self.dsn
    
    @property
    def result_backend(self) -> str:
        return self.dsn


class JWTConfig(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    secret: str = Field(alias="JWT_SECRET")
    algorithm: str = Field(default="HS256", alias="JWT_ALG")
    expire_minutes: int = Field(default=60, alias="JWT_EXPIRE_MIN")
    refresh_expire_days: int = Field(default=7, alias="JWT_REFRESH_EXPIRE_DAYS")
    audience: str = Field(default="llm-support-agent", alias="JWT_AUDIENCE")
    issuer: str = Field(default="llm-support-agent", alias="JWT_ISSUER")

    @property
    def access_token_expire_minutes(self) -> int:
        return self.expire_minutes

    @field_validator("secret")
    @classmethod
    def validate_secret(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError("JWT_SECRET must be at least 32 characters long")

        weak_secrets = [
            "your-super-secret-key-change-in-production",
            "your-super-secret-jwt-key-change-in-production",
            "CHANGE_ME",
            "change-me",
            "secret",
            "password",
        ]

        if any(weak in v.lower() for weak in weak_secrets):
            raise ValueError(
                "JWT_SECRET contains weak or default value. "
                "Generate a strong secret with: openssl rand -hex 32"
            )

        return v


class OllamaConfig(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")
    
    base_url: str = Field(default="http://ollama:11434", alias="OLLAMA_BASE_URL")
    model_chat: str = Field(default="qwen2.5:3b", alias="OLLAMA_MODEL_CHAT")
    model_embed: str = Field(default="nomic-embed-text", alias="OLLAMA_MODEL_EMBED")
    timeout: int = Field(default=120, alias="OLLAMA_TIMEOUT")
    temperature: float = Field(default=0.2, alias="OLLAMA_TEMPERATURE")
    embedding_dim: int = Field(default=768, alias="EMBEDDING_DIM")


class CeleryConfig(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    broker_url: str = Field(default="redis://redis:6379/0", alias="CELERY_BROKER_URL")
    result_backend: str = Field(default="redis://redis:6379/0", alias="CELERY_RESULT_BACKEND")
    task_timeout_seconds: int = Field(default=300, alias="CELERY_TASK_TIMEOUT_SECONDS")
    task_always_eager: bool = Field(default=False, alias="CELERY_TASK_ALWAYS_EAGER")
    task_ignore_result: bool = Field(default=False, alias="CELERY_TASK_IGNORE_RESULT")
    task_retry_backoff_min: int = Field(default=60, alias="CELERY_TASK_RETRY_BACKOFF_MIN")
    task_max_retries: int = Field(default=3, alias="CELERY_TASK_MAX_RETRIES")
    task_retry_backoff_max: int = Field(default=600, alias="CELERY_TASK_RETRY_BACKOFF_MAX")


class FeatureFlagsConfig(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")
    
    dark_mode: bool = Field(default=True, alias="FEATURE_DARK_MODE")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    env: str = Field(default="dev", alias="ENV")
    app_name: str = Field(default="llm-support-agent", alias="APP_NAME")
    app_version: str = Field(default="0.2.0", alias="APP_VERSION")
    debug: bool = Field(default=False, alias="DEBUG")
    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8000, alias="PORT")
    workers: int = Field(default=2, alias="WORKERS")
    
    cors_origins: str = Field(
        default="http://localhost:3000,http://127.0.0.1:3000",
        alias="CORS_ORIGINS"
    )
    
    # Убраны дублирующие поля — теперь только через nested конфиги
    jwt_secret: str = Field(alias="JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALG")
    jwt_expire_minutes: int = Field(default=60, alias="JWT_EXPIRE_MIN")
    
    jira_enabled: bool = Field(default=False, alias="JIRA_ENABLED")
    jira_base_url: str = Field(default="", alias="JIRA_BASE_URL")
    jira_email: str = Field(default="", alias="JIRA_EMAIL")
    jira_api_token: str = Field(default="", alias="JIRA_API_TOKEN")
    jira_project_key: str = Field(default="", alias="JIRA_PROJECT_KEY")
    jira_issue_type: str = Field(default="Task", alias="JIRA_ISSUE_TYPE")
    
    zendesk_enabled: bool = Field(default=False, alias="ZENDESK_ENABLED")
    zendesk_subdomain: str = Field(default="", alias="ZENDESK_SUBDOMAIN")
    zendesk_email: str = Field(default="", alias="ZENDESK_EMAIL")
    zendesk_api_token: str = Field(default="", alias="ZENDESK_API_TOKEN")
    
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_format: str = Field(default="json", alias="LOG_FORMAT")
    sentry_dsn: str | None = Field(default=None, alias="SENTRY_DSN")
    prometheus_enabled: bool = Field(default=True, alias="PROMETHEUS_ENABLED")

    # Demo mode
    demo_mode_enabled: bool = Field(default=False, alias="DEMO_MODE_ENABLED")
    demo_seed_on_startup: bool = Field(default=False, alias="DEMO_SEED_ON_STARTUP")
    
    _database: DatabaseConfig | None = None
    _redis: RedisConfig | None = None
    _jwt: JWTConfig | None = None
    _ollama: OllamaConfig | None = None
    _celery: CeleryConfig | None = None
    _features: FeatureFlagsConfig | None = None
    
    @field_validator("jwt_secret")
    @classmethod
    def validate_jwt_secret(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError("JWT_SECRET must be at least 32 characters long")
        
        weak_secrets = [
            "your-super-secret-key-change-in-production",
            "your-super-secret-jwt-key-change-in-production",
            "CHANGE_ME",
            "change-me",
            "secret",
            "password",
        ]
        
        if any(weak in v.lower() for weak in weak_secrets):
            raise ValueError(
                "JWT_SECRET contains weak or default value. "
                "Generate a strong secret with: openssl rand -hex 32"
            )
        
        return v
    
    @field_validator("cors_origins")
    @classmethod
    def validate_cors_origins(cls, v: str) -> str:
        origins = [o.strip() for o in v.split(",") if o.strip()]
        
        for origin in origins:
            if origin == "*":
                continue
            
            if not origin.startswith(("http://", "https://")):
                raise ValueError(f"Invalid CORS origin format: {origin}")
        
        return v
    
    @property
    def cors_origins_list(self) -> List[str]:
        origins = [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]
        
        if self.env == "prod" and "*" in origins:
            raise ValueError("Wildcard CORS origins not allowed in production")
        
        return origins
    
    @property
    def access_token_expire_minutes(self) -> int:
        return self.jwt_expire_minutes
    
    @property
    def database(self) -> DatabaseConfig:
        if self._database is None:
            self._database = DatabaseConfig()
        return self._database
    
    @property
    def redis(self) -> RedisConfig:
        if self._redis is None:
            self._redis = RedisConfig()
        return self._redis
    
    @property
    def jwt(self) -> JWTConfig:
        if self._jwt is None:
            self._jwt = JWTConfig()
        return self._jwt
    
    @property
    def ollama(self) -> OllamaConfig:
        if self._ollama is None:
            self._ollama = OllamaConfig()
        return self._ollama
    
    @property
    def celery(self) -> CeleryConfig:
        if self._celery is None:
            self._celery = CeleryConfig()
        return self._celery
    
    @property
    def features(self) -> FeatureFlagsConfig:
        if self._features is None:
            self._features = FeatureFlagsConfig()
        return self._features


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()


__all__ = [
    "Settings",
    "DatabaseConfig",
    "RedisConfig",
    "JWTConfig",
    "OllamaConfig",
    "CeleryConfig",
    "FeatureFlagsConfig",
    "settings",
    "get_settings",
]