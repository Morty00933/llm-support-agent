"""Dispatcher that fans-out ticket updates to external systems asynchronously."""

from __future__ import annotations

from typing import Any, Sequence

from sqlalchemy import select

from ...core.config import settings
from ...core.db import SessionLocal
from ...domain.models import Ticket, Message
from ...domain import repos
from .jira import JiraClient, JiraError
from .zendesk import ZendeskClient, ZendeskError


async def _load_ticket_with_message(
    ticket_id: int, tenant_id: int, message_id: int | None
):
    async with SessionLocal() as session:
        ticket = await session.get(Ticket, ticket_id)
        if not ticket or ticket.tenant_id != tenant_id:
            raise ValueError("ticket not found")
        message: Message | None = None
        if message_id is not None:
            message = await session.get(Message, message_id)
        if message is None:
            message = (
                (
                    await session.execute(
                        select(Message)
                        .where(Message.ticket_id == ticket.id)
                        .order_by(Message.id.desc())
                        .limit(1)
                    )
                )
                .scalars()
                .first()
            )
        messages = await repos.list_messages(session, ticket.id, limit=50)
        await session.commit()
        return ticket, message, messages


def _render_conversation(messages: Sequence[Message]) -> str:
    lines: list[str] = []
    for msg in messages:
        role = msg.role or "user"
        lines.append(f"[{role}] {msg.content.strip()}")
    return "\n".join(lines)


def _render_kb_hits(kb_hits: Sequence[dict[str, Any]] | None) -> str:
    if not kb_hits:
        return "(no KB hits)"
    lines: list[str] = []
    for hit in kb_hits:
        source = hit.get("source", "unknown")
        score = hit.get("score")
        chunk = hit.get("chunk", "").strip()
        lines.append(f"- {source} (score={score}): {chunk[:400]}")
    return "\n".join(lines)


async def _sync_jira(
    ticket: Ticket,
    message: Message | None,
    conversation: str,
    kb_hits: Sequence[dict[str, Any]] | None,
    escalate: bool,
) -> dict[str, Any]:
    if not settings.JIRA_ENABLED:
        return {"skipped": True, "reason": "jira disabled"}
    if not all(
        [
            settings.JIRA_BASE_URL,
            settings.JIRA_EMAIL,
            settings.JIRA_API_TOKEN,
            settings.JIRA_PROJECT_KEY,
        ]
    ):
        return {"skipped": True, "reason": "jira config incomplete"}

    async with SessionLocal() as session:
        client = JiraClient(
            settings.JIRA_BASE_URL,
            settings.JIRA_EMAIL,
            settings.JIRA_API_TOKEN,
        )
        ref = await repos.get_external_ref(session, ticket.id, "jira")
        description = (
            f"Tenant #{ticket.tenant_id} ticket #{ticket.id}: {ticket.title}\n\n"
            f"Latest assistant reply:\n{(message.content if message else 'n/a')}\n\n"
            f"Conversation:\n{conversation}\n\n"
            f"KB context:\n{_render_kb_hits(kb_hits)}"
        )
        result: dict[str, Any]
        try:
            if ref is None:
                issue = await client.create_issue(
                    project_key=settings.JIRA_PROJECT_KEY,
                    summary=f"Ticket #{ticket.id}: {ticket.title}",
                    description=description,
                    issue_type=settings.JIRA_ISSUE_TYPE or "Task",
                )
                key = issue.get("key") or issue.get("id")
                await repos.upsert_external_ref(
                    session,
                    tenant_id=ticket.tenant_id,
                    ticket_id=ticket.id,
                    system="jira",
                    reference=str(key),
                    metadata={"url": issue.get("self")},
                )
                result = {"created": True, "key": key}
            else:
                await client.add_comment(ref.reference, description)
                result = {"created": False, "key": ref.reference}
                if escalate and settings.JIRA_ESCALATION_TRANSITION:
                    try:
                        await client.transition_issue(
                            ref.reference, settings.JIRA_ESCALATION_TRANSITION
                        )
                        result["transitioned"] = True
                    except JiraError as err:  # pragma: no cover
                        result["transition_error"] = str(err)
        except JiraError as err:
            result = {"error": str(err)}
        await session.commit()
        return result


async def _sync_zendesk(
    ticket: Ticket,
    message: Message | None,
    conversation: str,
    kb_hits: Sequence[dict[str, Any]] | None,
    escalate: bool,
) -> dict[str, Any]:
    if not settings.ZENDESK_ENABLED:
        return {"skipped": True, "reason": "zendesk disabled"}
    if not all(
        [
            settings.ZENDESK_SUBDOMAIN,
            settings.ZENDESK_EMAIL,
            settings.ZENDESK_API_TOKEN,
        ]
    ):
        return {"skipped": True, "reason": "zendesk config incomplete"}

    async with SessionLocal() as session:
        client = ZendeskClient(
            subdomain=settings.ZENDESK_SUBDOMAIN,
            email=settings.ZENDESK_EMAIL,
            api_token=settings.ZENDESK_API_TOKEN,
        )
        ref = await repos.get_external_ref(session, ticket.id, "zendesk")
        comment = (
            f"Assistant reply:\n{(message.content if message else 'n/a')}\n\n"
            f"Conversation:\n{conversation}\n\n"
            f"KB context:\n{_render_kb_hits(kb_hits)}"
        )
        result: dict[str, Any]
        try:
            if ref is None:
                ticket_payload = await client.create_ticket(
                    subject=f"Tenant {ticket.tenant_id} ticket #{ticket.id}: {ticket.title}",
                    comment=comment,
                    priority=(
                        "urgent"
                        if escalate
                        else (settings.ZENDESK_DEFAULT_PRIORITY or "normal")
                    ),
                    tags=["llm-agent", "tenant-%s" % ticket.tenant_id],
                )
                ticket_id = ticket_payload.get("ticket", {}).get("id")
                await repos.upsert_external_ref(
                    session,
                    tenant_id=ticket.tenant_id,
                    ticket_id=ticket.id,
                    system="zendesk",
                    reference=str(ticket_id),
                    metadata={"url": ticket_payload.get("ticket", {}).get("url")},
                )
                result = {"created": True, "id": ticket_id}
            else:
                await client.add_comment(int(ref.reference), comment, public=True)
                result = {"created": False, "id": ref.reference}
        except ZendeskError as err:
            result = {"error": str(err)}
        await session.commit()
        return result


async def dispatch_ticket_sync(
    *,
    ticket_id: int,
    tenant_id: int,
    message_id: int | None,
    kb_hits: Sequence[dict[str, Any]] | None,
    escalate: bool,
) -> dict[str, Any]:
    if not (settings.JIRA_ENABLED or settings.ZENDESK_ENABLED):
        return {"skipped": True, "reason": "no integrations enabled"}

    try:
        ticket, message, messages = await _load_ticket_with_message(
            ticket_id, tenant_id, message_id
        )
    except ValueError as err:
        return {"error": str(err)}

    conversation = _render_conversation(messages)
    results: dict[str, Any] = {}
    if settings.JIRA_ENABLED:
        results["jira"] = await _sync_jira(
            ticket, message, conversation, kb_hits, escalate
        )
    if settings.ZENDESK_ENABLED:
        results["zendesk"] = await _sync_zendesk(
            ticket, message, conversation, kb_hits, escalate
        )
    return results
