from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from ..deps import get_db, tenant_dep
from ...domain.models import Ticket, Message
from ...agent.loop import Agent, AgentResult

router = APIRouter(prefix="/v1/support", tags=["support"])

class AgentAnswerIn(BaseModel):
    """Свободная форма запроса к агенту (без привязки к тикету)."""
    query: str
    kb_limit: int = 5
    temperature: float = 0.2

class AgentAnswerOut(BaseModel):
    reply: str
    used_context: str | None
    kb_hits: list[dict]
    escalated: bool
    reason: str

@router.post("/answer", response_model=AgentAnswerOut)
async def answer_freeform(
    body: AgentAnswerIn,
    db: AsyncSession = Depends(get_db),
    tenant: int = Depends(tenant_dep),
):
    agent = Agent()
    res: AgentResult = await agent.answer_freeform(
        db,
        tenant_id=tenant,
        query=body.query,
        kb_limit=body.kb_limit,
        temperature=body.temperature,
    )
    return AgentAnswerOut(**res.__dict__)

class TicketAnswerOut(BaseModel):
    reply: str
    used_context: str | None
    kb_hits: list[dict]
    escalated: bool
    reason: str
    saved_message_id: int | None = None

@router.post("/tickets/{ticket_id}/answer", response_model=TicketAnswerOut)
async def answer_for_ticket(
    ticket_id: int,
    db: AsyncSession = Depends(get_db),
    tenant: int = Depends(tenant_dep),
    save: bool = Query(True, description="Сохранить ответ ассистента в сообщения тикета"),
    temperature: float = Query(0.2, ge=0, le=2.0),
    kb_limit: int = Query(5, ge=1, le=20),
):
    # Проверим тикет
    t = await db.get(Ticket, ticket_id)
    if not t or t.tenant_id != tenant:
        raise HTTPException(status_code=404, detail="ticket not found")

    agent = Agent()
    res: AgentResult = await agent.answer_for_ticket(
        db,
        tenant_id=tenant,
        ticket_id=ticket_id,
        kb_limit=kb_limit,
        temperature=temperature,
    )

    saved_id: int | None = None
    if save:
        m = Message(ticket_id=t.id, role="agent", content=res.reply)
        db.add(m)
        await db.flush()
        saved_id = m.id

    return TicketAnswerOut(
        reply=res.reply,
        used_context=res.used_context,
        kb_hits=res.kb_hits,
        escalated=res.escalated,
        reason=res.reason,
        saved_message_id=saved_id,
    )
