# -*- coding: utf-8 -*-
"""Message formatting utilities.

УНИФИЦИРУЕТ форматирование истории сообщений из:
- agent/loop.py: _build_conversation (УДАЛЁН)
- services/agent.py: _format_history
"""
from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class MessageLike(Protocol):
    """Protocol for message-like objects."""
    role: str
    content: str


# Маппинг ролей на человекочитаемые имена
ROLE_NAMES: dict[str, str] = {
    "user": "Клиент",
    "assistant": "Ассистент",
    "agent": "Ассистент",
    "system": "Система",
}

# Маппинг для LLM формата
LLM_ROLE_MAP: dict[str, str] = {
    "user": "user",
    "assistant": "assistant",
    "agent": "assistant",
    "system": "system",
}


def truncate_message(content: str, max_length: int = 500, suffix: str = "...") -> str:
    """
    Обрезает сообщение до максимальной длины.
    
    Args:
        content: Текст сообщения
        max_length: Максимальная длина
        suffix: Суффикс для обрезанного текста
    
    Returns:
        Обрезанный текст
    """
    if len(content) <= max_length:
        return content
    return content[:max_length - len(suffix)] + suffix


def format_conversation_history(
    messages: list[MessageLike | dict[str, Any]],
    max_messages: int = 10,
    max_content_length: int = 500,
    use_role_names: bool = True,
) -> str:
    """
    Форматирует историю сообщений для включения в промпт.
    
    Args:
        messages: Список сообщений
        max_messages: Максимальное количество сообщений (берутся последние)
        max_content_length: Максимальная длина контента
        use_role_names: Использовать человекочитаемые имена ролей
    
    Returns:
        Отформатированная история
    
    Examples:
        >>> msgs = [{"role": "user", "content": "Привет"}]
        >>> format_conversation_history(msgs)
        "Клиент: Привет"
    """
    if not messages:
        return ""
    
    recent_messages = messages[-max_messages:] if len(messages) > max_messages else messages
    
    formatted = []
    for msg in recent_messages:
        if isinstance(msg, dict):
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
        else:
            role = msg.role
            content = msg.content
        
        if use_role_names:
            display_role = ROLE_NAMES.get(role, role)
        else:
            display_role = role
        
        truncated_content = truncate_message(content, max_content_length)
        formatted.append(f"{display_role}: {truncated_content}")
    
    return "\n".join(formatted)


def build_llm_messages(
    messages: list[MessageLike | dict[str, Any]],
    system_prompt: str | None = None,
    max_messages: int | None = None,
) -> list[dict[str, str]]:
    """
    Строит список сообщений для LLM API.
    
    Args:
        messages: Список сообщений
        system_prompt: Опциональный системный промпт
        max_messages: Максимальное количество сообщений
    
    Returns:
        Список сообщений в формате LLM API
    """
    result = []
    
    if system_prompt:
        result.append({"role": "system", "content": system_prompt})
    
    if max_messages is not None:
        messages = messages[-max_messages:]
    
    for msg in messages:
        if isinstance(msg, dict):
            role = msg.get("role", "user")
            content = msg.get("content", "")
        else:
            role = msg.role
            content = msg.content
        
        llm_role = LLM_ROLE_MAP.get(role, "user")
        
        if llm_role == "system" and system_prompt:
            continue
        
        result.append({"role": llm_role, "content": content})
    
    return result
