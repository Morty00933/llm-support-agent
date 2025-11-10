# LLM Support Agent

## Overview

LLM Support Agent is a local-first helpdesk stack that bundles a React single-page app, a FastAPI backend, Postgres with pgvector, Ollama for chat + embeddings, and Celery workers. All services are wired for multi-tenant scenarios via JWT (`/v1/auth/login`) and the `X-Tenant-Id` header.

The backend ships with a fully managed schema: Alembic migrations bootstrap the database, enable `pgcrypto`/`vector`, create all tenant/ticket/knowledge-base tables, and seed a default tenant (`id=1`, name `default`) with the demo user `user@example.com` / `secret`.

## Service topology

| Service | Purpose | Host mapping |
|---------|---------|--------------|
| ui      | Nginx + SPA + proxy     | 8080 → 80  |
| api     | FastAPI (uvicorn)       | 8000 → 8000 |
| db      | PostgreSQL + pgvector   | 5432 → 5432 |
| redis   | Redis for Celery        | 6379 → 6379 |
| ollama  | Ollama models           | 11434 → 11434 |
| worker  | Celery worker           | internal |

The UI proxies API calls to `http://api:8000/v1/*` and `/health`.

## Database migrations

Alembic revisions ship in `alembic/versions/`:

1. `0000_bootstrap.py` — installs `pgcrypto`, `vector`, creates `alembic_version` (VARCHAR(128)), and builds tenants, users, tickets, messages with proper defaults.
2. `0002_kb_chunks.py` — provisions the complete `kb_chunks` schema (`embedding_vector VECTOR(:EMBEDDING_DIM)`, JSONB metadata, hash uniqueness, IVFFLAT index) plus supporting indexes.
3. `0003_kb_metadata_and_external_refs.py` — idempotent column/table guards and SHA-256 backfill for existing chunks.
4. `0004_kb_vector_and_indexes.py` — ensures vector/archived columns and indexes exist when upgrading older installs.
5. `0005_seed_default_tenant.py` — inserts the demo tenant + user with a bcrypt hash for `secret`.
6. `0006_integration_sync_logs.py` — audit logs for external sync jobs.

Running containers or local processes now uses a shared entrypoint (`ops/entrypoint.sh`) that executes `alembic upgrade head` before launching uvicorn or Celery, keeping schemas current without manual intervention.

## Configuration defaults

`src/core/config.py` exposes sane defaults via Pydantic settings:

- `DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/app`
- `OLLAMA_BASE_URL=http://ollama:11434`
- `OLLAMA_MODEL_CHAT=qwen2.5:3b`
- `OLLAMA_MODEL_EMBED=nomic-embed-text-v1.5`
- `EMBEDDING_DIM=768`

Startup checks in `src/api/main.py` enforce `EMBEDDING_DIM > 0`, require non-empty model/base URL values, and perform a best-effort Ollama reachability probe (warning if unavailable). A dependency health endpoint (`GET /health/deps`) reports database and Ollama status, returning HTTP 503 on failures.

The shared embedding client (`src/services/embeddings.py`) now retries transient failures, validates vector length, and raises user-facing `EmbeddingServiceError`s so `/v1/kb/*` endpoints return informative 4xx responses instead of 500s.

## Quick start

```bash
# build and start all services
docker compose up -d

# verify health via the API proxy
curl -s http://127.0.0.1:8080/health
curl -s http://127.0.0.1:8080/health/deps | jq

# optional smoke test (requires python)
make smoke
```

The SPA lives at <http://localhost:8080>. Authenticated routes expect the seeded user (`user@example.com` / `secret`, tenant `1`).

### Smoke test

`make smoke` executes `scripts/smoke.py`, which performs the following against `http://localhost:8080`:

1. `GET /health`
2. `POST /v1/auth/login`
3. `POST /v1/kb/upsert` with two sample chunks
4. `POST /v1/kb/search`

Failures or non-200 responses abort the script with a non-zero exit code.

## UI proxy & environment

The SPA is served via `ui/nginx.conf`, forwarding:

```nginx
location /v1/ { proxy_pass http://api:8000/v1/; }
location /health { proxy_pass http://api:8000/health; }
```

Configure the frontend API base through `ui/.env` (template provided as `ui/.env.example`):

```
VITE_API_BASE_URL=http://localhost:8080
```

The Zustand store (`ui/src/store/auth.ts`) defaults to that base and normalises trailing slashes. Logging out resets the API base to the environment default.

## API reference cheat-sheet

All endpoints are under `http://localhost:8080/v1/*` unless stated otherwise.

| Purpose | Method | Path |
|---------|--------|------|
| Health (proxy) | GET | `/health` |
| Dependency health | GET | `/health/deps` |
| Metrics | GET | `/metrics` |
| Login | POST | `/v1/auth/login` |
| KB upsert | POST | `/v1/kb/upsert` |
| KB search | POST | `/v1/kb/search` |
| KB archive | POST | `/v1/kb/archive` |
| KB delete | POST | `/v1/kb/delete` |
| KB reindex | POST | `/v1/kb/reindex` |

### Bash / curl examples

```bash
BASE="http://127.0.0.1:8080"
TENANT=1
TOKEN=$(curl -s "$BASE/v1/auth/login" \
  -H 'Content-Type: application/json' \
  -d '{"email":"user@example.com","password":"secret","tenant":1}' | jq -r .access_token)

curl -s "$BASE/v1/kb/upsert" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Tenant-Id: $TENANT" \
  -H 'Content-Type: application/json' \
  -d '{"source":"docs","chunks":[{"content":"Reset your password via email."},{"content":"Contact support for MFA issues."}]}'

curl -s "$BASE/v1/kb/search" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Tenant-Id: $TENANT" \
  -H 'Content-Type: application/json' \
  -d '{"query":"password reset"}' | jq
```

### PowerShell 7 examples

```powershell
$Base = "http://127.0.0.1:8080"
$Tenant = 1

$login = Invoke-RestMethod -Uri "$Base/v1/auth/login" -Method Post -ContentType 'application/json' -Body '{"email":"user@example.com","password":"secret","tenant":1}'
$headers = @{ 'Authorization' = "Bearer $($login.access_token)"; 'X-Tenant-Id' = $Tenant; 'Content-Type' = 'application/json' }

Invoke-RestMethod -Uri "$Base/v1/kb/upsert" -Method Post -Headers $headers -Body '{"source":"docs","chunks":[{"content":"Reset your password via email."}]}'
Invoke-RestMethod -Uri "$Base/v1/kb/search" -Method Post -Headers $headers -Body '{"query":"password"}'
```

## Troubleshooting tips

- `Signature has expired` responses trigger a frontend reset; log in again to refresh credentials.
- `Embedding size mismatch` or `Ollama embeddings request failed` indicates either a misconfigured `EMBEDDING_DIM` or missing Ollama model; update `.env` or ensure the Ollama container has pulled `nomic-embed-text-v1.5`.
- `GET /health/deps` returning 503 lists `database_error` / `ollama_error` payloads to help diagnose connectivity.

## Tests

Run unit tests with `pytest`. The smoke test (`make smoke`) ensures a freshly started stack answers auth + KB flows end-to-end.
