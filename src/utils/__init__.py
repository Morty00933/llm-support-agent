# -*- coding: utf-8 -*-
"""Utility functions package.

Вынесено из дублирующегося кода:
- prompt.py: форматирование KB контекста
- messages.py: форматирование истории сообщений
"""
from .prompt import format_kb_context, format_kb_chunk
from .messages import format_conversation_history, truncate_message, build_llm_messages

__all__ = [
    # Prompt utilities
    "format_kb_context",
    "format_kb_chunk",
    # Message utilities
    "format_conversation_history",
    "truncate_message",
    "build_llm_messages",
]
