"""Add KB metadata fields and ticket external refs

Revision ID: 0003_kb_metadata_and_external_refs
Revises: 0002_kb_chunks
Create Date: 2024-07-05 00:00:00
"""

from __future__ import annotations

from typing import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "0003_kb_metadata_and_external_refs"
down_revision = "0002_kb_chunks"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "kb_chunks",
        sa.Column("chunk_hash", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "kb_chunks",
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.add_column(
        "kb_chunks",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
    )
    op.create_index(
        "uq_kb_chunk_tenant_source_hash",
        "kb_chunks",
        ["tenant_id", "source", "chunk_hash"],
        unique=True,
    )

    op.create_table(
        "ticket_external_refs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("ticket_id", sa.Integer(), nullable=False),
        sa.Column("system", sa.String(length=32), nullable=False),
        sa.Column("reference", sa.String(length=128), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["ticket_id"], ["tickets.id"], ondelete="CASCADE"),
    )
    op.create_index(
        "ix_ticket_external_refs_tenant_id",
        "ticket_external_refs",
        ["tenant_id"],
    )
    op.create_index(
        "ix_ticket_external_refs_ticket_id",
        "ticket_external_refs",
        ["ticket_id"],
    )
    op.create_index(
        "ix_ticket_external_refs_system",
        "ticket_external_refs",
        ["system"],
    )
    op.create_index(
        "uq_ticket_external_system",
        "ticket_external_refs",
        ["ticket_id", "system"],
        unique=True,
    )

    # Populate chunk_hash for existing rows using sha256
    op.execute(
        """
        UPDATE kb_chunks
        SET chunk_hash = encode(digest(coalesce(chunk, ''), 'sha256'), 'hex')
        WHERE chunk_hash IS NULL
        """
    )
    op.alter_column("kb_chunks", "chunk_hash", nullable=False)
    op.alter_column("kb_chunks", "updated_at", nullable=False)


def downgrade() -> None:
    op.drop_index("uq_ticket_external_system", table_name="ticket_external_refs")
    op.drop_index("ix_ticket_external_refs_system", table_name="ticket_external_refs")
    op.drop_index(
        "ix_ticket_external_refs_ticket_id", table_name="ticket_external_refs"
    )
    op.drop_index(
        "ix_ticket_external_refs_tenant_id", table_name="ticket_external_refs"
    )
    op.drop_table("ticket_external_refs")

    op.drop_index("uq_kb_chunk_tenant_source_hash", table_name="kb_chunks")
    op.drop_column("kb_chunks", "updated_at")
    op.drop_column("kb_chunks", "metadata")
    op.drop_column("kb_chunks", "chunk_hash")
