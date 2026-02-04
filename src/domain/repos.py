from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timezone
from typing import Any, Sequence

from sqlalchemy import select, update, delete, and_, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.dialects.postgresql import insert

from src.domain.models import (
    User,
    Tenant,
    Ticket,
    Message,
    KBChunk,
    TicketExternalRef,
    IntegrationSyncLog,
)

logger = logging.getLogger(__name__)


async def list_tenants(session: AsyncSession) -> Sequence[Tenant]:
    stmt = select(Tenant).order_by(Tenant.id)
    result = await session.execute(stmt)
    return result.scalars().all()


async def create_tenant(
    session: AsyncSession,
    name: str,
    slug: str | None = None,
) -> Tenant:
    tenant = Tenant(
        name=name,
        slug=slug or name.lower().replace(" ", "-"),
        is_active=True,
    )
    session.add(tenant)
    await session.flush()
    await session.refresh(tenant)
    return tenant


async def get_tenant_stats(session: AsyncSession, tenant_id: int) -> dict[str, Any]:
    ticket_counts = await session.execute(
        select(
            Ticket.status,
            func.count(Ticket.id).label("count")
        )
        .where(Ticket.tenant_id == tenant_id)
        .group_by(Ticket.status)
    )
    tickets_by_status: dict[str, int] = {row.status: row.count for row in ticket_counts}

    total_tickets = sum(tickets_by_status.values())
    
    user_count = await session.execute(
        select(func.count(User.id)).where(User.tenant_id == tenant_id)
    )
    
    kb_count = await session.execute(
        select(func.count(KBChunk.id))
        .where(and_(KBChunk.tenant_id == tenant_id, KBChunk.is_current.is_(True)))
    )
    
    return {
        "tickets_by_status": tickets_by_status,
        "total_tickets": total_tickets,
        "total_users": user_count.scalar_one(),
        "total_kb_chunks": kb_count.scalar_one(),
    }


async def get_user_by_email(
    session: AsyncSession,
    tenant_id: int,
    email: str,
) -> User | None:
    stmt = select(User).where(
        and_(User.tenant_id == tenant_id, User.email == email)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def create_user(
    session: AsyncSession,
    tenant_id: int,
    email: str,
    hashed_password: str,
    full_name: str | None = None,
    role: str = "user",
) -> User:
    user = User(
        tenant_id=tenant_id,
        email=email,
        hashed_password=hashed_password,
        full_name=full_name,
        role=role,
        is_active=True,
    )
    session.add(user)
    await session.flush()
    await session.refresh(user)
    return user


async def list_tickets(
    session: AsyncSession,
    tenant_id: int,
    status: str | None = None,
    skip: int = 0,
    limit: int = 100,
    load_messages: bool = True,  # Changed default to True to prevent N+1
) -> Sequence[Ticket]:
    """List tickets for a tenant.

    Args:
        session: Database session
        tenant_id: Tenant ID
        status: Optional status filter
        skip: Number of records to skip
        limit: Maximum number of records
        load_messages: Load messages with tickets (default: True to avoid N+1 queries)

    Returns:
        Sequence of tickets
    """
    stmt = (
        select(Ticket)
        .where(Ticket.tenant_id == tenant_id)
        .order_by(desc(Ticket.updated_at))
        .offset(skip)
        .limit(limit)
    )

    if status:
        stmt = stmt.where(Ticket.status == status)

    if load_messages:
        stmt = stmt.options(selectinload(Ticket.messages))

    result = await session.execute(stmt)
    return result.scalars().all()


async def get_ticket(
    session: AsyncSession,
    tenant_id: int,
    ticket_id: int,
    load_messages: bool = True,  # Changed default to True to prevent N+1
) -> Ticket | None:
    """Get a single ticket by ID.

    Args:
        session: Database session
        tenant_id: Tenant ID
        ticket_id: Ticket ID
        load_messages: Load messages with ticket (default: True to avoid N+1 queries)

    Returns:
        Ticket or None if not found
    """
    stmt = select(Ticket).where(
        and_(Ticket.tenant_id == tenant_id, Ticket.id == ticket_id)
    )

    if load_messages:
        stmt = stmt.options(selectinload(Ticket.messages))

    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def create_ticket(
    session: AsyncSession,
    tenant_id: int,
    title: str,
    description: str | None = None,
    priority: str = "medium",
    source: str = "web",
    created_by_id: int | None = None,
    metadata: dict[str, Any] | None = None,
) -> Ticket:
    ticket = Ticket(
        tenant_id=tenant_id,
        title=title,
        description=description,
        priority=priority,
        source=source,
        status="open",
        created_by_id=created_by_id,
        metadata_json=metadata,
    )
    session.add(ticket)
    await session.flush()
    await session.refresh(ticket)
    return ticket


async def update_ticket(
    session: AsyncSession,
    ticket_id: int,
    **kwargs: Any,
) -> Ticket | None:
    update_data = {k: v for k, v in kwargs.items() if v is not None}
    
    if not update_data:
        result = await session.execute(
            select(Ticket).where(Ticket.id == ticket_id)
        )
        return result.scalar_one_or_none()
    
    update_data["updated_at"] = datetime.now(timezone.utc)
    
    stmt = (
        update(Ticket)
        .where(Ticket.id == ticket_id)
        .values(**update_data)
        .returning(Ticket)
    )
    result = await session.execute(stmt)
    await session.flush()
    
    ticket = result.scalar_one_or_none()
    if ticket:
        await session.refresh(ticket)
    return ticket


async def delete_ticket(
    session: AsyncSession,
    tenant_id: int,
    ticket_id: int,
) -> bool:
    stmt = delete(Ticket).where(
        and_(Ticket.tenant_id == tenant_id, Ticket.id == ticket_id)
    )
    result = await session.execute(stmt)
    return result.rowcount > 0


async def get_ticket_messages(
    session: AsyncSession,
    ticket_id: int,
    skip: int = 0,
    limit: int = 100,
) -> Sequence[Message]:
    stmt = (
        select(Message)
        .where(Message.ticket_id == ticket_id)
        .order_by(Message.created_at)
        .offset(skip)
        .limit(limit)
    )
    result = await session.execute(stmt)
    return result.scalars().all()


async def create_message(
    session: AsyncSession,
    ticket_id: int,
    content: str,
    role: str = "user",
    metadata: dict[str, Any] | None = None,
) -> Message:
    message = Message(
        ticket_id=ticket_id,
        content=content,
        role=role,
        metadata_json=metadata,
    )
    session.add(message)
    await session.flush()
    await session.refresh(message)
    return message


async def upsert_kb_chunks(
    session: AsyncSession,
    tenant_id: int,
    source: str,
    chunks: list[dict[str, Any]],
) -> dict[str, int]:
    created = 0
    updated = 0
    skipped = 0
    
    for chunk_data in chunks:
        content = chunk_data.get("content", chunk_data.get("chunk", ""))
        if not content:
            skipped += 1
            continue
        
        chunk_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        
        stmt = insert(KBChunk).values(
            tenant_id=tenant_id,
            source=source,
            chunk=content,
            chunk_hash=chunk_hash,
            metadata_json=chunk_data.get("metadata"),
            is_current=True,
            version=1,
        )
        
        stmt = stmt.on_conflict_do_update(
            index_elements=['tenant_id', 'chunk_hash'],
            set_={
                'source': source,
                'updated_at': datetime.now(timezone.utc),
            }
        )
        
        result = await session.execute(stmt)
        
        if result.rowcount == 1:
            created += 1
        else:
            updated += 1
    
    await session.flush()
    return {"created": created, "updated": updated, "skipped": skipped}


async def delete_kb_source(
    session: AsyncSession,
    tenant_id: int,
    source: str,
) -> int:
    stmt = (
        delete(KBChunk)
        .where(
            and_(
                KBChunk.tenant_id == tenant_id,
                KBChunk.source == source,
            )
        )
    )
    result = await session.execute(stmt)
    await session.flush()
    return result.rowcount


async def upsert_external_ref(
    session: AsyncSession,
    tenant_id: int,
    ticket_id: int,
    system: str,
    reference: str,
    metadata: dict[str, Any] | None = None,
    external_url: str | None = None,
) -> TicketExternalRef:
    """Upsert external reference for a ticket.

    Args:
        session: Database session
        tenant_id: Tenant ID
        ticket_id: Ticket ID
        system: External system name (jira, zendesk, etc.)
        reference: External reference ID
        metadata: Optional metadata
        external_url: Optional external URL (will be validated)

    Returns:
        TicketExternalRef

    Raises:
        ValueError: If external_url is invalid
    """
    # Validate external_url if provided
    if external_url is not None:
        from pydantic import HttpUrl, ValidationError
        try:
            # Validate URL format
            HttpUrl(external_url)
        except ValidationError:
            raise ValueError(f"Invalid external_url: {external_url}")

    stmt = insert(TicketExternalRef).values(
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        system=system,
        reference=reference,
        external_url=external_url,
        metadata_json=metadata,
    )
    
    update_dict = {
        'reference': reference,
        'metadata_json': metadata,
        'updated_at': datetime.now(timezone.utc),
    }
    if external_url is not None:
        update_dict['external_url'] = external_url

    stmt = stmt.on_conflict_do_update(
        index_elements=['tenant_id', 'ticket_id', 'system'],
        set_=update_dict
    )
    
    await session.execute(stmt)
    await session.flush()

    ref_result = await session.execute(
        select(TicketExternalRef).where(
            and_(
                TicketExternalRef.tenant_id == tenant_id,
                TicketExternalRef.ticket_id == ticket_id,
                TicketExternalRef.system == system,
            )
        )
    )
    return ref_result.scalar_one()


async def get_external_ref(
    session: AsyncSession,
    tenant_id: int,
    ticket_id: int,
    system: str,
) -> TicketExternalRef | None:
    stmt = select(TicketExternalRef).where(
        and_(
            TicketExternalRef.tenant_id == tenant_id,
            TicketExternalRef.ticket_id == ticket_id,
            TicketExternalRef.system == system,
        )
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def record_integration_sync(
    session: AsyncSession,
    tenant_id: int,
    ticket_id: int,
    system: str,
    status: str,
    details: dict[str, Any] | None = None,
) -> IntegrationSyncLog:
    log = IntegrationSyncLog(
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        system=system,
        status=status,
        details=details,
    )
    session.add(log)
    await session.flush()
    await session.refresh(log)
    return log


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, user_id: int) -> User | None:
        stmt = select(User).where(User.id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email(self, tenant_id: int, email: str) -> User | None:
        return await get_user_by_email(self.session, tenant_id, email)

    async def create(
        self,
        tenant_id: int,
        email: str,
        hashed_password: str,
        full_name: str | None = None,
        role: str = "user",
    ) -> User:
        return await create_user(
            self.session,
            tenant_id=tenant_id,
            email=email,
            hashed_password=hashed_password,
            full_name=full_name,
            role=role,
        )

    async def update(self, user_id: int, **kwargs: Any) -> User | None:
        update_data = {k: v for k, v in kwargs.items() if v is not None}
        
        if not update_data:
            return await self.get_by_id(user_id)
        
        update_data["updated_at"] = datetime.now(timezone.utc)
        
        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(**update_data)
            .returning(User)
        )
        result = await self.session.execute(stmt)
        await self.session.flush()
        
        user = result.scalar_one_or_none()
        if user:
            await self.session.refresh(user)
        return user

    async def list_by_tenant(
        self,
        tenant_id: int,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[User]:
        stmt = (
            select(User)
            .where(User.tenant_id == tenant_id)
            .order_by(User.id)
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()


class TenantRepository:
    """Repository for Tenant operations - fully self-contained implementation."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, tenant_id: int) -> Tenant | None:
        """Get tenant by ID."""
        stmt = select(Tenant).where(Tenant.id == tenant_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> Tenant | None:
        """Get tenant by slug."""
        stmt = select(Tenant).where(Tenant.slug == slug)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list(self, skip: int = 0, limit: int = 100) -> Sequence[Tenant]:
        """List all tenants with pagination."""
        stmt = select(Tenant).order_by(Tenant.id).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def create(self, name: str, slug: str | None = None) -> Tenant:
        """Create a new tenant."""
        tenant = Tenant(
            name=name,
            slug=slug or name.lower().replace(" ", "-"),
            is_active=True,
        )
        self.session.add(tenant)
        await self.session.flush()
        await self.session.refresh(tenant)
        return tenant

    async def update(self, tenant_id: int, **kwargs: Any) -> Tenant | None:
        """Update tenant by ID."""
        stmt = (
            update(Tenant)
            .where(Tenant.id == tenant_id)
            .values(**kwargs, updated_at=datetime.now(timezone.utc))
            .returning(Tenant)
        )
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.scalar_one_or_none()

    async def get_stats(self, tenant_id: int) -> dict[str, Any]:
        """Get statistics for a tenant."""
        # Get ticket counts by status
        ticket_counts = await self.session.execute(
            select(
                Ticket.status,
                func.count(Ticket.id).label("count")
            )
            .where(Ticket.tenant_id == tenant_id)
            .group_by(Ticket.status)
        )
        tickets_by_status: dict[str, int] = {row.status: row.count for row in ticket_counts}

        total_tickets = sum(tickets_by_status.values())

        # Get user count
        user_count = await self.session.execute(
            select(func.count(User.id)).where(User.tenant_id == tenant_id)
        )

        # Get KB chunk count
        kb_count = await self.session.execute(
            select(func.count(KBChunk.id))
            .where(and_(KBChunk.tenant_id == tenant_id, KBChunk.is_current.is_(True)))
        )

        return {
            "tickets_by_status": tickets_by_status,
            "total_tickets": total_tickets,
            "total_users": user_count.scalar_one(),
            "total_kb_chunks": kb_count.scalar_one(),
        }


class TicketRepository:
    """Repository for Ticket operations - fully self-contained implementation."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(
        self, ticket_id: int, load_messages: bool = False
    ) -> Ticket | None:
        """Get ticket by ID."""
        stmt = select(Ticket).where(Ticket.id == ticket_id)

        if load_messages:
            stmt = stmt.options(selectinload(Ticket.messages))

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get(self, tenant_id: int, ticket_id: int) -> Ticket | None:
        """Get ticket by ID and tenant (tenant-scoped)."""
        stmt = select(Ticket).where(
            and_(Ticket.id == ticket_id, Ticket.tenant_id == tenant_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(
        self,
        tenant_id: int,
        title: str,
        description: str | None = None,
        priority: str = "medium",
        source: str = "web",
        created_by_id: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Ticket:
        """Create a new ticket."""
        ticket = Ticket(
            tenant_id=tenant_id,
            title=title,
            description=description,
            priority=priority,
            source=source,
            status="open",
            created_by_id=created_by_id,
            metadata_json=metadata,
        )
        self.session.add(ticket)
        await self.session.flush()
        await self.session.refresh(ticket)
        return ticket

    async def update(self, ticket_id: int, **kwargs: Any) -> Ticket | None:
        """Update ticket by ID."""
        update_data = {k: v for k, v in kwargs.items() if v is not None}

        if not update_data:
            result = await self.session.execute(
                select(Ticket).where(Ticket.id == ticket_id)
            )
            return result.scalar_one_or_none()

        update_data["updated_at"] = datetime.now(timezone.utc)

        stmt = (
            update(Ticket)
            .where(Ticket.id == ticket_id)
            .values(**update_data)
            .returning(Ticket)
        )
        result = await self.session.execute(stmt)
        await self.session.flush()

        ticket = result.scalar_one_or_none()
        if ticket:
            await self.session.refresh(ticket)
        return ticket

    async def list(
        self,
        tenant_id: int,
        status: str | None = None,
        skip: int = 0,
        limit: int = 100,
        load_messages: bool = False,
    ) -> Sequence[Ticket]:
        """List tickets for a tenant with optional filtering."""
        stmt = select(Ticket).where(Ticket.tenant_id == tenant_id)

        if status:
            stmt = stmt.where(Ticket.status == status)

        if load_messages:
            stmt = stmt.options(selectinload(Ticket.messages))

        stmt = stmt.order_by(desc(Ticket.created_at)).offset(skip).limit(limit)

        result = await self.session.execute(stmt)
        return result.scalars().all()

    # Backward compatibility alias
    async def list_by_tenant(
        self,
        tenant_id: int,
        status: str | None = None,
        skip: int = 0,
        limit: int = 100,
        load_messages: bool = False,
    ) -> Sequence[Ticket]:
        """Backward compatibility alias for list()."""
        return await self.list(tenant_id, status, skip, limit, load_messages)

    async def count(self, tenant_id: int, status: str | None = None) -> int:
        """Count tickets for a tenant."""
        stmt = select(func.count(Ticket.id)).where(Ticket.tenant_id == tenant_id)

        if status:
            stmt = stmt.where(Ticket.status == status)

        result = await self.session.execute(stmt)
        return result.scalar_one()

    # Backward compatibility alias
    async def count_by_tenant(
        self, tenant_id: int, status: str | None = None
    ) -> int:
        """Backward compatibility alias for count()."""
        return await self.count(tenant_id, status)

    async def delete(self, tenant_id: int, ticket_id: int) -> bool:
        """Delete a ticket."""
        stmt = delete(Ticket).where(
            and_(Ticket.tenant_id == tenant_id, Ticket.id == ticket_id)
        )
        result = await self.session.execute(stmt)
        return result.rowcount > 0


class MessageRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_by_ticket(
        self, ticket_id: int, skip: int = 0, limit: int = 100
    ) -> Sequence[Message]:
        return await get_ticket_messages(self.session, ticket_id, skip, limit)

    async def create(
        self,
        ticket_id: int,
        content: str,
        role: str = "user",
        metadata: dict[str, Any] | None = None,
    ) -> Message:
        return await create_message(self.session, ticket_id, content, role, metadata)


class KBChunkRepository:
    """Repository for KB Chunk operations - fully self-contained implementation."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, chunk_id: int) -> KBChunk | None:
        """Get KB chunk by ID."""
        stmt = select(KBChunk).where(KBChunk.id == chunk_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_hash(
        self, tenant_id: int, chunk_hash: str
    ) -> KBChunk | None:
        """Get KB chunk by hash for a tenant."""
        stmt = select(KBChunk).where(
            and_(
                KBChunk.tenant_id == tenant_id,
                KBChunk.chunk_hash == chunk_hash,
                KBChunk.is_current.is_(True),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def search_by_embedding(
        self,
        tenant_id: int,
        embedding: list[float],
        limit: int = 5,
    ) -> Sequence[KBChunk]:
        """Search KB chunks by embedding similarity."""
        try:
            stmt = (
                select(KBChunk)
                .where(
                    and_(
                        KBChunk.tenant_id == tenant_id,
                        KBChunk.is_current.is_(True),
                        KBChunk.embedding_vector.isnot(None),
                    )
                )
                .order_by(KBChunk.embedding_vector.cosine_distance(embedding))
                .limit(limit)
            )
        except Exception as e:
            logger.warning(f"Vector search not available, falling back to basic search: {e}")
            stmt = (
                select(KBChunk)
                .where(
                    and_(
                        KBChunk.tenant_id == tenant_id,
                        KBChunk.is_current.is_(True),
                    )
                )
                .limit(limit)
            )

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def archive_by_source(self, tenant_id: int, source: str) -> int:
        """Archive all chunks from a source."""
        stmt = (
            update(KBChunk)
            .where(
                and_(
                    KBChunk.tenant_id == tenant_id,
                    KBChunk.source == source,
                    KBChunk.is_current.is_(True),
                )
            )
            .values(is_current=False, archived_at=datetime.now(timezone.utc))
        )
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount

    async def list_by_tenant(
        self, tenant_id: int, skip: int = 0, limit: int = 100
    ) -> Sequence[KBChunk]:
        """List KB chunks for a tenant with pagination."""
        stmt = (
            select(KBChunk)
            .where(
                and_(
                    KBChunk.tenant_id == tenant_id,
                    KBChunk.is_current.is_(True),
                )
            )
            .order_by(desc(KBChunk.created_at))
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def upsert(
        self,
        tenant_id: int,
        source: str,
        chunks: list[dict[str, Any]],
    ) -> dict[str, int]:
        """Upsert KB chunks for a tenant and source.

        Args:
            tenant_id: Tenant ID
            source: Source identifier
            chunks: List of chunk dictionaries with 'content'/'chunk' and optional 'metadata'

        Returns:
            Dictionary with counts: created, updated, skipped
        """
        created = 0
        updated = 0
        skipped = 0

        for chunk_data in chunks:
            content = chunk_data.get("content", chunk_data.get("chunk", ""))
            if not content:
                skipped += 1
                continue

            chunk_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()

            stmt = insert(KBChunk).values(
                tenant_id=tenant_id,
                source=source,
                chunk=content,
                chunk_hash=chunk_hash,
                metadata_json=chunk_data.get("metadata"),
                is_current=True,
                version=1,
            )

            stmt = stmt.on_conflict_do_update(
                index_elements=['tenant_id', 'chunk_hash'],
                set_={
                    'source': source,
                    'updated_at': datetime.now(timezone.utc),
                }
            )

            result = await self.session.execute(stmt)

            if result.rowcount == 1:
                created += 1
            else:
                updated += 1

        await self.session.flush()
        return {"created": created, "updated": updated, "skipped": skipped}

    async def delete_source(self, tenant_id: int, source: str) -> int:
        """Delete all chunks from a source for a tenant.

        Args:
            tenant_id: Tenant ID
            source: Source identifier

        Returns:
            Number of deleted chunks
        """
        stmt = (
            delete(KBChunk)
            .where(
                and_(
                    KBChunk.tenant_id == tenant_id,
                    KBChunk.source == source,
                )
            )
        )
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount


__all__ = [
    "list_tenants",
    "create_tenant",
    "get_tenant_stats",
    "get_user_by_email",
    "create_user",
    "list_tickets",
    "get_ticket",
    "create_ticket",
    "update_ticket",
    "delete_ticket",
    "get_ticket_messages",
    "create_message",
    "upsert_kb_chunks",
    "delete_kb_source",
    "upsert_external_ref",
    "get_external_ref",
    "record_integration_sync",
    "UserRepository",
    "TenantRepository",
    "TicketRepository",
    "MessageRepository",
    "KBChunkRepository",
]
