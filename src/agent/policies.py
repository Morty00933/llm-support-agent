# -*- coding: utf-8 -*-
"""Agent policies - escalation logic and prompts."""
from __future__ import annotations

import re
from typing import Set, FrozenSet, Any


DEFAULT_TEMPERATURE: float = 0.2
DEFAULT_TOP_P: float = 0.9
MAX_STEPS: int = 4
MIN_KB_SCORE_THRESHOLD: float = 0.5


ESCALATION_KEYWORDS: dict[str, Set[str]] = {
    "en": {
        "refund", "chargeback", "money back",
        "lawsuit", "lawyer", "attorney", "legal", "sue", "court",
        "complaint", "fraud", "scam",
        "escalate", "supervisor", "manager",
        "police", "report",
    },
    "ru": {
        "возврат", "деньги назад", "вернуть деньги",
        "жалоба", "суд", "юрист", "адвокат", "прокуратура",
        "мошенничество", "обман",
        "эскалация", "руководитель", "менеджер", "начальник",
        "полиция", "заявление",
    },
}

ALL_ESCALATION_KEYWORDS: FrozenSet[str] = frozenset(
    keyword
    for keywords in ESCALATION_KEYWORDS.values()
    for keyword in keywords
)

ESCALATE_KEYWORDS = ALL_ESCALATION_KEYWORDS

LOW_CONFIDENCE_PHRASES: FrozenSet[str] = frozenset({
    "i don't know",
    "i'm not sure",
    "i cannot",
    "contact support",
    "speak to a human",
    "escalate",
    "не знаю",
    "не уверен",
    "не могу",
    "обратитесь к оператору",
    "свяжитесь с поддержкой",
})


SYSTEM_PROMPT_BASE: str = (
    "You are a helpful support assistant. "
    "Answer concisely and precisely. "
    "If you are not certain, say so and propose next steps. "
    "Prefer actionable steps, bullet points, and short paragraphs."
)

SYSTEM_PROMPT: str = """Ты — ИИ-ассистент службы поддержки. Твоя задача — помогать пользователям решать их проблемы.

ПРАВИЛА:
1. Отвечай кратко и по делу, без лишней воды
2. Используй информацию из базы знаний, если она релевантна
3. Если не знаешь ответа — честно скажи об этом и предложи связаться с оператором
4. Будь вежлив и профессионален
5. Структурируй ответ, если нужно перечислить шаги
6. Отвечай на том же языке, на котором задан вопрос

КОНТЕКСТ ИЗ БАЗЫ ЗНАНИЙ:
{context}

ИСТОРИЯ ДИАЛОГА:
{history}
"""

NO_CONTEXT_NOTE: str = "(База знаний пуста или не содержит релевантной информации)"


def build_system_prompt(
    context: str | None = None,
    history: str | None = None,
) -> str:
    """Build system prompt with context and history."""
    return SYSTEM_PROMPT.format(
        context=context or NO_CONTEXT_NOTE,
        history=history or "(Новый диалог)",
    )


def should_escalate(
    text: str,
    kb_hits: list[dict[str, Any]] | None = None,
    min_kb_score: float = 0.5,
) -> tuple[bool, str | None]:
    """Check text for escalation triggers."""
    text_lower = text.lower()

    for keyword in ALL_ESCALATION_KEYWORDS:
        if keyword in text_lower:
            return True, f"Trigger word: '{keyword}'"

    for phrase in LOW_CONFIDENCE_PHRASES:
        if phrase in text_lower:
            return True, "Low confidence response"

    if kb_hits is not None and len(kb_hits) > 0:
        scores = []
        for hit in kb_hits:
            if isinstance(hit, dict):
                scores.append(hit.get("score", 0))

        if scores:
            best_score = max(scores)
            if best_score < min_kb_score:
                return True, f"Low KB match score: {best_score:.2f}"

    return False, None


def detect_language(text: str) -> str:
    """Detect language by characters."""
    cyrillic_count = len(re.findall(r'[а-яёА-ЯЁ]', text))
    latin_count = len(re.findall(r'[a-zA-Z]', text))
    return "ru" if cyrillic_count > latin_count else "en"


def trim_text(text: str, max_chars: int, tail: str = "...") -> str:
    """Trim text to max length with tail."""
    if len(text) <= max_chars:
        return text
    return text[: max(0, max_chars - len(tail))] + tail


def normalize_whitespace(s: str) -> str:
    """Collapse whitespace and newlines."""
    return re.sub(r"\s+", " ", s).strip()
