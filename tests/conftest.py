"""
Pytest Configuration and Shared Fixtures

This module provides pytest configuration and shared fixtures for all tests.
Fixtures defined here are available to all test modules.

Usage in tests:
    >>> def test_something(test_config):
    ...     assert test_config.environment == "test"
"""

import pytest
import asyncio
import os
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock
from pathlib import Path

# Add src to path for imports
import sys

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.config import (
    AppConfig,
    DatabaseConfig,
    LLMConfig,
    AgentConfig,
    RAGConfig,
    IngestionConfig,
    UIConfig,
)


# =============================================================================
# Pytest Configuration
# =============================================================================


def pytest_configure(config):
    """Configure pytest."""
    # Set environment to test
    os.environ["ENVIRONMENT"] = "test"


@pytest.fixture(scope="session")
def event_loop():
    """
    Create event loop for async tests.

    This fixture ensures we have a single event loop for the entire test session.
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# =============================================================================
# Configuration Fixtures
# =============================================================================


@pytest.fixture
def test_config() -> AppConfig:
    """
    Test configuration fixture.

    Returns:
        AppConfig with test-appropriate values
    """
    return AppConfig(
        database=DatabaseConfig(
            url="http://test-supabase.local",
            key="test-supabase-key",
            connection_pool_size=5,
            max_retries=1,
            timeout_seconds=10,
        ),
        llm=LLMConfig(
            openai_api_key="test-openai-key",
            anthropic_api_key="test-anthropic-key",
            default_model="gpt-4o-mini",
            default_provider="openai",
            temperature=0.0,  # Deterministic for tests
            max_tokens=1000,
            request_timeout=30,
        ),
        agent=AgentConfig(
            max_iterations=5,
            log_level="DEBUG",
            enable_safety=False,  # Disable for faster tests
            enable_reflection=True,
        ),
        rag=RAGConfig(
            max_chunks_per_query=5,
            similarity_threshold=0.5,
            enable_evaluation=False,  # Disable for faster tests
            enable_reranking=False,
        ),
        ingestion=IngestionConfig(
            batch_size=5,
            max_retries=1,
            enable_web_scraping=False,
            enable_rss=False,
        ),
        ui=UIConfig(
            enable_debug=True,
        ),
        default_user_id="test-user-id-00000000-0000-000000000001",
        environment="test",
    )


@pytest.fixture
def database_config() -> DatabaseConfig:
    """Database configuration fixture."""
    return DatabaseConfig(
        url="http://test-supabase.local",
        key="test-key",
    )


@pytest.fixture
def llm_config() -> LLMConfig:
    """LLM configuration fixture."""
    return LLMConfig(
        openai_api_key="test-openai-key",
        default_model="gpt-4o-mini",
    )


@pytest.fixture
def agent_config() -> AgentConfig:
    """Agent configuration fixture."""
    return AgentConfig(
        max_iterations=5,
        log_level="DEBUG",
        enable_safety=False,
    )


# =============================================================================
# Mock Fixtures
# =============================================================================


@pytest.fixture
def mock_supabase_client():
    """
    Mock Supabase client.

    Returns:
        MagicMock configured to simulate Supabase client
    """
    client = MagicMock()

    # Mock table operations
    table_mock = MagicMock()
    table_mock.select.return_value = table_mock
    table_mock.insert.return_value = table_mock
    table_mock.update.return_value = table_mock
    table_mock.delete.return_value = table_mock
    table_mock.eq.return_value = table_mock
    table_mock.single.return_value = table_mock
    table_mock.execute.return_value = MagicMock(data=[], error=None)

    client.table.return_value = table_mock

    return client


@pytest.fixture
def mock_openai_client():
    """
    Mock OpenAI client.

    Returns:
        AsyncMock configured to simulate OpenAI client
    """
    client = AsyncMock()

    # Mock completion response
    completion_mock = AsyncMock()
    completion_mock.choices = [
        MagicMock(
            message=MagicMock(content="Test response"), finish_reason="stop"
        )
    ]
    completion_mock.usage = MagicMock(
        prompt_tokens=10, completion_tokens=20, total_tokens=30
    )

    client.chat.completions.create.return_value = completion_mock

    # Mock embedding response
    embedding_mock = AsyncMock()
    embedding_mock.data = [MagicMock(embedding=[0.1] * 1536)]
    client.embeddings.create.return_value = embedding_mock

    return client


@pytest.fixture
def mock_anthropic_client():
    """
    Mock Anthropic client.

    Returns:
        AsyncMock configured to simulate Anthropic client
    """
    client = AsyncMock()

    # Mock message response
    message_mock = AsyncMock()
    message_mock.content = [MagicMock(text="Test response")]
    message_mock.stop_reason = "end_turn"
    message_mock.usage = MagicMock(
        input_tokens=10, output_tokens=20
    )

    client.messages.create.return_value = message_mock

    return client


# =============================================================================
# Data Fixtures
# =============================================================================


@pytest.fixture
def sample_user_context():
    """Sample user context data."""
    return {
        "user_id": "test-user-id",
        "week": 7,
        "topics": ["Attention Mechanisms", "Transformers"],
        "difficulty": "intermediate",
        "preferences": {
            "format": "visual",
            "pacing": "moderate",
        },
        "struggles": ["math notation"],
        "recent_feedback": [],
    }


@pytest.fixture
def sample_tool_result():
    """Sample tool result data."""
    return {
        "success": True,
        "data": {
            "message": "Test tool executed successfully",
            "results": [{"id": 1, "value": "test"}],
        },
        "error": None,
    }


@pytest.fixture
def sample_agent_plan():
    """Sample agent plan data."""
    return {
        "action_type": "TOOL_CALL",
        "tool": "search-content",
        "args": {
            "query": "transformers attention mechanism",
            "k": 5,
        },
        "reasoning": "Need to search for relevant content",
    }


@pytest.fixture
def sample_insight():
    """Sample insight data."""
    return {
        "title": "Understanding Attention Mechanisms",
        "explanation": "Attention mechanisms allow models to focus on relevant parts of input...",
        "practical_takeaway": "Use attention to improve model performance on sequence tasks",
        "source": {
            "title": "The Illustrated Transformer",
            "url": "https://example.com/transformer",
        },
        "difficulty": "intermediate",
        "tags": ["attention", "transformers", "nlp"],
    }


@pytest.fixture
def sample_digest():
    """Sample digest data."""
    return {
        "insights": [
            {
                "title": "Insight 1",
                "explanation": "Explanation 1",
                "practical_takeaway": "Takeaway 1",
                "source": {"title": "Source 1", "url": "https://example.com/1"},
            }
        ],
        "date": "2024-11-23",
        "quality_badge": "✨",
        "ragas_scores": {
            "faithfulness": 0.9,
            "context_precision": 0.85,
            "average": 0.875,
        },
        "metadata": {
            "query": "test query",
            "num_sources": 5,
        },
        "num_insights": 1,
    }


# =============================================================================
# Async Fixtures
# =============================================================================


@pytest.fixture
async def async_mock_supabase_client():
    """Async mock Supabase client."""
    client = AsyncMock()

    # Mock async operations
    async def mock_execute():
        return MagicMock(data=[], error=None)

    table_mock = AsyncMock()
    table_mock.select.return_value = table_mock
    table_mock.insert.return_value = table_mock
    table_mock.eq.return_value = table_mock
    table_mock.execute = mock_execute

    client.table.return_value = table_mock

    return client


# =============================================================================
# Parametrize Helpers
# =============================================================================


# Common test user IDs
TEST_USER_IDS = [
    "00000000-0000-0000-0000-000000000001",
    "test-user-id",
]

# Common difficulty levels
DIFFICULTY_LEVELS = ["beginner", "intermediate", "advanced"]

# Common LLM providers
LLM_PROVIDERS = ["openai", "anthropic"]


# =============================================================================
# Utilities
# =============================================================================


@pytest.fixture
def temp_file(tmp_path):
    """Create a temporary file for testing."""

    def _create_file(filename: str, content: str = ""):
        file_path = tmp_path / filename
        file_path.write_text(content)
        return file_path

    return _create_file


@pytest.fixture
def temp_dir(tmp_path):
    """Create a temporary directory for testing."""

    def _create_dir(dirname: str):
        dir_path = tmp_path / dirname
        dir_path.mkdir(parents=True, exist_ok=True)
        return dir_path

    return _create_dir
