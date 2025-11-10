"""Эмбеддинги через Ollama /api/embeddings."""

from __future__ import annotations

import array
import asyncio
import logging
from dataclasses import dataclass
from typing import Iterable

import httpx

from ..core.config import settings

logger = logging.getLogger(__name__)
_LOGGED_CONFIGURATION = False


class EmbeddingServiceError(Exception):
    """Ошибка при обращении к сервису эмбеддингов."""

    def __init__(self, message: str, *, status_code: int = 422) -> None:
        super().__init__(message)
        self.status_code = status_code


@dataclass(slots=True)
class EmbeddingResult:
    """Результат вызова Ollama embeddings."""

    vector: list[float]
    buffer: bytes


async def _fetch_embedding(
    client: httpx.AsyncClient,
    *,
    base: str,
    model: str,
    text: str,
    retries: int,
) -> EmbeddingResult:
    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            response = await client.post(
                f"{base}/api/embeddings",
                json={"model": model, "prompt": text},
            )
            response.raise_for_status()
            payload = response.json()
            vector = payload.get("embedding")
            if not isinstance(vector, list):
                raise EmbeddingServiceError("embedding response did not include vector data")
            if len(vector) != settings.EMBEDDING_DIM:
                raise EmbeddingServiceError(
                    f"embedding size mismatch: got {len(vector)}, expected {settings.EMBEDDING_DIM}",
                    status_code=422,
                )

            float_vector = [float(v) for v in vector]
            arr = array.array("f", float_vector)

            global _LOGGED_CONFIGURATION
            if not _LOGGED_CONFIGURATION:
                logger.debug(
                    "Ollama embeddings configured: base=%s model=%s dim=%s",
                    base,
                    model,
                    settings.EMBEDDING_DIM,
                )
                _LOGGED_CONFIGURATION = True

            return EmbeddingResult(vector=float_vector, buffer=arr.tobytes())
        except httpx.HTTPStatusError as exc:  # pragma: no cover - network branch
            detail = exc.response.text.strip()
            status = exc.response.status_code
            raise EmbeddingServiceError(
                f"Ollama embeddings request failed ({status}): {detail or exc.response.reason_phrase}",
                status_code=424 if status >= 500 else 422,
            ) from exc
        except (httpx.RequestError, httpx.TimeoutException) as exc:  # pragma: no cover
            last_error = exc
            if attempt >= retries:
                raise EmbeddingServiceError(
                    f"Ollama embeddings request failed after retries: {exc}",
                    status_code=424,
                ) from exc
            await asyncio.sleep(0.5 * (attempt + 1))

    raise EmbeddingServiceError(
        f"Unable to obtain embedding after retries: {last_error}",
        status_code=424,
    )


async def embed_texts(
    texts: Iterable[str], *, retries: int = 2
) -> list[EmbeddingResult]:
    payloads = [t for t in texts]
    if not payloads:
        return []

    base_url = settings.OLLAMA_BASE_URL.strip()
    if not base_url:
        raise EmbeddingServiceError("Ollama base URL is not configured", status_code=422)
    model = settings.OLLAMA_MODEL_EMBED.strip()
    if not model:
        raise EmbeddingServiceError("Embedding model name is not configured", status_code=422)

    base = base_url.rstrip("/")

    timeout = httpx.Timeout(30.0, connect=5.0)
    results: list[EmbeddingResult] = []
    async with httpx.AsyncClient(timeout=timeout) as client:
        for text in payloads:
            result = await _fetch_embedding(
                client, base=base, model=model, text=text, retries=retries
            )
            results.append(result)
    return results
