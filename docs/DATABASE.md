# Database Schema Documentation

## Overview

The system uses PostgreSQL with pgvector extension for semantic search capabilities.

## Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              ENTITY RELATIONSHIP DIAGRAM                                 │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                          │
│   ┌───────────────────┐                                                                 │
│   │      tenants      │                                                                 │
│   ├───────────────────┤                                                                 │
│   │ PK id             │                                                                 │
│   │    name           │                                                                 │
│   │    slug           │                                                                 │
│   │    is_active      │                                                                 │
│   │    created_at     │                                                                 │
│   │    updated_at     │                                                                 │
│   └─────────┬─────────┘                                                                 │
│             │                                                                            │
│             │ 1:N                                                                        │
│             │                                                                            │
│   ┌─────────┴─────────────────────────────────────────────────────────┐                │
│   │                              │                                     │                │
│   ▼                              ▼                                     ▼                │
│   ┌───────────────────┐   ┌───────────────────┐              ┌───────────────────┐     │
│   │       users       │   │      tickets      │              │     kb_chunks     │     │
│   ├───────────────────┤   ├───────────────────┤              ├───────────────────┤     │
│   │ PK id             │   │ PK id             │              │ PK id             │     │
│   │ FK tenant_id  ────┼───│ FK tenant_id  ────┼──────────────│ FK tenant_id      │     │
│   │    email          │   │    title          │              │    source         │     │
│   │    hashed_password│   │    description    │              │    chunk          │     │
│   │    full_name      │   │    status         │              │    chunk_hash     │     │
│   │    role           │   │    priority       │              │    embedding_vec  │     │
│   │    is_active      │   │    source         │              │    metadata_json  │     │
│   │    created_at     │   │ FK assigned_to ───┼──┐           │    version        │     │
│   │    updated_at     │   │ FK created_by_id ─┼──┼──┐        │    is_current     │     │
│   └─────────┬─────────┘   │    metadata_json  │  │  │        │    created_at     │     │
│             │             │    created_at     │  │  │        │    updated_at     │     │
│             │             │    updated_at     │  │  │        │    archived_at    │     │
│             │             └─────────┬─────────┘  │  │        └───────────────────┘     │
│             │                       │            │  │                                   │
│             │ 1:N                   │ 1:N        │  │                                   │
│             │                       │            │  │                                   │
│             │                       ▼            │  │                                   │
│             │             ┌───────────────────┐  │  │                                   │
│             │             │     messages      │  │  │                                   │
│             │             ├───────────────────┤  │  │                                   │
│             │             │ PK id             │  │  │                                   │
│             │             │ FK ticket_id  ────┼──┘  │                                   │
│             │             │    role           │     │                                   │
│             │             │    content        │     │                                   │
│             │             │    metadata_json  │     │                                   │
│             │             │    created_at     │     │                                   │
│             │             └───────────────────┘     │                                   │
│             │                                       │                                   │
│             └───────────────────────────────────────┘                                   │
│                                                                                          │
│   ┌───────────────────┐              ┌───────────────────┐                              │
│   │ticket_external_refs│              │integration_sync_  │                              │
│   ├───────────────────┤              │      logs         │                              │
│   │ PK id             │              ├───────────────────┤                              │
│   │ FK tenant_id      │              │ PK id             │                              │
│   │ FK ticket_id      │              │ FK tenant_id      │                              │
│   │    system         │              │    system         │                              │
│   │    external_id    │              │    direction      │                              │
│   │    external_url   │              │    status         │                              │
│   │    metadata_json  │              │    records_proc   │                              │
│   │    created_at     │              │    error_message  │                              │
│   │    updated_at     │              │    started_at     │                              │
│   └───────────────────┘              │    completed_at   │                              │
│                                      │    metadata_json  │                              │
│                                      └───────────────────┘                              │
│                                                                                          │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

## Table Definitions

### tenants

Multi-tenant organization container.

```sql
CREATE TABLE tenants (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(255) NOT NULL UNIQUE,
    slug            VARCHAR(64) UNIQUE,
    is_active       BOOLEAN DEFAULT TRUE NOT NULL,
    created_at      TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at      TIMESTAMPTZ DEFAULT NOW() NOT NULL
);
```

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PRIMARY KEY | Auto-increment ID |
| name | VARCHAR(255) | NOT NULL, UNIQUE | Organization name |
| slug | VARCHAR(64) | UNIQUE | URL-friendly identifier |
| is_active | BOOLEAN | DEFAULT TRUE | Tenant status |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | Creation timestamp |
| updated_at | TIMESTAMPTZ | DEFAULT NOW() | Last update timestamp |

---

### users

System users with role-based access.

```sql
CREATE TABLE users (
    id                  SERIAL PRIMARY KEY,
    tenant_id           INTEGER NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    email               VARCHAR(255) NOT NULL,
    hashed_password     VARCHAR(255) NOT NULL,
    full_name           VARCHAR(255),
    role                VARCHAR(32) DEFAULT 'user' NOT NULL,
    is_active           BOOLEAN DEFAULT TRUE NOT NULL,
    created_at          TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at          TIMESTAMPTZ DEFAULT NOW() NOT NULL,

    UNIQUE(tenant_id, email)
);

CREATE INDEX ix_users_tenant_email ON users(tenant_id, email);
CREATE INDEX ix_users_email ON users(email);
```

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PRIMARY KEY | Auto-increment ID |
| tenant_id | INTEGER | FK → tenants(id) | Organization reference |
| email | VARCHAR(255) | NOT NULL | User email (unique per tenant) |
| hashed_password | VARCHAR(255) | NOT NULL | Bcrypt password hash |
| full_name | VARCHAR(255) | | Display name |
| role | VARCHAR(32) | DEFAULT 'user' | user/agent/admin/superadmin |
| is_active | BOOLEAN | DEFAULT TRUE | Account status |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | Registration timestamp |
| updated_at | TIMESTAMPTZ | DEFAULT NOW() | Last update timestamp |

**Roles:**
- `user` - Regular user, can create/view own tickets
- `agent` - Support agent, can view/update all tickets
- `admin` - Administrator, full tenant management
- `superadmin` - System admin, cross-tenant access

---

### tickets

Support tickets with status tracking.

```sql
CREATE TABLE tickets (
    id              SERIAL PRIMARY KEY,
    tenant_id       INTEGER NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    title           VARCHAR(255) NOT NULL,
    description     TEXT,
    status          VARCHAR(32) DEFAULT 'open' NOT NULL,
    priority        VARCHAR(32) DEFAULT 'medium' NOT NULL,
    source          VARCHAR(64),
    assigned_to     INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_by_id   INTEGER REFERENCES users(id) ON DELETE SET NULL,
    metadata_json   JSONB,
    created_at      TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at      TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE INDEX ix_tickets_tenant ON tickets(tenant_id);
CREATE INDEX ix_tickets_status ON tickets(status);
CREATE INDEX ix_tickets_tenant_status ON tickets(tenant_id, status);
CREATE INDEX ix_tickets_updated_at ON tickets(updated_at);
```

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PRIMARY KEY | Auto-increment ID |
| tenant_id | INTEGER | FK → tenants(id) | Organization reference |
| title | VARCHAR(255) | NOT NULL | Ticket subject |
| description | TEXT | | Detailed description |
| status | VARCHAR(32) | DEFAULT 'open' | Current status |
| priority | VARCHAR(32) | DEFAULT 'medium' | Priority level |
| source | VARCHAR(64) | | Origin (web/email/api) |
| assigned_to | INTEGER | FK → users(id) | Assigned agent |
| created_by_id | INTEGER | FK → users(id) | Ticket creator |
| metadata_json | JSONB | | Additional metadata |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | Creation timestamp |
| updated_at | TIMESTAMPTZ | DEFAULT NOW() | Last update timestamp |

**Status Values:**
```
┌─────────┐     ┌─────────────┐     ┌──────────────────┐     ┌──────────┐
│  open   │────►│ in_progress │────►│ pending_customer │────►│ resolved │
└─────────┘     └─────────────┘     └──────────────────┘     └──────────┘
     │                │                      │                     │
     │                │                      │                     │
     │                ▼                      │                     ▼
     │          ┌───────────┐               │               ┌──────────┐
     │          │ escalated │◄──────────────┘               │  closed  │
     │          └───────────┘                               └──────────┘
     │                │                                           ▲
     │                ▼                                           │
     │          ┌─────────────┐                                   │
     └─────────►│  reopened   │───────────────────────────────────┘
                └─────────────┘
```

**Priority Values:** `low`, `medium`, `high`, `urgent`

---

### messages

Conversation messages within tickets.

```sql
CREATE TABLE messages (
    id              SERIAL PRIMARY KEY,
    ticket_id       INTEGER NOT NULL REFERENCES tickets(id) ON DELETE CASCADE,
    role            VARCHAR(32) NOT NULL,
    content         TEXT NOT NULL,
    metadata_json   JSONB,
    created_at      TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE INDEX ix_messages_ticket_id ON messages(ticket_id);
CREATE INDEX ix_messages_created_at ON messages(created_at);
```

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PRIMARY KEY | Auto-increment ID |
| ticket_id | INTEGER | FK → tickets(id) | Parent ticket |
| role | VARCHAR(32) | NOT NULL | user/assistant/system |
| content | TEXT | NOT NULL | Message content |
| metadata_json | JSONB | | AI metadata (model, tokens, etc.) |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | Message timestamp |

**Role Values:**
- `user` - Customer message
- `assistant` - AI-generated response
- `system` - System notification

---

### kb_chunks

Knowledge base chunks with vector embeddings for semantic search.

```sql
CREATE TABLE kb_chunks (
    id              SERIAL PRIMARY KEY,
    tenant_id       INTEGER NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    source          VARCHAR(255) NOT NULL,
    chunk           TEXT NOT NULL,
    chunk_hash      VARCHAR(64) NOT NULL,
    embedding_vector VECTOR(768),
    metadata_json   JSONB,
    version         INTEGER DEFAULT 1 NOT NULL,
    is_current      BOOLEAN DEFAULT TRUE NOT NULL,
    created_at      TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at      TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    archived_at     TIMESTAMPTZ,

    UNIQUE(tenant_id, chunk_hash)
);

CREATE INDEX ix_kb_tenant_source ON kb_chunks(tenant_id, source);
CREATE INDEX ix_kb_embedding ON kb_chunks
    USING ivfflat (embedding_vector vector_cosine_ops)
    WITH (lists = 100);
```

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PRIMARY KEY | Auto-increment ID |
| tenant_id | INTEGER | FK → tenants(id) | Organization reference |
| source | VARCHAR(255) | NOT NULL | Source document/file |
| chunk | TEXT | NOT NULL | Text content |
| chunk_hash | VARCHAR(64) | NOT NULL | SHA256 hash for dedup |
| embedding_vector | VECTOR(768) | | nomic-embed-text embedding |
| metadata_json | JSONB | | Chunk metadata |
| version | INTEGER | DEFAULT 1 | Version number |
| is_current | BOOLEAN | DEFAULT TRUE | Active version flag |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | Creation timestamp |
| updated_at | TIMESTAMPTZ | DEFAULT NOW() | Last update timestamp |
| archived_at | TIMESTAMPTZ | | Archive timestamp |

**Vector Search Query:**
```sql
SELECT id, source, chunk,
       1 - (embedding_vector <=> $query_vector) AS score
FROM kb_chunks
WHERE tenant_id = $tenant_id
  AND is_current = TRUE
ORDER BY embedding_vector <=> $query_vector
LIMIT 5;
```

---

### ticket_external_refs

Links to external systems (Jira, Zendesk, etc.).

```sql
CREATE TABLE ticket_external_refs (
    id              SERIAL PRIMARY KEY,
    tenant_id       INTEGER NOT NULL,
    ticket_id       INTEGER NOT NULL REFERENCES tickets(id) ON DELETE CASCADE,
    system          VARCHAR(32) NOT NULL,
    external_id     VARCHAR(255) NOT NULL,
    external_url    VARCHAR(512),
    metadata_json   JSONB,
    created_at      TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at      TIMESTAMPTZ DEFAULT NOW() NOT NULL,

    UNIQUE(system, external_id)
);
```

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PRIMARY KEY | Auto-increment ID |
| tenant_id | INTEGER | NOT NULL | Organization reference |
| ticket_id | INTEGER | FK → tickets(id) | Local ticket |
| system | VARCHAR(32) | NOT NULL | External system (jira/zendesk) |
| external_id | VARCHAR(255) | NOT NULL | External ticket ID |
| external_url | VARCHAR(512) | | Link to external ticket |
| metadata_json | JSONB | | Sync metadata |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | Creation timestamp |
| updated_at | TIMESTAMPTZ | DEFAULT NOW() | Last update timestamp |

---

### integration_sync_logs

Audit log for integration synchronization.

```sql
CREATE TABLE integration_sync_logs (
    id                  SERIAL PRIMARY KEY,
    tenant_id           INTEGER NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    system              VARCHAR(32) NOT NULL,
    direction           VARCHAR(16) NOT NULL,
    status              VARCHAR(16) NOT NULL,
    records_processed   INTEGER DEFAULT 0 NOT NULL,
    error_message       TEXT,
    started_at          TIMESTAMPTZ NOT NULL,
    completed_at        TIMESTAMPTZ,
    metadata_json       JSONB
);
```

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PRIMARY KEY | Auto-increment ID |
| tenant_id | INTEGER | FK → tenants(id) | Organization reference |
| system | VARCHAR(32) | NOT NULL | Integration system |
| direction | VARCHAR(16) | NOT NULL | inbound/outbound |
| status | VARCHAR(16) | NOT NULL | pending/running/success/failed |
| records_processed | INTEGER | DEFAULT 0 | Number of records |
| error_message | TEXT | | Error details |
| started_at | TIMESTAMPTZ | NOT NULL | Sync start time |
| completed_at | TIMESTAMPTZ | | Sync completion time |
| metadata_json | JSONB | | Additional metadata |

---

## Indexes Summary

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              INDEX STRATEGY                                              │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                          │
│  PRIMARY INDEXES (B-tree)                                                               │
│  ────────────────────────                                                               │
│  • All tables have auto-increment primary key                                           │
│                                                                                          │
│  LOOKUP INDEXES (B-tree)                                                                │
│  ───────────────────────                                                                │
│  • ix_users_tenant_email      - Fast user lookup by tenant + email                      │
│  • ix_users_email             - Global email search                                     │
│  • ix_tickets_tenant          - Tickets by tenant                                       │
│  • ix_tickets_status          - Tickets by status                                       │
│  • ix_tickets_tenant_status   - Tickets by tenant + status (common query)              │
│  • ix_tickets_updated_at      - Recent tickets sorting                                  │
│  • ix_messages_ticket_id      - Messages by ticket                                      │
│  • ix_kb_tenant_source        - KB chunks by tenant + source                           │
│                                                                                          │
│  VECTOR INDEX (IVFFlat)                                                                 │
│  ──────────────────────                                                                 │
│  • ix_kb_embedding            - Approximate nearest neighbor search                     │
│                                 Using cosine similarity                                  │
│                                 100 lists for ~10K chunks                               │
│                                                                                          │
│  UNIQUE CONSTRAINTS                                                                     │
│  ─────────────────────                                                                  │
│  • tenants(name)              - Unique tenant names                                     │
│  • tenants(slug)              - Unique tenant slugs                                     │
│  • users(tenant_id, email)    - Unique email per tenant                                │
│  • kb_chunks(tenant_id, chunk_hash) - Prevent duplicate chunks                         │
│  • ticket_external_refs(system, external_id) - Unique external refs                    │
│                                                                                          │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

## Data Flow

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              DATA FLOW DIAGRAM                                           │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                          │
│                    ┌──────────────────────────────────────────────┐                     │
│                    │              USER CREATES TICKET              │                     │
│                    └──────────────────────┬───────────────────────┘                     │
│                                           │                                              │
│                                           ▼                                              │
│   ┌─────────────────────────────────────────────────────────────────────────────────┐   │
│   │                                                                                  │   │
│   │   1. INSERT INTO tickets (tenant_id, title, description, ...)                   │   │
│   │      └─────────────────────────────────────────────────────────┐                │   │
│   │                                                                 │                │   │
│   │   2. AgentService triggered                                     │                │   │
│   │      │                                                          │                │   │
│   │      ├── 2.1 Build search query (title + description)          │                │   │
│   │      │                                                          │                │   │
│   │      ├── 2.2 Generate query embedding                           │                │   │
│   │      │       └── Ollama nomic-embed-text → [768 floats]        │                │   │
│   │      │                                                          │                │   │
│   │      ├── 2.3 Vector search in kb_chunks                         │                │   │
│   │      │       SELECT * FROM kb_chunks                            │                │   │
│   │      │       WHERE tenant_id = ?                                │                │   │
│   │      │       ORDER BY embedding_vector <=> query_vector         │                │   │
│   │      │       LIMIT 5                                            │                │   │
│   │      │                                                          │                │   │
│   │      ├── 2.4 Build prompt with KB context                       │                │   │
│   │      │                                                          │                │   │
│   │      ├── 2.5 Generate response                                  │                │   │
│   │      │       └── Ollama qwen2.5:3b → AI response                │                │   │
│   │      │                                                          │                │   │
│   │      └── 2.6 Check escalation triggers                          │                │   │
│   │              │                                                   │                │   │
│   │              ├── Keywords: "refund", "lawsuit", "возврат"...   │                │   │
│   │              └── Low KB score < 0.5                             │                │   │
│   │                                                                 │                │   │
│   │   3. INSERT INTO messages (ticket_id, role='assistant', ...)   │                │   │
│   │                                                                 │                │   │
│   │   4. If escalation needed:                                      │                │   │
│   │      UPDATE tickets SET status = 'escalated' WHERE id = ?       │                │   │
│   │                                                                 │                │   │
│   └─────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                          │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

## Migrations

Migrations are managed by Alembic:

```
alembic/
├── env.py                      # Migration environment config
├── script.py.mako              # Migration template
└── versions/
    ├── 001_initial.py          # Create all tables
    ├── 002_kb_unique_constraint.py   # Add KB dedup constraint
    └── 003_add_ticket_metadata.py    # Add metadata_json to tickets
```

**Run migrations:**
```bash
# Apply all migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Generate new migration
alembic revision --autogenerate -m "description"
```

## Next: [API Reference](./API.md)
