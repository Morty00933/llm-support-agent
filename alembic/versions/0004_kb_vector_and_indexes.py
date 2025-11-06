"""add pgvector support and kb metadata indexes"""

from __future__ import annotations

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
            if self.dim:
                return f"vector({self.dim})"
            return "vector"


# revision identifiers, used by Alembic.
revision = "0004_kb_vector_and_indexes"
down_revision = "0003_kb_metadata_and_external_refs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.add_column(
        "kb_chunks", sa.Column("embedding_vector", Vector(dim=None), nullable=True)
    )
    op.add_column(
        "kb_chunks",
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_kb_chunks_archived_at",
        "kb_chunks",
        ["archived_at"],
    )
    op.create_index(
        "ix_kb_chunks_metadata_tags",
        "kb_chunks",
        [sa.text("(metadata -> 'tags')")],
        postgresql_using="gin",
    )
    op.create_index(
        "ix_kb_chunks_metadata_language",
        "kb_chunks",
        [sa.text("(metadata -> 'language')")],
        postgresql_using="gin",
    )
    op.create_index(
        "ix_kb_chunks_embedding_vector_cosine",
        "kb_chunks",
        ["embedding_vector"],
        postgresql_using="ivfflat",
        postgresql_with={"lists": "100"},
        postgresql_ops={"embedding_vector": "vector_cosine_ops"},
    )


def downgrade() -> None:
    op.drop_index("ix_kb_chunks_embedding_vector_cosine", table_name="kb_chunks")
    op.drop_index("ix_kb_chunks_metadata_language", table_name="kb_chunks")
    op.drop_index("ix_kb_chunks_metadata_tags", table_name="kb_chunks")
    op.drop_index("ix_kb_chunks_archived_at", table_name="kb_chunks")
    op.drop_column("kb_chunks", "archived_at")
    op.drop_column("kb_chunks", "embedding_vector")
