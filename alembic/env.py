from __future__ import annotations

import os
import sys
from logging.config import fileConfig
from typing import Optional

from alembic import context
from sqlalchemy import engine_from_config, pool
import sqlalchemy as sa

# --- Alembic config (alembic.ini) ---
config = context.config

# Логи Alembic (по желанию можно выключить)
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# --- Помощники ---------------------------------------------------------------


def _ensure_project_on_path() -> None:
    """
    Добавляет корень проекта в PYTHONPATH, чтобы работал import src.*
    Ожидаем структуру: /app (workdir) -> /app/src/...
    """
    root = os.path.abspath(os.getcwd())
    if root not in sys.path:
        sys.path.insert(0, root)


def _get_settings_url_fallback() -> Optional[str]:
    """
    Пытаемся импортировать DSN из src.core.config.settings.
    """
    try:
        from src.core.config import settings  # type: ignore

        return settings.SQLALCHEMY_DATABASE_URI
    except Exception:
        return None


def _to_sync_driver(url: str) -> str:
    """
    Для миграций Alembic используем sync-драйвер.
    Преобразуем postgresql+asyncpg:// → postgresql+psycopg://
    """
    if url.startswith("postgresql+asyncpg://"):
        return "postgresql+psycopg://" + url.split("postgresql+asyncpg://", 1)[1]
    return url


# --- Определяем SQLALCHEMY URL ----------------------------------------------

_ensure_project_on_path()

db_url = os.getenv("POSTGRES_DSN") or _get_settings_url_fallback()
if not db_url:
    # Последняя линия обороны — пытаемся прочитать то, что уже задано в alembic.ini
    try:
        db_url = config.get_main_option("sqlalchemy.url")
    except Exception:
        db_url = None

if not db_url:
    raise RuntimeError(
        "Alembic: database URL is not set. "
        "Set POSTGRES_DSN env var or ensure src.core.config.settings is importable."
    )

sync_url = _to_sync_driver(db_url)
config.set_main_option("sqlalchemy.url", sync_url)

# --- Метаданные моделей (для autogenerate) ----------------------------------

try:
    from src.domain.models import Base  # type: ignore

    target_metadata = Base.metadata
except Exception:
    # Если не используете autogenerate, можно оставить None
    target_metadata = None

# --- Конфигурация context.configure -----------------------------------------


VERSION_TABLE_KWARGS = {
    "version_table": "alembic_version",
    "version_table_create": True,
    "version_table_column": sa.Column(
        "version_num", sa.String(length=128), nullable=False
    ),
}


def run_migrations_offline() -> None:
    """
    Запуск миграций в offline-режиме (генерация SQL без подключения к БД).
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,  # если включите autogenerate — будет сравнивать типы
        **VERSION_TABLE_KWARGS,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Запуск миграций в online-режиме (с подключением к БД).
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        future=True,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,  # полезно при autogenerate
            **VERSION_TABLE_KWARGS,
        )

        with context.begin_transaction():
            context.run_migrations()


# --- Точка входа ------------------------------------------------------------

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
