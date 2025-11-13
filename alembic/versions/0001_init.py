"""Compatibility revision retained for historic databases."""

from __future__ import annotations

# revision identifiers, used by Alembic.
revision: str = "0001_init"
down_revision: str | None = "0001_enable_extensions"
branch_labels = None
depends_on = None


def upgrade() -> None:  # pragma: no cover - compatibility shim
    """No-op placeholder to keep the legacy revision id in the graph."""


def downgrade() -> None:  # pragma: no cover - compatibility shim
    """No downgrade steps for the compatibility shim."""
