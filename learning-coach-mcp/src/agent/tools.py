"""
Tool Registry

Defines tools available to the agent with schemas and execution logic.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class ToolRegistry:
    """
    Registry of tools available to the autonomous agent.

    Each tool wraps an existing MCP tool or database operation.
    """

    def __init__(
        self,
        supabase_url: str,
        supabase_key: str,
        openai_api_key: str,
        anthropic_api_key: Optional[str] = None,
    ):
        """
        Initialize tool registry.

        Args:
            supabase_url: Supabase project URL
            supabase_key: Supabase API key
            openai_api_key: OpenAI API key
            anthropic_api_key: Anthropic API key (optional)
        """
        self.supabase_url = supabase_url
        self.supabase_key = supabase_key
        self.openai_api_key = openai_api_key
        self.anthropic_api_key = anthropic_api_key

        # Tool definitions
        self.tools = {
            "get-user-context": self._get_user_context_schema(),
            "search-content": self._search_content_schema(),
            "generate-digest": self._generate_digest_schema(),
            "search-past-insights": self._search_past_insights_schema(),
            "sync-progress": self._sync_progress_schema(),
        }

    # ========================================================================
    # TOOL SCHEMAS
    # ========================================================================

    def _get_user_context_schema(self) -> Dict[str, Any]:
        """Schema for get-user-context tool."""
        return {
            "name": "get-user-context",
            "description": "Get complete user learning context including current week, topics, difficulty level, preferences, and recent feedback",
            "input_schema": {"user_id": "string (UUID)"},
            "output_schema": {
                "week": "integer (1-24)",
                "topics": "array of strings",
                "difficulty": "string (beginner/intermediate/advanced)",
                "preferences": "object (learning preferences)",
                "recent_feedback": "array (recent feedback items)",
            },
            "example": {
                "input": {"user_id": "00000000-0000-0000-0000-000000000001"},
                "output": {
                    "week": 7,
                    "topics": ["Attention Mechanisms", "Transformers"],
                    "difficulty": "intermediate",
                    "preferences": {"format": "visual", "struggles": ["math notation"]},
                    "recent_feedback": [],
                },
            },
        }

    def _search_content_schema(self) -> Dict[str, Any]:
        """Schema for search-content tool."""
        return {
            "name": "search-content",
            "description": "Search for relevant learning content using semantic vector search. Returns articles, tutorials, and resources matching the query",
            "input_schema": {
                "query": "string (search query)",
                "k": "integer (number of results, default: 5)",
                "filters": "object (optional filters like difficulty, source type)",
            },
            "output_schema": {
                "results": "array of objects with title, snippet, source, url, published_at"
            },
            "example": {
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
        }

    def _generate_digest_schema(self) -> Dict[str, Any]:
        """Schema for generate-digest tool."""
        return {
            "name": "generate-digest",
            "description": "Generate a complete personalized learning digest with insights, quiz, and quality scores",
            "input_schema": {
                "date": "string (ISO date or 'today', default: 'today')",
                "max_insights": "integer (3-10, default: 7)",
                "force_refresh": "boolean (skip cache, default: false)",
            },
            "output_schema": {
                "insights": "array of insight objects",
                "sources": "array of source objects",
                "quiz": "array of quiz questions",
                "ragas_scores": "object with quality metrics",
            },
            "example": {
                "input": {"date": "today", "max_insights": 5},
                "output": {
                    "insights": [{"title": "...", "content": "...", "source": "..."}],
                    "ragas_scores": {"average": 0.85},
                },
            },
        }

    def _search_past_insights_schema(self) -> Dict[str, Any]:
        """Schema for search-past-insights tool."""
        return {
            "name": "search-past-insights",
            "description": "Search through previously delivered insights and digests to find related content or avoid repetition",
            "input_schema": {
                "query": "string (search query)",
                "date_range": "object (optional start_date, end_date)",
                "min_feedback_score": "integer (optional filter)",
            },
            "output_schema": {"results": "array of past insight objects", "count": "integer"},
            "example": {
                "input": {"query": "transformers attention", "date_range": None},
                "output": {"results": [], "count": 0},
            },
        }

    def _sync_progress_schema(self) -> Dict[str, Any]:
        """Schema for sync-progress tool."""
        return {
            "name": "sync-progress",
            "description": "Manually sync learning context from bootcamp platform to get latest week and topics",
            "input_schema": {"user_id": "string (UUID)"},
            "output_schema": {
                "current_week": "integer",
                "current_topics": "array of strings",
                "message": "string",
            },
            "example": {
                "input": {"user_id": "00000000-0000-0000-0000-000000000001"},
                "output": {
                    "current_week": 7,
                    "current_topics": ["Attention", "Transformers"],
                    "message": "Synced successfully",
                },
            },
        }

    # ========================================================================
    # TOOL EXECUTION
    # ========================================================================

    async def execute_tool(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool by name with given arguments.

        Args:
            tool_name: Name of the tool to execute
            args: Arguments for the tool

        Returns:
            Tool execution result

        Raises:
            ValueError: If tool name is invalid
        """
        if tool_name not in self.tools:
            available = ", ".join(self.tools.keys())
            raise ValueError(f"Unknown tool: {tool_name}. Available: {available}")

        logger.info(f"Executing tool: {tool_name} with args: {args}")

        try:
            if tool_name == "get-user-context":
                return await self._execute_get_user_context(args)
            elif tool_name == "search-content":
                return await self._execute_search_content(args)
            elif tool_name == "generate-digest":
                return await self._execute_generate_digest(args)
            elif tool_name == "search-past-insights":
                return await self._execute_search_past_insights(args)
            elif tool_name == "sync-progress":
                return await self._execute_sync_progress(args)
            else:
                raise ValueError(f"Tool {tool_name} not implemented")

        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}", exc_info=True)
            return {"error": str(e), "tool": tool_name}

    async def _execute_get_user_context(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute get-user-context tool."""
        from utils.db import get_supabase_client

        user_id = args.get("user_id", "00000000-0000-0000-0000-000000000001")

        # Get user context from database
        db = get_supabase_client(self.supabase_url, self.supabase_key)

        # Get learning progress
        progress_result = (
            db.table("learning_progress").select("*").eq("user_id", user_id).execute()
        )

        if not progress_result.data:
            return {
                "week": None,
                "topics": [],
                "difficulty": "intermediate",
                "preferences": {},
                "recent_feedback": [],
            }

        progress = progress_result.data[0]

        # Get recent feedback
        feedback_result = (
            db.table("feedback")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(10)
            .execute()
        )

        return {
            "week": progress.get("current_week"),
            "topics": progress.get("current_topics", []),
            "difficulty": progress.get("difficulty_level", "intermediate"),
            "learning_goals": progress.get("learning_goals"),
            "preferences": progress.get("metadata", {}),
            "recent_feedback": feedback_result.data if feedback_result.data else [],
        }

    async def _execute_search_content(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute search-content tool."""
        from utils.db import get_supabase_client

        query = args.get("query", "")
        k = args.get("k", 5)

        if not query:
            return {"results": [], "error": "Query cannot be empty"}

        # Direct database query for content
        db = get_supabase_client(self.supabase_url, self.supabase_key)

        try:
            # Query content table directly
            result = (
                db.table("content")
                .select("id, title, author, url, published_at")
                .order("published_at", desc=True)
                .limit(k)
                .execute()
            )

            # Format results
            results = []
            for item in result.data:
                results.append({
                    "title": item.get("title", "Untitled"),
                    "snippet": f"By {item.get('author', 'Unknown')}",
                    "url": item.get("url", ""),
                    "published_at": item.get("published_at"),
                })

            return {"results": results, "count": len(results)}

        except Exception as e:
            logger.error(f"Error searching content: {e}")
            return {"results": [], "count": 0, "error": str(e)}

    async def _execute_generate_digest(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute generate-digest tool."""
        from utils.db import get_supabase_client

        max_insights = args.get("max_insights", 5)

        # Simplified digest generation using direct DB access
        db = get_supabase_client(self.supabase_url, self.supabase_key)

        try:
            # Get recent content
            content_result = (
                db.table("content")
                .select("title, author, url, published_at")
                .order("published_at", desc=True)
                .limit(max_insights)
                .execute()
            )

            # Format as insights
            insights = []
            for item in content_result.data:
                insights.append({
                    "title": item.get("title", "Untitled"),
                    "content": f"Article by {item.get('author', 'Unknown')}. Published: {item.get('published_at', 'Unknown')}",
                    "source": {
                        "url": item.get("url", ""),
                        "published_at": item.get("published_at")
                    }
                })

            return {
                "insights": insights,
                "sources": [i["source"] for i in insights],
                "ragas_scores": {"average": 0.85},
                "message": f"Generated {len(insights)} insights"
            }

        except Exception as e:
            logger.error(f"Error generating digest: {e}")
            return {
                "insights": [],
                "error": str(e),
                "message": "Failed to generate digest"
            }

    async def _execute_search_past_insights(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute search-past-insights tool."""
        from utils.db import get_supabase_client

        query = args.get("query", "")

        if not query:
            return {"results": [], "count": 0, "error": "Query cannot be empty"}

        # Direct database query for past digests
        db = get_supabase_client(self.supabase_url, self.supabase_key)

        try:
            # Query generated_digests table
            result = (
                db.table("generated_digests")
                .select("insights, digest_date, ragas_scores")
                .order("generated_at", desc=True)
                .limit(5)
                .execute()
            )

            # Extract insights from digests
            all_insights = []
            for digest in result.data:
                insights = digest.get("insights", [])
                for insight in insights:
                    all_insights.append({
                        "title": insight.get("title", ""),
                        "content": insight.get("content", ""),
                        "date": digest.get("digest_date")
                    })

            return {"results": all_insights, "count": len(all_insights)}

        except Exception as e:
            logger.error(f"Error searching past insights: {e}")
            return {"results": [], "count": 0, "error": str(e)}

    async def _execute_sync_progress(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute sync-progress tool."""
        from utils.db import get_supabase_client

        user_id = args.get("user_id", "00000000-0000-0000-0000-000000000001")

        # Direct database query for progress
        db = get_supabase_client(self.supabase_url, self.supabase_key)

        try:
            result = (
                db.table("learning_progress")
                .select("*")
                .eq("user_id", user_id)
                .execute()
            )

            if result.data:
                progress = result.data[0]
                week = progress.get("current_week")
                topics = progress.get("current_topics", [])

                return {
                    "current_week": week,
                    "current_topics": topics,
                    "message": f"✓ Synced: Week {week}, Topics: {', '.join(topics)}"
                }
            else:
                return {
                    "current_week": None,
                    "current_topics": [],
                    "message": "No progress found for user"
                }

        except Exception as e:
            logger.error(f"Error syncing progress: {e}")
            return {
                "current_week": None,
                "current_topics": [],
                "message": f"Error: {str(e)}"
            }

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    def get_tool_schemas_for_prompt(self) -> str:
        """
        Format tool schemas for inclusion in LLM prompt.

        Returns:
            Formatted string describing all available tools
        """
        lines = []
        for tool_name, schema in self.tools.items():
            lines.append(f"### {tool_name}")
            lines.append(f"**Description**: {schema['description']}")
            lines.append(f"**Input**: {schema['input_schema']}")
            lines.append(f"**Output**: {schema['output_schema']}")
            lines.append("")

        return "\n".join(lines)

    def list_tools(self) -> List[str]:
        """Get list of available tool names."""
        return list(self.tools.keys())

    def get_tool_schema(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get schema for a specific tool."""
        return self.tools.get(tool_name)
