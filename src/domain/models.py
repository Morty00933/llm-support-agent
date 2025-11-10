from __future__ import annotations
from typing import Any

from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped
from sqlalchemy import (
    Integer,
    String,
    Text,
    ForeignKey,
    Index,
    DateTime,
    func,
    LargeBinary,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import UserDefinedType
from ..core.config import settings

try:  # pragma: no cover - optional dependency
    from pgvector.sqlalchemy import Vector

    HAS_PGVECTOR = True
except ModuleNotFoundError:  # pragma: no cover - fallback stub for local/dev envs
    HAS_PGVECTOR = False

    class Vector(UserDefinedType):
        """Минимальная заглушка для поля vector, когда pgvector не установлен."""

        cache_ok = True

        def __init__(self, dim: int | None = None) -> None:
            super().__init__()
            self.dim = dim

        def get_col_spec(self, **kw: Any) -> str:
            if self.dim:
                return f"vector({self.dim})"
            return "vector"

        def bind_processor(self, dialect):
            def process(value):
                if value is None:
                    return None
                return "[" + ",".join(str(float(v)) for v in value) + "]"

            return process

        def result_processor(self, dialect, coltype):
            def process(value):
                if value is None:
                    return None
                text = value.strip()
                if text.startswith("[") and text.endswith("]"):
                    text = text[1:-1]
                if not text:
                    return []
                return [float(part) for part in text.split(",")]

            return process

        class comparator_factory(UserDefinedType.Comparator):
            def cosine_distance(self, other):  # type: ignore[override]
                return func.cosine_distance(self.expr, other)


class Base(DeclarativeBase):
    """База для всех ORM-моделей."""

    pass


class Tenant(Base):
    __tablename__ = "tenants"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), unique=True)
    slug: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("tenant_id", "email", name="uq_users_tenant_email"),
        Index("ix_users_tenant_id", "tenant_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class Ticket(Base):
    __tablename__ = "tickets"
    __table_args__ = (
        Index("ix_tickets_tenant_id", "tenant_id"),
        Index("ix_tickets_status", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="open")
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class Message(Base):
    __tablename__ = "messages"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ticket_id: Mapped[int] = mapped_column(
        ForeignKey("tickets.id", ondelete="CASCADE"), index=True
    )
    role: Mapped[str] = mapped_column(String(16))  # 'user' | 'agent' | 'system'
    content: Mapped[str] = mapped_column(Text())
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


Index("ix_messages_ticket_created", Message.ticket_id, Message.created_at)


class KBChunk(Base):
    __tablename__ = "kb_chunks"
    _vector_dim = settings.EMBEDDING_DIM if HAS_PGVECTOR else None  # type: ignore[name-defined]

    _table_args = [
        UniqueConstraint(
            "tenant_id", "source", "chunk_hash", name="uq_kb_chunk_tenant_source_hash"
        ),
        Index("ix_kb_tenant_source", "tenant_id", "source"),
        Index("ix_kb_tenant_created", "tenant_id", "created_at"),
        Index("ix_kb_tenant_archived", "tenant_id", "archived_at"),
    ]
    if HAS_PGVECTOR:
        _table_args.append(
            Index(
                "ix_kb_chunks_embedding_vector_cosine",
                "embedding_vector",
                postgresql_using="ivfflat",
                postgresql_with={"lists": "100"},
                postgresql_ops={"embedding_vector": "vector_cosine_ops"},
            )
        )
    __table_args__ = tuple(_table_args)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    source: Mapped[str] = mapped_column(String(255), nullable=False)
    chunk: Mapped[str] = mapped_column(Text(), nullable=False)
    chunk_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(
        "metadata", JSONB, nullable=True
    )
    embedding: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    embedding_vector: Mapped[list[float] | None] = mapped_column(
        Vector(_vector_dim), nullable=True
    )
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    archived_at: Mapped[DateTime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class TicketExternalRef(Base):
    __tablename__ = "ticket_external_refs"
    __table_args__ = (
        Index("ix_ticket_external_refs_tenant_id", "tenant_id"),
        Index("ix_ticket_external_refs_ticket_id", "ticket_id"),
        Index("ix_ticket_external_refs_system", "system"),
        UniqueConstraint("ticket_id", "system", name="uq_ticket_external_system"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    ticket_id: Mapped[int] = mapped_column(
        ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False
    )
    system: Mapped[str] = mapped_column(String(32), nullable=False)
    reference: Mapped[str] = mapped_column(String(128), nullable=False)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(
        "metadata", JSONB, nullable=True
    )
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
class IntegrationSyncLog(Base):
    __tablename__ = "integration_sync_logs"
    __table_args__ = (
        Index(
            "ix_integration_sync_logs_ticket_system",
            "ticket_id",
            "system",
            "created_at",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    ticket_id: Mapped[int] = mapped_column(
        ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False
    )
    system: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    details_json: Mapped[dict[str, Any] | None] = mapped_column(
        "details", JSONB, nullable=True
    )
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


