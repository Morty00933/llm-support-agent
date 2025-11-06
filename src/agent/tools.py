from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Any, Optional, Callable

from sqlalchemy.ext.asyncio import AsyncSession

from ..schemas.kb import KBSearchIn
from ..services.knowledge import search_kb
from .llm import OllamaChat


# ===== Базовый протокол инструмента =====


class Tool(Protocol):
    """
    Контракт инструмента.
    Инструмент — асинхронно вызываемый объект, возвращающий JSON-совместимый результат.
    """

    name: str
    description: str

    async def __call__(self, **kwargs) -> Any: ...


# ===== Реестр инструментов =====

_TOOLS: dict[str, Tool] = {}


def register_tool(tool: Tool) -> None:
    """Регистрирует инструмент по уникальному имени."""
    if tool.name in _TOOLS:
        raise ValueError(f"Tool {tool.name!r} already registered")
    _TOOLS[tool.name] = tool


def get_tool(name: str) -> Tool:
    """Получить инструмент по имени или бросить ошибку, если он не зарегистрирован."""
    try:
        return _TOOLS[name]
    except KeyError:
        raise KeyError(f"Tool {name!r} is not registered")


def list_tools() -> list[str]:
    """Список имён зарегистрированных инструментов (отсортированный)."""
    return sorted(_TOOLS.keys())


# ===== Реальные инструменты =====


class SearchKBTool:
    """
    Поиск по базе знаний арендатора (tenant) с семантическим скорингом.

    Вызов:
      await tool(tenant_id=1, query="reset password", limit=5, session=db_session)
    """

    name = "search_kb"
    description = (
        "Search tenant knowledge base for most relevant chunks by semantic similarity."
    )

    def __init__(self, session_getter: Optional[Callable[[], AsyncSession]] = None):
        self._session_getter = session_getter

    async def __call__(
        self,
        *,
        tenant_id: int,
        query: str,
        limit: int = 5,
        session: Optional[AsyncSession] = None,
        source: str | None = None,
        tags: list[str] | None = None,
        language: str | None = None,
        include_metadata: bool = True,
    ) -> list[dict]:
        if session is None:
            if not self._session_getter:
                raise RuntimeError(
                    "SearchKBTool requires 'session' or session_getter()"
                )
            session = self._session_getter()
        if not query:
            return []
        filters = KBSearchIn(
            query=query,
            limit=limit,
            source=source,
            tags=tags,
            language=language,
            include_metadata=include_metadata,
        )
        return await search_kb(session, tenant_id, query, limit, filters=filters)


@dataclass
class AnswerWithLLMParams:
    """
    Параметры для инструмента AnswerWithLLMTool — полезен вне «агентного цикла»:
    просто «сгенерировать ответ» на запрос пользователя с опциональным контекстом.
    """

    prompt: str  # основной запрос пользователя
    system_prompt: str | None = None  # системный промпт (style/role), если нужен
    context: str | None = None  # релевантный контекст (например, собранный из KB)
    temperature: float = 0.2
    top_p: float = 0.9
    stop: list[str] | None = None


class AnswerWithLLMTool:
    """
    Универсальный инструмент генерации ответа через Ollama Chat API.

    Пример:
      tool = AnswerWithLLMTool()
      await tool(
        prompt="How to reset password?",
        context="1) Go to settings -> security ...",
        system_prompt="You are helpful assistant.",
        temperature=0.3
      )
    """

    name = "answer_llm"
    description = "Generate a concise answer with Ollama using optional system prompt and context."

    def __init__(self, chat_factory: Optional[Callable[[], OllamaChat]] = None):
        self._chat_factory = chat_factory or (lambda: OllamaChat())

    async def __call__(self, **kwargs) -> dict:
        # Валидация входных параметров
        try:
            params = AnswerWithLLMParams(**kwargs)  # type: ignore[arg-type]
        except TypeError as e:
            raise ValueError(f"Invalid arguments for {self.name}: {e}")

        messages: list[dict[str, str]] = []
        if params.system_prompt:
            messages.append({"role": "system", "content": params.system_prompt})
        if params.context:
            messages.append(
                {"role": "system", "content": f"Relevant context:\n{params.context}"}
            )
        messages.append({"role": "user", "content": params.prompt})

        chat = self._chat_factory()
        reply = await chat.chat(
            messages,
            temperature=params.temperature,
            top_p=params.top_p,
            stop=params.stop,
        )
        return {
            "reply": reply.strip(),
            "used_context": params.context or None,
        }


# Регистрация стандартных инструментов
register_tool(SearchKBTool())
register_tool(AnswerWithLLMTool())
