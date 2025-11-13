"""Enable pgcrypto & vector extensions"""

from alembic import op

revision = "0001_enable_extensions"
down_revision = "0000_alter_alembic_version_len"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto;")
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")


def downgrade():
    # обычно EXTENSION не откатывают
    pass