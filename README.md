
# LLM Support Agent — Полный README

> **TL;DR**  
> Готовая локальная система поддержки с RAG: SPA (Nginx) → FastAPI API → Postgres/Redis → Ollama (LLM + эмбеддинги) → Celery worker.  
> Мультитенантность по `X-Tenant-Id` + JWT. Полный набор команд, схемы и примеры запросов ниже.

---

## Содержание
- [Обзор](#обзор)
- [Архитектура](#архитектура)
- [Сервисы и порты](#сервисы-и-порты)
- [Поток запроса (E2E)](#поток-запроса-e2e)
- [Установка и запуск](#установка-и-запуск)
  - [Быстрый старт](#быстрый-старт)
  - [Сборка UI](#сборка-ui)
  - [Модели Ollama](#модели-ollama)
  - [Миграции БД](#миграции-бд)
- [Мультиарендность (Tenant)](#мультиарендность-tenant)
  - [Создание арендатора (Tenant 2)](#создание-арендатора-tenant-2)
  - [Частые ошибки по Tenant](#частые-ошибки-по-tenant)
- [API](#api)
  - [Здоровье](#здоровье)
  - [Аутентификация](#аутентификация)
  - [База знаний (KB)](#база-знаний-kb)
  - [Тикеты и сообщения](#тикеты-и-сообщения)
  - [Агент (Support)](#агент-support)
- [Практические сценарии](#практические-сценарии)
  - [RAG-проверка на KB](#rag-проверка-на-kb)
  - [Диалог через Tickets](#диалог-через-tickets)
  - [Свободный вопрос агенту](#свободный-вопрос-агенту)
- [Клиенты и инструменты](#клиенты-и-инструменты)
  - [PowerShell 7 (Windows)](#powershell-7-windows)
  - [curl (bash / Git Bash / WSL)](#curl-bash--git-bash--wsl)
  - [Postman / REST Client](#postman--rest-client)
- [Траблшутинг](#траблшутинг)
- [Тестирование](#тестирование)
- [Безопасность и ограничения демо](#безопасность-и-ограничения-демо)
- [Как это работает внутри (детали реализации)](#как-это-работает-внутри-детали-реализации)
- [Чек-лист эксплуатации](#чек-лист-эксплуатации)

---

## Обзор

**LLM Support Agent** — это локально развёртываемый ассистент поддержки пользователей, который:
- хранит знания в Postgres (векторный поиск по эмбеддингам от Ollama),
- отвечает на вопросы через LLM (например, `llama3.1:8b`),
- ведёт тикеты с лентой сообщений,
- поддерживает **мультиарендность** (каждый запрос должен указывать `X-Tenant-Id`),
- отдает SPA через Nginx с реверс-прокси на API.

---

## Архитектура

. — Корень проекта
├─ alembic/ — миграции БД (Alembic)
│  ├─ env.py — настройка окружения Alembic
│  ├─ script.py.mako — шаблон миграций
│  └─ versions/ — версии миграций
│     ├─ 0001_init.py — инициализация схемы
│     └─ 0002_kb_chunks.py — таблица для кусочков KB
├─ migrations/ — заготовка/старые миграции
├─ nginx/ — конфигурация Nginx (reverse-proxy для API)
│  └─ nginx.conf
├─ ops/ — мониторинг и логи
│  ├─ loki-config.yaml — конфиг Loki для логов
│  └─ prometheus.yml — конфиг Prometheus для метрик
├─ src/ — **Backend (FastAPI + Celery)**
│  ├─ agent/ — логика LLM-агента
│  │  ├─ llm.py — работа с LLM
│  │  ├─ loop.py — цикл агента
│  │  ├─ policies.py — правила/политики
│  │  └─ tools.py — инструменты для агента
│  ├─ api/ — FastAPI-приложение
│  │  ├─ main.py — точка входа (ASGI-приложение)
│  │  ├─ deps.py — зависимости (сессия БД и т.п.)
│  │  ├─ middlewares.py — мидлвары (CORS, tenant, tracing)
│  │  ├─ telemetry.py — метрики и OpenTelemetry
│  │  └─ routers/ — эндпоинты
│  │     ├─ admin.py — административные
│  │     ├─ auth.py — аутентификация
│  │     ├─ kb.py — работа с knowledge base
│  │     ├─ support.py — сервисные
│  │     └─ tickets.py — тикеты
│  ├─ core/ — инфраструктура
│  │  ├─ celery_app.py — конфиг Celery
│  │  ├─ config.py — настройки (env)
│  │  ├─ db.py — база данных
│  │  ├─ logging.py — логирование
│  │  ├─ metrics.py — метрики
│  │  ├─ security.py — безопасность/JWT
│  │  ├─ rate_limit.py — ограничение запросов
│  │  └─ circuit_breaker.py — защита от сбоев
│  ├─ domain/ — модели и репозитории
│  │  ├─ models.py — ORM-модели
│  │  └─ repos.py — репозитории
│  ├─ schemas/ — Pydantic-схемы
│  │  ├─ auth.py — схемы аутентификации
│  │  ├─ kb.py — схемы KB
│  │  └─ tickets.py — схемы тикетов
│  ├─ services/ — бизнес-логика
│  │  ├─ embeddings.py — генерация эмбеддингов
│  │  ├─ knowledge.py — работа с KB
│  │  ├─ search.py — поиск
│  │  └─ integrations/ — интеграции
│  │     ├─ jira.py — клиент Jira
│  │     └─ zendesk.py — клиент Zendesk
│  └─ tasks/ — фоновые задачи Celery
│     └─ agent_tasks.py — задачи агента
├─ tests/ — тесты (пока заглушки)
│  ├─ test_auth.py — тесты аутентификации
│  ├─ test_tickets.py — тесты тикетов
│  └─ test_agent_integration.py — интеграция агента
├─ ui/ — **Frontend (Vite + React + TypeScript + Tailwind)**
│  ├─ Dockerfile — сборка фронтенда
│  ├─ nginx.conf — конфиг Nginx для статики
│  ├─ package.json — зависимости
│  ├─ vite.config.ts — конфиг сборщика Vite
│  └─ src/
│     ├─ main.tsx — точка входа React
│     ├─ router.tsx — маршруты
│     ├─ components/ — общие компоненты
│     │  ├─ Guard.tsx — защита роутов
│     │  └─ Layout.tsx — базовый шаблон
│     ├─ pages/ — страницы
│     │  ├─ Agent.tsx — управление агентом
│     │  ├─ KB.tsx — база знаний
│     │  ├─ Login.tsx — логин
│     │  ├─ Settings.tsx — настройки
│     │  └─ Tickets.tsx — тикеты
│     ├─ lib/ — утилиты
│     │  ├─ api.ts — клиент API
│     │  └─ queryClient.ts — React Query
│     └─ store/ — хранилище (zustand)
│        └─ auth.ts — состояние авторизации
├─ docker-compose.yml — compose для разработки
├─ docker-compose.prod.yml — compose для продакшена
├─ Dockerfile — сборка backend
├─ Makefile — команды для сборки/запуска
├─ .env / .env.example — переменные окружения
├─ pyproject.toml — конфигурация Python-пакета
├─ ops/prometheus.yml — мониторинг Prometheus
├─ ops/loki-config.yaml — конфиг Loki
└─ README.md — описание проекта (пустой)


**Ключевые моменты:**
- UI → Nginx (`/api/*` → `api:8000`, пробрасываем `Authorization` и др. заголовки).
- FastAPI даёт `/v1/*` ручки и использует Postgres + Ollama.
- Эмбеддинги создаются через модель `nomic-embed-text`, ответы — через `llama3.1:8b` (по умолчанию; можно поменять).
- Мультиарендность через заголовок `X-Tenant-Id` + JWT.

---

## Сервисы и порты

| Сервис  | Назначение                 | Порт (host→container) |
|---------|----------------------------|------------------------|
| ui      | Nginx + SPA + RP на API    | `8080 → 80`            |
| api     | FastAPI                    | `8000 → 8000`          |
| db      | PostgreSQL                 | `5432 → 5432`          |
| redis   | Redis (для Celery)         | `6379 → 6379`          |
| ollama  | Ollama (LLM+embeddings)    | `11434 → 11434`        |
| worker  | Celery worker (опционально)| — (внутрисетевой)      |

---

## Поток запроса (E2E)

1. Пользователь заходит на `http://localhost:8080` → SPA.
2. SPA обращается к API через `http://localhost:8080/api/...` (Nginx RP).
3. Авторизация: `POST /api/v1/auth/login` → получаем JWT.
4. Клиент в каждом запросе передаёт `Authorization: Bearer <token>` и `X-Tenant-Id: <id>`.
5. Для ответа агента:
   - KB: `upsert` → тексты превращаются в эмбеддинги (Ollama) и сохраняются в Postgres.
   - `search` → RAG-достраивание контекста по эмбеддингам.
   - LLM генерирует ответ по последнему user-сообщению тикета или свободному запросу.
6. Ответ возвращается клиенту; опционально сохраняется как сообщение тикета.

---

## Установка и запуск

### Быстрый старт

```bash
# 1) Запустить всё
docker compose up -d

# 2) Проверить API напрямую и через Nginx
curl -s http://127.0.0.1:8000/health
curl -s http://127.0.0.1:8080/api/health
```

> **Windows/PowerShell 7**: см. раздел ниже про `-NoProxy` и UTF‑8.

### Сборка UI

```bash
docker compose build ui
docker compose up -d --force-recreate --no-deps ui
# либо перезагрузить конфиг без пересборки
docker compose exec ui nginx -s reload
```

**Важно (Nginx):**
```nginx
location /api/ {
  proxy_pass http://api:8000/;
  proxy_set_header Host $host;
  proxy_set_header X-Real-IP $remote_addr;
  proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
  proxy_set_header X-Forwarded-Proto $scheme;
  proxy_set_header Authorization $http_authorization;  # обязательно!
  proxy_read_timeout 300;
}
```

### Модели Ollama

```bash
# убедиться, что контейнер ollama поднят
docker compose up -d ollama

# загрузить модели
docker compose exec ollama ollama pull llama3.1:8b
docker compose exec ollama ollama pull nomic-embed-text

# sanity-check эмбеддингов
docker compose exec ollama sh -lc 'printf "{\n  \"model\": \"nomic-embed-text\",\n  \"input\": \"hello\"\n}\n" \
  | ollama run nomic-embed-text'
```

### Миграции БД

```bash
# применить все миграции
docker compose run --rm api alembic upgrade head

# пример проверок
PG=$(docker compose ps -q db)
docker exec -it "$PG" psql -U postgres -d app -c "SELECT to_regclass('public.kb_chunks');"
docker exec -it "$PG" psql -U postgres -d app -c "TABLE tenants;"
```

---

## Мультиарендность (Tenant)

Каждый запрос к бизнес-ручкам требует **двух** вещей:
1) `Authorization: Bearer <jwt>` — токен из `/v1/auth/login` (в теле указываем `tenant`),
2) заголовок `X-Tenant-Id: <int>` — явный идентификатор арендатора.

Если `tenant_id` не существует в таблице `tenants`, то, например, `KB upsert` упадёт с
`ForeignKeyViolationError` (как в логах).

### Создание арендатора (Tenant 2)

Сейчас администратора для создания арендаторов в API **нет**, создаём напрямую в БД:

```bash
PG=$(docker compose ps -q db)

# создать арендатора с id=2
docker exec -it "$PG" psql -U postgres -d app -c \
  "INSERT INTO tenants (id, code, name) VALUES (2, 'acme', 'ACME Inc.') ON CONFLICT (id) DO NOTHING;"

# безопасно поправить sequence
docker exec -it "$PG" psql -U postgres -d app -c \
  "SELECT setval(pg_get_serial_sequence('tenants','id'), GREATEST((SELECT COALESCE(MAX(id),1) FROM tenants), 1));"
```

После этого можно логиниться с `tenant=2` и использовать `X-Tenant-Id: 2`.

### Частые ошибки по Tenant

- **Нет строки в `tenants`** → 500/IntegrityError при upsert в KB.  
  Решение: вставить запись в `tenants`, как выше.
- **`X-Tenant-Id` не соответствует токену** — соблюдайте консистентность: логинитесь с нужным tenant и передавайте тот же id в заголовке.
- **UI показывает чужие данные** — демо-аутентификация не делает реального разделения пользователей (см. ниже «Безопасность и ограничения»).

---

## API

### Здоровье

- `GET /health` — прямой API (порт 8000).
- `GET /api/health` — через Nginx (порт 8080).

### Аутентификация

> **Демо!** Любая почта/пароль принимаются, пароль **не** проверяется. Поликтика — демонстрационная.

- `POST /v1/auth/login`  
  **Body:**
  ```json
  { "email": "user@example.com", "password": "x", "tenant": 1 }
  ```
  **Response:**
  ```json
  { "access_token": "..." }
  ```

**Далее добавляйте заголовки:**
```
Authorization: Bearer <access_token>
X-Tenant-Id: 1
```

### База знаний (KB)

- `POST /v1/kb/upsert` — добавить/обновить кусочки знаний с авто-эмбеддингом.
  ```json
  {
    "source": "docs",
    "chunks": [
      { "content": "FAQ 1" },
      { "content": "FAQ 2" }
    ]
  }
  ```
  **Response:**
  ```json
  { "inserted": 2 }
  ```

- `POST /v1/kb/search` — векторный поиск.
  ```json
  { "query": "FAQ", "limit": 5 }
  ```
  **Response:**
  ```json
  {
    "results": [
      { "id": 9, "source": "docs", "chunk": "FAQ 1", "score": 0.3723 }
    ]
  }
  ```

### Тикеты и сообщения

- `POST /v1/tickets/` — создать тикет.
  ```json
  { "title": "Пароль — проверка" }
  ```
  **Response:** `{ "id": 26, "title": "...", "status": "open" }`

- `POST /v1/tickets/{ticket_id}/messages` — добавить сообщение.
  ```json
  { "role": "user", "content": "Как сменить пароль?" }
  ```
  **Response:** `{ "id": 21, "role": "user", "content": "..."} `

- `GET /v1/tickets/{ticket_id}/messages` — лента сообщений тикета.

> Агент в режиме тикета берёт **последнее user-сообщение** из ленты как вопрос.

### Агент (Support)

- `POST /v1/support/answer` — свободный вопрос (вне тикета).
  ```json
  { "query": "Как сменить пароль?", "kb_limit": 5, "temperature": 0.2 }
  ```
  **Response:**
  ```json
  {
    "reply": "...",
    "used_context": "- (source, score=...) chunk...",
    "kb_hits": [{ "id": 1, "source": "...", "chunk": "...", "score": 0.85 }],
    "escalated": false,
    "reason": "Direct answer generated"
  }
  ```

- `POST /v1/support/tickets/{ticket_id}/answer?save=true` — ответ по тикету + сохранить ответ в ленту.
  ```json
  { "query": "", "kb_limit": 5, "temperature": 0.2 }
  ```
  **Response:** как выше + `saved_message_id`.

---

## Практические сценарии

### RAG-проверка на KB

```powershell
# PowerShell 7
$Base = "http://127.0.0.1:8080/api"

# 1) логин
$resp  = Invoke-RestMethod -NoProxy -Method Post -Uri "$Base/v1/auth/login" -ContentType "application/json" -Body (@{ email="user@example.com"; password="x"; tenant=1 } | ConvertTo-Json)
$auth  = @{ "Authorization" = "Bearer " + $resp.access_token; "X-Tenant-Id" = "1" }

# 2) upsert знаний
$kbBody = @{
  source = "jump_v1"
  chunks = @(
    @{ content = "Как сделать прыжок. Шаг 1: Нажмите кнопку «Прыжок». Шаг 2: Удерживайте для высокого прыжка." },
    @{ content = "Прыжок выполняется клавишей Space. Двойное нажатие — двойной прыжок." }
  )
} | ConvertTo-Json -Depth 5

Invoke-RestMethod -NoProxy -Method Post -Uri "$Base/v1/kb/upsert" -Headers $auth -ContentType "application/json" -Body $kbBody

# 3) поиск
$searchBody = @{ query="Как сделать прыжок"; limit=5 } | ConvertTo-Json
Invoke-RestMethod -NoProxy -Method Post -Uri "$Base/v1/kb/search" -Headers $auth -ContentType "application/json" -Body $searchBody
```

### Диалог через Tickets

```powershell
# 1) создать тикет
$t = Invoke-RestMethod -NoProxy -Method Post -Uri "$Base/v1/tickets/" -Headers $auth -ContentType "application/json" -Body (@{ title="Прыжок — проверка" } | ConvertTo-Json)
$tid = $t.id

# 2) добавить user-сообщение (вопрос)
$msgBody = @{ role="user"; content="Как сделать прыжок" } | ConvertTo-Json
Invoke-RestMethod -NoProxy -Method Post -Uri "$Base/v1/tickets/$tid/messages" -Headers $auth -ContentType "application/json" -Body $msgBody

# 3) получить ответ агента (и сохранить его как сообщение)
$askBody = @{ query=""; kb_limit=5; temperature=0.2 } | ConvertTo-Json
Invoke-RestMethod -NoProxy -Method Post -Uri "$Base/v1/support/tickets/$tid/answer?save=true" -Headers $auth -ContentType "application/json" -Body $askBody

# 4) посмотреть ленту
Invoke-RestMethod -NoProxy -Method Get -Uri "$Base/v1/tickets/$tid/messages" -Headers $auth
```

### Свободный вопрос агенту

```powershell
$askBody = @{ query="Как сменить пароль?"; kb_limit=5; temperature=0.2 } | ConvertTo-Json
Invoke-RestMethod -NoProxy -Method Post -Uri "$Base/v1/support/answer" -Headers $auth -ContentType "application/json" -Body $askBody
```

---

## Клиенты и инструменты

### PowerShell 7 (Windows)

- Используйте **PowerShell 7+**, а не Windows PowerShell 5.1 (исправляет UTF‑8 и прокси-нюансы).
- Временно отключить прокси для локальных запросов:
  ```powershell
  $env:HTTP_PROXY=""
  $env:HTTPS_PROXY=""
  $env:NO_PROXY="localhost,127.0.0.1,::1"
  [System.Net.WebRequest]::DefaultWebProxy = New-Object System.Net.WebProxy
  ```
- Для отправки русского текста **не указывайте вручную** `; charset=utf-8` в Content-Type — PS7 делает верно сам.
- Если всё же нужен файл с UTF-8 без BOM:
  ```powershell
  $json = @{ role="user"; content="Как сделать прыжок" } | ConvertTo-Json -Depth 5
  [IO.File]::WriteAllText("$pwd\msg.json", $json, (New-Object System.Text.UTF8Encoding $false))
  Invoke-RestMethod -NoProxy -Method Post -Uri "$Base/v1/tickets/$tid/messages" -Headers $auth -ContentType "application/json" -InFile "$pwd\msg.json"
  ```

### curl (bash / Git Bash / WSL)

```bash
BASE="http://127.0.0.1:8080/api"
TOKEN=$(curl -s -X POST "$BASE/v1/auth/login" -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"x","tenant":1}' | jq -r .access_token)

curl -s -X POST "$BASE/v1/kb/upsert" \
  -H "Authorization: Bearer $TOKEN" -H "X-Tenant-Id: 1" -H "Content-Type: application/json" \
  -d '{"source":"docs","chunks":[{"content":"FAQ 1"},{"content":"FAQ 2"}]}'
```

### Postman / REST Client
Импортируйте ручки вручную или используйте `/docs` (Swagger UI).  
> JSON OpenAPI может быть по пути `/openapi.json` (через Nginx: `/api/openapi.json`).

---

## Траблшутинг

- **502 Bad Gateway через `/api/*`**, при этом `:8000/health` ок  
  — Проверьте, что Nginx в контейнере `ui` доступен и видит `api` по сети Docker.  
  — Часто виноваты системные прокси клиента: используйте `-NoProxy` в PS7.
- **`Invalid auth scheme` / `Authorization header required`**  
  — Убедитесь, что в Nginx добавлен `proxy_set_header Authorization $http_authorization;`  
  — И что вы реально передаёте `Authorization: Bearer ...` (не пустой).
- **`ForeignKeyViolationError` при `kb/upsert`**  
  — Создайте нужный tenant в БД (см. раздел выше).
- **Кириллица превратилась в `???`**  
  — Пользуйтесь **PowerShell 7**, а не 5.1. Не добавляйте вручную `; charset=utf-8`.
- **UI: Failed to fetch**  
  — Обычно из‑за отсутствия JWT-прокидывания через Nginx или CORS/прокси клиента.

---

## Тестирование

- Бэкенд (из контейнера api):
  ```bash
  docker compose run --rm api pytest -q
  ```
  Рекомендуемые группы тестов (примерная структура):
  - `tests/test_auth.py` — логин, проверка заголовков.
  - `tests/test_kb.py` — upsert/search, проверка ранжирования.
  - `tests/test_tenants.py` — отсутствие/наличие tenant, негативные кейсы.
  - `tests/test_tickets.py` — создание тикета, лента сообщений.
  - `tests/test_agent.py` — ответ по тикету и freeform, mock Ollama.
- Линтеры/типизация (если подключены):
  ```bash
  docker compose run --rm api ruff .
  docker compose run --rm api mypy src
  ```

---

## Безопасность и ограничения демо

- **Логин принимает любые e‑mail/пароль** — это **демо**. Для продакшена интегрируйте реальную аутентификацию.
- **Мультиарендность на совести клиента** — сервер доверяет `X-Tenant-Id`. Для реального разделения добавляйте users/roles привязанные к tenant.
- **LLM‑ответы** — вероятностные; добавляйте guardrails и/или модерацию.
- **Ollama модели** — локальные, занимают место на диске, проверьте ресурсы хоста.

---

## Как это работает внутри (детали реализации)

- **Маршруты FastAPI**
  - `/health` — ping.
  - `/v1/auth/login` — выдает JWT (демо). Токен потом проверяется middleware.
  - `/v1/kb/*` — upsert/search:
    - upsert: для каждого `chunks[].content` → `POST /api/embeddings` (Ollama, `nomic-embed-text`) → сохраняется `embedding` (+ текст) в `kb_chunks` с `tenant_id` и `source`.
    - search: такая же эмбеддинг‑функция на запрос → поиск ближайших кусочков (через SQL/функции сравнения).
  - `/v1/tickets/*` — тикеты и их сообщения (таблицы `tickets`, `messages`).
  - `/v1/support/*` — агент:
    - **freeform**: берёт `query` из тела, делает RAG (`kb_limit`) и вызывает LLM (`llama3.1:8b`) с подготовленным промптом.
    - **tickets/{id}/answer**: достаёт **последнее user‑сообщение** из ленты тикета и делает то же; если `save=true`, сохраняет ответ как `role="agent"` в `messages`.
- **Middleware**:
  - Проверка `Authorization` на всех бизнес‑ручках, логика извлечения tenant из заголовка, CORS.
- **Хранилище**:
  - `tenants(id, code, name)` — арендаторы.
  - `kb_chunks(id, tenant_id, source, chunk, embedding BYTEA, ...)`.
  - `tickets(id, tenant_id, title, status, ...)`.
  - `messages(id, ticket_id, role, content, ...)`.
- **Worker** (Celery) — резерв на фоновую обработку (например, массивный импорт KB), брокер Redis.

---

## Чек-лист эксплуатации

- [ ] Скачены модели Ollama: `llama3.1:8b`, `nomic-embed-text`  
- [ ] Применены миграции Alembic  
- [ ] Есть запись в `tenants` (минимум id=1)  
- [ ] Nginx пробрасывает `Authorization`  
- [ ] В клиенте есть `Authorization: Bearer ...` и `X-Tenant-Id`  
- [ ] PowerShell 7, отключён прокси/включён `-NoProxy` при локальной отладке  
- [ ] KB наполнена; по запросам из тикетов ответы приходят корректно

---

## Полезные команды (сборник)

```bash
# Статусы
docker compose ps
docker compose logs -f api
docker compose logs -f ui
docker compose logs -f ollama

# Пересобрать только UI
docker compose build ui && docker compose up -d --force-recreate --no-deps ui

# Перезапуск API+UI
docker compose up -d --force-recreate ui api

# Проверка доступности API из контейнера UI
docker compose exec ui sh -lc "wget -qO- http://api:8000/health || echo FAIL"

# Зайти в psql
PG=$(docker compose ps -q db)
docker exec -it "$PG" psql -U postgres -d app

# Провести миграции
docker compose run --rm api alembic upgrade head

# Подкачать модели
docker compose exec ollama ollama pull llama3.1:8b
docker compose exec ollama ollama pull nomic-embed-text
```

---

**Готово.** Этот README отражает реальное состояние проекта (по переписке и проверке команд): архитектура, ручки, команды, типовые проблемы и их решения. Если нужно — добавлю диаграммы в PNG/SVG и Makefile/Taskfile для одношагового запуска.
