"""Seed default tenant and demo user."""

from __future__ import annotations

from typing import Sequence

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0005_seed_default_tenant"
down_revision: str | None = "0004_kb_vector_and_indexes"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

DEFAULT_TENANT_ID = 1
DEFAULT_TENANT_NAME = "default"
DEFAULT_USER_EMAIL = "user@example.com"
DEFAULT_USER_PASSWORD_HASH = "$2b$12$yNYI1t4bm/FYnGV8eK3opaYauSgu5nJGV1koRaSPoaqe7i0rGUN7K"  # bcrypt for "secret"


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            INSERT INTO tenants (id, name, slug)
            VALUES (:tenant_id, :tenant_name, :tenant_slug)
            ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, slug = EXCLUDED.slug
            """
        ),
        {"tenant_id": DEFAULT_TENANT_ID, "tenant_name": DEFAULT_TENANT_NAME, "tenant_slug": DEFAULT_TENANT_NAME},
    )

    op.execute(
        sa.text(
            """
            INSERT INTO users (tenant_id, email, password_hash)
            VALUES (:tenant_id, :email, :password_hash)
            ON CONFLICT ON CONSTRAINT uq_users_tenant_email
            DO UPDATE SET password_hash = EXCLUDED.password_hash
            """
        ),
        {
            "tenant_id": DEFAULT_TENANT_ID,
            "email": DEFAULT_USER_EMAIL,
            "password_hash": DEFAULT_USER_PASSWORD_HASH,
        },
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            "DELETE FROM users WHERE tenant_id = :tenant_id AND email = :email"
        ),
        {"tenant_id": DEFAULT_TENANT_ID, "email": DEFAULT_USER_EMAIL},
    )
    op.execute(
        sa.text("DELETE FROM tenants WHERE id = :tenant_id"),
        {"tenant_id": DEFAULT_TENANT_ID},
    )
