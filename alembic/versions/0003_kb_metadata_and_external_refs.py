"""Ensure metadata helpers exist and backfill chunk hashes."""

from __future__ import annotations

from typing import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.engine import reflection

# revision identifiers, used by Alembic.
revision: str = "0003_kb_metadata_and_external_refs"
down_revision: str | None = "0002_kb_chunks"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def _column_names(inspector: reflection.Inspector, table: str) -> set[str]:
    return {col["name"] for col in inspector.get_columns(table)}


def _has_index(inspector: reflection.Inspector, table: str, name: str) -> bool:
    return any(idx["name"] == name for idx in inspector.get_indexes(table))


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    cols = _column_names(inspector, "kb_chunks")
    if "chunk_hash" not in cols:
        op.add_column("kb_chunks", sa.Column("chunk_hash", sa.String(length=64), nullable=True))
    if "metadata" not in cols:
        op.add_column(
            "kb_chunks",
            sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        )
    if "updated_at" not in cols:
        op.add_column(
            "kb_chunks",
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=True,
            ),
        )

    if not _has_index(inspector, "kb_chunks", "uq_kb_chunk_tenant_source_hash"):
        op.create_unique_constraint(
            "uq_kb_chunk_tenant_source_hash",
            "kb_chunks",
            ["tenant_id", "source", "chunk_hash"],
        )

    if not inspector.has_table("ticket_external_refs"):
        op.create_table(
            "ticket_external_refs",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("tenant_id", sa.Integer(), nullable=False),
            sa.Column("ticket_id", sa.Integer(), nullable=False),
            sa.Column("system", sa.String(length=32), nullable=False),
            sa.Column("reference", sa.String(length=128), nullable=False),
            sa.Column(
                "metadata",
                postgresql.JSONB(astext_type=sa.Text()),
                nullable=True,
            ),
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

    op.execute(
        """
        UPDATE kb_chunks
        SET chunk_hash = encode(digest(coalesce(chunk, ''), 'sha256'), 'hex')
        WHERE chunk_hash IS NULL
        """
    )

    # Ensure new columns are non-nullable where appropriate now that data is backfilled.
    op.alter_column("kb_chunks", "chunk_hash", nullable=False)
    op.alter_column("kb_chunks", "updated_at", nullable=False)


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())

    if inspector.has_table("ticket_external_refs"):
        if _has_index(inspector, "ticket_external_refs", "uq_ticket_external_system"):
            op.drop_index(
                "uq_ticket_external_system", table_name="ticket_external_refs"
            )
        for idx in (
            "ix_ticket_external_refs_system",
            "ix_ticket_external_refs_ticket_id",
            "ix_ticket_external_refs_tenant_id",
        ):
            if _has_index(inspector, "ticket_external_refs", idx):
                op.drop_index(idx, table_name="ticket_external_refs")
        op.drop_table("ticket_external_refs")

    for column in ("updated_at", "metadata", "chunk_hash"):
        if column in _column_names(inspector, "kb_chunks"):
            op.drop_column("kb_chunks", column)
