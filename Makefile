.PHONY: help dev dev-full dev-gpu prod prod-monitoring monitoring stop restart restart-backend restart-frontend \
	logs logs-backend logs-frontend logs-ollama logs-celery \
	build build-backend build-frontend build-no-cache \
	migrate migrate-down migrate-create db-shell db-reset \
	ollama-pull ollama-list ollama-rm \
	test test-cov test-unit test-e2e lint lint-fix typecheck format \
	shell shell-backend shell-frontend redis-cli \
	seed-demo clean clean-volumes clean-all status health stats backup-db restore-db

.DEFAULT_GOAL := help

help: ## Show this help message
	@echo LLM Support Agent - Development Commands
	@echo ""
	@echo Available commands:
	@echo   dev              - Start development environment
	@echo   dev-full         - Start with Celery worker
	@echo   prod             - Start production environment
	@echo   monitoring       - Start Prometheus + Grafana
	@echo   stop             - Stop all services
	@echo   restart          - Restart all services
	@echo   logs             - View all logs
	@echo   logs-backend     - View backend logs
	@echo   logs-frontend    - View frontend logs
	@echo   build            - Build all containers
	@echo   migrate          - Run database migrations
	@echo   test             - Run all tests
	@echo   test-cov         - Run tests with coverage
	@echo   lint             - Run linter
	@echo   shell            - Open backend shell
	@echo   db-shell         - Open PostgreSQL shell
	@echo   redis-cli        - Open Redis CLI
	@echo   health           - Check service health
	@echo   clean            - Remove containers and networks
	@echo   ollama-pull      - Download AI models

# ============================================================
# DEVELOPMENT
# ============================================================

dev: ## Start development environment
	@echo Starting development environment...
	@docker-compose up -d --build
	@echo ""
	@echo Services started!
	@echo   Frontend:  http://localhost:3000
	@echo   Backend:   http://localhost:8000
	@echo   API Docs:  http://localhost:8000/docs
	@echo   Ollama:    http://localhost:11434
	@echo ""
	@echo Tip: Run 'make ollama-pull' to download AI models

dev-full: ## Start with Celery worker
	@echo Starting full stack...
	docker-compose --profile full up -d --build

dev-gpu: ## Start with GPU support
	@echo Starting with GPU acceleration...
	docker-compose -f docker-compose.yml -f docker-compose.gpu.yml up -d --build

monitoring: ## Start monitoring stack
	@echo Starting monitoring stack...
	docker-compose -f docker-compose.monitoring.yml up -d
	@echo ""
	@echo   Prometheus: http://localhost:9090
	@echo   Grafana:    http://localhost:3001 (admin/admin)

# ============================================================
# PRODUCTION
# ============================================================

prod: ## Start production environment
	@echo Starting production environment...
	docker-compose -f docker-compose.prod.yml up -d --build

prod-monitoring: ## Start production with monitoring
	@echo Starting production with monitoring...
	docker-compose -f docker-compose.prod.yml -f docker-compose.monitoring.yml up -d --build

# ============================================================
# CONTROL
# ============================================================

stop: ## Stop all services
	@echo Stopping services...
	docker-compose down
	-docker-compose -f docker-compose.monitoring.yml down

restart: ## Restart all services
	@echo Restarting services...
	docker-compose restart

restart-backend: ## Restart backend only
	docker-compose restart backend

restart-frontend: ## Restart frontend only
	docker-compose restart frontend

# ============================================================
# LOGS
# ============================================================

logs: ## View logs from all services
	docker-compose logs -f

logs-backend: ## View backend logs
	docker-compose logs -f backend

logs-frontend: ## View frontend logs
	docker-compose logs -f frontend

logs-ollama: ## View Ollama logs
	docker-compose logs -f ollama

logs-celery: ## View Celery worker logs
	docker-compose logs -f celery

# ============================================================
# BUILD
# ============================================================

build: ## Build all containers
	@echo Building containers...
	docker-compose build

build-backend: ## Build backend only
	docker-compose build backend

build-frontend: ## Build frontend only
	docker-compose build frontend

build-no-cache: ## Rebuild without cache
	@echo Building without cache...
	docker-compose build --no-cache

# ============================================================
# DATABASE
# ============================================================

migrate: ## Run database migrations
	@echo Running migrations...
	docker-compose exec backend alembic upgrade head

migrate-down: ## Rollback last migration
	@echo Rolling back migration...
	docker-compose exec backend alembic downgrade -1

migrate-create: ## Create new migration (use: make migrate-create NAME=description)
	docker-compose exec backend alembic revision --autogenerate -m "$(NAME)"

db-shell: ## Open PostgreSQL shell
	docker-compose exec postgres psql -U postgres -d llm_agent

db-reset: ## Reset database (WARNING: destroys all data)
	@echo WARNING: This will destroy all database data!
	@echo Press Ctrl+C to cancel, or Enter to continue...
	@read -r dummy
	docker-compose down -v
	docker-compose up -d postgres redis
	@echo Waiting for database to start...
	@sleep 5
	docker-compose up -d backend
	@echo Database reset complete

# ============================================================
# OLLAMA
# ============================================================

ollama-pull: ## Download AI models
	@echo Downloading AI models...
	@echo   Chat model: qwen2.5:3b
	docker-compose exec ollama ollama pull qwen2.5:3b
	@echo   Embedding model: nomic-embed-text
	docker-compose exec ollama ollama pull nomic-embed-text
	@echo Models downloaded!

ollama-list: ## List available models
	docker-compose exec ollama ollama list

ollama-rm: ## Remove a model (use: make ollama-rm MODEL=name)
	docker-compose exec ollama ollama rm $(MODEL)

# ============================================================
# TESTING
# ============================================================

test: ## Run all tests
	@echo Running tests...
	docker-compose exec backend pytest tests/ -v

test-cov: ## Run tests with coverage
	@echo Running tests with coverage...
	docker-compose exec backend pytest tests/ -v --cov=src --cov-report=term --cov-report=html

test-unit: ## Run unit tests only
	docker-compose exec backend pytest tests/test_unit*.py -v

test-e2e: ## Run E2E tests only
	docker-compose exec backend pytest tests/test_e2e.py -v

lint: ## Run linter
	@echo Running linter...
	docker-compose exec backend ruff check src/ tests/

lint-fix: ## Auto-fix linting issues
	docker-compose exec backend ruff check --fix src/ tests/

typecheck: ## Run type checking
	@echo Running type checker...
	docker-compose exec backend mypy src/ --ignore-missing-imports

format: ## Format code
	docker-compose exec backend ruff format src/ tests/

# ============================================================
# SHELL ACCESS
# ============================================================

shell: shell-backend ## Alias for shell-backend

shell-backend: ## Open backend container shell
	docker-compose exec backend /bin/bash

shell-frontend: ## Open frontend container shell
	docker-compose exec frontend /bin/sh

redis-cli: ## Open Redis CLI
	docker-compose exec redis redis-cli

# ============================================================
# DEMO DATA
# ============================================================

seed-demo: ## Seed demo users and tickets
	@echo Seeding demo data...
	docker-compose exec backend python scripts/seed_demo_users.py
	@echo ""
	@echo Demo accounts:
	@echo   Admin:   admin@demo.com   / Admin123
	@echo   User:    user@demo.com    / User1234
	@echo   Support: support@demo.com / Support123

# ============================================================
# CLEANUP
# ============================================================

clean: ## Stop and remove containers, networks
	@echo Cleaning up containers and networks...
	docker-compose down --remove-orphans
	-docker-compose -f docker-compose.monitoring.yml down --remove-orphans

clean-volumes: ## Remove all volumes (WARNING: deletes all data)
	@echo WARNING: This will delete all data!
	@echo Press Ctrl+C to cancel, or Enter to continue...
	@read -r dummy
	docker-compose down -v --remove-orphans
	@echo Volumes removed

clean-all: ## Remove everything including images
	@echo WARNING: This will remove all containers, volumes, and images!
	@echo Press Ctrl+C to cancel, or Enter to continue...
	@read -r dummy
	docker-compose down -v --remove-orphans --rmi all
	-docker-compose -f docker-compose.monitoring.yml down -v --remove-orphans --rmi all
	@echo Everything removed

# ============================================================
# MONITORING
# ============================================================

status: ## Show service status
	@echo Service Status:
	docker-compose ps

health: ## Check service health
	@echo Health Check:
	@echo   Backend:
	@curl -sf http://localhost:8000/health >/dev/null 2>&1 && echo     OK || echo     FAIL
	@echo   Frontend:
	@curl -sf http://localhost:3000 >/dev/null 2>&1 && echo     OK || echo     FAIL
	@echo   Ollama:
	@curl -sf http://localhost:11434/api/tags >/dev/null 2>&1 && echo     OK || echo     FAIL

stats: ## Show container resource usage
	docker stats --no-stream

# ============================================================
# UTILITIES
# ============================================================

backup-db: ## Backup database to ./backups/
	@mkdir -p backups
	@echo Creating database backup...
	@docker-compose exec -T postgres pg_dump -U postgres llm_agent > backups/backup_$(shell date +%Y%m%d_%H%M%S).sql
	@echo Backup created in backups/

restore-db: ## Restore database (use: make restore-db FILE=path/to/backup.sql)
	@echo WARNING: This will replace current database!
	@echo Press Ctrl+C to cancel, or Enter to continue...
	@read -r dummy
	@cat $(FILE) | docker-compose exec -T postgres psql -U postgres llm_agent
	@echo Database restored
