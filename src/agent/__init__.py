# -*- coding: utf-8 -*-
"""Agent package.

Provides escalation policies and system prompts for AI agent.
Main agent logic is in src/services/agent.py (AgentService).

УДАЛЕНО (дубликаты и сломанные файлы):
- loop.py (дубликат services/agent.py + импорт несуществующего services/kb.py)
- llm.py (дубликат services/ollama.py + неправильные настройки)
- tools.py (импорт несуществующей функции search_kb + не используется)
"""
from .policies import (
    # Функции
    should_escalate,
    build_system_prompt,
    detect_language,
    trim_text,
    normalize_whitespace,
    # Константы
    ESCALATION_KEYWORDS,
    ALL_ESCALATION_KEYWORDS,
    ESCALATE_KEYWORDS,
    LOW_CONFIDENCE_PHRASES,
    SYSTEM_PROMPT,
    SYSTEM_PROMPT_BASE,
    NO_CONTEXT_NOTE,
    MAX_STEPS,
    DEFAULT_TEMPERATURE,
)

__all__ = [
    # Functions
    "should_escalate",
    "build_system_prompt",
    "detect_language",
    "trim_text",
    "normalize_whitespace",
    # Constants
    "ESCALATION_KEYWORDS",
    "ALL_ESCALATION_KEYWORDS",
    "ESCALATE_KEYWORDS",
    "LOW_CONFIDENCE_PHRASES",
    "SYSTEM_PROMPT",
    "SYSTEM_PROMPT_BASE",
    "NO_CONTEXT_NOTE",
    "MAX_STEPS",
    "DEFAULT_TEMPERATURE",
]
