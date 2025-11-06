from __future__ import annotations
from dataclasses import dataclass
from typing import Sequence, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..domain.models import Ticket, Message
from ..core.config import settings
from .llm import OllamaChat
from .policies import (
    build_system_prompt,
    trim_text,
    should_escalate,
    normalize_whitespace,
)
from .tools import get_tool


@dataclass
class AgentResult:
    """
    Результат работы агента.
    """
    reply: str                      # Сгенерированный ответ ассистента
    used_context: str | None        # Текстовый контекст (слип из KB), если был
    kb_hits: list[dict]             # Сырые документы из поиска по KB
    escalated: bool                 # Нужно ли эскалировать
    reason: str                     # Пояснение решения/идеи


class Agent:
    """
    Простой агент «одним проходом»: (история тикета) → (поиск по KB) → (LLM ответ).
    При необходимости можно развить до multi-step с инструментами и памятью.
    """

    def __init__(self, chat: Optional[OllamaChat] = None):
        self.chat = chat or OllamaChat()

    # ---------- Вспомогательные сборщики контекста ----------

    @staticmethod
    async def _load_ticket(session: AsyncSession, tenant_id: int, ticket_id: int) -> Ticket:
        t = await session.get(Ticket, ticket_id)
        if not t or t.tenant_id != tenant_id:
            raise ValueError("ticket not found or tenant mismatch")
        return t

    @staticmethod
    async def _load_messages(session: AsyncSession, ticket_id: int, limit: int = 50) -> list[Message]:
        rows = (
            await session.execute(
                select(Message).where(Message.ticket_id == ticket_id).order_by(Message.id.asc()).limit(limit)
            )
        ).scalars().all()
        return list(rows)

    @staticmethod
    def _messages_to_prompt(messages: Sequence[Message], max_chars_each: int = 1500, max_total_chars: int = 6000) -> str:
        """
        Конвертирует историю сообщений тикета в компактный текст для LLM.
        """
        out: list[str] = []
        total = 0
        for m in messages:
            role = m.role.lower()
            if role not in {"user", "agent", "system"}:
                role = "user"
            text = normalize_whitespace(m.content)
            text = trim_text(text, max_chars_each)
            chunk = f"[{role}] {text}"
            if total + len(chunk) > max_total_chars:
                break
            out.append(chunk)
            total += len(chunk)
        return "\n".join(out)

    @staticmethod
    def _kb_hits_to_context(hits: list[dict], max_chars: int = 3000) -> str:
        """
        Сшивает найденные куски KB в один контекст.
        """
        lines: list[str] = []
        used = 0
        for h in hits:
            line = f"- ({h.get('source','unknown')}, score={h.get('score')}) {normalize_whitespace(h.get('chunk',''))}"
            line = trim_text(line, 1200)
            if used + len(line) > max_chars:
                break
            lines.append(line)
            used += len(line)
        return "\n".join(lines)

    # ---------- Публичные методы агента ----------

    async def answer_for_ticket(
        self,
        session: AsyncSession,
        *,
        tenant_id: int,
        ticket_id: int,
        kb_limit: int = 5,
        temperature: float = 0.2,
    ) -> AgentResult:
        """
        Генерирует ответ по тикету:
        - загружает тикет и историю сообщений;
        - делает семантический поиск по KB (по заголовку + последнему пользовательскому сообщению);
        - собирает промпт и спрашивает LLM (Ollama);
        - не пишет ответ в БД — оставлено на API-уровень.
        """
        ticket = await self._load_ticket(session, tenant_id, ticket_id)
        history = await self._load_messages(session, ticket_id)

        # Собираем поисковый запрос из заголовка + последнего user-сообщения, если есть
        last_user = next((m for m in reversed(history) if m.role.lower() == "user"), None)
        query = ticket.title
        if last_user:
            query = f"{ticket.title}. {last_user.content}"

        # Инструмент поиска по KB
        search_kb = get_tool("search_kb")
        kb_hits: list[dict] = await search_kb(tenant_id=tenant_id, query=query, limit=kb_limit, session=session)

        # Контекст для системного промпта
        kb_context = self._kb_hits_to_context(kb_hits) if kb_hits else ""
        system_prompt = build_system_prompt(kb_context or None)

        # Историю тикета превратим в единый user-контент, чтобы не раздувать промпт
        conversation_compact = self._messages_to_prompt(history)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": conversation_compact},
        ]

        reply = await self.chat.chat(messages, temperature=temperature)

        escalated = should_escalate(conversation_compact) or should_escalate(reply)
        reason = "Escalation keywords detected" if escalated else "Direct answer generated"

        return AgentResult(
            reply=reply.strip(),
            used_context=kb_context or None,
            kb_hits=kb_hits,
            escalated=bool(escalated),
            reason=reason,
        )

    async def answer_freeform(
        self,
        session: AsyncSession,
        *,
        tenant_id: int,
        query: str,
        kb_limit: int = 5,
        temperature: float = 0.2,
    ) -> AgentResult:
        """
        Ответ «без тикета»: запрос пользователя → поиск по KB → LLM.
        """
        search_kb = get_tool("search_kb")
        kb_hits: list[dict] = await search_kb(tenant_id=tenant_id, query=query, limit=kb_limit, session=session)
        kb_context = self._kb_hits_to_context(kb_hits) if kb_hits else ""
        system_prompt = build_system_prompt(kb_context or None)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": normalize_whitespace(query)},
        ]

        reply = await self.chat.chat(messages, temperature=temperature)
        escalated = should_escalate(query) or should_escalate(reply)
        reason = "Escalation keywords detected" if escalated else "Direct answer generated"

        return AgentResult(
            reply=reply.strip(),
            used_context=kb_context or None,
            kb_hits=kb_hits,
            escalated=bool(escalated),
            reason=reason,
        )
