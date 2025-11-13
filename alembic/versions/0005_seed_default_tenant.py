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
# bcrypt для пароля "secret"
DEFAULT_USER_PASSWORD_HASH = (
    "$2b$12$yNYI1t4bm/FYnGV8eK3opaYauSgu5nJGV1koRaSPoaqe7i0rGUN7K"
)


def upgrade() -> None:
    # Вставляем/обновляем tenant
    tenant_stmt = (
        sa.text(
            """
            INSERT INTO tenants (id, name, slug)
            VALUES (:tenant_id, :tenant_name, :tenant_slug)
            ON CONFLICT (id) DO UPDATE
                SET name = EXCLUDED.name,
                    slug = EXCLUDED.slug
            """
        )
        .bindparams(
            sa.bindparam("tenant_id", value=DEFAULT_TENANT_ID),
            sa.bindparam("tenant_name", value=DEFAULT_TENANT_NAME),
            sa.bindparam("tenant_slug", value=DEFAULT_TENANT_NAME),
        )
    )
    op.execute(tenant_stmt)

    # Вставляем/обновляем demo-юзера
    user_stmt = (
        sa.text(
            """
            INSERT INTO users (tenant_id, email, password_hash)
            VALUES (:tenant_id, :email, :password_hash)
            ON CONFLICT ON CONSTRAINT uq_users_tenant_email
            DO UPDATE SET password_hash = EXCLUDED.password_hash
            """
        )
        .bindparams(
            sa.bindparam("tenant_id", value=DEFAULT_TENANT_ID),
            sa.bindparam("email", value=DEFAULT_USER_EMAIL),
            sa.bindparam("password_hash", value=DEFAULT_USER_PASSWORD_HASH),
        )
    )
    op.execute(user_stmt)


def downgrade() -> None:
    delete_user_stmt = (
        sa.text(
            """
            DELETE FROM users
            WHERE tenant_id = :tenant_id AND email = :email
            """
        )
        .bindparams(
            sa.bindparam("tenant_id", value=DEFAULT_TENANT_ID),
            sa.bindparam("email", value=DEFAULT_USER_EMAIL),
        )
    )
    op.execute(delete_user_stmt)

    delete_tenant_stmt = (
        sa.text(
            "DELETE FROM tenants WHERE id = :tenant_id"
        ).bindparams(
            sa.bindparam("tenant_id", value=DEFAULT_TENANT_ID),
        )
    )
    op.execute(delete_tenant_stmt)
