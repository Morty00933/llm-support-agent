"""Базовые классы для доменных событий."""
from __future__ import annotations

from abc import ABC
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, Awaitable
from uuid import uuid4
import asyncio


@dataclass(frozen=True, kw_only=True)
class DomainEvent(ABC):
    """Базовый класс доменного события."""
    
    event_id: str = field(default_factory=lambda: str(uuid4()))
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    tenant_id: int | None = None
    
    @property
    def event_type(self) -> str:
        return self.__class__.__name__


EventHandler = Callable[[DomainEvent], Awaitable[None]]


class EventDispatcher:
    """Диспетчер доменных событий."""

    _instance: "EventDispatcher | None" = None
    _handlers: dict[type[DomainEvent], list[EventHandler]]
    _global_handlers: list[EventHandler]

    def __new__(cls) -> "EventDispatcher":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._handlers = {}
            cls._instance._global_handlers = []
        return cls._instance
    
    def subscribe(
        self,
        event_type: type[DomainEvent],
        handler: EventHandler,
    ) -> None:
        """Подписка на конкретный тип события."""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
    
    def subscribe_all(self, handler: EventHandler) -> None:
        """Подписка на все события."""
        self._global_handlers.append(handler)
    
    async def publish(self, event: DomainEvent) -> None:
        """Публикация события."""
        handlers = self._handlers.get(type(event), []) + self._global_handlers
        
        if handlers:
            await asyncio.gather(
                *[handler(event) for handler in handlers],
                return_exceptions=True,
            )
    
    async def publish_all(self, events: list[DomainEvent]) -> None:
        """Публикация нескольких событий."""
        for event in events:
            await self.publish(event)
    
    @classmethod
    def reset(cls) -> None:
        """Сброс (для тестов)."""
        cls._instance = None


event_dispatcher = EventDispatcher()


def on_event(event_type: type[DomainEvent]):
    """Декоратор для регистрации обработчика события."""
    def decorator(handler: EventHandler) -> EventHandler:
        event_dispatcher.subscribe(event_type, handler)
        return handler
    return decorator
