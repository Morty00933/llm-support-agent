"""Initial core schema for LLM Support Agent"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# Revision identifiers
revision = "0001_init"
down_revision = "0000_bootstrap"
branch_labels = None
depends_on = None


def upgrade():
    # --- Tenants ---
    op.create_table(
        "tenants",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(128), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # --- Users ---
    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("tenant_id", sa.Integer, sa.ForeignKey("tenants.id", ondelete="CASCADE")),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean, server_default=sa.text("true")),
        sa.Column("is_superuser", sa.Boolean, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # --- Knowledge Base ---
    op.create_table(
        "kb",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("tenant_id", sa.Integer, sa.ForeignKey("tenants.id", ondelete="CASCADE")),
        sa.Column("source", sa.String(64), nullable=False),
        sa.Column("language", sa.String(8), default="en"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "kb_chunks",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("kb_id", sa.Integer, sa.ForeignKey("kb.id", ondelete="CASCADE")),
        sa.Column("chunk", sa.Text, nullable=False),
        sa.Column("chunk_hash", sa.String(64)),
        sa.Column("tags", postgresql.ARRAY(sa.String(64))),
        sa.Column("metadata", postgresql.JSONB),
        sa.Column("embedding", postgresql.ARRAY(sa.Float)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_index("ix_kb_chunks_hash", "kb_chunks", ["chunk_hash"])
    op.create_index("ix_kb_chunks_tags", "kb_chunks", ["tags"], postgresql_using="gin")

    # --- Tickets ---
    op.create_table(
        "tickets",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("tenant_id", sa.Integer, sa.ForeignKey("tenants.id", ondelete="CASCADE")),
        sa.Column("subject", sa.String(255)),
        sa.Column("content", sa.Text),
        sa.Column("status", sa.String(32), server_default="open"),
        sa.Column("priority", sa.String(32), server_default="normal"),
        sa.Column("external_ref", sa.String(128)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # --- Integration logs ---
    op.create_table(
        "integration_sync_logs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("tenant_id", sa.Integer, sa.ForeignKey("tenants.id", ondelete="CASCADE")),
        sa.Column("provider", sa.String(64)),
        sa.Column("status", sa.String(32)),
        sa.Column("details", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade():
    op.drop_table("integration_sync_logs")
    op.drop_table("tickets")
    op.drop_index("ix_kb_chunks_tags")
    op.drop_index("ix_kb_chunks_hash")
    op.drop_table("kb_chunks")
    op.drop_table("kb")
    op.drop_table("users")
    op.drop_table("tenants")
