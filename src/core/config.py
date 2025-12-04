"""
Centralized Configuration Management

This module provides a centralized configuration system for the Agentic Learning Coach.
All configuration is loaded from environment variables with sensible defaults.

Usage:
    >>> from src.core.config import AppConfig
    >>> config = AppConfig.from_env()
    >>> print(config.database.url)
"""

import os
from dataclasses import dataclass, field
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@dataclass
class DatabaseConfig:
    """Database configuration for Supabase."""

    url: str
    key: str
    connection_pool_size: int = 10
    max_retries: int = 3
    timeout_seconds: int = 30

    def __post_init__(self):
        """Validate database configuration."""
        if not self.url:
            raise ValueError("SUPABASE_URL is required")
        if not self.key:
            raise ValueError("SUPABASE_KEY is required")


@dataclass
class LLMConfig:
    """LLM configuration for OpenAI and Anthropic."""

    openai_api_key: str
    anthropic_api_key: Optional[str] = None
    default_model: str = "gpt-4o-mini"
    default_provider: str = "openai"  # "openai" or "anthropic"
    temperature: float = 0.3
    max_tokens: int = 8000
    request_timeout: int = 60

    def __post_init__(self):
        """Validate LLM configuration."""
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required")
        if self.default_provider not in ("openai", "anthropic"):
            raise ValueError("default_provider must be 'openai' or 'anthropic'")
        if self.default_provider == "anthropic" and not self.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY required when using anthropic provider")


@dataclass
class AgentConfig:
    """Agent execution configuration."""

    max_iterations: int = 10
    log_level: str = "INFO"
    enable_safety: bool = True
    enable_reflection: bool = True
    planning_model: str = "gpt-4o-mini"
    reflection_model: str = "gpt-4o-mini"

    def __post_init__(self):
        """Validate agent configuration."""
        if self.max_iterations < 1:
            raise ValueError("max_iterations must be at least 1")
        if self.log_level not in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"):
            raise ValueError(f"Invalid log_level: {self.log_level}")


@dataclass
class RAGConfig:
    """RAG pipeline configuration."""

    embedding_model: str = "text-embedding-3-small"
    similarity_threshold: float = 0.7
    max_chunks_per_query: int = 10
    chunk_size: int = 1000
    chunk_overlap: int = 200
    enable_reranking: bool = False
    enable_evaluation: bool = True

    def __post_init__(self):
        """Validate RAG configuration."""
        if not 0 <= self.similarity_threshold <= 1:
            raise ValueError("similarity_threshold must be between 0 and 1")
        if self.max_chunks_per_query < 1:
            raise ValueError("max_chunks_per_query must be at least 1")


@dataclass
class IngestionConfig:
    """Content ingestion configuration."""

    batch_size: int = 10
    max_retries: int = 3
    retry_delay_seconds: int = 5
    enable_web_scraping: bool = True
    enable_rss: bool = True


@dataclass
class UIConfig:
    """UI configuration."""

    templates_dir: Optional[str] = None
    static_dir: Optional[str] = None
    theme: str = "dark"
    enable_debug: bool = False


@dataclass
class AppConfig:
    """
    Application configuration.

    This is the main configuration class that aggregates all sub-configurations.
    """

    database: DatabaseConfig
    llm: LLMConfig
    agent: AgentConfig
    rag: RAGConfig
    ingestion: IngestionConfig
    ui: UIConfig
    default_user_id: str
    environment: str = "development"  # "development", "production", "test"

    @classmethod
    def from_env(cls) -> "AppConfig":
        """
        Load configuration from environment variables.

        Returns:
            AppConfig instance with values from environment

        Raises:
            ValueError: If required environment variables are missing
        """
        return cls(
            database=DatabaseConfig(
                url=os.getenv("SUPABASE_URL", ""),
                key=os.getenv("SUPABASE_KEY", ""),
                connection_pool_size=int(
                    os.getenv("DB_CONNECTION_POOL_SIZE", "10")
                ),
                max_retries=int(os.getenv("DB_MAX_RETRIES", "3")),
                timeout_seconds=int(os.getenv("DB_TIMEOUT_SECONDS", "30")),
            ),
            llm=LLMConfig(
                openai_api_key=os.getenv("OPENAI_API_KEY", ""),
                anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
                default_model=os.getenv("LLM_DEFAULT_MODEL", "gpt-4o-mini"),
                default_provider=os.getenv("LLM_DEFAULT_PROVIDER", "openai"),
                temperature=float(os.getenv("LLM_TEMPERATURE", "0.3")),
                max_tokens=int(os.getenv("LLM_MAX_TOKENS", "8000")),
                request_timeout=int(os.getenv("LLM_REQUEST_TIMEOUT", "60")),
            ),
            agent=AgentConfig(
                max_iterations=int(os.getenv("AGENT_MAX_ITERATIONS", "10")),
                log_level=os.getenv("AGENT_LOG_LEVEL", "INFO"),
                enable_safety=os.getenv("AGENT_ENABLE_SAFETY", "true").lower()
                == "true",
                enable_reflection=os.getenv("AGENT_ENABLE_REFLECTION", "true").lower()
                == "true",
                planning_model=os.getenv("AGENT_PLANNING_MODEL", "gpt-4o-mini"),
                reflection_model=os.getenv("AGENT_REFLECTION_MODEL", "gpt-4o-mini"),
            ),
            rag=RAGConfig(
                embedding_model=os.getenv("RAG_EMBEDDING_MODEL", "text-embedding-3-small"),
                similarity_threshold=float(os.getenv("RAG_SIMILARITY_THRESHOLD", "0.7")),
                max_chunks_per_query=int(os.getenv("RAG_MAX_CHUNKS", "10")),
                chunk_size=int(os.getenv("RAG_CHUNK_SIZE", "1000")),
                chunk_overlap=int(os.getenv("RAG_CHUNK_OVERLAP", "200")),
                enable_reranking=os.getenv("RAG_ENABLE_RERANKING", "false").lower()
                == "true",
                enable_evaluation=os.getenv("RAG_ENABLE_EVALUATION", "true").lower()
                == "true",
            ),
            ingestion=IngestionConfig(
                batch_size=int(os.getenv("INGESTION_BATCH_SIZE", "10")),
                max_retries=int(os.getenv("INGESTION_MAX_RETRIES", "3")),
                retry_delay_seconds=int(os.getenv("INGESTION_RETRY_DELAY", "5")),
                enable_web_scraping=os.getenv(
                    "INGESTION_ENABLE_WEB_SCRAPING", "true"
                ).lower()
                == "true",
                enable_rss=os.getenv("INGESTION_ENABLE_RSS", "true").lower() == "true",
            ),
            ui=UIConfig(
                templates_dir=os.getenv("UI_TEMPLATES_DIR"),
                static_dir=os.getenv("UI_STATIC_DIR"),
                theme=os.getenv("UI_THEME", "dark"),
                enable_debug=os.getenv("UI_DEBUG", "false").lower() == "true",
            ),
            default_user_id=os.getenv(
                "DEFAULT_USER_ID", "00000000-0000-0000-0000-000000000001"
            ),
            environment=os.getenv("ENVIRONMENT", "development"),
        )

    @classmethod
    def for_testing(cls) -> "AppConfig":
        """
        Create configuration for testing.

        Returns:
            AppConfig with test-appropriate values
        """
        return cls(
            database=DatabaseConfig(
                url="http://test-supabase.local",
                key="test-key",
                connection_pool_size=5,
            ),
            llm=LLMConfig(
                openai_api_key="test-openai-key",
                default_model="gpt-4o-mini",
            ),
            agent=AgentConfig(
                max_iterations=5,
                log_level="DEBUG",
                enable_safety=False,
            ),
            rag=RAGConfig(
                max_chunks_per_query=5,
                enable_evaluation=False,
            ),
            ingestion=IngestionConfig(
                batch_size=5,
                enable_web_scraping=False,
            ),
            ui=UIConfig(
                enable_debug=True,
            ),
            default_user_id="test-user-id",
            environment="test",
        )

    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == "production"

    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == "development"

    def is_test(self) -> bool:
        """Check if running in test environment."""
        return self.environment == "test"
