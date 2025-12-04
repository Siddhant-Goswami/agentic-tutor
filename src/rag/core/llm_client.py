"""
Unified LLM Client

Provides a single interface for both OpenAI and Anthropic LLM calls,
simplifying model switching and testing.
"""

import logging
from typing import Optional, Dict, Any, List
from enum import Enum

logger = logging.getLogger(__name__)


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


class LLMClient:
    """Unified client for OpenAI and Anthropic LLMs."""

    def __init__(
        self,
        provider: LLMProvider = LLMProvider.OPENAI,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        default_temperature: float = 0.7,
        default_max_tokens: int = 4000,
    ):
        """
        Initialize LLM client.

        Args:
            provider: LLM provider (openai or anthropic)
            model: Model name (uses provider defaults if not specified)
            api_key: API key for the provider
            default_temperature: Default temperature for generation
            default_max_tokens: Default max tokens for generation
        """
        self.provider = provider
        self.default_temperature = default_temperature
        self.default_max_tokens = default_max_tokens

        # Set default models per provider
        if model:
            self.model = model
        else:
            self.model = "gpt-4o" if provider == LLMProvider.OPENAI else "claude-sonnet-4-5-20250929"

        # Initialize provider client
        if provider == LLMProvider.OPENAI:
            from openai import AsyncOpenAI
            self.client = AsyncOpenAI(api_key=api_key)
            logger.info(f"Initialized OpenAI client with model: {self.model}")
        elif provider == LLMProvider.ANTHROPIC:
            from anthropic import AsyncAnthropic
            self.client = AsyncAnthropic(api_key=api_key)
            logger.info(f"Initialized Anthropic client with model: {self.model}")
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    async def generate(
        self,
        system: str,
        user: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> str:
        """
        Generate completion from LLM.

        Args:
            system: System prompt
            user: User prompt
            temperature: Temperature override (uses default if not specified)
            max_tokens: Max tokens override (uses default if not specified)
            **kwargs: Additional provider-specific parameters

        Returns:
            Generated text response

        Raises:
            Exception: If LLM call fails
        """
        temperature = temperature if temperature is not None else self.default_temperature
        max_tokens = max_tokens if max_tokens is not None else self.default_max_tokens

        try:
            if self.provider == LLMProvider.OPENAI:
                return await self._generate_openai(system, user, temperature, max_tokens, **kwargs)
            else:
                return await self._generate_anthropic(system, user, temperature, max_tokens, **kwargs)
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            raise

    async def _generate_openai(
        self,
        system: str,
        user: str,
        temperature: float,
        max_tokens: int,
        **kwargs,
    ) -> str:
        """Generate completion using OpenAI API."""
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )

        # Validate response
        if not response.choices:
            raise ValueError("OpenAI returned no choices")

        content = response.choices[0].message.content
        if content is None:
            raise ValueError("OpenAI returned None content")

        return content

    async def _generate_anthropic(
        self,
        system: str,
        user: str,
        temperature: float,
        max_tokens: int,
        **kwargs,
    ) -> str:
        """Generate completion using Anthropic API."""
        response = await self.client.messages.create(
            model=self.model,
            system=system,
            messages=[{"role": "user", "content": user}],
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )

        # Validate response
        if not response.content:
            raise ValueError("Anthropic returned no content")

        text = response.content[0].text
        if text is None:
            raise ValueError("Anthropic returned None text")

        return text

    async def generate_structured(
        self,
        system: str,
        user: str,
        response_format: Dict[str, Any],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Generate structured JSON response (OpenAI only for now).

        Args:
            system: System prompt
            user: User prompt
            response_format: JSON schema for structured output
            temperature: Temperature override
            max_tokens: Max tokens override

        Returns:
            Parsed JSON response

        Raises:
            NotImplementedError: If provider doesn't support structured output
        """
        if self.provider != LLMProvider.OPENAI:
            raise NotImplementedError("Structured output only supported for OpenAI")

        import json

        temperature = temperature if temperature is not None else self.default_temperature
        max_tokens = max_tokens if max_tokens is not None else self.default_max_tokens

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
            response_format=response_format,
        )

        return json.loads(response.choices[0].message.content)

    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about current model configuration.

        Returns:
            Dictionary with model info
        """
        return {
            "provider": self.provider,
            "model": self.model,
            "default_temperature": self.default_temperature,
            "default_max_tokens": self.default_max_tokens,
        }
