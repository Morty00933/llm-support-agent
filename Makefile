run: ; docker compose up --build
prod: ; docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
fmt: ; ruff check --fix . && black .
test: ; pytest -q
migrate: ; alembic upgrade head
revision: ; alembic revision -m "$m"
