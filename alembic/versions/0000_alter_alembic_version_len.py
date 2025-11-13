"""Make alembic_version.version_num longer"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "0000_alter_alembic_version_len"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Увеличиваем длину колонки, но только если таблица уже существует
    op.execute("""
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
    """)


def downgrade():
    # откат не обязателен
    pass
