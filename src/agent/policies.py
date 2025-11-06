from __future__ import annotations
import re

# Базовый системный промпт. При необходимости расширяйте политиками/ролями.
SYSTEM_PROMPT_BASE = (
    "You are a helpful support assistant. "
    "Answer concisely and precisely. "
    "If you are not certain, say so and propose next steps. "
    "Prefer actionable steps, bullet points, and short paragraphs."
)

# Хард-лимит итераций «агентного» цикла (если будете делать многотуровый reasoning)
MAX_STEPS = 4

# Простая эвристика «эскалации»: ключевые слова
ESCALATE_KEYWORDS = {
    "refund",
    "complaint",
    "escalate",
    "supervisor",
    "chargeback",
    "lawsuit",
    "юрист",
    "жалоба",
    "эскалация",
}


def build_system_prompt(context: str | None = None) -> str:
    """
    Сборка системного промпта: базовый + опциональный контекст (из KB).
    """
    if context:
        return f"{SYSTEM_PROMPT_BASE}\n\nRelevant context:\n{context}\n"
    return SYSTEM_PROMPT_BASE


def should_escalate(text: str) -> bool:
    """
    Очень простая эвристика: если встречается ключевое слово из списка.
    """
    low = text.lower()
    return any(k in low for k in ESCALATE_KEYWORDS)


def trim_text(text: str, max_chars: int, tail: str = "…") -> str:
    """
    Жёстко обрезает текст по длине (UTF-8 безопасно в Python), добавляя хвост.
    """
    if len(text) <= max_chars:
        return text
    return text[: max(0, max_chars - len(tail))] + tail


def normalize_whitespace(s: str) -> str:
    """
    Схлопывает пробелы/переводы строк для аккуратного контекста.
    """
    return re.sub(r"\s+", " ", s).strip()
