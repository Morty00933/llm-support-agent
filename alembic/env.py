"""Alembic environment configuration - MINIMAL & ROBUST VERSION (no dependency on app config)."""

from logging.config import fileConfig
from sqlalchemy import pool, create_engine
from alembic import context
import os

# Импортируем ТОЛЬКО метаданные моделей — это единственное, что нужно Alembic
from src.domain.models import Base

# Логирование из alembic.ini (если есть)
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Метаданные для миграций
target_metadata = Base.metadata


def get_database_url() -> str:
    """
    Формируем синхронный URL для Alembic напрямую из переменных окружения.
    Эти переменные гарантированно есть благодаря docker-compose.yml
    """
    user = os.getenv("DB_USER", "postgres")
    password = os.getenv("DB_PASSWORD", "postgres")
    host = os.getenv("DB_HOST", "postgres")
    port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME", "llm_agent")

    # Alembic требует СИНХРОННЫЙ драйвер: psycopg, а не asyncpg
    return f"postgresql+psycopg://{user}:{password}@{host}:{port}/{db_name}"


def run_migrations_offline() -> None:
    """Offline mode."""
    url = get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Online mode — подключаемся к БД."""
    engine = create_engine(
        get_database_url(),
        poolclass=pool.NullPool,
    )

    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


# Запуск
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()