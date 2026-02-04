# API Reference

Полная документация REST API для LLM Support Agent.

## Базовая информация

| Параметр | Значение |
|----------|----------|
| Base URL | `http://localhost:8000/v1` |
| Формат | JSON |
| Авторизация | Bearer Token (JWT) |
| Content-Type | `application/json` |

## Аутентификация

Все эндпоинты (кроме `/auth/register` и `/auth/login`) требуют JWT токен в заголовке:

```
Authorization: Bearer <access_token>
```

---

## 🔐 Auth API

### Регистрация пользователя

```http
POST /v1/auth/register
```

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securePassword123",
  "full_name": "John Doe",
  "tenant_id": 1
}
```

**Response:** `201 Created`
```json
{
  "id": 1,
  "email": "user@example.com",
  "full_name": "John Doe",
  "tenant_id": 1,
  "role": "user",
  "is_active": true,
  "created_at": "2024-01-15T10:30:00Z"
}
```

**Коды ошибок:**
| Код | Описание |
|-----|----------|
| 400 | Слабый пароль |
| 409 | Email уже зарегистрирован |

---

### Вход (OAuth2 форма)

```http
POST /v1/auth/login
Content-Type: application/x-www-form-urlencoded
```

**Request Body:**
```
username=user@example.com&password=securePassword123
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

---

### Вход (JSON)

```http
POST /v1/auth/login/json
```

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securePassword123",
  "tenant_id": 1
}
```

**Response:** Аналогично OAuth2 форме

---

### Обновление токена

```http
POST /v1/auth/refresh
```

**Request Body:**
```json
{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

---

### Получение профиля

```http
GET /v1/auth/me
Authorization: Bearer <token>
```

**Response:** `200 OK`
```json
{
  "id": 1,
  "email": "user@example.com",
  "full_name": "John Doe",
  "tenant_id": 1,
  "role": "user",
  "is_active": true,
  "created_at": "2024-01-15T10:30:00Z"
}
```

---

### Обновление профиля

```http
PATCH /v1/auth/me
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "full_name": "John Smith"
}
```

---

### Смена пароля

```http
POST /v1/auth/change-password
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "current_password": "oldPassword123",
  "new_password": "newSecurePassword456"
}
```

---

## 🎫 Tickets API

### Список тикетов

```http
GET /v1/tickets?status=open&skip=0&limit=100
Authorization: Bearer <token>
```

**Query параметры:**
| Параметр | Тип | Описание |
|----------|-----|----------|
| status | string | Фильтр по статусу |
| skip | int | Пропустить N записей (пагинация) |
| limit | int | Лимит записей (1-1000) |

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "tenant_id": 1,
    "title": "Cannot login to my account",
    "description": "I'm getting an error when...",
    "status": "open",
    "priority": "high",
    "source": "web",
    "assigned_to": null,
    "created_by_id": 5,
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  }
]
```

---

### Создание тикета

```http
POST /v1/tickets
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "title": "Cannot login to my account",
  "description": "I'm getting error code 500 when trying to login",
  "priority": "high",
  "source": "web",
  "auto_respond": true
}
```

**Параметры:**
| Поле | Тип | Обязательно | Описание |
|------|-----|-------------|----------|
| title | string | ✅ | Заголовок (1-255 символов) |
| description | string | ❌ | Описание проблемы |
| priority | string | ❌ | `critical`, `high`, `medium`, `low` |
| source | string | ❌ | Источник: `web`, `email`, `api` |
| auto_respond | bool | ❌ | Автоответ AI (default: true) |

**Response:** `201 Created`

---

### Получение тикета

```http
GET /v1/tickets/{ticket_id}
Authorization: Bearer <token>
```

**Доступ:** Создатель, назначенный агент, или admin

---

### Обновление тикета

```http
PATCH /v1/tickets/{ticket_id}
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "status": "in_progress",
  "assigned_to": 3,
  "priority": "critical"
}
```

**Статусы тикетов:**
```
open → in_progress → pending_customer → pending_agent → escalated → resolved → closed
                                                                          ↓
                                                                      reopened → open
```

---

### Удаление тикета

```http
DELETE /v1/tickets/{ticket_id}
Authorization: Bearer <token>
```

**Требуется:** `admin` роль

---

### Сообщения тикета

```http
GET /v1/tickets/{ticket_id}/messages?skip=0&limit=100
Authorization: Bearer <token>
```

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "ticket_id": 1,
    "role": "user",
    "content": "I cannot login to my account",
    "created_at": "2024-01-15T10:30:00Z"
  },
  {
    "id": 2,
    "ticket_id": 1,
    "role": "assistant",
    "content": "I understand you're having login issues...",
    "created_at": "2024-01-15T10:30:05Z"
  }
]
```

---

### Добавление сообщения

```http
POST /v1/tickets/{ticket_id}/messages
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "content": "I've tried resetting my password but still can't login",
  "role": "user",
  "auto_respond": true
}
```

---

## 🤖 Agent API

### Проверка здоровья AI

```http
GET /v1/agent/health
Authorization: Bearer <token>
```

**Response:** `200 OK`
```json
{
  "ollama_available": true,
  "chat_model": "llama3.2",
  "embed_model": "nomic-embed-text",
  "models_loaded": ["llama3.2:latest", "nomic-embed-text:latest"]
}
```

---

### Генерация ответа на тикет

```http
POST /v1/agent/respond/{ticket_id}
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "save_response": true,
  "max_context": 5
}
```

**Response:** `200 OK`
```json
{
  "content": "Based on your description, here's what you can try...",
  "needs_escalation": false,
  "escalation_reason": null,
  "context_used": [
    {
      "id": 15,
      "source": "faq.md",
      "chunk": "To reset your password...",
      "score": 0.89
    }
  ],
  "model": "llama3.2"
}
```

---

### Свободный вопрос (Playground)

```http
POST /v1/agent/ask
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "question": "How do I reset my password?",
  "max_context": 5
}
```

---

### Автоответ в фоне

```http
POST /v1/agent/auto-respond/{ticket_id}
Authorization: Bearer <token>
```

**Response:** `202 Accepted`
```json
{
  "status": "accepted",
  "message": "Auto-response triggered for ticket 123",
  "ticket_id": 123
}
```

---

## 📚 Knowledge Base API

### Список чанков

```http
GET /v1/kb/chunks?skip=0&limit=100
Authorization: Bearer <token>
```

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "source": "faq.md",
    "chunk": "To reset your password, go to Settings > Security...",
    "version": 1,
    "is_current": true
  }
]
```

---

### Загрузка чанков

```http
POST /v1/kb/chunks
Authorization: Bearer <token>
```

**Требуется:** `agent` или `admin` роль

**Request Body:**
```json
{
  "source": "product-docs.md",
  "chunks": [
    {
      "content": "Our product supports multiple languages...",
      "metadata": {"section": "features", "page": 1}
    },
    {
      "content": "To configure notifications, navigate to...",
      "metadata": {"section": "settings", "page": 5}
    }
  ]
}
```

**Response:** `201 Created`
```json
{
  "created": 2,
  "updated": 0,
  "skipped": 0,
  "embeddings": {
    "success": 2,
    "failed": 0
  }
}
```

---

### Семантический поиск

```http
POST /v1/kb/search
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "query": "how to reset password",
  "limit": 5
}
```

**Response:** `200 OK`
```json
[
  {
    "id": 15,
    "source": "faq.md",
    "chunk": "To reset your password, go to Settings > Security > Reset Password...",
    "score": 0.92
  },
  {
    "id": 23,
    "source": "troubleshooting.md",
    "chunk": "If you've forgotten your password, you can recover it via email...",
    "score": 0.85
  }
]
```

---

### Удаление источника

```http
DELETE /v1/kb/sources/{source}
Authorization: Bearer <token>
```

**Требуется:** `admin` роль

**Response:** `200 OK`
```json
{
  "deleted": 15,
  "source": "old-docs.md"
}
```

---

### Переиндексация

```http
POST /v1/kb/reindex?source=docs.md
Authorization: Bearer <token>
```

**Требуется:** `agent` или `admin` роль

**Response:** `200 OK`
```json
{
  "status": "success",
  "success": 50,
  "failed": 0
}
```

---

### Загрузка документа

```http
POST /v1/kb/upload?source=manual
Authorization: Bearer <token>
Content-Type: multipart/form-data
```

**Требуется:** `admin` роль

**Поддерживаемые форматы:** `.txt`, `.md`, `.pdf`, `.docx`

**Response:** `200 OK`
```json
{
  "filename": "user-manual.pdf",
  "source": "manual",
  "chunks_processed": 45,
  "validation": {
    "size_bytes": 1048576,
    "mime_type": "application/pdf",
    "sha256": "abc123..."
  },
  "created": 45,
  "updated": 0,
  "embeddings": {
    "success": 45,
    "failed": 0
  }
}
```

---

## 👥 Users API

### Список пользователей

```http
GET /v1/users?skip=0&limit=100
Authorization: Bearer <token>
```

**Требуется:** `admin` роль

---

### Создание пользователя

```http
POST /v1/users
Authorization: Bearer <token>
```

**Требуется:** `admin` роль

**Request Body:**
```json
{
  "email": "agent@example.com",
  "password": "securePassword123",
  "full_name": "Support Agent",
  "role": "agent"
}
```

**Доступные роли для создания:** `user`, `agent`, `admin`

> ⚠️ `superadmin` можно установить только через базу данных

---

### Получение пользователя

```http
GET /v1/users/{user_id}
Authorization: Bearer <token>
```

**Требуется:** `admin` роль

---

### Обновление пользователя

```http
PATCH /v1/users/{user_id}
Authorization: Bearer <token>
```

**Требуется:** `admin` роль

**Request Body:**
```json
{
  "full_name": "Updated Name",
  "is_active": false
}
```

---

### Изменение роли

```http
PATCH /v1/users/{user_id}/role
Authorization: Bearer <token>
```

**Требуется:** `admin` роль

**Request Body:**
```json
{
  "role": "agent"
}
```

**Ограничения:**
- Нельзя изменить свою роль
- Нельзя установить `superadmin` через API
- Admin не может понизить другого admin

---

### Деактивация пользователя

```http
DELETE /v1/users/{user_id}
Authorization: Bearer <token>
```

**Требуется:** `admin` роль

Soft delete — устанавливает `is_active=false`

---

## 🏢 Tenants API

### Список тенантов

```http
GET /v1/tenants
Authorization: Bearer <token>
```

**Требуется:** `admin` роль

---

### Текущий тенант

```http
GET /v1/tenants/current
Authorization: Bearer <token>
```

---

### Статистика тенанта

```http
GET /v1/tenants/current/stats
Authorization: Bearer <token>
```

**Response:** `200 OK`
```json
{
  "tickets_by_status": {
    "open": 15,
    "in_progress": 8,
    "resolved": 45,
    "closed": 120
  },
  "total_tickets": 188,
  "total_users": 25,
  "total_kb_chunks": 350
}
```

---

### Создание тенанта

```http
POST /v1/tenants
Authorization: Bearer <token>
```

**Требуется:** `admin` роль

**Request Body:**
```json
{
  "name": "Acme Corporation",
  "slug": "acme"
}
```

---

## Коды ошибок

### HTTP статусы

| Код | Описание |
|-----|----------|
| 200 | Успешный запрос |
| 201 | Ресурс создан |
| 202 | Запрос принят (async) |
| 204 | Успех без контента |
| 400 | Некорректный запрос |
| 401 | Не авторизован |
| 403 | Доступ запрещён |
| 404 | Не найдено |
| 409 | Конфликт (duplicate) |
| 422 | Ошибка валидации |
| 500 | Внутренняя ошибка |
| 503 | Сервис недоступен |

### Формат ошибок

```json
{
  "detail": "User not found"
}
```

Или расширенный формат:
```json
{
  "type": "validation_error",
  "title": "Validation Error",
  "status": 422,
  "detail": "Request validation failed",
  "errors": [
    {"field": "email", "message": "Invalid email format"},
    {"field": "password", "message": "Password too short"}
  ]
}
```

---

## Матрица доступа по ролям

| Endpoint | user | agent | admin | superadmin |
|----------|------|-------|-------|------------|
| **Auth** |
| POST /auth/register | ✅ | ✅ | ✅ | ✅ |
| POST /auth/login | ✅ | ✅ | ✅ | ✅ |
| GET /auth/me | ✅ | ✅ | ✅ | ✅ |
| **Tickets** |
| GET /tickets | ✅ own | ✅ all | ✅ all | ✅ all |
| POST /tickets | ✅ | ✅ | ✅ | ✅ |
| PATCH /tickets/{id} | ✅ own | ✅ all | ✅ all | ✅ all |
| DELETE /tickets/{id} | ❌ | ❌ | ✅ | ✅ |
| **Knowledge Base** |
| GET /kb/chunks | ✅ | ✅ | ✅ | ✅ |
| POST /kb/search | ✅ | ✅ | ✅ | ✅ |
| POST /kb/chunks | ❌ | ✅ | ✅ | ✅ |
| POST /kb/reindex | ❌ | ✅ | ✅ | ✅ |
| POST /kb/upload | ❌ | ❌ | ✅ | ✅ |
| DELETE /kb/sources/{s} | ❌ | ❌ | ✅ | ✅ |
| **Users** |
| GET /users | ❌ | ❌ | ✅ | ✅ |
| POST /users | ❌ | ❌ | ✅ | ✅ |
| PATCH /users/{id}/role | ❌ | ❌ | ✅ | ✅ |
| **Tenants** |
| GET /tenants/current | ✅ | ✅ | ✅ | ✅ |
| GET /tenants | ❌ | ❌ | ✅ | ✅ |
| POST /tenants | ❌ | ❌ | ✅ | ✅ |

---

## Примеры использования

### cURL

```bash
# Регистрация
curl -X POST http://localhost:8000/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"secure123","full_name":"John"}'

# Логин
curl -X POST http://localhost:8000/v1/auth/login/json \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"secure123"}'

# Создание тикета
curl -X POST http://localhost:8000/v1/tickets \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"Help needed","description":"Cannot login"}'

# Поиск в KB
curl -X POST http://localhost:8000/v1/kb/search \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"reset password","limit":5}'
```

### Python

```python
import httpx

BASE_URL = "http://localhost:8000/v1"

async def main():
    async with httpx.AsyncClient() as client:
        # Login
        resp = await client.post(f"{BASE_URL}/auth/login/json", json={
            "email": "user@example.com",
            "password": "secure123"
        })
        token = resp.json()["access_token"]

        headers = {"Authorization": f"Bearer {token}"}

        # Create ticket
        resp = await client.post(f"{BASE_URL}/tickets", headers=headers, json={
            "title": "Help needed",
            "description": "I cannot login to my account"
        })
        ticket = resp.json()

        # Search KB
        resp = await client.post(f"{BASE_URL}/kb/search", headers=headers, json={
            "query": "password reset",
            "limit": 5
        })
        results = resp.json()
```

### JavaScript/TypeScript

```typescript
const BASE_URL = 'http://localhost:8000/v1';

async function main() {
  // Login
  const loginResp = await fetch(`${BASE_URL}/auth/login/json`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      email: 'user@example.com',
      password: 'secure123'
    })
  });
  const { access_token } = await loginResp.json();

  const headers = {
    'Authorization': `Bearer ${access_token}`,
    'Content-Type': 'application/json'
  };

  // Create ticket with auto-response
  const ticketResp = await fetch(`${BASE_URL}/tickets`, {
    method: 'POST',
    headers,
    body: JSON.stringify({
      title: 'Help needed',
      description: 'Cannot access my account',
      auto_respond: true
    })
  });
  const ticket = await ticketResp.json();

  // Get AI response
  const agentResp = await fetch(`${BASE_URL}/agent/respond/${ticket.id}`, {
    method: 'POST',
    headers,
    body: JSON.stringify({ save_response: true })
  });
  const response = await agentResp.json();
}
```

---

## Rate Limiting

В текущей версии rate limiting не реализован. Рекомендации:

- Для production используйте reverse proxy (nginx, traefik) с rate limiting
- Рекомендуемые лимиты:
  - Auth endpoints: 5 req/min
  - Agent endpoints: 10 req/min
  - Other endpoints: 100 req/min

---

## WebSocket API

```
ws://localhost:8000/v1/ws/{ticket_id}
```

Для real-time обновлений тикетов. Требует JWT токен в query параметре:

```
ws://localhost:8000/v1/ws/123?token=<access_token>
```

**События:**
```json
{"type": "message", "data": {"id": 1, "content": "...", "role": "assistant"}}
{"type": "status_change", "data": {"status": "in_progress"}}
{"type": "escalation", "data": {"reason": "User requested human agent"}}
```
