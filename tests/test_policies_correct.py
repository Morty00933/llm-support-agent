"""
Tests for agent policies - correct implementation
"""
import pytest
from src.agent.policies import (
    should_escalate,
    build_system_prompt,
    detect_language,
    trim_text,
    normalize_whitespace,
    ESCALATION_KEYWORDS,
    ALL_ESCALATION_KEYWORDS,
    LOW_CONFIDENCE_PHRASES,
    DEFAULT_TEMPERATURE,
    MAX_STEPS,
)


class TestShouldEscalate:
    """Tests for should_escalate function"""

    def test_escalate_refund_english(self):
        """Test escalation on refund request in English"""
        needs_escalation, reason = should_escalate("I want a refund please")
        assert needs_escalation is True
        assert "refund" in reason.lower()

    def test_escalate_complaint_english(self):
        """Test escalation on complaint in English"""
        needs_escalation, reason = should_escalate("I want to file a complaint")
        assert needs_escalation is True
        assert reason is not None

    def test_escalate_lawsuit(self):
        """Test escalation on legal threat"""
        needs_escalation, reason = should_escalate("I will sue you")
        assert needs_escalation is True
        assert reason is not None

    def test_escalate_russian_keywords(self):
        """Test escalation on Russian keywords"""
        needs_escalation, reason = should_escalate("Я хочу возврат денег")
        assert needs_escalation is True
        assert reason is not None

    def test_no_escalation_normal(self):
        """Test no escalation for normal query"""
        needs_escalation, reason = should_escalate("How do I reset my password?")
        assert needs_escalation is False
        assert reason is None

    def test_no_escalation_greeting(self):
        """Test no escalation for greeting"""
        needs_escalation, reason = should_escalate("Hello, how are you?")
        assert needs_escalation is False
        assert reason is None

    def test_escalate_low_confidence(self):
        """Test escalation on low confidence phrase"""
        needs_escalation, reason = should_escalate("I don't know the answer")
        assert needs_escalation is True
        assert "confidence" in reason.lower()

    def test_escalate_mixed_case(self):
        """Test escalation with mixed case"""
        needs_escalation, reason = should_escalate("I WANT A REFUND NOW!")
        assert needs_escalation is True
        assert reason is not None

    def test_escalate_low_kb_score(self):
        """Test escalation on low KB match score"""
        kb_hits = [{"score": 0.3}, {"score": 0.2}]
        needs_escalation, reason = should_escalate(
            "test query",
            kb_hits=kb_hits,
            min_kb_score=0.5
        )
        assert needs_escalation is True
        assert "score" in reason.lower()

    def test_no_escalate_good_kb_score(self):
        """Test no escalation with good KB score"""
        kb_hits = [{"score": 0.9}, {"score": 0.8}]
        needs_escalation, reason = should_escalate(
            "test query",
            kb_hits=kb_hits,
            min_kb_score=0.5
        )
        assert needs_escalation is False
        assert reason is None


class TestBuildSystemPrompt:
    """Tests for build_system_prompt function"""

    def test_build_with_context(self):
        """Test building system prompt with context"""
        prompt = build_system_prompt(
            context="Password reset instructions",
            history="User: Hello",
        )
        assert "Password reset instructions" in prompt
        assert "User: Hello" in prompt
        assert len(prompt) > 100

    def test_build_without_context(self):
        """Test building system prompt without context"""
        prompt = build_system_prompt(context=None, history=None)
        assert len(prompt) > 50
        assert "ИИ-ассистент" in prompt or "ассистент" in prompt.lower()

    def test_build_with_empty_context(self):
        """Test building with empty context"""
        prompt = build_system_prompt(context="", history="")
        assert "Новый диалог" in prompt


class TestDetectLanguage:
    """Tests for detect_language function"""

    def test_detect_russian(self):
        """Test detecting Russian language"""
        result = detect_language("Привет, как дела?")
        assert result == "ru"

    def test_detect_english(self):
        """Test detecting English language"""
        result = detect_language("Hello, how are you?")
        assert result == "en"

    def test_detect_mixed_more_russian(self):
        """Test detecting mixed text with more Russian"""
        result = detect_language("Привет hello мир world тест")
        assert result == "ru"

    def test_detect_mixed_more_english(self):
        """Test detecting mixed text with more English"""
        result = detect_language("Hello привет world мир test")
        assert result == "en"


class TestTrimText:
    """Tests for trim_text function"""

    def test_trim_short_text(self):
        """Test trimming short text"""
        result = trim_text("Hello", max_chars=100)
        assert result == "Hello"

    def test_trim_long_text(self):
        """Test trimming long text"""
        text = "A" * 100
        result = trim_text(text, max_chars=50)
        assert len(result) == 50
        assert result.endswith("...")

    def test_trim_with_custom_tail(self):
        """Test trimming with custom tail"""
        text = "A" * 100
        result = trim_text(text, max_chars=50, tail="[cut]")
        assert result.endswith("[cut]")


class TestNormalizeWhitespace:
    """Tests for normalize_whitespace function"""

    def test_normalize_multiple_spaces(self):
        """Test normalizing multiple spaces"""
        result = normalize_whitespace("Hello    world")
        assert result == "Hello world"

    def test_normalize_newlines(self):
        """Test normalizing newlines"""
        result = normalize_whitespace("Hello\n\nworld")
        assert result == "Hello world"

    def test_normalize_tabs(self):
        """Test normalizing tabs"""
        result = normalize_whitespace("Hello\t\tworld")
        assert result == "Hello world"

    def test_normalize_mixed_whitespace(self):
        """Test normalizing mixed whitespace"""
        result = normalize_whitespace("  Hello  \n  world  \t  ")
        assert result == "Hello world"


class TestConstants:
    """Tests for module constants"""

    def test_escalation_keywords_exist(self):
        """Test ESCALATION_KEYWORDS constant"""
        assert "en" in ESCALATION_KEYWORDS
        assert "ru" in ESCALATION_KEYWORDS
        assert "refund" in ESCALATION_KEYWORDS["en"]
        assert "возврат" in ESCALATION_KEYWORDS["ru"]

    def test_all_escalation_keywords(self):
        """Test ALL_ESCALATION_KEYWORDS constant"""
        assert len(ALL_ESCALATION_KEYWORDS) > 0
        assert "refund" in ALL_ESCALATION_KEYWORDS

    def test_low_confidence_phrases(self):
        """Test LOW_CONFIDENCE_PHRASES constant"""
        assert len(LOW_CONFIDENCE_PHRASES) > 0
        assert "i don't know" in LOW_CONFIDENCE_PHRASES

    def test_default_temperature(self):
        """Test DEFAULT_TEMPERATURE constant"""
        assert DEFAULT_TEMPERATURE == 0.2
        assert isinstance(DEFAULT_TEMPERATURE, float)

    def test_max_steps(self):
        """Test MAX_STEPS constant"""
        assert MAX_STEPS == 4
        assert isinstance(MAX_STEPS, int)
