"""
Tool Schema Definitions

This module contains schema definitions for all agent tools.
Schemas are separated from implementation for clarity and reusability.

Usage:
    >>> from src.agent.tools.schemas import get_user_context_schema
    >>> schema = get_user_context_schema()
    >>> print(schema.name)
    get-user-context
"""

from src.agent.tools.base import ToolSchema


def get_user_context_schema() -> ToolSchema:
    """Schema for get-user-context tool."""
    return ToolSchema(
        name="get-user-context",
        description="Get complete user learning context including current week, topics, difficulty level, preferences, and recent feedback",
        input_schema={"user_id": "string (UUID)"},
        output_schema={
            "week": "integer (1-24)",
            "topics": "array of strings",
            "difficulty": "string (beginner/intermediate/advanced)",
            "preferences": "object (learning preferences)",
            "recent_feedback": "array (recent feedback items)",
        },
        requires_approval=False,
        example={
            "input": {"user_id": "00000000-0000-0000-0000-000000000001"},
            "output": {
                "week": 7,
                "topics": ["Attention Mechanisms", "Transformers"],
                "difficulty": "intermediate",
                "preferences": {"format": "visual", "struggles": ["math notation"]},
                "recent_feedback": [],
            },
        },
        tags=["user", "context", "database"],
    )


def search_content_schema() -> ToolSchema:
    """Schema for search-content tool."""
    return ToolSchema(
        name="search-content",
        description="Search for relevant learning content using semantic vector search. Returns articles, tutorials, and resources matching the query",
        input_schema={
            "query": "string (search query)",
            "k": "integer (number of results, default: 5)",
            "filters": "object (optional filters like difficulty, source type)",
        },
        output_schema={
            "results": "array of objects with title, snippet, source, url, published_at"
        },
        requires_approval=False,
        example={
            "input": {
                "query": "attention mechanisms in transformers",
                "k": 5,
                "filters": {},
            },
            "output": {
                "results": [
                    {
                        "title": "The Illustrated Transformer",
                        "snippet": "Visual explanation...",
                        "source": "Jay Alammar Blog",
                        "url": "https://...",
                    }
                ]
            },
        },
        tags=["search", "rag", "content"],
    )


def generate_digest_schema() -> ToolSchema:
    """Schema for generate-digest tool."""
    return ToolSchema(
        name="generate-digest",
        description="Generate personalized learning digest using RAG pipeline. Retrieves relevant content via semantic search, synthesizes insights with Claude, and validates quality with RAGAS. Use for both daily digests (7 insights) and answering learning questions (3 insights with explicit_query).",
        input_schema={
            "date": "string (ISO date or 'today', default: 'today')",
            "max_insights": "integer (2-10, default: 7 for digest, 3 for Q&A)",
            "force_refresh": "boolean (skip cache, default: true)",
            "user_context": "object (REQUIRED: user's learning context from get-user-context, must include user_id)",
            "explicit_query": "string (optional: for Q&A mode, e.g. 'What is MCP and how to use it?')",
        },
        output_schema={
            "success": "boolean (true if insights generated successfully)",
            "insights": "array of insight objects with title, explanation, practical_takeaway, source",
            "ragas_scores": "object with faithfulness, context_precision, context_recall, average",
            "quality_badge": "string (✨ high / ✓ good / ⚠️ low)",
            "metadata": "object with query, learning_context, sources, etc.",
            "num_insights": "integer (count of insights generated)",
            "error": "string (only present if success=false)",
        },
        requires_approval=False,
        example={
            "input": {
                "date": "today",
                "max_insights": 5,
                "user_context": {
                    "week": 7,
                    "topics": ["Transformers", "Attention"],
                    "difficulty": "intermediate",
                },
            },
            "output": {
                "insights": [
                    {"title": "...", "explanation": "...", "source": {...}}
                ],
                "ragas_scores": {"average": 0.85, "faithfulness": 0.88},
                "quality_badge": "✨",
            },
        },
        tags=["digest", "rag", "synthesis"],
    )


def search_past_insights_schema() -> ToolSchema:
    """Schema for search-past-insights tool."""
    return ToolSchema(
        name="search-past-insights",
        description="Search through previously delivered insights and digests to find related content or avoid repetition",
        input_schema={
            "query": "string (search query)",
            "date_range": "object (optional start_date, end_date)",
            "min_feedback_score": "integer (optional filter)",
        },
        output_schema={
            "results": "array of past insight objects",
            "count": "integer"
        },
        requires_approval=False,
        example={
            "input": {"query": "transformers attention", "date_range": None},
            "output": {"results": [], "count": 0},
        },
        tags=["search", "history", "database"],
    )


def sync_progress_schema() -> ToolSchema:
    """Schema for sync-progress tool."""
    return ToolSchema(
        name="sync-progress",
        description="Manually sync learning context from bootcamp platform to get latest week and topics",
        input_schema={"user_id": "string (UUID)"},
        output_schema={
            "current_week": "integer",
            "current_topics": "array of strings",
            "message": "string",
        },
        requires_approval=False,
        example={
            "input": {"user_id": "00000000-0000-0000-0000-000000000001"},
            "output": {
                "current_week": 7,
                "current_topics": ["Attention", "Transformers"],
                "message": "Synced successfully",
            },
        },
        tags=["sync", "bootcamp", "integration"],
    )


def web_search_schema() -> ToolSchema:
    """Schema for web-search tool."""
    return ToolSchema(
        name="web-search",
        description="Search the web for educational content when database doesn't have sufficient information. Returns results with full citations. NOTE: Web results are not from curated sources and should be clearly marked.",
        input_schema={
            "query": "string (search query)",
            "max_results": "integer (1-10, default: 5)",
            "search_depth": "string ('basic' or 'advanced', default: 'basic')",
            "include_domains": "array of strings (optional, MUST be full domains like ['wikipedia.org', 'github.com'], NOT TLDs like ['edu', 'org'])",
        },
        output_schema={
            "results": "array of objects with title, content, url, published_date, score",
            "source_api": "string (which API was used: 'tavily' or 'fallback')",
            "citations": "array of citation objects",
            "search_metadata": "object with query and timestamp",
        },
        requires_approval=True,  # Web search requires approval
        example={
            "input": {
                "query": "transformer architecture attention mechanism tutorials",
                "max_results": 5,
            },
            "output": {
                "results": [
                    {
                        "title": "The Illustrated Transformer",
                        "content": "Visual explanation of transformer architecture...",
                        "url": "https://jalammar.github.io/illustrated-transformer/",
                        "score": 0.95,
                        "source_type": "web_search",
                    }
                ],
                "source_api": "tavily",
                "citations": [
                    {
                        "title": "The Illustrated Transformer",
                        "url": "https://jalammar.github.io/illustrated-transformer/",
                        "author": "Jay Alammar",
                    }
                ],
            },
        },
        tags=["search", "web", "external", "requires_approval"],
    )


def analyze_content_coverage_schema() -> ToolSchema:
    """Schema for analyze-content-coverage tool."""
    return ToolSchema(
        name="analyze-content-coverage",
        description="Analyze existing database content to identify what we have and what's missing for a given query. Determines if web search is needed.",
        input_schema={
            "query": "string (user's learning query)",
            "user_id": "string (UUID)",
            "user_context": "object (optional user learning context)",
        },
        output_schema={
            "db_results_count": "integer",
            "topics_covered": "array of strings",
            "coverage_gaps": "array of gap objects",
            "existing_sources": "array of source objects",
            "needs_web_search": "boolean",
            "confidence_score": "float (0.0 to 1.0)",
        },
        requires_approval=False,
        example={
            "input": {
                "query": "quantum computing basics",
                "user_id": "00000000-0000-0000-0000-000000000001",
            },
            "output": {
                "db_results_count": 1,
                "topics_covered": ["quantum", "computing"],
                "coverage_gaps": [
                    {
                        "topic": "quantum gates",
                        "reason": "No content on quantum gates found",
                        "priority": "high",
                        "suggested_query": "quantum gates tutorial",
                    }
                ],
                "existing_sources": [
                    {
                        "title": "Introduction to Quantum Computing",
                        "url": "https://example.com/quantum",
                    }
                ],
                "needs_web_search": True,
                "confidence_score": 0.4,
            },
        },
        tags=["analysis", "coverage", "rag"],
    )


# Registry of all schema factory functions
SCHEMA_REGISTRY = {
    "get-user-context": get_user_context_schema,
    "search-content": search_content_schema,
    "generate-digest": generate_digest_schema,
    "search-past-insights": search_past_insights_schema,
    "sync-progress": sync_progress_schema,
    "web-search": web_search_schema,
    "analyze-content-coverage": analyze_content_coverage_schema,
}


def get_all_schemas() -> dict[str, ToolSchema]:
    """
    Get all tool schemas.

    Returns:
        Dictionary mapping tool names to schemas
    """
    return {name: factory() for name, factory in SCHEMA_REGISTRY.items()}


def get_schema(tool_name: str) -> ToolSchema:
    """
    Get schema for a specific tool.

    Args:
        tool_name: Name of the tool

    Returns:
        ToolSchema for the tool

    Raises:
        KeyError: If tool not found
    """
    if tool_name not in SCHEMA_REGISTRY:
        raise KeyError(f"No schema found for tool: {tool_name}")
    return SCHEMA_REGISTRY[tool_name]()
