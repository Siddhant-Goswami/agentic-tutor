"""
Edge case tests for LLM Client.

Tests for edge cases like None content, empty responses, etc.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from src.rag.core.llm_client import LLMClient, LLMProvider


class TestLLMClientEdgeCases:
    """Test edge cases in LLM client."""

    @pytest.mark.asyncio
    @patch("openai.AsyncOpenAI")
    async def test_generate_openai_none_content(self, mock_openai_class):
        """Test that OpenAI returning None content raises error."""
        # Setup
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        # Mock response with None content
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content=None))]
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        # Create client
        llm_client = LLMClient(
            provider=LLMProvider.OPENAI,
            model="gpt-4o",
            api_key="test-key",
        )

        # Test that None content raises ValueError
        with pytest.raises(ValueError, match="OpenAI returned None content"):
            await llm_client.generate(system="test", user="test")

    @pytest.mark.asyncio
    @patch("openai.AsyncOpenAI")
    async def test_generate_openai_empty_choices(self, mock_openai_class):
        """Test that OpenAI returning empty choices raises error."""
        # Setup
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        # Mock response with empty choices
        mock_response = Mock()
        mock_response.choices = []
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        # Create client
        llm_client = LLMClient(
            provider=LLMProvider.OPENAI,
            model="gpt-4o",
            api_key="test-key",
        )

        # Test that empty choices raises ValueError
        with pytest.raises(ValueError, match="OpenAI returned no choices"):
            await llm_client.generate(system="test", user="test")

    @pytest.mark.asyncio
    @patch("anthropic.AsyncAnthropic")
    async def test_generate_anthropic_none_text(self, mock_anthropic_class):
        """Test that Anthropic returning None text raises error."""
        # Setup
        mock_client = Mock()
        mock_anthropic_class.return_value = mock_client

        # Mock response with None text
        mock_response = Mock()
        mock_response.content = [Mock(text=None)]
        mock_client.messages.create = AsyncMock(return_value=mock_response)

        # Create client
        llm_client = LLMClient(
            provider=LLMProvider.ANTHROPIC,
            model="claude-sonnet-4-5-20250929",
            api_key="test-key",
        )

        # Test that None text raises ValueError
        with pytest.raises(ValueError, match="Anthropic returned None text"):
            await llm_client.generate(system="test", user="test")

    @pytest.mark.asyncio
    @patch("anthropic.AsyncAnthropic")
    async def test_generate_anthropic_empty_content(self, mock_anthropic_class):
        """Test that Anthropic returning empty content raises error."""
        # Setup
        mock_client = Mock()
        mock_anthropic_class.return_value = mock_client

        # Mock response with empty content
        mock_response = Mock()
        mock_response.content = []
        mock_client.messages.create = AsyncMock(return_value=mock_response)

        # Create client
        llm_client = LLMClient(
            provider=LLMProvider.ANTHROPIC,
            model="claude-sonnet-4-5-20250929",
            api_key="test-key",
        )

        # Test that empty content raises ValueError
        with pytest.raises(ValueError, match="Anthropic returned no content"):
            await llm_client.generate(system="test", user="test")

    @pytest.mark.asyncio
    @patch("openai.AsyncOpenAI")
    async def test_generate_openai_valid_content(self, mock_openai_class):
        """Test that valid OpenAI response works correctly."""
        # Setup
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        # Mock valid response
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Valid response"))]
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        # Create client
        llm_client = LLMClient(
            provider=LLMProvider.OPENAI,
            model="gpt-4o",
            api_key="test-key",
        )

        # Test that valid content is returned
        result = await llm_client.generate(system="test", user="test")
        assert result == "Valid response"

    @pytest.mark.asyncio
    @patch("anthropic.AsyncAnthropic")
    async def test_generate_anthropic_valid_content(self, mock_anthropic_class):
        """Test that valid Anthropic response works correctly."""
        # Setup
        mock_client = Mock()
        mock_anthropic_class.return_value = mock_client

        # Mock valid response
        mock_response = Mock()
        mock_response.content = [Mock(text="Valid response")]
        mock_client.messages.create = AsyncMock(return_value=mock_response)

        # Create client
        llm_client = LLMClient(
            provider=LLMProvider.ANTHROPIC,
            model="claude-sonnet-4-5-20250929",
            api_key="test-key",
        )

        # Test that valid content is returned
        result = await llm_client.generate(system="test", user="test")
        assert result == "Valid response"
