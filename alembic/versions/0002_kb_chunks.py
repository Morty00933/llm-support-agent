"""add kb_chunks table + indexes"""

from alembic import op
import sqlalchemy as sa

revision = "0002_kb_chunks"
down_revision = "0001_init"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "kb_chunks",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "tenant_id",
            sa.Integer,
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("source", sa.String(255), nullable=False),
        sa.Column("chunk", sa.Text, nullable=False),
        sa.Column("embedding", sa.LargeBinary, nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")
        ),
    )
    op.create_index("ix_kb_tenant_source", "kb_chunks", ["tenant_id", "source"])
    op.create_index("ix_kb_tenant_created", "kb_chunks", ["tenant_id", "created_at"])


def downgrade():
    op.drop_index("ix_kb_tenant_source", table_name="kb_chunks")
    op.drop_index("ix_kb_tenant_created", table_name="kb_chunks")
    op.drop_table("kb_chunks")
