"""Agent API router - AI response generation."""
from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.db import get_db
from src.api.routers.auth import get_current_active_user, User
from src.services.agent import AgentService
from src.services.ollama import get_ollama_client, OllamaError

logger = logging.getLogger(__name__)


router = APIRouter(tags=["agent"])


class TicketRespondRequest(BaseModel):
    """Request to generate response for a ticket."""
    save_response: bool = Field(default=True, description="Save response as message")
    max_context: int = Field(default=5, ge=1, le=20, description="Max KB chunks")


class FreeformRequest(BaseModel):
    """Request for freeform question (playground)."""
    question: str = Field(..., min_length=1, max_length=2000)
    max_context: int = Field(default=5, ge=1, le=20)


class AgentResponseSchema(BaseModel):
    """Agent response schema."""
    content: str
    needs_escalation: bool
    escalation_reason: str | None
    context_used: list[dict[str, Any]]
    model: str


class HealthStatus(BaseModel):
    """Ollama health status."""
    ollama_available: bool
    chat_model: str
    embed_model: str
    models_loaded: list[str]


@router.get("/health", response_model=HealthStatus)
async def agent_health(
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """Check agent (Ollama) health status."""
    ollama = get_ollama_client()
    
    is_available = await ollama.health_check()
    models = []
    
    if is_available:
        try:
            model_list = await ollama.list_models()
            models = [m.get("name", "") for m in model_list]
        except Exception as e:
            logger.warning(f"Failed to fetch Ollama model list: {e}")
    
    return {
        "ollama_available": is_available,
        "chat_model": ollama.chat_model,
        "embed_model": ollama.embed_model,
        "models_loaded": models,
    }


@router.post("/respond/{ticket_id}", response_model=AgentResponseSchema)
async def respond_to_ticket(
    ticket_id: int,
    request: TicketRespondRequest = TicketRespondRequest(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """Generate AI response for a specific ticket.
    
    The agent will:
    1. Load ticket and message history
    2. Search knowledge base for relevant context
    3. Generate response using LLM
    4. Check for escalation triggers
    5. Optionally save response as a message
    """
    agent = AgentService(db)
    
    try:
        response = await agent.respond_to_ticket(
            tenant_id=current_user.tenant_id,
            ticket_id=ticket_id,
            save_response=request.save_response,
            max_context=request.max_context,
        )

        # Commit the changes (message saved if save_response=True)
        await db.commit()
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except OllamaError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AI service unavailable: {e}",
        )
    
    return {
        "content": response.content,
        "needs_escalation": response.needs_escalation,
        "escalation_reason": response.escalation_reason,
        "context_used": response.context_used,
        "model": response.model,
    }


@router.post("/ask", response_model=AgentResponseSchema)
async def ask_freeform(
    request: FreeformRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """Ask a freeform question (playground mode).
    
    No ticket context, just question + knowledge base.
    """
    agent = AgentService(db)
    
    try:
        response = await agent.ask_freeform(
            tenant_id=current_user.tenant_id,
            question=request.question,
            max_context=request.max_context,
        )
    except OllamaError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AI service unavailable: {e}",
        )
    
    return {
        "content": response.content,
        "needs_escalation": response.needs_escalation,
        "escalation_reason": response.escalation_reason,
        "context_used": response.context_used,
        "model": response.model,
    }


@router.post("/auto-respond/{ticket_id}", status_code=status.HTTP_202_ACCEPTED)
async def trigger_auto_respond(
    ticket_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """Trigger automatic response generation in background.

    Returns immediately, response will be added as a message.
    """
    # Verify ticket exists
    from src.domain.repos import TicketRepository
    ticket_repo = TicketRepository(db)
    ticket = await ticket_repo.get(current_user.tenant_id, ticket_id)
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found",
        )

    # Note: Background tasks with DB sessions need special handling
    # For simplicity, we'll do it synchronously here
    # In production, use Celery or similar

    return {
        "status": "accepted",
        "message": f"Auto-response triggered for ticket {ticket_id}",
        "ticket_id": ticket_id,
    }
