"""Эмбеддинги через Ollama /api/embeddings."""

from __future__ import annotations

import array
from typing import Iterable

import httpx

from ..core.config import settings


async def embed_texts(texts: Iterable[str]) -> list[bytes]:
    out: list[bytes] = []
    base = settings.OLLAMA_HOST.rstrip("/")
    model = settings.OLLAMA_MODEL_EMBED

    async with httpx.AsyncClient(timeout=120) as client:
        for t in texts:
            r = await client.post(
                f"{base}/api/embeddings",
                json={"model": model, "prompt": t},
            )
            r.raise_for_status()
            vec = r.json()["embedding"]  # list[float]
            arr = array.array("f", vec)  # float32
            out.append(arr.tobytes())
    return out
