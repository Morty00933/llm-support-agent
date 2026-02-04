# LLM Support Agent

> **Production-ready AI-powered customer support system** with local LLM inference (Ollama), semantic search (pgvector), real-time communication (WebSocket), and multi-tenant architecture.

[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18.2+-blue.svg)](https://reactjs.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16+-blue.svg)](https://www.postgresql.org)
[![Redis](https://img.shields.io/badge/Redis-7.0+-red.svg)](https://redis.io)
[![Ollama](https://img.shields.io/badge/Ollama-qwen2.5-orange.svg)](https://ollama.ai)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-blue.svg)](https://www.typescriptlang.org)
[![Docker](https://img.shields.io/badge/Docker-Compose-blue.svg)](https://docs.docker.com/compose/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## Содержание

- [Возможности](#-возможности)
- [Технологический стек](#-технологический-стек)
- [Быстрый старт](#-быстрый-старт)
- [Структура проекта](#-структура-проекта)
- [Архитектура системы](#-архитектура-системы)
- [База данных](#-база-данных)
- [API Reference](#-api-reference)
- [Конфигурация](#️-конфигурация)
- [Разработка](#-разработка)
- [Тестирование](#-тестирование)
- [Мониторинг](#-мониторинг)
- [Безопасность](#-безопасность)
- [Производительность](#-производительность)
- [Деплой в Production](#-деплой-в-production)
- [Troubleshooting](#-troubleshooting)
- [Roadmap](#-roadmap)

## Документация

| Документ | Описание |
|----------|----------|
| [ Архитектура](docs/ARCHITECTURE.md) | Диаграммы системы, компоненты, потоки запросов, безопасность |
| [ База данных](docs/DATABASE.md) | ERD схема, описание таблиц, индексы, миграции |
| [ API Reference](docs/API.md) | Полное описание REST API, примеры, коды ошибок |
| [ Инфраструктура](INFRASTRUCTURE.md) | Docker, CI/CD, мониторинг, деплой |

---

##  Возможности

###  Основные функции

| Функция | Описание |
|---------|----------|
| ** Ticket Management** | Полный жизненный цикл тикетов: создание, назначение, приоритизация, отслеживание статусов, история изменений |
| ** AI Agent** | Автоматические ответы на базе локального LLM (Ollama). Поддержка qwen2.5, phi3, llama3 и других моделей |
| ** Knowledge Base** | База знаний с семантическим поиском через pgvector. RAG-архитектура для контекстных ответов |
| ** Real-time Chat** | WebSocket-коммуникация для мгновенных обновлений тикетов и чата |
| ** Multi-tenancy** | Полная изоляция данных для множества организаций в одной инсталляции |
| ** Authentication** | JWT-аутентификация с refresh-токенами, RBAC (роли и разрешения) |

###  Production-Ready функции

| Функция | Описание |
|---------|----------|
| ** Rate Limiting** | Распределённый rate limiter на Redis со sliding window алгоритмом |
| ** File Validation** | Безопасная загрузка файлов с проверкой MIME-типов, размера и сканированием на вредоносный контент |
| ** CI/CD Pipeline** | GitHub Actions для автотестов, сборки Docker-образов и деплоя |
| ** Docker Optimized** | Multi-stage сборка с уменьшением размера образа на 40% |
| ** Monitoring** | Prometheus метрики + Grafana дашборды с алертами |
| ** WebSockets** | Двунаправленная real-time коммуникация |
| ** Frontend Performance** | Code splitting, lazy loading, virtual scrolling для больших списков |
| ** Storybook** | Документация компонентов с интерактивными примерами |
| ** Demo Mode** | Автоматическое заполнение демо-данными для презентаций |

###  Интеграции

| Сервис | Возможности |
|--------|-------------|
| **Jira** | Двухсторонняя синхронизация тикетов, создание issues |
| **Zendesk** | Импорт и синхронизация тикетов поддержки |

---

##  Технологический стек

### Backend

| Технология | Версия | Назначение |
|------------|--------|------------|
| **Python** | 3.11+ | Язык программирования |
| **FastAPI** | 0.109+ | Async веб-фреймворк с автодокументацией |
| **SQLAlchemy** | 2.0+ | Async ORM с поддержкой типов |
| **PostgreSQL** | 16+ | Основная база данных |
| **pgvector** | 0.5+ | Расширение для векторного поиска |
| **Redis** | 7.0+ | Кэширование, rate limiting, очереди задач |
| **Celery** | 5.3+ | Асинхронные фоновые задачи |
| **Alembic** | 1.13+ | Миграции базы данных |
| **Pydantic** | 2.5+ | Валидация данных и настроек |
| **Ollama** | latest | Локальный LLM runtime |

### Frontend

| Технология | Версия | Назначение |
|------------|--------|------------|
| **React** | 18.2+ | UI библиотека |
| **TypeScript** | 5.0+ | Типизация JavaScript |
| **Vite** | 5.0+ | Сборщик с HMR |
| **TailwindCSS** | 3.4+ | Utility-first CSS фреймворк |
| **Zustand** | 4.0+ | Легковесный state management |
| **React Router** | 6.0+ | Клиентский роутинг |
| **Axios** | 1.6+ | HTTP клиент с interceptors |
| **React Window** | 1.8+ | Виртуализация списков |
| **Storybook** | 7.6+ | Документация компонентов |

### DevOps & Monitoring

| Технология | Назначение |
|------------|------------|
| **Docker** | Контейнеризация |
| **Docker Compose** | Оркестрация локального окружения |
| **GitHub Actions** | CI/CD пайплайны |
| **Prometheus** | Сбор метрик |
| **Grafana** | Визуализация и алерты |
| **Nginx** | Reverse proxy, статика |

### AI/ML

| Модель | Размер | Назначение | RAM |
|--------|--------|------------|-----|
| **qwen2.5:3b** | ~2GB | Генерация ответов | 4GB+ |
| **qwen2.5:1.5b** | ~1GB | Легковесная генерация | 2GB+ |
| **nomic-embed-text** | ~300MB | Векторные эмбеддинги (768 dim) | 1GB+ |
| **phi3:mini** | ~2.3GB | Альтернативная модель | 4GB+ |
| **llama3:8b** | ~4.7GB | Высокое качество | 8GB+ |

---

##  Быстрый старт

### Системные требования

| Ресурс | Минимум | Рекомендуется |
|--------|---------|---------------|
| **CPU** | 4 cores | 8 cores |
| **RAM** | 8 GB | 16 GB |
| **Disk** | 20 GB | 50 GB SSD |
| **Docker** | 20.10+ | latest |
| **Docker Compose** | 2.0+ | latest |

### Вариант 1: Production Mode (рекомендуется)

```bash
# 1. Клонировать репозиторий
git clone <repository-url>
cd llm-support-agent

# 2. Скопировать шаблон конфигурации
cp .env.example .env

# 3. Сгенерировать безопасный JWT секрет
openssl rand -hex 32
# Вставить результат в .env: JWT_SECRET=<generated>

# 4. Изменить пароли в .env (DB_PASSWORD, REDIS_PASSWORD)

# 5. Запустить все сервисы
make prod

# 6. Скачать AI модели (первый запуск, ~2GB)
make ollama-pull

# 7. Проверить здоровье сервисов
make health
```

**Точки доступа:**

| Сервис | URL | Описание |
|--------|-----|----------|
| Frontend | http://localhost:3000 | React приложение |
| Backend API | http://localhost:8000 | FastAPI сервер |
| API Docs | http://localhost:8000/docs | Swagger UI |
| ReDoc | http://localhost:8000/redoc | Альтернативная документация |
| Grafana | http://localhost:3001 | Мониторинг (admin/admin) |
| Prometheus | http://localhost:9090 | Метрики |
| Storybook | http://localhost:6006 | Компоненты (npm run storybook) |

### Вариант 2: Development Mode

```bash
# Запустить dev окружение с hot reload
make dev

# Скачать модели
make ollama-pull

# Включить демо-режим (опционально)
# Отредактировать .env:
#   DEMO_MODE_ENABLED=true
#   DEMO_SEED_ON_STARTUP=true

# Перезапустить для применения
make restart

# Смотреть логи
make logs
```

### Вариант 3: Только Backend (для разработки фронтенда отдельно)

```bash
# Запустить только backend сервисы
docker-compose up -d postgres redis ollama backend

# Frontend запустить локально
cd frontend
npm install
npm run dev
```

### Демо-аккаунты

После включения demo mode доступны следующие учётные записи:

| Роль | Email | Пароль | Права |
|------|-------|--------|-------|
| **Admin** | admin@demo.com | admin123 | Полный доступ к системе |
| **Agent** | support@demo.com | support123 | Работа с тикетами, KB |
| **User** | user@demo.com | user123 | Создание тикетов |

---

##  Структура проекта

```
llm-support-agent/
│
├──  .github/                     # CI/CD конфигурация
│   └── workflows/
│       ├── test.yml                # Тесты и линтинг на PR
│       ├── docker.yml              # Сборка и пуш Docker образов
│       └── deploy-staging.yml      # Автодеплой на staging
│
├──  alembic/                     # Миграции базы данных
│   ├── env.py                      # Конфигурация Alembic
│   └── versions/                   # Файлы миграций
│       ├── 001_initial.py          # Начальная схема
│       ├── 002_kb_unique_constraint.py
│       └── 003_add_ticket_metadata.py
│
├──  frontend/                    # React приложение
│   ├──  .storybook/              # Storybook конфигурация
│   │   ├── main.ts
│   │   └── preview.ts
│   │
│   ├──  src/
│   │   ├──  api/                 # API клиент
│   │   │   └── client.ts           # Axios с interceptors
│   │   │
│   │   ├──  components/          # React компоненты
│   │   │   ├──  common/          # Переиспользуемые
│   │   │   │   ├── Button.tsx
│   │   │   │   ├── Button.stories.tsx
│   │   │   │   ├── Badge.tsx
│   │   │   │   ├── Badge.stories.tsx
│   │   │   │   ├── Input.tsx
│   │   │   │   └── Input.stories.tsx
│   │   │   ├──  Layout/          # Макеты страниц
│   │   │   │   ├── Header.tsx
│   │   │   │   ├── Sidebar.tsx
│   │   │   │   └── MainLayout.tsx
│   │   │   └── VirtualTicketList.tsx  # Виртуализированный список
│   │   │
│   │   ├──  hooks/               # Custom React hooks
│   │   │   ├── index.ts
│   │   │   ├── useAuth.tsx         # Аутентификация
│   │   │   ├── useWebSocket.ts     # WebSocket подключение
│   │   │   └── useTickets.ts       # Работа с тикетами
│   │   │
│   │   ├──  pages/               # Страницы приложения
│   │   │   ├── index.ts            # Экспорты
│   │   │   ├── Dashboard.tsx       # Главная с статистикой
│   │   │   ├── Login.tsx           # Авторизация
│   │   │   ├── Tickets.tsx         # Список тикетов
│   │   │   ├── TicketDetail.tsx    # Детали тикета + чат
│   │   │   ├── TicketNew.tsx       # Создание тикета
│   │   │   ├── KnowledgeBase.tsx   # Управление KB
│   │   │   ├── Playground.tsx      # Тестирование AI
│   │   │   └── Settings.tsx        # Настройки
│   │   │
│   │   ├──  store/               # Zustand state management
│   │   │   └── index.ts
│   │   │
│   │   ├──  utils/               # Утилиты
│   │   │   └── formatters.ts
│   │   │
│   │   ├── App.tsx                 # Root компонент с роутингом
│   │   ├── main.tsx                # Entry point
│   │   └── index.css               # Глобальные стили
│   │
│   ├── Dockerfile                  # Docker для frontend
│   ├── Dockerfile.prod             # Production сборка
│   ├── nginx.conf                  # Nginx конфигурация
│   ├── vite.config.ts              # Vite + оптимизации
│   ├── tailwind.config.js          # TailwindCSS
│   ├── tsconfig.json               # TypeScript
│   └── package.json                # Dependencies
│
├──  monitoring/                  # Observability
│   ├── prometheus.yml              # Prometheus конфиг
│   ├──  prometheus/
│   │   └── alerts.yml              # Правила алертов
│   └──  grafana/
│       ├──  dashboards/
│       │   ├── dashboard-provider.yml
│       │   └── llm-support-agent.json  # Готовый дашборд
│       └──  datasources/
│           └── prometheus.yml
│
├──  nginx/                       # Nginx конфигурация
│   └── nginx.conf
│
├──  scripts/                     # Утилиты
│   ├── __init__.py
│   └── seed_demo_users.py          # Скрипт создания демо-данных
│
├──  src/                         # Backend (FastAPI)
│   ├── main.py                     # Entry point, lifespan events
│   │
│   ├──  api/                     # API слой
│   │   ├── __init__.py
│   │   ├── dependencies.py         # DI для роутеров
│   │   ├── middlewares.py          # CORS, Rate Limiting, Logging
│   │   ├── telemetry.py            # Prometheus метрики
│   │   │
│   │   ├──  routers/             # Эндпоинты
│   │   │   ├── __init__.py
│   │   │   ├── auth.py             # /v1/auth/*
│   │   │   ├── tickets.py          # /v1/tickets/*
│   │   │   ├── kb.py               # /v1/kb/*
│   │   │   ├── agent.py            # /v1/agent/*
│   │   │   ├── tenants.py          # /v1/tenants/*
│   │   │   ├── integrations.py     # /v1/integrations/*
│   │   │   ├── websockets.py       # /v1/ws/*
│   │   │   └── demo.py             # /v1/demo/*
│   │   │
│   │   └──  websockets/          # WebSocket менеджер
│   │       ├── __init__.py
│   │       └── manager.py          # Connection management
│   │
│   ├──  core/                    # Ядро приложения
│   │   ├── __init__.py
│   │   ├──  config/              # Конфигурация
│   │   │   ├── __init__.py         # Settings с Pydantic
│   │   │   ├── jwt.py              # JWT настройки
│   │   │   └── feature_flags.py    # Feature toggles
│   │   │
│   │   ├──  errors/              # Обработка ошибок
│   │   │   ├── __init__.py
│   │   │   ├── handlers.py         # Exception handlers
│   │   │   ├── http.py             # HTTP exceptions
│   │   │   └── correlation.py      # Request correlation IDs
│   │   │
│   │   ├── db.py                   # Database engine & session
│   │   ├── security.py             # Password hashing, JWT
│   │   ├── permissions.py          # RBAC система
│   │   ├── exceptions.py           # Custom exceptions
│   │   ├── rate_limit_redis.py     # Distributed rate limiter
│   │   ├── metrics.py              # Prometheus metrics
│   │   ├── logging.py              # Structured logging
│   │   ├── celery_app.py           # Celery configuration
│   │   ├── circuit_breaker.py      # Circuit breaker pattern
│   │   └── demo_data.py            # Demo data seeder
│   │
│   ├──  domain/                  # Доменный слой
│   │   ├── __init__.py
│   │   ├── models.py               # SQLAlchemy ORM модели
│   │   ├── repos.py                # Repository pattern
│   │   └── exceptions.py           # Domain exceptions
│   │
│   ├──  services/                # Бизнес-логика
│   │   ├── __init__.py
│   │   ├── agent.py                # AI Agent оркестрация
│   │   ├── ollama.py               # Ollama HTTP клиент
│   │   ├── embedding.py            # Embedding service
│   │   ├── knowledge.py            # Knowledge base service
│   │   ├── file_validation.py      # File upload validation
│   │   ├── document_parser.py      # PDF/DOCX парсинг
│   │   └──  integrations/
│   │       ├── __init__.py
│   │       ├── jira.py             # Jira API клиент
│   │       └── zendesk.py          # Zendesk API клиент
│   │
│   ├──  agent/                   # AI Agent логика
│   │   ├── __init__.py
│   │   └── policies.py             # Эскалация, системные промпты
│   │
│   ├──  application/             # Application layer
│   │   └──  events/
│   │       └── base.py             # Domain events
│   │
│   ├──  schemas/                 # Pydantic schemas
│   │   └── __init__.py
│   │
│   └──  utils/                   # Утилиты
│       ├── __init__.py
│       ├── prompt.py               # Prompt engineering
│       └── messages.py             # Message formatting
│
├──  tests/                       # Тесты
│   ├── __init__.py
│   ├── conftest.py                 # Pytest fixtures
│   ├── test_auth.py                # Auth тесты
│   ├── test_tickets.py             # Tickets тесты
│   ├── test_kb.py                  # Knowledge Base тесты
│   ├── test_agent.py               # AI Agent тесты
│   ├── test_health.py              # Health check тесты
│   ├── test_multitenancy.py        # Multi-tenant тесты
│   ├── test_integrations_health.py # Integration тесты
│   ├── test_unit_services.py       # Unit тесты сервисов
│   ├── test_e2e.py                 # End-to-end тесты
│   └──  e2e/                     # E2E test suite
│       ├── __init__.py
│       ├── conftest.py
│       ├── test_auth_flow.py
│       ├── test_ticket_workflow.py
│       └── test_kb_management.py
│
├──  docker-compose.yml           # Development stack
├──  docker-compose.prod.yml      # Production stack
├──  docker-compose.monitoring.yml # Monitoring stack
├──  docker-compose.gpu.yml       # GPU support for Ollama
│
├──  Dockerfile.backend           # Backend Dockerfile (dev)
├──  Dockerfile.backend.prod      # Backend Dockerfile (prod)
├──  entrypoint.sh                # Container entrypoint script
│
├──  Makefile                     # Development commands
├──  requirements.txt             # Python dependencies
├──  pyproject.toml               # Python project config
├──  pytest.ini                   # Pytest configuration
├──  alembic.ini                  # Alembic configuration
├──  .pre-commit-config.yaml      # Pre-commit hooks
├──  .gitignore                   # Git ignore rules
├──  .gitattributes               # Git attributes
├──  .env.example                 # Environment template
├──  .coveragerc                  # Coverage configuration
│
├──  INFRASTRUCTURE.md            # Infrastructure documentation
├──  README.md                    # This file
└──  LICENSE                      # MIT License
```

---

##  Архитектура системы

>  **Подробная документация:** [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

### Обзор архитектуры

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLIENTS                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │ Web Browser  │  │ Mobile App   │  │  API Client  │  │   Webhook    │    │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘    │
└─────────┼─────────────────┼─────────────────┼─────────────────┼─────────────┘
          │                 │                 │                 │
          └────────────────┬┴─────────────────┴─────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            NGINX (Reverse Proxy)                             │
│  • SSL/TLS termination  • Load balancing  • Static files  • Gzip            │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │
          ┌────────────────────────┼────────────────────────┐
          │                        │                        │
          ▼                        ▼                        ▼
┌─────────────────┐    ┌─────────────────────┐    ┌─────────────────┐
│    Frontend     │    │      Backend        │    │    WebSocket    │
│  (React + Vite) │    │     (FastAPI)       │    │    Server       │
│                 │    │                     │    │                 │
│ • Dashboard     │    │ • REST API          │    │ • Real-time     │
│ • Tickets       │    │ • Authentication    │    │   updates       │
│ • KB Management │    │ • Business Logic    │    │ • Chat          │
│ • AI Playground │    │ • Validation        │    │ • Notifications │
└─────────────────┘    └──────────┬──────────┘    └─────────────────┘
                                  │
         ┌────────────────────────┼────────────────────────┐
         │                        │                        │
         ▼                        ▼                        ▼
┌─────────────────┐    ┌─────────────────────┐    ┌─────────────────┐
│   PostgreSQL    │    │       Redis         │    │     Ollama      │
│   + pgvector    │    │                     │    │                 │
│                 │    │ • Rate Limiting     │    │ • qwen2.5:3b    │
│ • Users         │    │ • Session Cache     │    │ • nomic-embed   │
│ • Tenants       │    │ • Celery Broker     │    │                 │
│ • Tickets       │    │ • Pub/Sub           │    │ Chat Generation │
│ • Messages      │    │                     │    │ Text Embeddings │
│ • KB Chunks     │    │                     │    │                 │
│   (vectors)     │    │                     │    │                 │
└─────────────────┘    └─────────────────────┘    └─────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Celery Workers                                     │
│  • Background tasks  • Scheduled jobs  • Email notifications                │
└─────────────────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Monitoring                                      │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐         │
│  │   Prometheus    │───▶│     Grafana     │    │     Sentry      │         │
│  │   (metrics)     │    │  (dashboards)   │    │   (errors)      │         │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘         │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Паттерны и принципы

| Паттерн | Применение |
|---------|------------|
| **Repository Pattern** | Абстракция доступа к данным (`src/domain/repos.py`) |
| **Service Layer** | Бизнес-логика изолирована в сервисах (`src/services/`) |
| **Dependency Injection** | FastAPI dependencies для DI |
| **Domain-Driven Design** | Чёткое разделение domain/application/infrastructure |
| **CQRS (частично)** | Разделение read/write операций в репозиториях |
| **Circuit Breaker** | Защита от каскадных сбоев внешних сервисов |

### Потоки данных

#### 1. Создание тикета с AI-ответом

```
User Request
     │
     ▼
┌─────────────┐
│  Frontend   │  POST /v1/tickets
└─────┬───────┘
      │
      ▼
┌─────────────┐
│   Router    │  Валидация, авторизация
└─────┬───────┘
      │
      ▼
┌─────────────┐
│ Repository  │  Создание тикета в БД
└─────┬───────┘
      │
      ▼
┌─────────────┐
│   Agent     │  1. Embed query (nomic-embed-text)
│  Service    │  2. Search KB (pgvector similarity)
│             │  3. Build prompt with context
│             │  4. Generate response (qwen2.5:3b)
└─────┬───────┘
      │
      ▼
┌─────────────┐
│  WebSocket  │  Broadcast update to connected clients
└─────────────┘
```

#### 2. Семантический поиск в KB

```
Search Query
     │
     ▼
┌─────────────────┐
│ Embedding       │  POST /api/embeddings
│ Service         │  nomic-embed-text → 768-dim vector
└─────┬───────────┘
      │
      ▼
┌─────────────────┐
│ pgvector        │  SELECT * FROM kb_chunks
│                 │  ORDER BY embedding <=> query_vec
│                 │  LIMIT 5
└─────┬───────────┘
      │
      ▼
┌─────────────────┐
│ Results         │  Top-K similar chunks
│ (scored)        │  with similarity scores
└─────────────────┘
```

---

## 🗄 База данных

>  **Подробная документация:** [docs/DATABASE.md](docs/DATABASE.md)

### Схема данных

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              tenants                                     │
├─────────────────────────────────────────────────────────────────────────┤
│ id (PK)        │ SERIAL                                                 │
│ name           │ VARCHAR(255) NOT NULL                                  │
│ slug           │ VARCHAR(100) UNIQUE NOT NULL                           │
│ is_active      │ BOOLEAN DEFAULT TRUE                                   │
│ created_at     │ TIMESTAMP DEFAULT NOW()                                │
│ updated_at     │ TIMESTAMP                                              │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ 1:N
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                               users                                      │
├─────────────────────────────────────────────────────────────────────────┤
│ id (PK)        │ SERIAL                                                 │
│ tenant_id (FK) │ INTEGER REFERENCES tenants(id) ON DELETE CASCADE       │
│ email          │ VARCHAR(255) NOT NULL                                  │
│ hashed_password│ VARCHAR(255) NOT NULL                                  │
│ full_name      │ VARCHAR(255)                                           │
│ role           │ ENUM('admin', 'agent', 'user') DEFAULT 'user'          │
│ is_active      │ BOOLEAN DEFAULT TRUE                                   │
│ created_at     │ TIMESTAMP DEFAULT NOW()                                │
│ updated_at     │ TIMESTAMP                                              │
├─────────────────────────────────────────────────────────────────────────┤
│ UNIQUE(tenant_id, email)                                                │
│ INDEX(tenant_id)                                                        │
│ INDEX(email)                                                            │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ 1:N
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                              tickets                                     │
├─────────────────────────────────────────────────────────────────────────┤
│ id (PK)        │ SERIAL                                                 │
│ tenant_id (FK) │ INTEGER REFERENCES tenants(id) ON DELETE CASCADE       │
│ title          │ VARCHAR(500) NOT NULL                                  │
│ description    │ TEXT                                                   │
│ status         │ ENUM('open','in_progress','pending_customer',          │
│                │       'pending_agent','escalated','resolved',          │
│                │       'closed','reopened') DEFAULT 'open'              │
│ priority       │ ENUM('low','medium','high','urgent') DEFAULT 'medium'  │
│ source         │ VARCHAR(50) DEFAULT 'web'                              │
│ assigned_to    │ INTEGER REFERENCES users(id) ON DELETE SET NULL        │
│ created_by_id  │ INTEGER REFERENCES users(id) ON DELETE SET NULL        │
│ metadata_json  │ JSONB DEFAULT '{}'                                     │
│ created_at     │ TIMESTAMP DEFAULT NOW()                                │
│ updated_at     │ TIMESTAMP                                              │
├─────────────────────────────────────────────────────────────────────────┤
│ INDEX(tenant_id)                                                        │
│ INDEX(status)                                                           │
│ INDEX(tenant_id, status)                                                │
│ INDEX(updated_at)                                                       │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ 1:N
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                              messages                                    │
├─────────────────────────────────────────────────────────────────────────┤
│ id (PK)        │ SERIAL                                                 │
│ ticket_id (FK) │ INTEGER REFERENCES tickets(id) ON DELETE CASCADE       │
│ role           │ ENUM('user', 'assistant', 'system')                    │
│ content        │ TEXT NOT NULL                                          │
│ metadata_json  │ JSONB DEFAULT '{}'                                     │
│ created_at     │ TIMESTAMP DEFAULT NOW()                                │
├─────────────────────────────────────────────────────────────────────────┤
│ INDEX(ticket_id)                                                        │
│ INDEX(created_at)                                                       │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                             kb_chunks                                    │
├─────────────────────────────────────────────────────────────────────────┤
│ id (PK)        │ SERIAL                                                 │
│ tenant_id (FK) │ INTEGER REFERENCES tenants(id) ON DELETE CASCADE       │
│ source         │ VARCHAR(500) NOT NULL (filename, URL, etc.)            │
│ chunk          │ TEXT NOT NULL                                          │
│ chunk_hash     │ VARCHAR(64) NOT NULL (SHA256)                          │
│ metadata_json  │ JSONB DEFAULT '{}'                                     │
│ is_current     │ BOOLEAN DEFAULT TRUE                                   │
│ version        │ INTEGER DEFAULT 1                                      │
│ archived_at    │ TIMESTAMP                                              │
│ embedding_vector│ VECTOR(768) (pgvector)                                │
│ created_at     │ TIMESTAMP DEFAULT NOW()                                │
│ updated_at     │ TIMESTAMP                                              │
├─────────────────────────────────────────────────────────────────────────┤
│ UNIQUE(tenant_id, chunk_hash)                                           │
│ INDEX(tenant_id)                                                        │
│ INDEX(source)                                                           │
│ INDEX(tenant_id, source)                                                │
│ INDEX(is_current)                                                       │
│ INDEX USING ivfflat (embedding_vector vector_cosine_ops)                │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                        ticket_external_refs                              │
├─────────────────────────────────────────────────────────────────────────┤
│ id (PK)        │ SERIAL                                                 │
│ tenant_id (FK) │ INTEGER REFERENCES tenants(id) ON DELETE CASCADE       │
│ ticket_id (FK) │ INTEGER REFERENCES tickets(id) ON DELETE CASCADE       │
│ system         │ VARCHAR(50) NOT NULL ('jira', 'zendesk')               │
│ external_id    │ VARCHAR(255) NOT NULL                                  │
│ external_url   │ VARCHAR(1000)                                          │
│ metadata_json  │ JSONB DEFAULT '{}'                                     │
│ created_at     │ TIMESTAMP DEFAULT NOW()                                │
│ updated_at     │ TIMESTAMP                                              │
├─────────────────────────────────────────────────────────────────────────┤
│ UNIQUE(system, external_id)                                             │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                       integration_sync_logs                              │
├─────────────────────────────────────────────────────────────────────────┤
│ id (PK)        │ SERIAL                                                 │
│ tenant_id (FK) │ INTEGER REFERENCES tenants(id) ON DELETE CASCADE       │
│ system         │ VARCHAR(50) NOT NULL                                   │
│ direction      │ ENUM('inbound', 'outbound')                            │
│ status         │ ENUM('started', 'completed', 'failed')                 │
│ records_processed│ INTEGER DEFAULT 0                                    │
│ error_message  │ TEXT                                                   │
│ started_at     │ TIMESTAMP DEFAULT NOW()                                │
│ completed_at   │ TIMESTAMP                                              │
│ metadata_json  │ JSONB DEFAULT '{}'                                     │
└─────────────────────────────────────────────────────────────────────────┘
```

### Enum значения

#### TicketStatus
```python
class TicketStatus(str, Enum):
    OPEN = "open"                     # Новый тикет
    IN_PROGRESS = "in_progress"       # В работе
    PENDING_CUSTOMER = "pending_customer"  # Ожидание ответа клиента
    PENDING_AGENT = "pending_agent"   # Ожидание агента
    ESCALATED = "escalated"           # Эскалирован
    RESOLVED = "resolved"             # Решён
    CLOSED = "closed"                 # Закрыт
    REOPENED = "reopened"             # Переоткрыт
```

#### TicketPriority
```python
class TicketPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"
```

#### UserRole
```python
class UserRole(str, Enum):
    ADMIN = "admin"     # Полный доступ
    AGENT = "agent"     # Работа с тикетами
    USER = "user"       # Создание тикетов
```

### Миграции

```bash
# Создать новую миграцию
docker-compose exec backend alembic revision --autogenerate -m "Add new_field to tickets"

# Применить все миграции
make migrate
# или
docker-compose exec backend alembic upgrade head

# Откатить последнюю миграцию
docker-compose exec backend alembic downgrade -1

# Посмотреть историю
docker-compose exec backend alembic history

# Текущая версия
docker-compose exec backend alembic current
```

---

##  API Reference

>  **Полная документация:** [docs/API.md](docs/API.md)

### Аутентификация

Все защищённые эндпоинты требуют JWT токен в заголовке:
```
Authorization: Bearer <access_token>
```

#### Endpoints

| Метод | Путь | Описание |
|-------|------|----------|
| `POST` | `/v1/auth/register` | Регистрация нового пользователя |
| `POST` | `/v1/auth/login` | Логин (form-data) |
| `POST` | `/v1/auth/login/json` | Логин (JSON body) |
| `POST` | `/v1/auth/refresh` | Обновление access token |
| `GET` | `/v1/auth/me` | Получить текущего пользователя |
| `PATCH` | `/v1/auth/me` | Обновить профиль |
| `POST` | `/v1/auth/change-password` | Сменить пароль |

#### Примеры

```bash
# Регистрация
curl -X POST http://localhost:8000/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123!",
    "full_name": "John Doe"
  }'

# Логин
curl -X POST http://localhost:8000/v1/auth/login/json \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123!"
  }'
# Response: { "access_token": "...", "refresh_token": "...", "token_type": "bearer" }

# Получить профиль
curl http://localhost:8000/v1/auth/me \
  -H "Authorization: Bearer <access_token>"
```

### Тикеты

| Метод | Путь | Описание |
|-------|------|----------|
| `GET` | `/v1/tickets` | Список тикетов (с фильтрацией) |
| `POST` | `/v1/tickets` | Создать тикет |
| `GET` | `/v1/tickets/{id}` | Получить тикет |
| `PATCH` | `/v1/tickets/{id}` | Обновить тикет |
| `DELETE` | `/v1/tickets/{id}` | Удалить тикет |
| `GET` | `/v1/tickets/{id}/messages` | Сообщения тикета |
| `POST` | `/v1/tickets/{id}/messages` | Добавить сообщение |

#### Query параметры для списка

| Параметр | Тип | Описание |
|----------|-----|----------|
| `skip` | int | Пропустить N записей (default: 0) |
| `limit` | int | Максимум записей (default: 50, max: 100) |
| `status` | string | Фильтр по статусу |
| `priority` | string | Фильтр по приоритету |
| `assigned_to` | int | Фильтр по assignee |

#### Примеры

```bash
# Список тикетов
curl "http://localhost:8000/v1/tickets?status=open&limit=10" \
  -H "Authorization: Bearer <token>"

# Создать тикет
curl -X POST http://localhost:8000/v1/tickets \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Не работает авторизация",
    "description": "При попытке войти получаю ошибку 500",
    "priority": "high"
  }'

# Обновить статус
curl -X PATCH http://localhost:8000/v1/tickets/1 \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"status": "in_progress"}'
```

### AI Agent

| Метод | Путь | Описание |
|-------|------|----------|
| `POST` | `/v1/agent/ask` | Задать вопрос AI (playground) |
| `POST` | `/v1/agent/respond/{ticket_id}` | Сгенерировать ответ для тикета |
| `POST` | `/v1/agent/auto-respond/{ticket_id}` | Автоответ с использованием KB |
| `GET` | `/v1/agent/health` | Проверить статус Ollama |

#### Примеры

```bash
# Задать вопрос напрямую
curl -X POST http://localhost:8000/v1/agent/ask \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Как настроить двухфакторную аутентификацию?",
    "use_kb": true
  }'

# Автоответ на тикет
curl -X POST http://localhost:8000/v1/agent/auto-respond/1 \
  -H "Authorization: Bearer <token>"
```

### Knowledge Base

| Метод | Путь | Описание |
|-------|------|----------|
| `GET` | `/v1/kb/chunks` | Список всех чанков |
| `POST` | `/v1/kb/chunks` | Добавить чанки |
| `DELETE` | `/v1/kb/sources/{source}` | Удалить по источнику |
| `POST` | `/v1/kb/search` | Семантический поиск |
| `POST` | `/v1/kb/reindex` | Переиндексировать эмбеддинги |
| `POST` | `/v1/kb/upload` | Загрузить файл (PDF, TXT, MD, DOCX) |

#### Примеры

```bash
# Добавить знания
curl -X POST http://localhost:8000/v1/kb/chunks \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "source": "faq.md",
    "chunks": [
      "Для сброса пароля перейдите в Настройки > Безопасность > Сброс пароля",
      "Двухфакторная аутентификация включается в разделе Безопасность"
    ]
  }'

# Семантический поиск
curl -X POST http://localhost:8000/v1/kb/search \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "как сбросить пароль",
    "limit": 5
  }'

# Загрузить файл
curl -X POST http://localhost:8000/v1/kb/upload \
  -H "Authorization: Bearer <token>" \
  -F "file=@documentation.pdf"
```

### WebSocket

| Путь | Описание |
|------|----------|
| `/v1/ws/tickets/{ticket_id}?token=<jwt>` | Real-time обновления тикета |
| `/v1/ws/chat?token=<jwt>` | AI чат со стримингом |
| `/v1/ws/notifications?token=<jwt>` | Глобальные уведомления |

#### Пример подключения (JavaScript)

```javascript
const token = "your_jwt_token";
const ws = new WebSocket(`ws://localhost:8000/v1/ws/tickets/1?token=${token}`);

ws.onopen = () => {
  console.log("Connected");
  ws.send(JSON.stringify({ type: "ping" }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log("Received:", data);
  // { type: "message_created", ticket_id: 1, message: {...} }
};

ws.onclose = () => console.log("Disconnected");
```

### Health & Metrics

| Путь | Описание |
|------|----------|
| `/health` | Общий health check |
| `/health/ready` | Readiness probe (DB + Redis) |
| `/health/live` | Liveness probe |
| `/metrics` | Prometheus метрики |

---

##  Конфигурация

### Переменные окружения

Полный список в `.env.example`. Основные:

#### Приложение

| Переменная | По умолчанию | Описание |
|------------|--------------|----------|
| `ENV` | `dev` | Окружение: `dev`, `test`, `prod` |
| `DEBUG` | `true` | Режим отладки |
| `APP_NAME` | `LLM Support Agent` | Название приложения |
| `HOST` | `0.0.0.0` | Хост сервера |
| `PORT` | `8000` | Порт сервера |
| `WORKERS` | `1` | Количество worker'ов (prod: 4) |
| `LOG_LEVEL` | `INFO` | Уровень логирования |

#### JWT

| Переменная | По умолчанию | Описание |
|------------|--------------|----------|
| `JWT_SECRET` | - | **ОБЯЗАТЕЛЬНО** Секретный ключ (32+ символов) |
| `JWT_ALG` | `HS256` | Алгоритм |
| `JWT_EXPIRE_MIN` | `60` | Время жизни access token (минуты) |
| `JWT_REFRESH_EXPIRE_DAYS` | `7` | Время жизни refresh token (дни) |

#### База данных

| Переменная | По умолчанию | Описание |
|------------|--------------|----------|
| `DB_HOST` | `postgres` | Хост PostgreSQL |
| `DB_PORT` | `5432` | Порт |
| `DB_USER` | `postgres` | Пользователь |
| `DB_PASSWORD` | `postgres` | Пароль |
| `DB_NAME` | `llm_agent` | Имя базы |
| `DB_POOL_SIZE` | `10` | Размер пула соединений |
| `DB_MAX_OVERFLOW` | `20` | Максимум дополнительных соединений |

#### Redis

| Переменная | По умолчанию | Описание |
|------------|--------------|----------|
| `REDIS_HOST` | `redis` | Хост Redis |
| `REDIS_PORT` | `6379` | Порт |
| `REDIS_PASSWORD` | - | Пароль (опционально) |
| `REDIS_DB` | `0` | Номер базы |
| `REDIS_SSL` | `false` | Использовать SSL |

#### Ollama

| Переменная | По умолчанию | Описание |
|------------|--------------|----------|
| `OLLAMA_BASE_URL` | `http://ollama:11434` | URL Ollama API |
| `OLLAMA_MODEL_CHAT` | `qwen2.5:3b` | Модель для чата |
| `OLLAMA_MODEL_EMBED` | `nomic-embed-text` | Модель для эмбеддингов |
| `OLLAMA_TIMEOUT` | `120` | Таймаут запросов (секунды) |
| `OLLAMA_TEMPERATURE` | `0.2` | Креативность (0.0-1.0) |
| `EMBEDDING_DIM` | `768` | Размерность эмбеддингов |

#### Интеграции

| Переменная | Описание |
|------------|----------|
| `JIRA_ENABLED` | Включить интеграцию с Jira |
| `JIRA_BASE_URL` | URL Jira инстанса |
| `JIRA_EMAIL` | Email пользователя |
| `JIRA_API_TOKEN` | API токен |
| `JIRA_PROJECT_KEY` | Ключ проекта |
| `ZENDESK_ENABLED` | Включить интеграцию с Zendesk |
| `ZENDESK_SUBDOMAIN` | Субдомен Zendesk |
| `ZENDESK_EMAIL` | Email |
| `ZENDESK_API_TOKEN` | API токен |

#### Feature Flags

| Переменная | По умолчанию | Описание |
|------------|--------------|----------|
| `DEMO_MODE_ENABLED` | `false` | Включить demo эндпоинты |
| `DEMO_SEED_ON_STARTUP` | `false` | Заполнить demo данные при старте |
| `PROMETHEUS_ENABLED` | `true` | Включить метрики |

#### CORS

| Переменная | Описание |
|------------|----------|
| `CORS_ORIGINS` | Разрешённые origins через запятую |

Пример:
```bash
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,https://app.example.com
```

---

##  Разработка

### Makefile команды

```bash
make help              # Показать все команды

# === Запуск ===
make dev               # Development окружение
make dev-full          # + Celery worker
make prod              # Production окружение
make prod-monitoring   # + Prometheus + Grafana
make stop              # Остановить все сервисы
make restart           # Перезапустить
make down              # Остановить и удалить контейнеры

# === Логи ===
make logs              # Все логи
make logs-backend      # Только backend
make logs-frontend     # Только frontend
make logs-ollama       # Только Ollama

# === База данных ===
make migrate           # Применить миграции
make migrate-create    # Создать миграцию (NAME=description)
make db-shell          # PostgreSQL shell
make redis-cli         # Redis CLI
make backup-db         # Создать бэкап
make restore-db        # Восстановить из бэкапа (FILE=path)

# === Тестирование ===
make test              # Запустить тесты
make test-cov          # С отчётом о покрытии
make test-watch        # Watch mode
make lint              # Линтер (ruff)
make format            # Форматирование (ruff format)
make type-check        # Проверка типов (mypy)

# === AI Модели ===
make ollama-pull       # Скачать модели
make ollama-list       # Список моделей

# === Мониторинг ===
make monitoring        # Запустить Prometheus + Grafana
make health            # Проверить здоровье сервисов
make stats             # Статистика контейнеров

# === Очистка ===
make clean             # Удалить контейнеры и volumes
make clean-all         # + удалить образы
make prune             # Docker system prune
```

### Локальная разработка без Docker

#### Backend

```bash
# Создать виртуальное окружение
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate     # Windows

# Установить зависимости
pip install -r requirements.txt

# Запустить PostgreSQL и Redis (docker)
docker-compose up -d postgres redis ollama

# Применить миграции
alembic upgrade head

# Запустить сервер
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend

```bash
cd frontend

# Установить зависимости
npm install

# Запустить dev сервер
npm run dev

# Storybook
npm run storybook

# Сборка
npm run build

# Линтинг
npm run lint
```

### Pre-commit hooks

```bash
# Установить
pip install pre-commit
pre-commit install

# Запустить вручную
pre-commit run --all-files
```

Настроенные хуки (`.pre-commit-config.yaml`):
- `ruff` - линтинг Python
- `ruff-format` - форматирование Python
- `mypy` - проверка типов
- `eslint` - линтинг TypeScript
- `prettier` - форматирование

---

##  Тестирование

### Структура тестов

```
tests/
├── conftest.py              # Общие fixtures
├── test_auth.py             # Аутентификация
├── test_tickets.py          # CRUD тикетов
├── test_kb.py               # Knowledge Base
├── test_agent.py            # AI Agent
├── test_health.py           # Health checks
├── test_multitenancy.py     # Изоляция данных
├── test_unit_services.py    # Unit тесты сервисов
└── e2e/                     # End-to-end
    ├── test_auth_flow.py
    ├── test_ticket_workflow.py
    └── test_kb_management.py
```

### Запуск тестов

```bash
# Все тесты
make test

# С покрытием
make test-cov

# Конкретный файл
docker-compose exec backend pytest tests/test_auth.py -v

# Конкретный тест
docker-compose exec backend pytest tests/test_auth.py::test_login_success -v

# С выводом print()
docker-compose exec backend pytest tests/test_agent.py -v -s

# Параллельно
docker-compose exec backend pytest -n auto

# Watch mode
docker-compose exec backend ptw tests/
```

### Fixtures (conftest.py)

```python
@pytest.fixture
async def db_session():
    """Async database session with rollback."""

@pytest.fixture
async def test_tenant(db_session):
    """Test tenant."""

@pytest.fixture
async def test_user(db_session, test_tenant):
    """Test user with JWT token."""

@pytest.fixture
async def auth_headers(test_user):
    """Authorization headers."""

@pytest.fixture
async def client(db_session):
    """Async HTTP test client."""
```

### Пример теста

```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_ticket(client: AsyncClient, auth_headers: dict):
    response = await client.post(
        "/v1/tickets",
        headers=auth_headers,
        json={
            "title": "Test Ticket",
            "description": "Test description",
            "priority": "high"
        }
    )

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Ticket"
    assert data["status"] == "open"
```

---

##  Мониторинг

### Запуск

```bash
# Запустить monitoring stack
make monitoring
# или
docker-compose -f docker-compose.monitoring.yml up -d
```

### Доступ

| Сервис | URL | Креды |
|--------|-----|-------|
| Grafana | http://localhost:3001 | admin / admin |
| Prometheus | http://localhost:9090 | - |

### Метрики

Backend экспортирует метрики на `/metrics`:

| Метрика | Тип | Описание |
|---------|-----|----------|
| `http_requests_total` | Counter | Всего HTTP запросов |
| `http_request_duration_seconds` | Histogram | Длительность запросов |
| `http_requests_in_progress` | Gauge | Запросов в обработке |
| `db_connections_active` | Gauge | Активные соединения с БД |
| `redis_operations_total` | Counter | Операции с Redis |
| `agent_responses_total` | Counter | Ответы AI агента |
| `agent_response_duration_seconds` | Histogram | Время генерации ответа |
| `kb_search_duration_seconds` | Histogram | Время поиска в KB |
| `rate_limit_violations_total` | Counter | Превышения rate limit |

### Алерты (Prometheus)

Настроены в `monitoring/prometheus/alerts.yml`:

| Алерт | Условие | Severity |
|-------|---------|----------|
| `HighErrorRate` | >5% ошибок за 5 мин | critical |
| `SlowAPIResponse` | P95 > 2s за 10 мин | warning |
| `HighCPUUsage` | >80% за 5 мин | warning |
| `HighMemoryUsage` | >85% | critical |
| `PostgresDown` | недоступен 1 мин | critical |
| `RedisDown` | недоступен 1 мин | critical |
| `OllamaDown` | недоступен 2 мин | warning |
| `HighDBConnections` | >80% пула | warning |

### Grafana Dashboard

Предустановленный дашборд включает:

- **Overview**: Запросы/сек, ошибки, latency
- **API Endpoints**: Топ эндпоинтов по latency и ошибкам
- **Database**: Соединения, время запросов
- **Redis**: Memory, hit rate, операции
- **AI Agent**: Время ответа, количество обращений к KB
- **System**: CPU, Memory, Network

---

## 🔒 Безопасность

### Реализованные меры

| Мера | Реализация |
|------|------------|
| **Аутентификация** | JWT с refresh токенами |
| **Хеширование паролей** | bcrypt (12 rounds) через passlib |
| **Валидация паролей** | Минимум 8 символов, uppercase, lowercase, digit |
| **CORS** | Настраиваемые origins |
| **Rate Limiting** | Redis sliding window (100 req/min/IP) |
| **SQL Injection** | SQLAlchemy ORM с параметризацией |
| **XSS** | React автоэкранирование |
| **File Upload** | MIME проверка, размер, сканирование |
| **Multi-tenancy** | Изоляция данных на уровне БД |
| **Input Validation** | Pydantic schemas |
| **HTTPS** | Поддержка через Nginx |
| **Correlation IDs** | Трассировка запросов |

### Password Policy

```python
# Минимальные требования:
- Длина >= 8 символов
- Хотя бы 1 заглавная буква
- Хотя бы 1 строчная буква
- Хотя бы 1 цифра
- Не в списке популярных паролей
- Не совпадает с email
```

### Rate Limiting

```python
# Конфигурация
MAX_REQUESTS = 100      # запросов
WINDOW_SECONDS = 60     # за период

# Исключения:
- /health/*
- /metrics
```

При превышении возвращается `429 Too Many Requests` с заголовком `Retry-After`.

### Checklist для Production

- [ ] Изменить все пароли по умолчанию
- [ ] Сгенерировать сильный `JWT_SECRET` (минимум 32 символа)
- [ ] Установить `DEBUG=false`
- [ ] Настроить CORS только для нужных доменов
- [ ] Включить Redis authentication
- [ ] Настроить SSL/TLS сертификаты
- [ ] Настроить Sentry для отслеживания ошибок
- [ ] Включить production логирование (JSON формат)
- [ ] Настроить автоматические бэкапы
- [ ] Настроить firewall правила
- [ ] Настроить fail2ban или аналог
- [ ] Регулярно обновлять зависимости

---

## ⚡ Производительность

### Бенчмарки

| Операция | Время | Условия |
|----------|-------|---------|
| AI ответ (короткий) | 1-2 сек | qwen2.5:3b, 100 токенов |
| AI ответ (длинный) | 3-8 сек | qwen2.5:3b, 500 токенов |
| Эмбеддинг текста | 20-50 мс | nomic-embed-text, 500 токенов |
| Поиск в KB | 40-60 мс | 1000 чанков, pgvector |
| Создание тикета | 50-100 мс | без AI |
| WebSocket latency | <10 мс | локальная сеть |
| JWT валидация | <1 мс | - |

### Оптимизации

#### Backend

- **Async/await** - неблокирующий I/O везде
- **Connection pooling** - PostgreSQL (10+20 overflow)
- **Redis caching** - rate limits, sessions
- **Batch processing** - массовые эмбеддинги
- **pgvector indexes** - IVFFlat для быстрого поиска

#### Frontend

- **Code splitting** - React.lazy для страниц
- **Lazy loading** - загрузка по требованию
- **Virtual scrolling** - react-window для длинных списков
- **Bundle optimization** - vendor chunks, tree shaking
- **Gzip compression** - Nginx

#### Docker

- **Multi-stage builds** - уменьшение размера на 40%
- **Layer caching** - быстрые пересборки
- **Alpine base** - минимальный размер
- **Non-root user** - безопасность

### Масштабирование

```yaml
# docker-compose.prod.yml
services:
  backend:
    deploy:
      replicas: 4
      resources:
        limits:
          cpus: '2'
          memory: 2G
```

---

## 🚢 Деплой в Production

### Docker Compose (простой)

```bash
# 1. Настроить .env
cp .env.example .env
# Изменить: JWT_SECRET, DB_PASSWORD, REDIS_PASSWORD

# 2. Запустить
make prod

# 3. Настроить Nginx reverse proxy (внешний)
```

### Kubernetes (масштабируемый)

Пример манифестов в `ops/kubernetes/` (если есть).

### Рекомендуемая инфраструктура

```
┌─────────────────────────────────────────────────────────────┐
│                    Load Balancer (LB)                        │
│                    (AWS ALB / GCP LB)                        │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                    Nginx Ingress                             │
│                    SSL Termination                           │
└─────────────────────────┬───────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
        ▼                 ▼                 ▼
┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│   Backend     │ │   Backend     │ │   Backend     │
│   (Pod 1)     │ │   (Pod 2)     │ │   (Pod 3)     │
└───────┬───────┘ └───────┬───────┘ └───────┬───────┘
        │                 │                 │
        └────────────────┬┴─────────────────┘
                         │
┌────────────────────────┼────────────────────────┐
│                        │                        │
▼                        ▼                        ▼
┌────────────┐    ┌────────────┐    ┌────────────┐
│ PostgreSQL │    │   Redis    │    │   Ollama   │
│  (Primary) │    │  (Cluster) │    │  (GPU Pod) │
│    + RDS   │    │            │    │            │
└────────────┘    └────────────┘    └────────────┘
```

---

## 🐛 Troubleshooting

### Ollama не отвечает

```bash
# Проверить статус
curl http://localhost:11434/api/tags

# Логи
docker logs llm-support-ollama

# Перезапустить
docker restart llm-support-ollama

# Скачать модели вручную
docker exec llm-support-ollama ollama pull qwen2.5:3b
docker exec llm-support-ollama ollama pull nomic-embed-text

# Проверить память
docker stats llm-support-ollama
```

### База данных не подключается

```bash
# Проверить PostgreSQL
docker-compose exec postgres pg_isready

# Проверить pgvector
docker-compose exec postgres psql -U postgres -d llm_agent \
  -c "SELECT * FROM pg_extension WHERE extname='vector';"

# Пересоздать базу
make stop
docker volume rm llm-support-agent_postgres_data
make dev
```

### Frontend не видит API

```bash
# Проверить CORS в .env
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# Проверить backend
curl http://localhost:8000/health

# Проверить proxy в vite.config.ts
```

### Миграции не применяются

```bash
# Проверить текущую версию
docker-compose exec backend alembic current

# Показать историю
docker-compose exec backend alembic history

# Принудительно применить
docker-compose exec backend alembic upgrade head --sql
docker-compose exec backend alembic upgrade head
```

### WebSocket не подключается

```bash
# Проверить эндпоинт
wscat -c "ws://localhost:8000/v1/ws/notifications?token=YOUR_JWT"

# Проверить токен - должен быть валидный JWT
# WebSocket требует ?token=<jwt> query параметр
```

### Rate Limit срабатывает

```bash
# Проверить Redis
docker-compose exec redis redis-cli
> KEYS rate_limit:*
> TTL rate_limit:127.0.0.1:/v1/tickets

# Очистить rate limits
> FLUSHDB
```

---

## 🗺 Roadmap

### 🔴 Высокий приоритет

- [ ] Email уведомления (обновления тикетов, упоминания)
- [ ] Расширенная аналитика (время ответа, % решения, точность AI)
- [ ] SLA management (дедлайны ответа/решения)
- [ ] Правила автоматической маршрутизации тикетов
- [ ] Кастомные поля для тикетов

### 🟡 Средний приоритет

- [ ] Telegram / Slack бот интеграция
- [ ] Расширенный RAG: чанкинг PDF/DOCX с сохранением структуры
- [ ] Мультиязычность (i18n)
- [ ] CSAT / NPS опросы
- [ ] Сохранённые ответы / шаблоны
- [ ] Внутренние заметки (только для агентов)
- [ ] Объединение / разделение тикетов
- [ ] Email-to-ticket конвертация

### 🟢 Низкий приоритет

- [ ] Dark mode toggle
- [ ] Мобильное приложение (React Native)
- [ ] Голосовой ввод
- [ ] Sentiment analysis
- [ ] Feedback loop для обучения AI
- [ ] Кастомные промпты для каждого tenant
- [ ] Экспорт тикетов (CSV, PDF)
- [ ] Webhooks для внешних интеграций

###  Технический долг

- [ ] Увеличить покрытие тестами до 80%+
- [ ] E2E тесты с Playwright
- [ ] OpenTelemetry трассировка
- [ ] Оптимизация запросов к БД
- [ ] Redis Cluster поддержка
- [ ] Horizontal scaling (multi-worker)
- [ ] API versioning стратегия

---

## 🤝 Contributing

1. Fork репозитория
2. Создать feature branch (`git checkout -b feature/amazing-feature`)
3. Commit изменений (`git commit -m 'Add amazing feature'`)
4. Push в branch (`git push origin feature/amazing-feature`)
5. Открыть Pull Request

### Guidelines

- Следовать PEP 8 для Python кода
- Использовать TypeScript strict mode для frontend
- Писать тесты для новых функций
- Обновлять документацию
- Запускать линтер перед коммитом: `make lint`

---

##  License

MIT License - см. файл [LICENSE](LICENSE)

---

## 🙏 Acknowledgments

- [Ollama](https://ollama.ai) - Локальный LLM runtime
- [FastAPI](https://fastapi.tiangolo.com) - Современный Python веб-фреймворк
- [pgvector](https://github.com/pgvector/pgvector) - Векторный поиск для PostgreSQL
- [React](https://reactjs.org) - UI библиотека
- [Qwen](https://qwen.ai) - Open-source LLM модели
- [TailwindCSS](https://tailwindcss.com) - CSS фреймворк

---

<div align="center">

**Built with ❤️ and 🤖**

**Production-Ready | Multi-Tenant | Self-Hosted | Privacy-First**

[Report Bug](../../issues) · [Request Feature](../../issues) · [Documentation](INFRASTRUCTURE.md)

</div>
