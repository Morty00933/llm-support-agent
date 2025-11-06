from __future__ import annotations
from typing import Iterable, Sequence, Optional
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from .models import Tenant, User, Ticket, Message, KBChunk


# ---------- Tenants ----------

async def get_tenant_by_slug(session: AsyncSession, slug: str) -> Optional[Tenant]:
    q = select(Tenant).where(Tenant.slug == slug).limit(1)
    return (await session.execute(q)).scalars().first()


async def create_tenant(session: AsyncSession, slug: str) -> Tenant:
    t = Tenant(slug=slug)
    session.add(t)
    await session.flush()
    return t


# ---------- Users ----------

async def get_user_by_email(session: AsyncSession, tenant_id: int, email: str) -> Optional[User]:
    q = select(User).where(User.tenant_id == tenant_id, User.email == email).limit(1)
    return (await session.execute(q)).scalars().first()


async def create_user(session: AsyncSession, tenant_id: int, email: str, password_hash: str) -> User:
    u = User(tenant_id=tenant_id, email=email, password_hash=password_hash)
    session.add(u)
    await session.flush()
    return u


# ---------- Tickets ----------

async def list_tickets(
    session: AsyncSession,
    tenant_id: int,
    limit: int = 50,
    offset: int = 0,
) -> Sequence[Ticket]:
    q = (
        select(Ticket)
        .where(Ticket.tenant_id == tenant_id)
        .order_by(Ticket.id.desc())
        .limit(limit)
        .offset(offset)
    )
    return (await session.execute(q)).scalars().all()


async def get_ticket(session: AsyncSession, tenant_id: int, ticket_id: int) -> Optional[Ticket]:
    t = await session.get(Ticket, ticket_id)
    if not t or t.tenant_id != tenant_id:
        return None
    return t


async def create_ticket(session: AsyncSession, tenant_id: int, title: str, status: str = "open") -> Ticket:
    t = Ticket(tenant_id=tenant_id, title=title, status=status)
    session.add(t)
    await session.flush()
    return t


async def update_ticket_status(session: AsyncSession, tenant_id: int, ticket_id: int, status: str) -> Optional[Ticket]:
    t = await get_ticket(session, tenant_id, ticket_id)
    if not t:
        return None
    t.status = status
    await session.flush()
    return t


# ---------- Messages ----------

async def add_message(session: AsyncSession, ticket_id: int, role: str, content: str) -> Message:
    m = Message(ticket_id=ticket_id, role=role, content=content)
    session.add(m)
    await session.flush()
    return m


async def list_messages(session: AsyncSession, ticket_id: int, limit: int = 200) -> Sequence[Message]:
    q = select(Message).where(Message.ticket_id == ticket_id).order_by(Message.id.asc()).limit(limit)
    return (await session.execute(q)).scalars().all()


# ---------- Knowledge Base ----------

async def upsert_kb_chunks(
    session: AsyncSession,
    tenant_id: int,
    source: str,
    chunks: Iterable[tuple[str, bytes | None]],
) -> int:
    """
    Наивная вставка без UPSERT. Для реального upsert добавьте уникальные индексы и on_conflict_do_update.
    chunks: iterable of (text, embedding_bytes)
    """
    total = 0
    for chunk_text, emb in chunks:
        kc = KBChunk(tenant_id=tenant_id, source=source, chunk=chunk_text, embedding=emb)
        session.add(kc)
        total += 1
    # flush происходит снаружи по контракту Session contextmanager в core.db
    return total


async def list_kb_chunks(session: AsyncSession, tenant_id: int, source: Optional[str] = None, limit: int = 1000) -> Sequence[KBChunk]:
    q = select(KBChunk).where(KBChunk.tenant_id == tenant_id).order_by(KBChunk.id.desc()).limit(limit)
    if source:
        q = q.where(KBChunk.source == source)
    return (await session.execute(q)).scalars().all()
