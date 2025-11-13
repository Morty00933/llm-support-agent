"""Create knowledge base chunks table with vector embeddings."""

from __future__ import annotations

from typing import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

try:  # pragma: no cover - optional dependency for typing accuracy
    from pgvector.sqlalchemy import Vector
except ModuleNotFoundError:  # pragma: no cover
    class Vector(sa.types.UserDefinedType):
        cache_ok = True

        def __init__(self, dim: int | None = None) -> None:
            super().__init__()
            self.dim = dim

        def get_col_spec(self, **kw):
            return f"vector({self.dim})" if self.dim else "vector"

from src.core.config import settings

# revision identifiers, used by Alembic.
revision: str = "0002_kb_chunks"
down_revision: str | None = "0001_rebootstrap_schema"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

EMBEDDING_DIM = settings.EMBEDDING_DIM


def upgrade() -> None:
    op.create_table(
        "kb_chunks",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "tenant_id",
            sa.Integer,
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("source", sa.String(length=255), nullable=False),
        sa.Column("chunk", sa.Text(), nullable=False),
        sa.Column("chunk_hash", sa.String(length=64), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("embedding", sa.LargeBinary(), nullable=True),
        sa.Column(
            "embedding_vector",
            Vector(dim=EMBEDDING_DIM),
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
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint(
            "tenant_id",
            "source",
            "chunk_hash",
            name="uq_kb_chunk_tenant_source_hash",
        ),
    )

    op.create_index(
        "ix_kb_tenant_source",
        "kb_chunks",
        ["tenant_id", "source"],
    )
    op.create_index(
        "ix_kb_tenant_created",
        "kb_chunks",
        ["tenant_id", "created_at"],
    )
    op.create_index(
        "ix_kb_tenant_archived",
        "kb_chunks",
        ["tenant_id", "archived_at"],
    )
    op.create_index(
        "ix_kb_chunks_embedding_vector_cosine",
        "kb_chunks",
        ["embedding_vector"],
        postgresql_using="ivfflat",
        postgresql_with={"lists": 100},
        postgresql_ops={"embedding_vector": "vector_cosine_ops"},
    )


def downgrade() -> None:
    op.drop_index("ix_kb_chunks_embedding_vector_cosine", table_name="kb_chunks")
    op.drop_index("ix_kb_tenant_archived", table_name="kb_chunks")
    op.drop_index("ix_kb_tenant_created", table_name="kb_chunks")
    op.drop_index("ix_kb_tenant_source", table_name="kb_chunks")
    op.drop_table("kb_chunks")
