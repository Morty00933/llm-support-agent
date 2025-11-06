from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..deps import get_db, tenant_dep
from ...domain.models import Ticket, Message
from ...schemas.tickets import TicketIn, TicketOut, MessageIn, MessageOut

router = APIRouter(prefix="/v1/tickets", tags=["tickets"])

@router.get("/", response_model=list[TicketOut])
async def list_tickets(
    db: AsyncSession = Depends(get_db),
    tenant: int = Depends(tenant_dep),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    q = (
        select(Ticket)
        .where(Ticket.tenant_id == tenant)
        .order_by(Ticket.id.desc())
        .limit(limit)
        .offset(offset)
    )
    rows = (await db.execute(q)).scalars().all()
    return [TicketOut(id=r.id, title=r.title, status=r.status) for r in rows]

@router.post("/", response_model=TicketOut, status_code=status.HTTP_201_CREATED)
async def create_ticket(
    body: TicketIn,
    db: AsyncSession = Depends(get_db),
    tenant: int = Depends(tenant_dep),
):
    t = Ticket(tenant_id=tenant, title=body.title, status="open")
    db.add(t)
    await db.flush()
    return TicketOut(id=t.id, title=t.title, status=t.status)

@router.get("/{ticket_id}", response_model=TicketOut)
async def get_ticket(
    ticket_id: int,
    db: AsyncSession = Depends(get_db),
    tenant: int = Depends(tenant_dep),
):
    t = await db.get(Ticket, ticket_id)
    if not t or t.tenant_id != tenant:
        raise HTTPException(status_code=404, detail="ticket not found")
    return TicketOut(id=t.id, title=t.title, status=t.status)

@router.post("/{ticket_id}/messages", response_model=MessageOut, status_code=status.HTTP_201_CREATED)
async def add_message(
    ticket_id: int,
    body: MessageIn,
    db: AsyncSession = Depends(get_db),
    tenant: int = Depends(tenant_dep),
):
    t = await db.get(Ticket, ticket_id)
    if not t or t.tenant_id != tenant:
        raise HTTPException(status_code=404, detail="ticket not found")

    m = Message(ticket_id=t.id, role=body.role, content=body.content)
    db.add(m)
    await db.flush()
    return MessageOut(id=m.id, role=m.role, content=m.content)

@router.get("/{ticket_id}/messages", response_model=list[MessageOut])
async def list_messages(
    ticket_id: int,
    db: AsyncSession = Depends(get_db),
    tenant: int = Depends(tenant_dep),
):
    t = await db.get(Ticket, ticket_id)
    if not t or t.tenant_id != tenant:
        raise HTTPException(status_code=404, detail="ticket not found")

    rows = (await db.execute(
        select(Message).where(Message.ticket_id == t.id).order_by(Message.id.asc())
    )).scalars().all()
    return [MessageOut(id=r.id, role=r.role, content=r.content) for r in rows]
