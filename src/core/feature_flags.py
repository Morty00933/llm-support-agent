from __future__ import annotations
from typing import Dict
import threading


class FeatureFlags:
    """
    Очень простая реализация feature-флагов (в памяти).
    Для production обычно используют LaunchDarkly, Unleash, Flipt и т.д.
    """

    def __init__(self):
        self._flags: Dict[str, bool] = {}
        self._lock = threading.Lock()

    def set(self, name: str, enabled: bool):
        with self._lock:
            self._flags[name] = enabled

    def get(self, name: str) -> bool:
        with self._lock:
            return self._flags.get(name, False)

    def all(self) -> dict[str, bool]:
        with self._lock:
            return dict(self._flags)


flags = FeatureFlags()
