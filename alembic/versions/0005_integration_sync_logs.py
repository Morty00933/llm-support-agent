"""integration sync log table"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0005_integration_sync_logs"
down_revision = "0004_kb_vector_and_indexes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "integration_sync_logs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("ticket_id", sa.Integer(), nullable=False),
        sa.Column("system", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("details", sa.dialects.postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["ticket_id"], ["tickets.id"], ondelete="CASCADE"),
    )
    op.create_index(
        "ix_integration_sync_logs_ticket_system",
        "integration_sync_logs",
        ["ticket_id", "system", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_integration_sync_logs_ticket_system", table_name="integration_sync_logs")
    op.drop_table("integration_sync_logs")
