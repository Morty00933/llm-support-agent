# -*- coding: utf-8 -*-
"""Prompt formatting utilities.

УНИФИЦИРУЕТ форматирование KB контекста из:
- agent/loop.py: _build_system_prompt (УДАЛЁН)
- agent/policies.py: build_system_prompt
- services/knowledge.py: get_context_for_query
- services/agent.py: _format_context
"""
from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class KBChunkLike(Protocol):
    """Protocol for KB chunk-like objects."""
    chunk: str
    source: str
    score: float


def format_kb_chunk(
    chunk: KBChunkLike | dict[str, Any],
    index: int,
    include_score: bool = True,
) -> str:
    """
    Форматирует один KB chunk для включения в промпт.
    
    Args:
        chunk: KB chunk (объект или dict)
        index: Номер чанка (1-based)
        include_score: Включать ли score в вывод
    
    Returns:
        Отформатированный текст чанка
    
    Examples:
        >>> format_kb_chunk({"chunk": "text", "source": "doc.md", "score": 0.85}, 1)
        "[1] Source: doc.md (relevance: 0.85)\\ntext"
    """
    if isinstance(chunk, dict):
        content = chunk.get("chunk", "")
        source = chunk.get("source", "Unknown")
        score = chunk.get("score", 0.0)
    else:
        content = chunk.chunk
        source = chunk.source
        score = chunk.score
    
    if include_score:
        return f"[{index}] Source: {source} (relevance: {score:.2f})\n{content}"
    else:
        return f"[{index}] Source: {source}\n{content}"


def format_kb_context(
    chunks: list[KBChunkLike | dict[str, Any]],
    separator: str = "\n\n",
    include_score: bool = True,
    max_chunks: int | None = None,
) -> str:
    """
    Форматирует список KB chunks для включения в системный промпт.
    
    Args:
        chunks: Список KB chunks
        separator: Разделитель между чанками
        include_score: Включать ли score
        max_chunks: Максимальное количество чанков (None = все)
    
    Returns:
        Отформатированный контекст или пустая строка
    
    Examples:
        >>> chunks = [{"chunk": "text1", "source": "a.md", "score": 0.9}]
        >>> format_kb_context(chunks)
        "[1] Source: a.md (relevance: 0.90)\\ntext1"
    """
    if not chunks:
        return ""
    
    if max_chunks is not None:
        chunks = chunks[:max_chunks]
    
    formatted = [
        format_kb_chunk(chunk, i, include_score)
        for i, chunk in enumerate(chunks, 1)
    ]
    
    return separator.join(formatted)
