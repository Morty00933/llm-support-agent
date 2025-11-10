"""Ensure vector column indexes exist for knowledge base chunks."""

from __future__ import annotations

from typing import Sequence

from alembic import op
import sqlalchemy as sa

try:  # pragma: no cover - optional dependency
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
revision: str = "0004_kb_vector_and_indexes"
down_revision: str | None = "0003_kb_metadata_and_external_refs"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    cols = {col["name"] for col in inspector.get_columns("kb_chunks")}

    if "embedding_vector" not in cols:
        op.add_column(
            "kb_chunks",
            sa.Column("embedding_vector", Vector(dim=settings.EMBEDDING_DIM), nullable=True),
        )
    if "archived_at" not in cols:
        op.add_column(
            "kb_chunks",
            sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        )

    existing_indexes = {idx["name"] for idx in inspector.get_indexes("kb_chunks")}
    if "ix_kb_tenant_archived" not in existing_indexes:
        op.create_index(
            "ix_kb_tenant_archived",
            "kb_chunks",
            ["tenant_id", "archived_at"],
        )
    if "ix_kb_chunks_embedding_vector_cosine" not in existing_indexes:
        op.create_index(
            "ix_kb_chunks_embedding_vector_cosine",
            "kb_chunks",
            ["embedding_vector"],
            postgresql_using="ivfflat",
            postgresql_with={"lists": 100},
            postgresql_ops={"embedding_vector": "vector_cosine_ops"},
        )


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    indexes = {idx["name"] for idx in inspector.get_indexes("kb_chunks")}
    if "ix_kb_chunks_embedding_vector_cosine" in indexes:
        op.drop_index("ix_kb_chunks_embedding_vector_cosine", table_name="kb_chunks")
    if "ix_kb_tenant_archived" in indexes:
        op.drop_index("ix_kb_tenant_archived", table_name="kb_chunks")

    cols = {col["name"] for col in inspector.get_columns("kb_chunks")}
    if "archived_at" in cols:
        op.drop_column("kb_chunks", "archived_at")
    if "embedding_vector" in cols:
        op.drop_column("kb_chunks", "embedding_vector")
