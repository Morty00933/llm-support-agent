FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Кладём метаданные и исходники
COPY pyproject.toml README.md /app/
COPY src /app/src
COPY alembic.ini /app/
COPY alembic /app/alembic

# Установка зависимостей и проекта (никакого apt)
RUN python -m pip install --upgrade pip \
 && python -m pip install "setuptools>=68" wheel \
 && python -m pip install -e .

EXPOSE 8000

CMD ["bash","-lc","uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --workers 2"]
