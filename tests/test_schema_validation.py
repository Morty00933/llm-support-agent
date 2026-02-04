"""
Tests for schema validation
"""
import pytest
from pydantic import ValidationError
from src.schemas import (
    UserCreate,
    UserLogin,
    UserUpdate,
    TicketCreate,
    TicketUpdate,
    MessageCreate,
    ChunkCreate,
    SearchQuery,
    Token,
    TenantCreate,
    FreeformRequest,
    AgentResponseSchema,
    TicketRespondRequest,
)


class TestUserSchemas:
    """Tests for user-related schemas"""

    def test_user_create_valid(self):
        """Test valid user creation"""
        user = UserCreate(
            email="test@example.com",
            password="ValidPass987",
            full_name="Test User",
            tenant_id=1
        )
        assert user.email == "test@example.com"
        assert user.password == "ValidPass987"

    def test_user_create_invalid_email(self):
        """Test user creation with invalid email"""
        with pytest.raises(ValidationError):
            UserCreate(
                email="invalid-email",
                password="ValidPass987",
                tenant_id=1
            )

    def test_user_create_short_password(self):
        """Test user creation with short password"""
        with pytest.raises(ValidationError):
            UserCreate(
                email="test@example.com",
                password="short",
                tenant_id=1
            )

    def test_user_login_valid(self):
        """Test valid login schema"""
        login = UserLogin(
            email="test@example.com",
            password="ValidPass987"
        )
        assert login.email == "test@example.com"

    def test_user_update_valid(self):
        """Test valid user update"""
        update = UserUpdate(full_name="New Name")
        assert update.full_name == "New Name"


class TestTicketSchemas:
    """Tests for ticket-related schemas"""

    def test_ticket_create_valid(self):
        """Test valid ticket creation"""
        ticket = TicketCreate(
            title="Test Ticket",
            description="Test description",
            priority="medium"
        )
        assert ticket.title == "Test Ticket"
        assert ticket.priority == "medium"

    def test_ticket_create_minimal(self):
        """Test minimal ticket creation"""
        ticket = TicketCreate(title="Minimal")
        assert ticket.title == "Minimal"
        assert ticket.priority == "medium"  # default

    def test_ticket_update_valid(self):
        """Test valid ticket update"""
        update = TicketUpdate(
            status="in_progress",
            priority="high"
        )
        assert update.status == "in_progress"
        assert update.priority == "high"

    def test_ticket_update_partial(self):
        """Test partial ticket update"""
        update = TicketUpdate(title="New Title")
        assert update.title == "New Title"
        assert update.status is None


class TestMessageSchemas:
    """Tests for message-related schemas"""

    def test_message_create_valid(self):
        """Test valid message creation"""
        message = MessageCreate(
            content="Test message",
            role="user"
        )
        assert message.content == "Test message"
        assert message.role == "user"

    def test_message_create_with_auto_respond(self):
        """Test message with auto_respond"""
        message = MessageCreate(
            content="Help",
            role="user",
            auto_respond=True
        )
        assert message.auto_respond is True


class TestKBSchemas:
    """Tests for knowledge base schemas"""

    def test_chunk_create_valid(self):
        """Test valid chunk creation"""
        chunk = ChunkCreate(
            source="test.md",
            content="Test content"
        )
        assert chunk.source == "test.md"
        assert chunk.content == "Test content"

    def test_chunk_create_with_metadata(self):
        """Test chunk with metadata"""
        chunk = ChunkCreate(
            source="test.md",
            content="Content",
            metadata={"category": "faq"}
        )
        assert chunk.metadata == {"category": "faq"}

    def test_search_query_valid(self):
        """Test valid search query"""
        search = SearchQuery(query="test query", limit=10)
        assert search.query == "test query"
        assert search.limit == 10


class TestAuthSchemas:
    """Tests for authentication schemas"""

    def test_token_response_valid(self):
        """Test valid token response"""
        token = Token(
            access_token="test_access",
            refresh_token="test_refresh",
            token_type="bearer",
            expires_in=3600
        )
        assert token.access_token == "test_access"
        assert token.token_type == "bearer"


class TestTenantSchemas:
    """Tests for tenant schemas"""

    def test_tenant_create_valid(self):
        """Test valid tenant creation"""
        tenant = TenantCreate(
            name="Test Tenant"
        )
        assert tenant.name == "Test Tenant"


class TestAgentSchemas:
    """Tests for agent schemas"""

    def test_freeform_request_valid(self):
        """Test valid freeform request"""
        request = FreeformRequest(
            question="test query"
        )
        assert request.question == "test query"

    def test_ticket_respond_request_valid(self):
        """Test valid ticket respond request"""
        request = TicketRespondRequest(
            save_response=True
        )
        assert request.save_response is True

    def test_agent_response_valid(self):
        """Test valid agent response"""
        response = AgentResponseSchema(
            content="Test response",
            needs_escalation=False,
            escalation_reason=None,
            context_used=[],
            model="test-model"
        )
        assert response.content == "Test response"
        assert response.needs_escalation is False

    def test_agent_response_with_escalation(self):
        """Test agent response with escalation"""
        response = AgentResponseSchema(
            content="Need human",
            needs_escalation=True,
            escalation_reason="Complex issue",
            context_used=[],
            model="test-model"
        )
        assert response.needs_escalation is True
        assert response.escalation_reason == "Complex issue"
