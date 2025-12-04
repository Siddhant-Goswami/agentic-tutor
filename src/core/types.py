"""
Shared Type Definitions for Agentic Learning Coach

This module provides type definitions, type aliases, and protocols used
throughout the application. Using these types improves code clarity and
enables static type checking with mypy.

Usage:
    >>> from src.core.types import UserId, ToolResult
    >>> user_id: UserId = "00000000-0000-0000-0000-000000000001"
    >>> result: ToolResult = {"success": True, "data": {...}}
"""

from typing import (
    Dict,
    Any,
    List,
    Optional,
    Protocol,
    TypedDict,
    Union,
    Literal,
    Callable,
    Awaitable,
)
from datetime import datetime, date
from uuid import UUID
from enum import Enum


# =============================================================================
# Type Aliases for Clarity
# =============================================================================

# IDs
UserId = str  # UUID string
SessionId = str  # UUID string
InsightId = str  # UUID string
SourceId = str  # UUID string
ToolName = str  # Tool identifier

# Data structures
JsonDict = Dict[str, Any]  # Generic JSON-like dictionary
Metadata = Dict[str, Any]  # Metadata dictionary


# =============================================================================
# Enums for Literal Types
# =============================================================================


class AgentStatus(str, Enum):
    """Agent execution status."""

    COMPLETED = "completed"
    TIMEOUT = "timeout"
    FAILED = "failed"
    NEEDS_APPROVAL = "needs_approval"
    NEEDS_CLARIFICATION = "needs_clarification"
    RUNNING = "running"


class ActionType(str, Enum):
    """Agent action types."""

    TOOL_CALL = "TOOL_CALL"
    COMPLETE = "COMPLETE"
    CLARIFY = "CLARIFY"
    PLAN_APPROVAL = "PLAN_APPROVAL"


class AgentPhase(str, Enum):
    """Agent execution phases."""

    SENSE = "SENSE"
    PLAN = "PLAN"
    ACT = "ACT"
    OBSERVE = "OBSERVE"
    REFLECT = "REFLECT"
    COMPLETE = "COMPLETE"
    ERROR = "ERROR"


class DifficultyLevel(str, Enum):
    """Learning difficulty levels."""

    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class QualityBadge(str, Enum):
    """Quality assessment badges."""

    HIGH = "✨"
    GOOD = "✓"
    LOW = "⚠️"


# =============================================================================
# TypedDicts for Structured Data
# =============================================================================


class UserContext(TypedDict, total=False):
    """
    User learning context structure.

    This represents the current state of a user's learning journey.
    """

    user_id: UserId
    week: int  # Current bootcamp week (1-24)
    topics: List[str]  # Current learning topics
    difficulty: str  # Learning difficulty level
    preferences: Dict[str, Any]  # User preferences (format, pacing, etc.)
    struggles: List[str]  # Topics user struggles with
    recent_feedback: List[Dict[str, Any]]  # Recent feedback items
    history: List[Dict[str, Any]]  # Learning history


class ToolResult(TypedDict):
    """
    Result from tool execution.

    All tools should return data in this format for consistency.
    """

    success: bool  # Whether execution succeeded
    data: JsonDict  # Result data
    error: Optional[str]  # Error message if failed


class AgentPlan(TypedDict, total=False):
    """
    Agent action plan.

    Represents a planned action the agent intends to take.
    """

    action_type: str  # "TOOL_CALL", "COMPLETE", "CLARIFY", "PLAN_APPROVAL"
    tool: Optional[ToolName]  # Tool to execute (if TOOL_CALL)
    args: Optional[JsonDict]  # Tool arguments
    reasoning: str  # Why this action
    output: Optional[JsonDict]  # Output data (if COMPLETE)
    question: Optional[str]  # Question for user (if CLARIFY)
    research_plan: Optional[Dict[str, Any]]  # Research plan (if PLAN_APPROVAL)


class InsightData(TypedDict):
    """
    Learning insight structure.

    Represents a single synthesized learning insight.
    """

    title: str  # Insight title
    explanation: str  # Detailed explanation
    practical_takeaway: str  # Actionable takeaway
    source: Dict[str, Any]  # Source information
    difficulty: str  # Difficulty level
    tags: List[str]  # Relevant tags/topics


class DigestData(TypedDict):
    """
    Learning digest structure.

    Represents a complete daily digest.
    """

    insights: List[InsightData]  # List of insights
    date: str  # ISO date string
    quality_badge: str  # Quality indicator
    ragas_scores: Dict[str, float]  # RAGAS evaluation scores
    metadata: Metadata  # Additional metadata
    num_insights: int  # Count of insights


class SearchResult(TypedDict):
    """
    Search result structure.

    Represents a single search result from RAG or web search.
    """

    title: str  # Result title
    snippet: str  # Brief content snippet
    content: str  # Full content (if available)
    source: str  # Source name
    url: str  # Source URL
    published_at: Optional[str]  # Publication date
    score: float  # Relevance score
    source_type: str  # "database" or "web_search"


class RAGASScores(TypedDict, total=False):
    """
    RAGAS evaluation scores.

    Represents quality metrics from RAGAS evaluation.
    """

    faithfulness: float  # Faithfulness to source (0-1)
    context_precision: float  # Precision of context (0-1)
    context_recall: float  # Recall of context (0-1)
    answer_relevancy: float  # Answer relevance (0-1)
    average: float  # Overall average score


class LogEntry(TypedDict):
    """
    Agent log entry structure.

    Represents a single log entry from agent execution.
    """

    timestamp: str  # ISO timestamp
    session_id: SessionId  # Session identifier
    iteration: int  # Iteration number
    phase: str  # Agent phase (SENSE, PLAN, etc.)
    content: JsonDict  # Phase-specific content
    duration_ms: int  # Duration in milliseconds


# =============================================================================
# Protocols (Interfaces)
# =============================================================================


class Tool(Protocol):
    """
    Protocol for tool implementations.

    Any class implementing this protocol can be used as a tool in the agent system.
    """

    @property
    def name(self) -> ToolName:
        """Get tool name."""
        ...

    @property
    def description(self) -> str:
        """Get tool description."""
        ...

    async def execute(self, **kwargs: Any) -> ToolResult:
        """
        Execute the tool.

        Args:
            **kwargs: Tool-specific arguments

        Returns:
            ToolResult with success status and data
        """
        ...

    async def validate_input(self, **kwargs: Any) -> bool:
        """
        Validate input arguments.

        Args:
            **kwargs: Arguments to validate

        Returns:
            True if valid, False otherwise
        """
        ...


class Repository(Protocol):
    """
    Protocol for repository implementations.

    Repositories provide data access abstraction following the Repository pattern.
    """

    async def get(self, id: str) -> Optional[Any]:
        """
        Get entity by ID.

        Args:
            id: Entity identifier

        Returns:
            Entity if found, None otherwise
        """
        ...

    async def save(self, entity: Any) -> str:
        """
        Save entity.

        Args:
            entity: Entity to save

        Returns:
            Entity ID
        """
        ...

    async def delete(self, id: str) -> bool:
        """
        Delete entity.

        Args:
            id: Entity identifier

        Returns:
            True if deleted, False if not found
        """
        ...

    async def list(
        self, offset: int = 0, limit: int = 100, filters: Optional[Dict[str, Any]] = None
    ) -> List[Any]:
        """
        List entities with pagination.

        Args:
            offset: Number of records to skip
            limit: Maximum number of records to return
            filters: Optional filters to apply

        Returns:
            List of entities
        """
        ...


class Synthesizer(Protocol):
    """
    Protocol for synthesizer implementations.

    Synthesizers convert retrieved content into structured insights.
    """

    async def synthesize_insights(
        self,
        retrieved_chunks: List[Dict[str, Any]],
        learning_context: UserContext,
        query: str,
        num_insights: int = 7,
    ) -> Dict[str, Any]:
        """
        Synthesize insights from content.

        Args:
            retrieved_chunks: Retrieved content chunks
            learning_context: User's learning context
            query: Original search query
            num_insights: Number of insights to generate

        Returns:
            Dictionary with insights and metadata
        """
        ...


class Renderer(Protocol):
    """
    Protocol for UI renderers.

    Renderers convert data structures into formatted output (HTML, markdown, etc.)
    """

    def render(self, data: Dict[str, Any]) -> str:
        """
        Render data to string output.

        Args:
            data: Data to render

        Returns:
            Rendered string (HTML, markdown, etc.)
        """
        ...


# =============================================================================
# Callable Types
# =============================================================================

# LLM completion function
LLMCompletionFunc = Callable[[str, str], Awaitable[str]]

# Tool execution function
ToolExecutionFunc = Callable[[ToolName, JsonDict], Awaitable[ToolResult]]

# Validation function
ValidationFunc = Callable[[Any], bool]


# =============================================================================
# Union Types for Common Patterns
# =============================================================================

# ID types that can be either string or UUID
IDType = Union[str, UUID]

# Date types that can be either date or datetime
DateType = Union[date, datetime, str]

# Configuration value types
ConfigValue = Union[str, int, float, bool, None]

# LLM provider types
LLMProvider = Literal["openai", "anthropic"]

# Search types
SearchType = Literal["semantic", "keyword", "hybrid"]


# =============================================================================
# Type Guards
# =============================================================================


def is_valid_user_id(value: Any) -> bool:
    """
    Check if value is a valid user ID.

    Args:
        value: Value to check

    Returns:
        True if valid user ID format
    """
    if not isinstance(value, str):
        return False
    try:
        UUID(value)
        return True
    except (ValueError, AttributeError):
        return False


def is_tool_result(value: Any) -> bool:
    """
    Check if value is a valid ToolResult.

    Args:
        value: Value to check

    Returns:
        True if valid ToolResult format
    """
    if not isinstance(value, dict):
        return False
    return (
        "success" in value
        and isinstance(value["success"], bool)
        and "data" in value
        and isinstance(value["data"], dict)
    )


def is_user_context(value: Any) -> bool:
    """
    Check if value is a valid UserContext.

    Args:
        value: Value to check

    Returns:
        True if valid UserContext format
    """
    if not isinstance(value, dict):
        return False
    required_keys = {"user_id"}
    return required_keys.issubset(value.keys())
