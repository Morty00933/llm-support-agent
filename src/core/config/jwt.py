"""JWT конфигурация - реэкспорт из основного модуля для обратной совместимости."""
from __future__ import annotations

from src.core.config import JWTConfig

__all__ = ["JWTConfig"]
