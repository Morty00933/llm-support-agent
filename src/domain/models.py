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
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import UserDefinedType

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
    slug: Mapped[str] = mapped_column(String(64), unique=True)


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    email: Mapped[str] = mapped_column(String(255), index=True)
    password_hash: Mapped[str] = mapped_column(String(255))


class Ticket(Base):
    __tablename__ = "tickets"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(32), index=True, default="open")


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
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    source: Mapped[str] = mapped_column(String(255), index=True)
    chunk: Mapped[str] = mapped_column(Text())
    chunk_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    embedding: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    embedding_vector: Mapped[list[float] | None] = mapped_column(
        Vector(None), nullable=True
    )
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(
        "metadata", JSONB, nullable=True
    )
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    archived_at: Mapped[DateTime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


Index("ix_kb_tenant_source", KBChunk.tenant_id, KBChunk.source)
Index("ix_kb_tenant_created", KBChunk.tenant_id, KBChunk.created_at)
Index(
    "uq_kb_chunk_tenant_source_hash",
    KBChunk.tenant_id,
    KBChunk.source,
    KBChunk.chunk_hash,
    unique=True,
)


class TicketExternalRef(Base):
    __tablename__ = "ticket_external_refs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    ticket_id: Mapped[int] = mapped_column(
        ForeignKey("tickets.id", ondelete="CASCADE"), index=True
    )
    system: Mapped[str] = mapped_column(String(32), index=True)
    reference: Mapped[str] = mapped_column(String(128))
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(
        "metadata", JSONB, nullable=True
    )
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


Index(
    "uq_ticket_external_system",
    TicketExternalRef.ticket_id,
    TicketExternalRef.system,
    unique=True,
)
