from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from src.services.ollama import get_ollama_client, OllamaError
from src.services.embedding import EmbeddingService, SearchResult
from src.domain import repos
from src.agent.policies import should_escalate, SYSTEM_PROMPT, NO_CONTEXT_NOTE

logger = logging.getLogger(__name__)


DEFAULT_TEMPERATURE: float = 0.2


@dataclass
class AgentResponse:
    content: str
    needs_escalation: bool
    escalation_reason: str | None
    context_used: list[dict[str, Any]]
    model: str


def _orm_message_to_dict(msg: Any) -> dict[str, Any]:
    return {
        "id": msg.id,
        "ticket_id": msg.ticket_id,
        "role": msg.role,
        "content": msg.content,
        "created_at": msg.created_at,
        "metadata_json": msg.metadata_json,
    }


def _orm_ticket_to_dict(ticket: Any) -> dict[str, Any]:
    return {
        "id": ticket.id,
        "tenant_id": ticket.tenant_id,
        "title": ticket.title,
        "description": ticket.description,
        "status": ticket.status,
        "priority": ticket.priority,
        "created_at": ticket.created_at,
        "updated_at": ticket.updated_at,
    }


class AgentService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.ollama = get_ollama_client()
    
    async def respond_to_ticket(
        self,
        tenant_id: int,
        ticket_id: int,
        max_context: int = 5,
        save_response: bool = True,
    ) -> AgentResponse:
        ticket_orm = await repos.get_ticket(self.db, tenant_id, ticket_id)
        if not ticket_orm:
            raise ValueError(f"Ticket {ticket_id} not found")
        
        ticket = _orm_ticket_to_dict(ticket_orm)
        
        messages_orm = await repos.get_ticket_messages(self.db, ticket_id, limit=50)
        messages = [_orm_message_to_dict(msg) for msg in messages_orm]
        
        search_query = self._build_search_query(ticket, messages)
        
        context_chunks = await self._search_kb(
            tenant_id=tenant_id,
            query=search_query,
            limit=max_context,
        )
        
        last_user_message = self._get_last_user_message(ticket, messages)
        
        context_text = self._format_context(context_chunks)
        history_text = self._format_history(messages)
        
        system_prompt = SYSTEM_PROMPT.format(
            context=context_text if context_text else NO_CONTEXT_NOTE,
            history=history_text if history_text else "(Новый тикет, история пуста)",
        )
        
        try:
            response_text = await self.ollama.generate(
                prompt=last_user_message,
                system=system_prompt,
                temperature=DEFAULT_TEMPERATURE,
            )
        except OllamaError as e:
            logger.error(f"Ollama generation failed: {e}")
            response_text = "Извините, не могу сгенерировать ответ. Попробуйте позже."
        
        needs_escalation, escalation_reason = should_escalate(
            last_user_message, response_text
        )
        
        if save_response:
            await self._save_response(
                ticket_id, response_text, context_chunks, needs_escalation
            )
        
        return AgentResponse(
            content=response_text,
            needs_escalation=needs_escalation,
            escalation_reason=escalation_reason,
            context_used=[
                {"id": c.id, "source": c.source, "chunk": c.chunk, "score": c.score}
                for c in context_chunks
            ],
            model=self.ollama.chat_model,
        )
    
    async def ask_freeform(
        self,
        tenant_id: int,
        question: str,
        max_context: int = 5,
    ) -> AgentResponse:
        context_chunks = await self._search_kb(
            tenant_id=tenant_id,
            query=question,
            limit=max_context,
        )
        
        context_text = self._format_context(context_chunks)
        
        system_prompt = SYSTEM_PROMPT.format(
            context=context_text if context_text else NO_CONTEXT_NOTE,
            history="(Режим playground, без истории)",
        )
        
        try:
            response_text = await self.ollama.generate(
                prompt=question,
                system=system_prompt,
                temperature=DEFAULT_TEMPERATURE,
            )
        except OllamaError as e:
            logger.error(f"Ollama generation failed: {e}")
            response_text = "Извините, не могу сгенерировать ответ. Попробуйте позже."
        
        needs_escalation, escalation_reason = should_escalate(
            question, response_text
        )
        
        return AgentResponse(
            content=response_text,
            needs_escalation=needs_escalation,
            escalation_reason=escalation_reason,
            context_used=[
                {"id": c.id, "source": c.source, "chunk": c.chunk, "score": c.score}
                for c in context_chunks
            ],
            model=self.ollama.chat_model,
        )
    
    async def _save_response(
        self,
        ticket_id: int,
        response_text: str,
        context_chunks: list[SearchResult],
        needs_escalation: bool,
    ) -> None:
        try:
            await repos.create_message(
                self.db,
                ticket_id=ticket_id,
                content=response_text,
                role="assistant",
                metadata={
                    "model": self.ollama.chat_model,
                    "context_chunks": len(context_chunks),
                    "escalation": needs_escalation,
                },
            )

            if needs_escalation:
                await repos.update_ticket(self.db, ticket_id, status="escalated")

            await self.db.flush()  # Flush but don't commit - let the caller handle commit
        except Exception as e:
            logger.error(f"Failed to save response for ticket {ticket_id}: {e}")
            raise
    
    async def _search_kb(
        self,
        tenant_id: int,
        query: str,
        limit: int,
    ) -> list[SearchResult]:
        embedding_service = EmbeddingService(self.db, self.ollama)
        
        try:
            return await embedding_service.search_semantic(
                tenant_id=tenant_id,
                query=query,
                limit=limit,
                min_score=0.3,
            )
        except Exception as e:
            logger.warning(f"Semantic search failed: {e}")
            return []
    
    def _build_search_query(
        self,
        ticket: dict[str, Any],
        messages: list[dict[str, Any]],
    ) -> str:
        parts = [ticket["title"]]
        
        if ticket.get("description"):
            parts.append(ticket["description"])
        
        for msg in reversed(messages):
            if msg["role"] == "user":
                parts.append(msg["content"])
                break
        
        return " ".join(parts)
    
    def _format_context(self, chunks: list[SearchResult]) -> str:
        if not chunks:
            return ""
        
        formatted = []
        for i, chunk in enumerate(chunks, 1):
            formatted.append(
                f"[{i}] Source: {chunk.source} (relevance: {chunk.score:.2f})\n{chunk.chunk}"
            )
        
        return "\n\n".join(formatted)
    
    def _format_history(self, messages: list[dict[str, Any]]) -> str:
        if not messages:
            return ""
        
        role_names = {
            "user": "Клиент",
            "assistant": "Ассистент",
            "agent": "Ассистент",
            "system": "Система",
        }
        
        formatted = []
        for msg in messages[-10:]:
            role = role_names.get(msg["role"], msg["role"])
            content = msg["content"]
            if len(content) > 500:
                content = content[:500] + "..."
            formatted.append(f"{role}: {content}")
        
        return "\n".join(formatted)
    
    def _get_last_user_message(
        self,
        ticket: dict[str, Any],
        messages: list[dict[str, Any]],
    ) -> str:
        for msg in reversed(messages):
            if msg["role"] == "user":
                return msg["content"]
        
        if ticket.get("description"):
            return f"{ticket['title']}\n\n{ticket['description']}"
        return ticket["title"]


def get_agent_service(db: AsyncSession) -> AgentService:
    return AgentService(db)
