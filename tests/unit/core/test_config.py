"""
Tests for src.core.config module.

Tests configuration loading, validation, and helper methods.
"""

import pytest
import os
from src.core.config import (
    AppConfig,
    DatabaseConfig,
    LLMConfig,
    AgentConfig,
    RAGConfig,
    IngestionConfig,
    UIConfig,
)


class TestDatabaseConfig:
    """Tests for DatabaseConfig."""

    def test_valid_config(self):
        """Test creating valid database config."""
        config = DatabaseConfig(url="http://localhost:54321", key="test-key")
        assert config.url == "http://localhost:54321"
        assert config.key == "test-key"
        assert config.connection_pool_size == 10  # Default

    def test_missing_url_raises_error(self):
        """Test that missing URL raises ValueError."""
        with pytest.raises(ValueError, match="SUPABASE_URL is required"):
            DatabaseConfig(url="", key="test-key")

    def test_missing_key_raises_error(self):
        """Test that missing key raises ValueError."""
        with pytest.raises(ValueError, match="SUPABASE_KEY is required"):
            DatabaseConfig(url="http://localhost", key="")


class TestLLMConfig:
    """Tests for LLMConfig."""

    def test_valid_config(self):
        """Test creating valid LLM config."""
        config = LLMConfig(openai_api_key="test-key")
        assert config.openai_api_key == "test-key"
        assert config.default_model == "gpt-4o-mini"
        assert config.temperature == 0.3

    def test_missing_openai_key_raises_error(self):
        """Test that missing OpenAI key raises ValueError."""
        with pytest.raises(ValueError, match="OPENAI_API_KEY is required"):
            LLMConfig(openai_api_key="")

    def test_invalid_provider_raises_error(self):
        """Test that invalid provider raises ValueError."""
        with pytest.raises(ValueError, match="default_provider must be"):
            LLMConfig(openai_api_key="test-key", default_provider="invalid")

    def test_anthropic_provider_requires_key(self):
        """Test that Anthropic provider requires Anthropic key."""
        with pytest.raises(ValueError, match="ANTHROPIC_API_KEY required"):
            LLMConfig(
                openai_api_key="test-key",
                default_provider="anthropic",
                anthropic_api_key=None,
            )


class TestAgentConfig:
    """Tests for AgentConfig."""

    def test_valid_config(self):
        """Test creating valid agent config."""
        config = AgentConfig()
        assert config.max_iterations == 10
        assert config.log_level == "INFO"
        assert config.enable_safety is True

    def test_invalid_max_iterations_raises_error(self):
        """Test that invalid max_iterations raises ValueError."""
        with pytest.raises(ValueError, match="max_iterations must be at least 1"):
            AgentConfig(max_iterations=0)

    def test_invalid_log_level_raises_error(self):
        """Test that invalid log_level raises ValueError."""
        with pytest.raises(ValueError, match="Invalid log_level"):
            AgentConfig(log_level="INVALID")


class TestRAGConfig:
    """Tests for RAGConfig."""

    def test_valid_config(self):
        """Test creating valid RAG config."""
        config = RAGConfig()
        assert config.embedding_model == "text-embedding-3-small"
        assert config.similarity_threshold == 0.7
        assert config.max_chunks_per_query == 10

    def test_invalid_similarity_threshold_raises_error(self):
        """Test that invalid similarity threshold raises ValueError."""
        with pytest.raises(ValueError, match="similarity_threshold must be between 0 and 1"):
            RAGConfig(similarity_threshold=1.5)

    def test_invalid_max_chunks_raises_error(self):
        """Test that invalid max_chunks raises ValueError."""
        with pytest.raises(ValueError, match="max_chunks_per_query must be at least 1"):
            RAGConfig(max_chunks_per_query=0)


class TestAppConfig:
    """Tests for AppConfig."""

    def test_for_testing_creates_valid_config(self):
        """Test that for_testing() creates valid test config."""
        config = AppConfig.for_testing()
        assert config.environment == "test"
        assert config.database.url == "http://test-supabase.local"
        assert config.llm.openai_api_key == "test-openai-key"
        assert config.agent.max_iterations == 5
        assert config.agent.enable_safety is False

    def test_is_test_method(self):
        """Test is_test() method."""
        config = AppConfig.for_testing()
        assert config.is_test() is True
        assert config.is_production() is False
        assert config.is_development() is False

    def test_is_development_method(self):
        """Test is_development() method."""
        config = AppConfig.for_testing()
        config.environment = "development"
        assert config.is_development() is True
        assert config.is_test() is False
        assert config.is_production() is False

    def test_is_production_method(self):
        """Test is_production() method."""
        config = AppConfig.for_testing()
        config.environment = "production"
        assert config.is_production() is True
        assert config.is_test() is False
        assert config.is_development() is False


class TestConfigFromEnv:
    """Tests for loading config from environment."""

    def test_from_env_with_minimal_env_vars(self, monkeypatch):
        """Test loading config from environment with minimal vars."""
        # Set required environment variables
        monkeypatch.setenv("SUPABASE_URL", "http://localhost:54321")
        monkeypatch.setenv("SUPABASE_KEY", "test-key")
        monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
        monkeypatch.delenv("ENVIRONMENT", raising=False)  # Remove test environment

        config = AppConfig.from_env()

        assert config.database.url == "http://localhost:54321"
        assert config.database.key == "test-key"
        assert config.llm.openai_api_key == "test-openai-key"
        assert config.environment == "development"  # Default

    def test_from_env_with_custom_values(self, monkeypatch):
        """Test loading config with custom environment values."""
        monkeypatch.setenv("SUPABASE_URL", "http://custom:54321")
        monkeypatch.setenv("SUPABASE_KEY", "custom-key")
        monkeypatch.setenv("OPENAI_API_KEY", "custom-openai-key")
        monkeypatch.setenv("AGENT_MAX_ITERATIONS", "15")
        monkeypatch.setenv("RAG_SIMILARITY_THRESHOLD", "0.8")
        monkeypatch.setenv("ENVIRONMENT", "production")

        config = AppConfig.from_env()

        assert config.agent.max_iterations == 15
        assert config.rag.similarity_threshold == 0.8
        assert config.environment == "production"
