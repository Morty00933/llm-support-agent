from __future__ import annotations
import time
import threading


class CircuitBreaker:
    """
    Простейший Circuit Breaker для защиты от зависших внешних сервисов.
    """

    def __init__(self, fail_max: int = 5, reset_timeout: int = 60):
        self.fail_max = fail_max
        self.reset_timeout = reset_timeout
        self._fail_counter = 0
        self._opened_since: float | None = None
        self._lock = threading.Lock()

    def allow_request(self) -> bool:
        with self._lock:
            if self._opened_since is None:
                return True
            if (time.time() - self._opened_since) > self.reset_timeout:
                # reset после таймаута
                self._fail_counter = 0
                self._opened_since = None
                return True
            return False

    def record_success(self):
        with self._lock:
            self._fail_counter = 0
            self._opened_since = None

    def record_failure(self):
        with self._lock:
            self._fail_counter += 1
            if self._fail_counter >= self.fail_max:
                self._opened_since = time.time()

    @property
    def state(self) -> str:
        with self._lock:
            if self._opened_since is not None:
                return "open"
            return "closed"
