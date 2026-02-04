# -*- coding: utf-8 -*-
"""Services package.

ИСПРАВЛЕНО:
- Убран импорт из llm.py (файл удалён, дубликат ollama.py)
- Единственный LLM клиент: OllamaClient из ollama.py
"""
from src.services.ollama import (
    OllamaClient,
    get_ollama_client,
    close_ollama_client,
    OllamaError,
    OllamaConnectionError,
    OllamaGenerationError,
    OllamaEmbeddingError,
)
from src.services.agent import AgentService, AgentResponse, get_agent_service
from src.services.embedding import EmbeddingService, SearchResult, get_embedding_service

__all__ = [
    # Ollama (единственный LLM клиент)
    "OllamaClient",
    "get_ollama_client",
    "close_ollama_client",
    "OllamaError",
    "OllamaConnectionError",
    "OllamaGenerationError",
    "OllamaEmbeddingError",
    # Agent
    "AgentService",
    "AgentResponse",
    "get_agent_service",
    # Embedding
    "EmbeddingService",
    "SearchResult",
    "get_embedding_service",
]
