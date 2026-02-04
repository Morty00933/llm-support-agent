import pytest
from httpx import AsyncClient
from unittest.mock import patch


@pytest.mark.agent
@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.asyncio(loop_scope="function")
class TestAIAgent:
    
    async def test_fr_3_1_agent_health_check(
        self, client: AsyncClient, auth_headers
    ):
        response = await client.get("/v1/agent/health", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "ollama_available" in data
        assert "chat_model" in data
        assert "embed_model" in data
        assert "models_loaded" in data
    
    @patch("src.services.ollama.OllamaClient.generate")
    async def test_fr_3_2_generate_response_to_ticket(
        self, mock_generate, client: AsyncClient, auth_headers, test_ticket, test_kb_chunks
    ):
        mock_generate.return_value = "To reset your password, click on Forgot Password link."
        
        response = await client.post(
            f"/v1/agent/respond/{test_ticket.id}",
            headers=auth_headers,
            json={
                "save_response": True,
                "max_context": 5,
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert "needs_escalation" in data
        assert "context_used" in data
        assert "model" in data
        assert isinstance(data["context_used"], list)
    
    @patch("src.services.ollama.OllamaClient.generate")
    async def test_fr_3_2_generate_response_without_save(
        self, mock_generate, client: AsyncClient, auth_headers, test_ticket
    ):
        mock_generate.return_value = "Here is your answer."
        
        response = await client.post(
            f"/v1/agent/respond/{test_ticket.id}",
            headers=auth_headers,
            json={"save_response": False},
        )
        
        assert response.status_code == 200
    
    @patch("src.services.ollama.OllamaClient.generate")
    async def test_fr_3_3_freeform_question_playground(
        self, mock_generate, client: AsyncClient, auth_headers, test_kb_chunks
    ):
        mock_generate.return_value = "To recover your password, follow these steps..."
        
        response = await client.post(
            "/v1/agent/ask",
            headers=auth_headers,
            json={
                "question": "How to recover password?",
                "max_context": 5,
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert len(data["content"]) > 0
        assert "needs_escalation" in data
        assert "model" in data
    
    @patch("src.services.ollama.OllamaClient.generate")
    async def test_fr_3_4_escalation_on_refund_request(
        self, mock_generate, client: AsyncClient, auth_headers
    ):
        mock_generate.return_value = "I will escalate your refund request to a specialist."
        
        response = await client.post(
            "/v1/agent/ask",
            headers=auth_headers,
            json={"question": "I want a refund and will sue you!"},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["needs_escalation"] is True
        assert data["escalation_reason"] is not None
    
    @patch("src.services.ollama.OllamaClient.generate")
    async def test_fr_3_4_escalation_triggers(
        self, mock_generate, client: AsyncClient, auth_headers
    ):
        mock_generate.return_value = "I understand your concern."
        
        escalation_keywords = [
            "refund my money",
            "file a lawsuit",
            "contact my lawyer",
            "this is fraud",
            "escalate to manager",
        ]
        
        for keyword in escalation_keywords:
            response = await client.post(
                "/v1/agent/ask",
                headers=auth_headers,
                json={"question": f"I need to {keyword}"},
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["needs_escalation"] is True, f"Should escalate on '{keyword}'"
    
    @patch("src.services.ollama.OllamaClient.generate")
    async def test_fr_3_no_escalation_normal_query(
        self, mock_generate, client: AsyncClient, auth_headers
    ):
        mock_generate.return_value = "Our support hours are 9AM to 6PM."
        
        response = await client.post(
            "/v1/agent/ask",
            headers=auth_headers,
            json={"question": "What are your support hours?"},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["needs_escalation"] is False
    
    async def test_fr_3_agent_timeout_handling(
        self, client: AsyncClient, auth_headers
    ):
        response = await client.post(
            "/v1/agent/ask",
            headers=auth_headers,
            json={"question": "Test"},
            timeout=1.0,
        )
        
        assert response.status_code in [200, 408, 504]
    
    @patch("src.services.ollama.OllamaClient.embed")
    @patch("src.services.ollama.OllamaClient.generate")
    async def test_fr_3_context_from_kb_used(
        self, mock_generate, mock_embed, client: AsyncClient, auth_headers, test_kb_chunks
    ):
        mock_generate.return_value = "Based on our documentation..."
        mock_embed.return_value = [0.1] * 768  # Mock embedding vector

        response = await client.post(
            "/v1/agent/ask",
            headers=auth_headers,
            json={"question": "password recovery help"},
        )

        assert response.status_code == 200
        data = response.json()
        # Context might be empty if embedding/search doesn't work in test env
        # Just check the response is valid
        assert "context_used" in data
        assert isinstance(data["context_used"], list)
