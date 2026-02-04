"""Tickets router - REFACTORED with dependencies and exceptions."""
from __future__ import annotations

import logging
from typing import Any
from datetime import datetime

from fastapi import APIRouter, Depends, Query, Response, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import (
    get_ticket_or_404,
    require_admin,
    validate_ticket_access,
    validate_ticket_update_access,
)
from src.api.routers.auth import User, get_current_active_user
from src.core.db import get_db
from src.domain.repos import TicketRepository, MessageRepository
from src.domain.models import Ticket, TicketStatus

logger = logging.getLogger(__name__)


router = APIRouter(tags=["tickets"])


class TicketCreate(BaseModel):
    """Create ticket schema."""
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    priority: str = Field(default="medium")
    source: str = Field(default="web")
    metadata: dict[str, Any] | None = None
    auto_respond: bool = Field(default=True, description="Trigger AI auto-response")


class TicketUpdate(BaseModel):
    """Update ticket schema."""
    title: str | None = None
    description: str | None = None
    status: str | None = None
    priority: str | None = None
    assigned_to: int | None = None


class TicketResponse(BaseModel):
    """Ticket response schema."""
    id: int
    tenant_id: int
    title: str
    description: str | None
    status: str
    priority: str
    source: str
    assigned_to: int | None
    created_by_id: int | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MessageCreate(BaseModel):
    """Create message schema."""
    content: str = Field(..., min_length=1)
    role: str = Field(default="user")
    auto_respond: bool = Field(default=True, description="Trigger AI response for user messages")


class MessageResponse(BaseModel):
    """Message response schema."""
    id: int
    ticket_id: int
    role: str
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}


@router.get("", response_model=list[TicketResponse])
async def list_tickets(
    status: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[Ticket]:
    """List tickets for current user's tenant."""
    ticket_repo = TicketRepository(db)
    tickets = await ticket_repo.list(
        tenant_id=current_user.tenant_id,
        status=status,
        skip=skip,
        limit=limit,
    )
    return list(tickets)


@router.post("", response_model=TicketResponse, status_code=status.HTTP_201_CREATED)
async def create_ticket(
    ticket_data: TicketCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """Create a new ticket with optional AI auto-response.

    If auto_respond=True (default), the AI agent will automatically
    generate a response based on the ticket content and knowledge base.
    """
    # Create ticket
    ticket_repo = TicketRepository(db)
    ticket = await ticket_repo.create(
        tenant_id=current_user.tenant_id,
        title=ticket_data.title,
        description=ticket_data.description,
        priority=ticket_data.priority,
        source=ticket_data.source,
        created_by_id=current_user.id,
        metadata=ticket_data.metadata,
    )
    # First commit the ticket so it's visible for FK constraints
    await db.commit()
    await db.refresh(ticket)

    # Save all ticket attributes BEFORE auto_respond (which commits/rollbacks and expires the object)
    ticket_dict = {
        "id": ticket.id,
        "tenant_id": ticket.tenant_id,
        "title": ticket.title,
        "description": ticket.description,
        "status": ticket.status,
        "priority": ticket.priority,
        "source": ticket.source,
        "assigned_to": ticket.assigned_to,
        "created_by_id": ticket.created_by_id,
        "created_at": ticket.created_at,
        "updated_at": ticket.updated_at,
    }
    ticket_id = ticket_dict["id"]

    # Trigger auto-response if enabled
    if ticket_data.auto_respond:
        try:
            from src.services.agent import AgentService

            # Use the same session for agent
            agent = AgentService(db)
            await agent.respond_to_ticket(
                tenant_id=current_user.tenant_id,
                ticket_id=ticket_id,
                save_response=True,
            )
            logger.info(f"Auto-response generated for ticket {ticket_id}")
            # Commit the agent's changes (message, potential status update)
            await db.commit()

            # Refresh ticket to get updated status if agent changed it
            await db.refresh(ticket)
            ticket_dict["status"] = ticket.status
            ticket_dict["updated_at"] = ticket.updated_at
        except Exception as e:
            # Log error but don't fail ticket creation
            logger.warning(f"Auto-response failed for ticket {ticket_id}: {e}")
            await db.rollback()  # Rollback only agent's changes

    return ticket_dict


@router.get("/{ticket_id}", response_model=TicketResponse)
async def get_ticket(
    ticket: Ticket = Depends(validate_ticket_access),
) -> Ticket:
    """Get a specific ticket.

    Uses validate_ticket_access dependency which:
    - Validates ticket exists (get_ticket_or_404)
    - Checks user has permission to view ticket
    - Returns ticket if all checks pass
    """
    return ticket


@router.patch("/{ticket_id}", response_model=TicketResponse)
async def update_ticket(
    ticket_data: TicketUpdate,
    db: AsyncSession = Depends(get_db),
    ticket: Ticket = Depends(validate_ticket_update_access),
) -> Ticket:
    """Update a ticket.

    Uses validate_ticket_update_access dependency which:
    - Validates ticket exists
    - Checks user has permission to update ticket
    """
    update_data = ticket_data.model_dump(exclude_unset=True)
    if not update_data:
        return ticket

    ticket_repo = TicketRepository(db)
    updated = await ticket_repo.update(ticket.id, **update_data)
    return updated


@router.delete("/{ticket_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def delete_ticket(
    db: AsyncSession = Depends(get_db),
    ticket: Ticket = Depends(get_ticket_or_404),
    admin_user: User = Depends(require_admin),
):
    """Delete a ticket (admin only).

    Uses dependencies:
    - get_ticket_or_404: Validates ticket exists
    - require_admin: Ensures user has admin role
    """
    # Soft delete - just close the ticket
    ticket_repo = TicketRepository(db)
    await ticket_repo.update(ticket.id, status=TicketStatus.CLOSED.value)


@router.get("/{ticket_id}/messages", response_model=list[MessageResponse])
async def get_ticket_messages(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    ticket: Ticket = Depends(validate_ticket_access),
) -> list:
    """Get messages for a ticket.

    Uses validate_ticket_access to ensure ticket exists and user has access.
    """
    message_repo = MessageRepository(db)
    messages = await message_repo.list_by_ticket(ticket.id, skip, limit)
    return list(messages)


@router.post("/{ticket_id}/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def create_message(
    message_data: MessageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    ticket: Ticket = Depends(validate_ticket_access),
) -> dict:
    """Add a message to a ticket.

    If role='user' and auto_respond=True, the AI agent will
    automatically generate a response.

    Uses validate_ticket_access to ensure ticket exists and user has access.
    """
    # Create user message
    message_repo = MessageRepository(db)
    message = await message_repo.create(
        ticket_id=ticket.id,
        content=message_data.content,
        role=message_data.role,
    )
    await db.flush()
    # Commit is handled by get_db() dependency

    # Save message data before auto-respond (to avoid detached instance issues)
    message_dict = {
        "id": message.id,
        "ticket_id": message.ticket_id,
        "role": message.role,
        "content": message.content,
        "created_at": message.created_at,
    }

    # Trigger auto-response for user messages
    if message_data.role == "user" and message_data.auto_respond:
        try:
            from src.services.agent import AgentService

            agent = AgentService(db)
            await agent.respond_to_ticket(
                tenant_id=current_user.tenant_id,
                ticket_id=ticket.id,
                save_response=True,
            )
            logger.info(f"Auto-response generated for message in ticket {ticket.id}")
        except Exception as e:
            logger.warning(f"Auto-response failed for ticket {ticket.id}: {e}")

    return message_dict
