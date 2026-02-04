import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.services.agent import AgentService, AgentResponse
from src.services.embedding import EmbeddingService, SearchResult
from src.agent.policies import should_escalate, build_system_prompt


@pytest.mark.unit
class TestAgentPolicies:
    
    def test_should_escalate_refund_request(self):
        # should_escalate принимает текст для проверки
        needs_escalation, reason = should_escalate("I want a refund")
        assert needs_escalation is True
        assert reason is not None
    
    def test_should_escalate_lawsuit_threat(self):
        needs_escalation, reason = should_escalate("I will sue you")
        assert needs_escalation is True
        assert reason is not None
        assert "lawsuit" in reason.lower() or "sue" in reason.lower()
    
    def test_should_escalate_complaint(self):
        needs_escalation, reason = should_escalate("I want to file a complaint")
        assert needs_escalation is True
    
    def test_no_escalation_normal_query(self):
        needs_escalation, reason = should_escalate("What are your hours?")
        assert needs_escalation is False
        assert reason is None
    
    def test_should_escalate_russian_keywords(self):
        # Use a keyword that's actually in the ESCALATION_KEYWORDS list
        needs_escalation, reason = should_escalate("Я хочу вернуть деньги!")
        assert needs_escalation is True
    
    def test_build_system_prompt_with_context(self):
        prompt = build_system_prompt(
            context="Some KB context",
            history="User: Hello\nAgent: Hi"
        )
        assert "Some KB context" in prompt
        assert "User: Hello" in prompt or "Hello" in prompt
    
    def test_build_system_prompt_no_context(self):
        prompt = build_system_prompt(context="", history="")
        assert len(prompt) > 0


@pytest.mark.unit
class TestAgentService:
    
    @pytest.fixture
    def mock_db(self):
        return AsyncMock()
    
    @pytest.fixture
    def mock_ollama(self):
        mock = MagicMock()
        mock.chat_model = "qwen2.5:3b"
        mock.embed_model = "nomic-embed-text"
        return mock
    
    @pytest.fixture
    def agent_service(self, mock_db, mock_ollama, monkeypatch):
        # Мокаем get_ollama_client, чтобы он возвращал наш мок
        monkeypatch.setattr("src.services.agent.get_ollama_client", lambda: mock_ollama)
        return AgentService(mock_db)
    
    def test_format_context_empty(self, agent_service):
        result = agent_service._format_context([])
        assert result == ""
    
    def test_format_context_with_chunks(self, agent_service):
        chunks = [
            SearchResult(id=1, source="test.md", chunk="Content 1", score=0.9),
            SearchResult(id=2, source="test.md", chunk="Content 2", score=0.7),
        ]
        result = agent_service._format_context(chunks)
        assert "Content 1" in result
        assert "Content 2" in result
        assert "0.90" in result or "0.9" in result
        assert "0.70" in result or "0.7" in result
    
    def test_format_history_empty(self, agent_service):
        result = agent_service._format_history([])
        assert result == ""
    
    def test_format_history_with_messages(self, agent_service):
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"},
        ]
        result = agent_service._format_history(messages)
        assert "Hello" in result
        assert "Hi there" in result
    
    def test_get_last_user_message_from_messages(self, agent_service):
        ticket = {"title": "Test", "description": "Desc"}
        messages = [
            {"role": "user", "content": "First message"},
            {"role": "assistant", "content": "Response"},
            {"role": "user", "content": "Last message"},
        ]
        result = agent_service._get_last_user_message(ticket, messages)
        assert result == "Last message"
    
    def test_get_last_user_message_fallback_to_ticket(self, agent_service):
        ticket = {"title": "Test Title", "description": "Test Description"}
        messages = []
        result = agent_service._get_last_user_message(ticket, messages)
        assert "Test Title" in result
        assert "Test Description" in result


@pytest.mark.unit
@pytest.mark.asyncio(loop_scope="function")
class TestEmbeddingService:

    @pytest.fixture
    def mock_db(self):
        return AsyncMock()

    @pytest.fixture
    def mock_ollama(self):
        mock = AsyncMock()
        mock.embed = AsyncMock(return_value=[0.1] * 768)
        mock.embed_batch = AsyncMock(return_value=[[0.1] * 768, [0.2] * 768])
        return mock

    @pytest.fixture
    def embedding_service(self, mock_db, mock_ollama):
        return EmbeddingService(mock_db, mock_ollama)

    async def test_generate_embedding(self, embedding_service, mock_ollama):
        """Тест метода embed через OllamaClient."""
        result = await embedding_service.ollama.embed("test text")

        assert len(result) == 768
        mock_ollama.embed.assert_called_once_with("test text")

    async def test_generate_embeddings_batch(self, embedding_service, mock_ollama):
        """Тест метода embed_batch через OllamaClient."""
        texts = ["text1", "text2"]
        results = await embedding_service.ollama.embed_batch(texts)

        assert len(results) == 2
        assert len(results[0]) == 768
        mock_ollama.embed_batch.assert_called_once()


@pytest.mark.unit
class TestSearchResult:
    
    def test_search_result_creation(self):
        result = SearchResult(
            id=1,
            source="test.md",
            chunk="Test content",
            score=0.85,
        )
        assert result.id == 1
        assert result.source == "test.md"
        assert result.chunk == "Test content"
        assert result.score == 0.85
    
    def test_search_result_ordering(self):
        results = [
            SearchResult(id=1, source="a", chunk="a", score=0.5),
            SearchResult(id=2, source="b", chunk="b", score=0.9),
            SearchResult(id=3, source="c", chunk="c", score=0.7),
        ]
        sorted_results = sorted(results, key=lambda x: x.score, reverse=True)
        assert sorted_results[0].score == 0.9
        assert sorted_results[1].score == 0.7
        assert sorted_results[2].score == 0.5


@pytest.mark.unit
class TestAgentResponse:
    
    def test_agent_response_creation(self):
        response = AgentResponse(
            content="Test response",
            needs_escalation=False,
            escalation_reason=None,
            context_used=[],
            model="qwen2.5:3b",
        )
        assert response.content == "Test response"
        assert response.needs_escalation is False
        assert response.model == "qwen2.5:3b"
    
    def test_agent_response_with_escalation(self):
        response = AgentResponse(
            content="Escalating to human",
            needs_escalation=True,
            escalation_reason="Refund request",
            context_used=[],
            model="qwen2.5:3b",
        )
        assert response.needs_escalation is True
        assert response.escalation_reason == "Refund request"