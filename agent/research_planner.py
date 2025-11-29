"""
Research Planner

Analyzes existing database content coverage and creates intelligent research plans
for web search when gaps are identified.
"""

import logging
from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class ContentGap:
    """Represents a gap in content coverage."""

    topic: str
    reason: str
    priority: str  # "high", "medium", "low"
    suggested_query: str


@dataclass
class ContentAnalysis:
    """Results of analyzing database content coverage."""

    query: str
    db_results_count: int
    topics_covered: List[str]
    coverage_gaps: List[ContentGap]
    existing_sources: List[Dict[str, Any]]
    needs_web_search: bool
    confidence_score: float  # 0.0 to 1.0


@dataclass
class SearchQuery:
    """A proposed web search query."""

    query: str
    rationale: str
    expected_results: int
    priority: str  # "high", "medium", "low"
    include_domains: Optional[List[str]] = None


@dataclass
class ResearchPlan:
    """A structured research plan for web search."""

    user_query: str
    content_analysis: ContentAnalysis
    search_queries: List[SearchQuery]
    estimated_total_searches: int
    estimated_api_credits: int
    created_at: str
    rationale: str


class ResearchPlanner:
    """
    Analyzes content coverage and creates research plans.

    Determines when web search is needed and generates intelligent
    search queries to fill knowledge gaps.
    """

    def __init__(
        self,
        supabase_url: str,
        supabase_key: str,
        openai_api_key: str,
        min_db_results_threshold: int = 3,
    ):
        """
        Initialize research planner.

        Args:
            supabase_url: Supabase project URL
            supabase_key: Supabase API key
            openai_api_key: OpenAI API key for LLM analysis
            min_db_results_threshold: Minimum DB results before considering web search
        """
        self.supabase_url = supabase_url
        self.supabase_key = supabase_key
        self.openai_api_key = openai_api_key
        self.min_db_results_threshold = min_db_results_threshold

    async def analyze_content_coverage(
        self,
        query: str,
        user_id: str,
        user_context: Optional[Dict[str, Any]] = None
    ) -> ContentAnalysis:
        """
        Analyze existing database content for a query.

        Args:
            query: User's search query
            user_id: User UUID
            user_context: Optional user learning context

        Returns:
            ContentAnalysis with coverage assessment
        """
        from utils.db import get_supabase_client

        logger.info(f"Analyzing content coverage for query: {query}")

        db = get_supabase_client(self.supabase_url, self.supabase_key)

        try:
            # Use proper semantic search instead of simple ILIKE
            # This uses embeddings and is much better at finding relevant content
            from .tools import ToolRegistry

            tools = ToolRegistry(
                supabase_url=self.supabase_url,
                supabase_key=self.supabase_key,
                openai_api_key=self.openai_api_key
            )

            # Use the search-content tool for semantic search
            search_result = await tools.execute_tool(
                "search-content",
                {
                    "query": query,
                    "k": 20,
                    "user_id": user_id
                }
            )

            # Extract results
            db_results = search_result.get("results", []) if search_result else []
            db_results_count = len(db_results)

            logger.info(f"Found {db_results_count} results in database")

            # Extract topics from results
            topics_covered = self._extract_topics_from_results(db_results)

            # Identify coverage gaps using LLM
            coverage_gaps = await self._identify_coverage_gaps(
                query=query,
                db_results=db_results,
                user_context=user_context
            )

            # Determine if web search is needed
            needs_web_search = (
                db_results_count < self.min_db_results_threshold or
                len(coverage_gaps) > 0
            )

            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(
                db_results_count=db_results_count,
                coverage_gaps=coverage_gaps
            )

            # Format existing sources
            existing_sources = [
                {
                    "title": item.get("title", "Untitled"),
                    "url": item.get("url", ""),
                    "author": item.get("author", "Unknown"),
                    "published_at": item.get("published_at", "")
                }
                for item in db_results[:5]  # Top 5
            ]

            return ContentAnalysis(
                query=query,
                db_results_count=db_results_count,
                topics_covered=topics_covered,
                coverage_gaps=coverage_gaps,
                existing_sources=existing_sources,
                needs_web_search=needs_web_search,
                confidence_score=confidence_score
            )

        except Exception as e:
            logger.error(f"Error analyzing content coverage: {e}", exc_info=True)

            # Return minimal analysis on error
            return ContentAnalysis(
                query=query,
                db_results_count=0,
                topics_covered=[],
                coverage_gaps=[
                    ContentGap(
                        topic=query,
                        reason="Database query failed",
                        priority="high",
                        suggested_query=query
                    )
                ],
                existing_sources=[],
                needs_web_search=True,
                confidence_score=0.0
            )

    def _extract_topics_from_results(self, results: List[Dict[str, Any]]) -> List[str]:
        """Extract topics from database results."""
        topics = set()

        for result in results:
            # Extract from title (simple word extraction)
            title = result.get("title", "")
            words = title.lower().split()

            # Filter for meaningful words (simple heuristic)
            meaningful_words = [
                word for word in words
                if len(word) > 4 and word.isalpha()
            ]
            topics.update(meaningful_words[:3])  # Top 3 words per title

            # Extract from metadata tags if available
            metadata = result.get("metadata", {})
            if isinstance(metadata, dict) and "tags" in metadata:
                topics.update(metadata["tags"][:3])

        return list(topics)[:10]  # Top 10 topics

    async def _identify_coverage_gaps(
        self,
        query: str,
        db_results: List[Dict[str, Any]],
        user_context: Optional[Dict[str, Any]] = None
    ) -> List[ContentGap]:
        """
        Use LLM to identify coverage gaps.

        Args:
            query: User's query
            db_results: Results found in database
            user_context: User's learning context

        Returns:
            List of identified content gaps
        """
        from openai import AsyncOpenAI
        import json

        # If we have enough results, assume good coverage
        if len(db_results) >= 5:
            return []

        # If no results, obvious gap
        if len(db_results) == 0:
            return [
                ContentGap(
                    topic=query,
                    reason="No content found in database",
                    priority="high",
                    suggested_query=query
                )
            ]

        # Use LLM to analyze gaps
        client = AsyncOpenAI(api_key=self.openai_api_key)

        # Format database results for LLM
        db_summary = "\n".join([
            f"- {r.get('title', 'Untitled')} by {r.get('author', 'Unknown')}"
            for r in db_results[:5]
        ])

        user_level = "intermediate"
        if user_context:
            user_level = user_context.get("difficulty", "intermediate")

        gap_analysis_prompt = f"""
Analyze content coverage for a learning query.

User Query: "{query}"
User Level: {user_level}

Database Results Found ({len(db_results)}):
{db_summary}

Task: Identify what topics or aspects are MISSING or insufficiently covered.

Consider:
1. Key concepts related to the query
2. Practical examples or tutorials
3. Advanced/beginner content based on user level
4. Recent developments or updates

Return a JSON array of gaps (max 3):
[
  {{
    "topic": "specific missing topic",
    "reason": "why this is missing or insufficient",
    "priority": "high|medium|low",
    "suggested_query": "web search query to fill this gap"
  }}
]

If coverage is sufficient, return empty array: []
"""

        try:
            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at analyzing educational content coverage."
                    },
                    {"role": "user", "content": gap_analysis_prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )

            response_text = response.choices[0].message.content.strip()

            # Parse JSON response
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0]

            gaps_data = json.loads(response_text.strip())

            # Convert to ContentGap objects
            gaps = [
                ContentGap(
                    topic=gap["topic"],
                    reason=gap["reason"],
                    priority=gap["priority"],
                    suggested_query=gap["suggested_query"]
                )
                for gap in gaps_data
            ]

            logger.info(f"Identified {len(gaps)} content gaps")
            return gaps

        except Exception as e:
            logger.error(f"Error identifying coverage gaps with LLM: {e}")

            # Fallback: simple gap
            return [
                ContentGap(
                    topic=query,
                    reason="Limited database coverage",
                    priority="medium",
                    suggested_query=query
                )
            ]

    def _calculate_confidence_score(
        self,
        db_results_count: int,
        coverage_gaps: List[ContentGap]
    ) -> float:
        """
        Calculate confidence score for database coverage.

        Args:
            db_results_count: Number of results found
            coverage_gaps: Identified gaps

        Returns:
            Confidence score from 0.0 to 1.0
        """
        # Base score from result count
        if db_results_count >= 10:
            base_score = 1.0
        elif db_results_count >= 5:
            base_score = 0.8
        elif db_results_count >= 3:
            base_score = 0.6
        elif db_results_count >= 1:
            base_score = 0.4
        else:
            base_score = 0.0

        # Penalty for gaps
        gap_penalty = len(coverage_gaps) * 0.15

        # Final score
        score = max(0.0, base_score - gap_penalty)

        return round(score, 2)

    async def create_research_plan(
        self,
        content_analysis: ContentAnalysis,
        user_context: Optional[Dict[str, Any]] = None
    ) -> ResearchPlan:
        """
        Create a structured research plan based on content analysis.

        Args:
            content_analysis: Results from analyze_content_coverage
            user_context: User's learning context

        Returns:
            ResearchPlan with proposed searches
        """
        logger.info("Creating research plan")

        # Generate search queries from gaps
        search_queries = []

        for gap in content_analysis.coverage_gaps:
            # Enhance query based on user context
            enhanced_query = gap.suggested_query

            if user_context:
                level = user_context.get("difficulty", "intermediate")
                if "beginner" in level.lower():
                    enhanced_query = f"{gap.suggested_query} tutorial for beginners"
                elif "advanced" in level.lower():
                    enhanced_query = f"{gap.suggested_query} advanced guide"

            # Note: include_domains must be full domains like "wikipedia.org", not just "org"
            # For now, we don't filter by domain to avoid errors
            search_queries.append(
                SearchQuery(
                    query=enhanced_query,
                    rationale=gap.reason,
                    expected_results=5,
                    priority=gap.priority,
                    include_domains=None  # No domain filtering - Tavily requires full domains
                )
            )

        # If no specific gaps but still need more content, add general query
        if not search_queries and content_analysis.needs_web_search:
            enhanced_general_query = content_analysis.query
            if user_context:
                level = user_context.get("difficulty", "intermediate")
                if "beginner" in level.lower():
                    enhanced_general_query = f"{content_analysis.query} tutorial for beginners"
                elif "advanced" in level.lower():
                    enhanced_general_query = f"{content_analysis.query} advanced guide"

            search_queries.append(
                SearchQuery(
                    query=enhanced_general_query,
                    rationale="Insufficient database coverage",
                    expected_results=5,
                    priority="medium",
                    include_domains=None  # No domain filtering
                )
            )

        # Estimate API usage
        estimated_total_searches = len(search_queries)
        estimated_api_credits = estimated_total_searches  # 1 credit per basic search

        # Create rationale
        rationale = self._generate_plan_rationale(content_analysis, search_queries)

        return ResearchPlan(
            user_query=content_analysis.query,
            content_analysis=content_analysis,
            search_queries=search_queries,
            estimated_total_searches=estimated_total_searches,
            estimated_api_credits=estimated_api_credits,
            created_at=datetime.now().isoformat(),
            rationale=rationale
        )

    def _generate_plan_rationale(
        self,
        analysis: ContentAnalysis,
        queries: List[SearchQuery]
    ) -> str:
        """Generate human-readable rationale for the research plan."""

        parts = []

        # Database status
        if analysis.db_results_count == 0:
            parts.append("No relevant content found in your database.")
        elif analysis.db_results_count < self.min_db_results_threshold:
            parts.append(
                f"Only {analysis.db_results_count} results found in database "
                f"(threshold: {self.min_db_results_threshold})."
            )
        else:
            parts.append(
                f"Found {analysis.db_results_count} results in database, "
                f"but coverage gaps identified."
            )

        # Gaps
        if analysis.coverage_gaps:
            gap_topics = [gap.topic for gap in analysis.coverage_gaps[:3]]
            parts.append(
                f"Missing coverage on: {', '.join(gap_topics)}."
            )

        # Proposed action
        parts.append(
            f"Proposing {len(queries)} web search(es) to supplement database content."
        )

        return " ".join(parts)
