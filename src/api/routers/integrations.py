from __future__ import annotations


from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.db import get_db
from src.domain import repos
from src.api.routers.auth import get_current_active_user, User


router = APIRouter(tags=["integrations"])


class JiraTicketCreate(BaseModel):
    ticket_id: int
    summary: str | None = None
    description: str | None = None


class ZendeskTicketCreate(BaseModel):
    ticket_id: int
    subject: str | None = None
    comment: str | None = None


class IntegrationStatus(BaseModel):
    system: str
    enabled: bool
    configured: bool
    last_sync: str | None = None


class ExternalRefResponse(BaseModel):
    id: int
    ticket_id: int
    system: str
    reference: str


@router.get("/status", response_model=list[IntegrationStatus])
async def get_integrations_status(
    current_user: User = Depends(get_current_active_user),
) -> list[dict]:
    return [
        {
            "system": "jira",
            "enabled": settings.jira_enabled,
            "configured": bool(settings.jira_base_url and settings.jira_api_token),
            "last_sync": None,
        },
        {
            "system": "zendesk",
            "enabled": settings.zendesk_enabled,
            "configured": bool(settings.zendesk_subdomain and settings.zendesk_api_token),
            "last_sync": None,
        },
    ]


@router.post("/jira/sync", response_model=ExternalRefResponse)
async def sync_to_jira(
    data: JiraTicketCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    if not settings.jira_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Jira integration is not enabled",
        )
    
    ticket = await repos.get_ticket(db, current_user.tenant_id, data.ticket_id)
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found",
        )
    
    existing_ref = await repos.get_external_ref(
        db, current_user.tenant_id, data.ticket_id, "jira"
    )
    if existing_ref:
        return {
            "id": existing_ref.id,
            "ticket_id": existing_ref.ticket_id,
            "system": existing_ref.system,
            "reference": existing_ref.reference,
        }
    
    jira_key = f"{settings.jira_project_key}-{data.ticket_id}"
    
    ref = await repos.upsert_external_ref(
        db,
        tenant_id=current_user.tenant_id,
        ticket_id=data.ticket_id,
        system="jira",
        reference=jira_key,
        metadata={"summary": data.summary or ticket.title},
    )
    
    await repos.record_integration_sync(
        db,
        tenant_id=current_user.tenant_id,
        ticket_id=data.ticket_id,
        system="jira",
        status="success",
        details={"jira_key": jira_key},
    )
    
    await db.commit()
    
    return {
        "id": ref.id,
        "ticket_id": ref.ticket_id,
        "system": ref.system,
        "reference": ref.reference,
    }


@router.get("/jira/{ticket_id}", response_model=ExternalRefResponse | None)
async def get_jira_reference(
    ticket_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict | None:
    ticket = await repos.get_ticket(db, current_user.tenant_id, ticket_id)
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found",
        )
    
    ref = await repos.get_external_ref(db, current_user.tenant_id, ticket_id, "jira")
    if not ref:
        return None
    
    return {
        "id": ref.id,
        "ticket_id": ref.ticket_id,
        "system": ref.system,
        "reference": ref.reference,
    }


@router.post("/zendesk/sync", response_model=ExternalRefResponse)
async def sync_to_zendesk(
    data: ZendeskTicketCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    if not settings.zendesk_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Zendesk integration is not enabled",
        )
    
    ticket = await repos.get_ticket(db, current_user.tenant_id, data.ticket_id)
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found",
        )
    
    existing_ref = await repos.get_external_ref(
        db, current_user.tenant_id, data.ticket_id, "zendesk"
    )
    if existing_ref:
        return {
            "id": existing_ref.id,
            "ticket_id": existing_ref.ticket_id,
            "system": existing_ref.system,
            "reference": existing_ref.reference,
        }
    
    zendesk_id = f"ZD-{data.ticket_id}"
    
    ref = await repos.upsert_external_ref(
        db,
        tenant_id=current_user.tenant_id,
        ticket_id=data.ticket_id,
        system="zendesk",
        reference=zendesk_id,
        metadata={"subject": data.subject or ticket.title},
    )
    
    await repos.record_integration_sync(
        db,
        tenant_id=current_user.tenant_id,
        ticket_id=data.ticket_id,
        system="zendesk",
        status="success",
        details={"zendesk_id": zendesk_id},
    )
    
    await db.commit()
    
    return {
        "id": ref.id,
        "ticket_id": ref.ticket_id,
        "system": ref.system,
        "reference": ref.reference,
    }


@router.get("/zendesk/{ticket_id}", response_model=ExternalRefResponse | None)
async def get_zendesk_reference(
    ticket_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict | None:
    ticket = await repos.get_ticket(db, current_user.tenant_id, ticket_id)
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found",
        )
    
    ref = await repos.get_external_ref(db, current_user.tenant_id, ticket_id, "zendesk")
    if not ref:
        return None
    
    return {
        "id": ref.id,
        "ticket_id": ref.ticket_id,
        "system": ref.system,
        "reference": ref.reference,
    }
