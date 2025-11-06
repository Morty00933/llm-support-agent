from __future__ import annotations
import httpx
from typing import Literal, Sequence
from ..core.config import settings

Role = Literal["system", "user", "assistant"]


class OllamaChat:
    """
    Лёгкая обёртка вокруг Ollama Chat API (/api/chat).

    Пример ответа API Ollama:
    {
      "model": "...",
      "created_at": "...",
      "message": {"role":"assistant","content":"..."},
      "done": true,
      "total_duration": 123,
      ...
    }
    """

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        timeout: float = 120.0,
    ):
        self.base_url = (base_url or settings.OLLAMA_HOST).rstrip("/")
        self.model = model or settings.OLLAMA_MODEL_CHAT
        self.timeout = timeout

    async def chat(
        self,
        messages: Sequence[dict[str, str]],
        *,
        temperature: float = 0.2,
        top_p: float = 0.9,
        stop: list[str] | None = None,
    ) -> str:
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": temperature, "top_p": top_p},
        }
        if stop:
            payload["stop"] = stop

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            r = await client.post(f"{self.base_url}/api/chat", json=payload)
            r.raise_for_status()
            data = r.json()
            msg = data.get("message") or {}
            return str(msg.get("content", "")).strip()
