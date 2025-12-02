"""
Tool Registry

Defines tools available to the agent with schemas and execution logic.
"""

import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

# Add MCP src to path for accessing shared utilities
project_root = Path(__file__).parent.parent
mcp_src_path = project_root / "learning-coach-mcp" / "src"
sys.path.insert(0, str(mcp_src_path))

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
            "web-search": self._web_search_schema(),
            "analyze-content-coverage": self._analyze_content_coverage_schema(),
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
            "description": "Generate personalized learning digest using RAG pipeline. Retrieves relevant content via semantic search, synthesizes insights with Claude, and validates quality with RAGAS. Use for both daily digests (7 insights) and answering learning questions (3 insights with explicit_query).",
            "input_schema": {
                "date": "string (ISO date or 'today', default: 'today')",
                "max_insights": "integer (2-10, default: 7 for digest, 3 for Q&A)",
                "force_refresh": "boolean (skip cache, default: true)",
                "user_context": "object (REQUIRED: user's learning context from get-user-context, must include user_id)",
                "explicit_query": "string (optional: for Q&A mode, e.g. 'What is MCP and how to use it?')",
            },
            "output_schema": {
                "success": "boolean (true if insights generated successfully)",
                "insights": "array of insight objects with title, explanation, practical_takeaway, source",
                "ragas_scores": "object with faithfulness, context_precision, context_recall, average",
                "quality_badge": "string (✨ high / ✓ good / ⚠️ low)",
                "metadata": "object with query, learning_context, sources, etc.",
                "num_insights": "integer (count of insights generated)",
                "error": "string (only present if success=false)",
            },
            "example": {
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
                    "insights": [{"title": "...", "explanation": "...", "source": {...}}],
                    "ragas_scores": {"average": 0.85, "faithfulness": 0.88},
                    "quality_badge": "✨",
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

    def _web_search_schema(self) -> Dict[str, Any]:
        """Schema for web-search tool."""
        return {
            "name": "web-search",
            "description": "Search the web for educational content when database doesn't have sufficient information. Returns results with full citations. NOTE: Web results are not from curated sources and should be clearly marked.",
            "input_schema": {
                "query": "string (search query)",
                "max_results": "integer (1-10, default: 5)",
                "search_depth": "string ('basic' or 'advanced', default: 'basic')",
                "include_domains": "array of strings (optional, MUST be full domains like ['wikipedia.org', 'github.com'], NOT TLDs like ['edu', 'org'])",
            },
            "output_schema": {
                "results": "array of objects with title, content, url, published_date, score",
                "source_api": "string (which API was used: 'tavily' or 'fallback')",
                "citations": "array of citation objects",
                "search_metadata": "object with query and timestamp"
            },
            "requires_approval": True,
            "example": {
                "input": {
                    "query": "transformer architecture attention mechanism tutorials",
                    "max_results": 5
                },
                "output": {
                    "results": [
                        {
                            "title": "The Illustrated Transformer",
                            "content": "Visual explanation of transformer architecture...",
                            "url": "https://jalammar.github.io/illustrated-transformer/",
                            "score": 0.95,
                            "source_type": "web_search"
                        }
                    ],
                    "source_api": "tavily",
                    "citations": [
                        {
                            "title": "The Illustrated Transformer",
                            "url": "https://jalammar.github.io/illustrated-transformer/",
                            "author": "Jay Alammar"
                        }
                    ]
                }
            }
        }

    def _analyze_content_coverage_schema(self) -> Dict[str, Any]:
        """Schema for analyze-content-coverage tool."""
        return {
            "name": "analyze-content-coverage",
            "description": "Analyze existing database content to identify what we have and what's missing for a given query. Determines if web search is needed.",
            "input_schema": {
                "query": "string (user's learning query)",
                "user_id": "string (UUID)",
                "user_context": "object (optional user learning context)"
            },
            "output_schema": {
                "db_results_count": "integer",
                "topics_covered": "array of strings",
                "coverage_gaps": "array of gap objects",
                "existing_sources": "array of source objects",
                "needs_web_search": "boolean",
                "confidence_score": "float (0.0 to 1.0)"
            },
            "example": {
                "input": {
                    "query": "quantum computing basics",
                    "user_id": "00000000-0000-0000-0000-000000000001"
                },
                "output": {
                    "db_results_count": 1,
                    "topics_covered": ["quantum", "computing"],
                    "coverage_gaps": [
                        {
                            "topic": "quantum gates",
                            "reason": "No content on quantum gates found",
                            "priority": "high",
                            "suggested_query": "quantum gates tutorial"
                        }
                    ],
                    "existing_sources": [
                        {
                            "title": "Introduction to Quantum Computing",
                            "url": "https://example.com/quantum"
                        }
                    ],
                    "needs_web_search": True,
                    "confidence_score": 0.4
                }
            }
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
            elif tool_name == "web-search":
                return await self._execute_web_search(args)
            elif tool_name == "analyze-content-coverage":
                return await self._execute_analyze_content_coverage(args)
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
        """
        Execute generate-digest tool using proper RAG pipeline.

        Now using direct imports since learning-coach-mcp is installed as a package.
        """
        from datetime import datetime, date
        from rag.digest_generator import DigestGenerator

        # Parse arguments
        date_str = args.get("date", "today")
        if date_str == "today":
            digest_date = date.today()
        else:
            try:
                digest_date = datetime.fromisoformat(date_str).date()
            except ValueError:
                digest_date = date.today()

        max_insights = args.get("max_insights", 7)
        force_refresh = args.get("force_refresh", True)  # Always force to avoid empty cache
        user_context = args.get("user_context", {})
        explicit_query = args.get("explicit_query")  # NEW: for Q&A mode

        # Get user_id from context
        user_id = user_context.get("user_id", "00000000-0000-0000-0000-000000000001")

        try:
            # Initialize proper DigestGenerator
            generator = DigestGenerator(
                supabase_url=self.supabase_url,
                supabase_key=self.supabase_key,
                openai_api_key=self.openai_api_key,
                anthropic_api_key=self.anthropic_api_key,
                ragas_min_score=0.70,
            )

            logger.info(f"Generating digest: date={digest_date}, insights={max_insights}, explicit_query={explicit_query}")

            # Call actual RAG pipeline
            result = await generator.generate(
                user_id=user_id,
                date=digest_date,
                max_insights=max_insights,
                force_refresh=force_refresh,
                explicit_query=explicit_query,  # Pass explicit query for Q&A mode
            )

            # Ensure proper format for agent with success indicator
            if result.get("insights"):
                return {
                    "success": True,
                    "insights": result["insights"],
                    "ragas_scores": result.get("ragas_scores", {}),
                    "quality_badge": result.get("quality_badge", "✓"),
                    "metadata": result.get("metadata", {}),
                    "num_insights": len(result["insights"])
                }
            else:
                # Empty insights = failure
                return {
                    "success": False,
                    "insights": [],
                    "error": result.get("metadata", {}).get("error", "No insights generated"),
                    "ragas_scores": {},
                    "num_insights": 0
                }

        except Exception as e:
            logger.error(f"Error generating digest: {e}", exc_info=True)
            return {
                "success": False,
                "insights": [],
                "error": str(e),
                "ragas_scores": {},
                "num_insights": 0
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

    async def _execute_web_search(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute web-search tool using Tavily API."""
        import os
        from datetime import datetime

        query = args.get("query", "")
        max_results = args.get("max_results", 5)
        search_depth = args.get("search_depth", "basic")
        include_domains = args.get("include_domains", [])

        if not query:
            return {"results": [], "error": "Query cannot be empty"}

        # Get Tavily API key from environment
        tavily_api_key = os.getenv("TAVILY_API_KEY")

        if not tavily_api_key:
            return {
                "results": [],
                "error": "TAVILY_API_KEY not found in environment. Please add it to your .env file.",
                "message": "Web search disabled: API key missing"
            }

        try:
            from tavily import TavilyClient

            # Initialize Tavily client
            client = TavilyClient(api_key=tavily_api_key)

            # Perform search
            search_params = {
                "query": query,
                "max_results": max_results,
                "search_depth": search_depth,
            }

            # Add domain filtering if specified
            if include_domains:
                search_params["include_domains"] = include_domains

            logger.info(f"Performing web search with Tavily: {query}")
            response = client.search(**search_params)

            # Extract and format results
            results = []
            citations = []

            for item in response.get("results", []):
                result_obj = {
                    "title": item.get("title", "Untitled"),
                    "content": item.get("content", ""),
                    "url": item.get("url", ""),
                    "score": item.get("score", 0.0),
                    "published_date": item.get("published_date", ""),
                    "source_type": "web_search"  # Mark as web search
                }
                results.append(result_obj)

                # Create citation
                citations.append({
                    "title": item.get("title", "Untitled"),
                    "url": item.get("url", ""),
                    "published_date": item.get("published_date", "")
                })

            return {
                "results": results,
                "count": len(results),
                "source_api": "tavily",
                "citations": citations,
                "search_metadata": {
                    "query": query,
                    "searched_at": datetime.now().isoformat(),
                    "search_depth": search_depth,
                    "max_results": max_results
                },
                "message": f"Found {len(results)} results from web search"
            }

        except ImportError:
            logger.error("Tavily package not installed")
            return {
                "results": [],
                "error": "tavily-python package not installed. Run: pip install tavily-python"
            }

        except Exception as e:
            logger.error(f"Error performing web search: {e}", exc_info=True)
            return {
                "results": [],
                "count": 0,
                "error": str(e),
                "message": "Web search failed"
            }

    async def _execute_analyze_content_coverage(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute analyze-content-coverage tool using ResearchPlanner."""
        from .research_planner import ResearchPlanner

        query = args.get("query", "")
        user_id = args.get("user_id", "00000000-0000-0000-0000-000000000001")
        user_context = args.get("user_context")

        if not query:
            return {"error": "Query cannot be empty"}

        try:
            # Initialize research planner
            planner = ResearchPlanner(
                supabase_url=self.supabase_url,
                supabase_key=self.supabase_key,
                openai_api_key=self.openai_api_key,
                min_db_results_threshold=3
            )

            # Analyze content coverage
            analysis = await planner.analyze_content_coverage(
                query=query,
                user_id=user_id,
                user_context=user_context
            )

            # Convert dataclass to dict
            return {
                "db_results_count": analysis.db_results_count,
                "topics_covered": analysis.topics_covered,
                "coverage_gaps": [
                    {
                        "topic": gap.topic,
                        "reason": gap.reason,
                        "priority": gap.priority,
                        "suggested_query": gap.suggested_query
                    }
                    for gap in analysis.coverage_gaps
                ],
                "existing_sources": analysis.existing_sources,
                "needs_web_search": analysis.needs_web_search,
                "confidence_score": analysis.confidence_score,
                "message": f"Analyzed coverage: {analysis.db_results_count} DB results, "
                           f"{len(analysis.coverage_gaps)} gaps identified"
            }

        except Exception as e:
            logger.error(f"Error analyzing content coverage: {e}", exc_info=True)
            return {
                "error": str(e),
                "db_results_count": 0,
                "needs_web_search": True
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
