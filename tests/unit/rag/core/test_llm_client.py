"""
Tests for Unified LLM Client
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.rag.core.llm_client import LLMClient, LLMProvider


class TestLLMClient:
    """Test cases for LLMClient."""

    def test_init_openai_default_model(self):
        """Test OpenAI client initialization with default model."""
        with patch("openai.AsyncOpenAI") as mock_openai:
            client = LLMClient(
                provider=LLMProvider.OPENAI,
                api_key="test_key"
            )

            assert client.provider == LLMProvider.OPENAI
            assert client.model == "gpt-4o"
            mock_openai.assert_called_once_with(api_key="test_key")

    def test_init_openai_custom_model(self):
        """Test OpenAI client initialization with custom model."""
        with patch("openai.AsyncOpenAI"):
            client = LLMClient(
                provider=LLMProvider.OPENAI,
                model="gpt-4o-mini",
                api_key="test_key"
            )

            assert client.model == "gpt-4o-mini"

    def test_init_anthropic_default_model(self):
        """Test Anthropic client initialization with default model."""
        with patch("anthropic.AsyncAnthropic") as mock_anthropic:
            client = LLMClient(
                provider=LLMProvider.ANTHROPIC,
                api_key="test_key"
            )

            assert client.provider == LLMProvider.ANTHROPIC
            assert client.model == "claude-sonnet-4-5-20250929"
            mock_anthropic.assert_called_once_with(api_key="test_key")

    def test_init_anthropic_custom_model(self):
        """Test Anthropic client initialization with custom model."""
        with patch("anthropic.AsyncAnthropic"):
            client = LLMClient(
                provider=LLMProvider.ANTHROPIC,
                model="claude-opus-4",
                api_key="test_key"
            )

            assert client.model == "claude-opus-4"

    def test_init_invalid_provider(self):
        """Test initialization with invalid provider raises error."""
        with pytest.raises(ValueError, match="Unsupported provider"):
            LLMClient(provider="invalid", api_key="test_key")

    @pytest.mark.asyncio
    async def test_generate_openai(self):
        """Test generate method with OpenAI."""
        with patch("openai.AsyncOpenAI") as mock_openai:
            # Setup mock
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "Generated response"

            mock_client = AsyncMock()
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            mock_openai.return_value = mock_client

            # Create client and generate
            client = LLMClient(provider=LLMProvider.OPENAI, api_key="test_key")
            result = await client.generate(
                system="System prompt",
                user="User prompt",
                temperature=0.5,
                max_tokens=1000
            )

            assert result == "Generated response"
            mock_client.chat.completions.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_anthropic(self):
        """Test generate method with Anthropic."""
        with patch("anthropic.AsyncAnthropic") as mock_anthropic:
            # Setup mock
            mock_response = MagicMock()
            mock_response.content = [MagicMock()]
            mock_response.content[0].text = "Generated response"

            mock_client = AsyncMock()
            mock_client.messages.create = AsyncMock(return_value=mock_response)
            mock_anthropic.return_value = mock_client

            # Create client and generate
            client = LLMClient(provider=LLMProvider.ANTHROPIC, api_key="test_key")
            result = await client.generate(
                system="System prompt",
                user="User prompt",
                temperature=0.5,
                max_tokens=1000
            )

            assert result == "Generated response"
            mock_client.messages.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_uses_default_params(self):
        """Test generate uses default temperature and max_tokens."""
        with patch("openai.AsyncOpenAI") as mock_openai:
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "Response"

            mock_client = AsyncMock()
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            mock_openai.return_value = mock_client

            client = LLMClient(
                provider=LLMProvider.OPENAI,
                api_key="test_key",
                default_temperature=0.8,
                default_max_tokens=2000
            )
            await client.generate(system="System", user="User")

            # Check that default params were used
            call_args = mock_client.chat.completions.create.call_args
            assert call_args.kwargs["temperature"] == 0.8
            assert call_args.kwargs["max_tokens"] == 2000

    @pytest.mark.asyncio
    async def test_generate_structured_openai(self):
        """Test structured generation with OpenAI."""
        with patch("openai.AsyncOpenAI") as mock_openai:
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = '{"key": "value"}'

            mock_client = AsyncMock()
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            mock_openai.return_value = mock_client

            client = LLMClient(provider=LLMProvider.OPENAI, api_key="test_key")
            result = await client.generate_structured(
                system="System",
                user="User",
                response_format={"type": "json_object"}
            )

            assert result == {"key": "value"}

    @pytest.mark.asyncio
    async def test_generate_structured_anthropic_raises_error(self):
        """Test structured generation with Anthropic raises NotImplementedError."""
        with patch("anthropic.AsyncAnthropic"):
            client = LLMClient(provider=LLMProvider.ANTHROPIC, api_key="test_key")

            with pytest.raises(NotImplementedError, match="Structured output only supported for OpenAI"):
                await client.generate_structured(
                    system="System",
                    user="User",
                    response_format={"type": "json_object"}
                )

    def test_get_model_info(self):
        """Test get_model_info returns correct information."""
        with patch("openai.AsyncOpenAI"):
            client = LLMClient(
                provider=LLMProvider.OPENAI,
                model="gpt-4o-mini",
                api_key="test_key",
                default_temperature=0.6,
                default_max_tokens=3000
            )

            info = client.get_model_info()

            assert info["provider"] == LLMProvider.OPENAI
            assert info["model"] == "gpt-4o-mini"
            assert info["default_temperature"] == 0.6
            assert info["default_max_tokens"] == 3000

    @pytest.mark.asyncio
    async def test_generate_handles_error(self):
        """Test generate handles errors gracefully."""
        with patch("openai.AsyncOpenAI") as mock_openai:
            mock_client = AsyncMock()
            mock_client.chat.completions.create = AsyncMock(
                side_effect=Exception("API Error")
            )
            mock_openai.return_value = mock_client

            client = LLMClient(provider=LLMProvider.OPENAI, api_key="test_key")

            with pytest.raises(Exception, match="API Error"):
                await client.generate(system="System", user="User")
