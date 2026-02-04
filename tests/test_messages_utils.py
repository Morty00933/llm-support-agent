"""
Tests for message formatting utilities
"""
from src.utils.messages import (
    truncate_message,
    format_conversation_history,
    build_llm_messages,
    ROLE_NAMES,
    LLM_ROLE_MAP,
)


class TestTruncateMessage:
    """Tests for truncate_message function"""

    def test_truncate_short_message(self):
        """Test truncating message shorter than max_length"""
        result = truncate_message("Hello", max_length=100)
        assert result == "Hello"

    def test_truncate_long_message(self):
        """Test truncating long message"""
        text = "A" * 100
        result = truncate_message(text, max_length=50)
        assert len(result) <= 50
        assert result.endswith("...")

    def test_truncate_with_custom_suffix(self):
        """Test truncating with custom suffix"""
        text = "A" * 100
        result = truncate_message(text, max_length=50, suffix="[...]")
        assert result.endswith("[...]")


class TestFormatConversationHistory:
    """Tests for format_conversation_history function"""

    def test_format_empty_messages(self):
        """Test formatting empty messages list"""
        result = format_conversation_history([])
        assert result == ""

    def test_format_single_message_dict(self):
        """Test formatting single message as dict"""
        messages = [{"role": "user", "content": "Hello"}]
        result = format_conversation_history(messages)
        assert "Клиент" in result
        assert "Hello" in result

    def test_format_multiple_messages(self):
        """Test formatting multiple messages"""
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"},
        ]
        result = format_conversation_history(messages)
        assert "Клиент: Hello" in result
        assert "Ассистент: Hi there" in result

    def test_format_with_max_messages(self):
        """Test formatting with max_messages limit"""
        messages = [
            {"role": "user", "content": f"Message {i}"}
            for i in range(20)
        ]
        result = format_conversation_history(messages, max_messages=5)
        lines = result.split("\n")
        assert len(lines) == 5

    def test_format_with_truncation(self):
        """Test formatting with content truncation"""
        long_text = "A" * 1000
        messages = [{"role": "user", "content": long_text}]
        result = format_conversation_history(messages, max_content_length=100)
        assert len(result) < 200  # Should be truncated

    def test_format_without_role_names(self):
        """Test formatting without role names"""
        messages = [{"role": "user", "content": "Hello"}]
        result = format_conversation_history(messages, use_role_names=False)
        assert "user: Hello" in result


class TestBuildLLMMessages:
    """Tests for build_llm_messages function"""

    def test_build_empty_messages(self):
        """Test building from empty messages list"""
        result = build_llm_messages([])
        assert result == []

    def test_build_with_system_prompt(self):
        """Test building with system prompt"""
        messages = [{"role": "user", "content": "Hello"}]
        result = build_llm_messages(messages, system_prompt="You are helpful")
        assert len(result) == 2
        assert result[0]["role"] == "system"
        assert result[0]["content"] == "You are helpful"

    def test_build_from_dict_messages(self):
        """Test building from dict messages"""
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi"},
        ]
        result = build_llm_messages(messages)
        assert len(result) == 2
        assert result[0]["role"] == "user"
        assert result[1]["role"] == "assistant"

    def test_build_with_max_messages(self):
        """Test building with max_messages limit"""
        messages = [
            {"role": "user", "content": f"Message {i}"}
            for i in range(20)
        ]
        result = build_llm_messages(messages, max_messages=5)
        assert len(result) == 5

    def test_build_role_mapping(self):
        """Test that agent role maps to assistant"""
        messages = [{"role": "agent", "content": "Response"}]
        result = build_llm_messages(messages)
        assert result[0]["role"] == "assistant"

    def test_skip_duplicate_system(self):
        """Test that system messages are skipped when system_prompt exists"""
        messages = [
            {"role": "system", "content": "Ignored"},
            {"role": "user", "content": "Hello"},
        ]
        result = build_llm_messages(messages, system_prompt="Used")
        # Should have system prompt + user message, not the system message from list
        assert len(result) == 2
        assert result[0]["content"] == "Used"


class TestConstants:
    """Tests for module constants"""

    def test_role_names_defined(self):
        """Test ROLE_NAMES constant"""
        assert "user" in ROLE_NAMES
        assert "assistant" in ROLE_NAMES
        assert ROLE_NAMES["user"] == "Клиент"

    def test_llm_role_map_defined(self):
        """Test LLM_ROLE_MAP constant"""
        assert "user" in LLM_ROLE_MAP
        assert "agent" in LLM_ROLE_MAP
        assert LLM_ROLE_MAP["agent"] == "assistant"
