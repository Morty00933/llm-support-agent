"""Ensure required PostgreSQL extensions are present."""

from __future__ import annotations

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001_enable_extensions"
down_revision: str | None = "0000_bootstrap"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto;")
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")


def downgrade() -> None:
    # Extensions are intentionally left in place.
    pass
