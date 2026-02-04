from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.db import get_session_context
from src.domain import repos

logger = logging.getLogger(__name__)


async def dispatch_ticket_sync(
    ticket_id: int,
    tenant_id: int,
    message_id: int | None = None,
    kb_hits: list[dict[str, Any]] | None = None,
    escalate: bool = False,
) -> dict[str, Any]:
    results: dict[str, Any] = {
        "ticket_id": ticket_id,
        "tenant_id": tenant_id,
        "synced_systems": [],
        "errors": [],
    }
    
    jira_enabled = settings.jira_enabled
    zendesk_enabled = settings.zendesk_enabled
    
    if not jira_enabled and not zendesk_enabled:
        logger.debug("No integrations enabled, skipping sync")
        results["message"] = "No integrations enabled"
        return results
    
    ticket_data = None
    async with get_session_context() as session:
        ticket = await repos.get_ticket(session, tenant_id, ticket_id, load_messages=False)
        if not ticket:
            logger.warning(f"Ticket {ticket_id} not found for tenant {tenant_id}")
            results["errors"].append(f"Ticket {ticket_id} not found")
            return results
        
        ticket_data = _serialize_ticket(ticket)
    
    if jira_enabled:
        try:
            jira_result = await _sync_to_jira(
                tenant_id, ticket_data, message_id, kb_hits, escalate
            )
            results["synced_systems"].append("jira")
            results["jira"] = jira_result
        except Exception as e:
            logger.error(f"Jira sync failed: {e}")
            results["errors"].append(f"Jira: {str(e)}")
    
    if zendesk_enabled:
        try:
            zendesk_result = await _sync_to_zendesk(
                tenant_id, ticket_data, message_id, kb_hits, escalate
            )
            results["synced_systems"].append("zendesk")
            results["zendesk"] = zendesk_result
        except Exception as e:
            logger.error(f"Zendesk sync failed: {e}")
            results["errors"].append(f"Zendesk: {str(e)}")
    
    async with get_session_context() as session:
        for system in results["synced_systems"]:
            await repos.record_integration_sync(
                session,
                tenant_id=tenant_id,
                ticket_id=ticket_id,
                system=system,
                status="success",
                details=results.get(system, {}),
            )
    
    return results


def _serialize_ticket(ticket: Any) -> dict[str, Any]:
    return {
        "id": ticket.id,
        "tenant_id": ticket.tenant_id,
        "title": ticket.title,
        "description": ticket.description,
        "status": ticket.status,
        "priority": ticket.priority,
        "created_at": ticket.created_at.isoformat() if ticket.created_at else None,
        "updated_at": ticket.updated_at.isoformat() if ticket.updated_at else None,
    }


async def _sync_to_jira(
    tenant_id: int,
    ticket: dict[str, Any],
    message_id: int | None,
    kb_hits: list[dict[str, Any]] | None,
    escalate: bool,
) -> dict[str, Any]:
    logger.info(f"Would sync ticket {ticket['id']} to Jira")
    return {"action": "skipped", "reason": "Jira client not configured"}


async def _sync_to_zendesk(
    tenant_id: int,
    ticket: dict[str, Any],
    message_id: int | None,
    kb_hits: list[dict[str, Any]] | None,
    escalate: bool,
) -> dict[str, Any]:
    logger.info(f"Would sync ticket {ticket['id']} to Zendesk")
    return {"action": "skipped", "reason": "Zendesk client not configured"}


async def dispatch_integration_sync(
    session: AsyncSession,
    tenant_id: int,
    ticket_id: int,
    system: str,
    reference: str,
    metadata: dict[str, Any] | None = None,
    status: str = "synced",
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    await repos.upsert_external_ref(
        session,
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        system=system.lower(),
        reference=reference,
        metadata=metadata or {},
    )

    await repos.record_integration_sync(
        session,
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        system=system.lower(),
        status=status,
        details=details or {},
    )

    logger.info(
        f"Integration sync completed: tenant={tenant_id} ticket={ticket_id} system={system} ref={reference}"
    )

    return {
        "system": system.lower(),
        "reference": reference,
        "status": "success",
        "message": f"Successfully synced with {system}",
    }


async def get_integration_reference(
    session: AsyncSession,
    tenant_id: int,
    ticket_id: int,
    system: str,
) -> dict[str, Any] | None:
    ref = await repos.get_external_ref(session, tenant_id, ticket_id, system.lower())
    if not ref:
        return None

    return {
        "system": ref.system,
        "reference": ref.reference,
        "metadata": ref.metadata_json or {},
        "created_at": ref.created_at.isoformat() if ref.created_at else None,
        "updated_at": ref.updated_at.isoformat() if ref.updated_at else None,
    }
