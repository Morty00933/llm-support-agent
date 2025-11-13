"""Compatibility shim to ensure alembic_version column length."""

from __future__ import annotations

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0000_alter_alembic_version_len"
down_revision: str | None = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
          IF EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name='alembic_version' AND column_name='version_num'
          ) THEN
            ALTER TABLE alembic_version ALTER COLUMN version_num TYPE VARCHAR(128);
          END IF;
        END
        $$;
        """
    )


def downgrade() -> None:
    # The column can remain widened.
    pass
