"""
Educational Synthesizer - Refactored

Synthesizes personalized learning insights from retrieved content using modular architecture.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from src.rag.core.llm_client import LLMClient
from src.rag.synthesis.prompt_builder import PromptBuilder
from src.rag.synthesis.parsers import InsightParser

logger = logging.getLogger(__name__)


class EducationalSynthesizer:
    """
    Synthesizes educational insights using modular architecture.

    This is a refactored version that uses:
    - LLMClient for unified LLM access
    - PromptBuilder for template-based prompts
    - InsightParser for response parsing
    """

    def __init__(
        self,
        llm_client: LLMClient,
        prompt_builder: Optional[PromptBuilder] = None,
        parser: Optional[InsightParser] = None,
        temperature: float = 0.3,
        max_tokens: int = 8000,
    ):
        """
        Initialize synthesizer with injected dependencies.

        Args:
            llm_client: Unified LLM client (OpenAI or Anthropic)
            prompt_builder: Prompt builder (creates default if not provided)
            parser: Insight parser (creates default if not provided)
            temperature: LLM temperature (default: 0.3 for consistency)
            max_tokens: Maximum tokens for generation (default: 8000)
        """
        self.llm_client = llm_client
        self.prompt_builder = prompt_builder or PromptBuilder()
        self.parser = parser or InsightParser()
        self.temperature = temperature
        self.max_tokens = max_tokens

        logger.info(
            f"EducationalSynthesizer initialized with {llm_client.get_model_info()['model']}"
        )

    async def synthesize_insights(
        self,
        retrieved_chunks: List[Dict[str, Any]],
        learning_context: Dict[str, Any],
        query: str,
        num_insights: int = 7,
        stricter: bool = False,
    ) -> Dict[str, Any]:
        """
        Synthesize personalized learning insights from retrieved content.

        Args:
            retrieved_chunks: Chunks retrieved from vector search
            learning_context: User's learning context (week, topics, level, goals)
            query: Original search query
            num_insights: Number of insights to generate (default: 7)
            stricter: Use stricter prompt for higher quality (default: False)

        Returns:
            Dictionary with insights array and metadata
            Format: {
                "insights": [list of insight dicts],
                "metadata": {metadata dict}
            }
        """
        logger.info(
            f"Synthesizing {num_insights} insights from {len(retrieved_chunks)} chunks"
        )

        # Validate inputs
        if not self.validate_input(retrieved_chunks, learning_context, query):
            return {
                "insights": [],
                "metadata": {"error": "Invalid inputs"}
            }

        try:
            # Build context from chunks
            context_text = self.prompt_builder.build_context_text(retrieved_chunks)

            # Build prompts using templates
            system_prompt, user_prompt = self.prompt_builder.build_synthesis_prompt(
                context_text=context_text,
                user_context=learning_context,
                query=query,
                num_insights=num_insights,
                stricter=stricter,
            )

            # Generate insights using LLM
            response_text = await self.llm_client.generate(
                system=system_prompt,
                user=user_prompt,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )

            # Parse and validate insights
            insights = self.parser.parse_insights(response_text)

            # Enrich with source references
            insights = self._enrich_insights(insights, retrieved_chunks)

            logger.info(f"Successfully synthesized {len(insights)} insights")

            return {
                "insights": insights,
                "metadata": {
                    "num_chunks_used": len(retrieved_chunks),
                    "model": self.llm_client.model,
                    "temperature": self.temperature,
                    "generated_at": datetime.now().isoformat(),
                    "query": query,
                    "num_insights_requested": num_insights,
                    "num_insights_generated": len(insights),
                },
            }

        except Exception as e:
            logger.error(f"Error synthesizing insights: {e}", exc_info=True)
            return {
                "insights": [],
                "metadata": {
                    "error": str(e),
                    "generated_at": datetime.now().isoformat(),
                },
            }

    def _enrich_insights(
        self,
        insights: List[Dict[str, Any]],
        retrieved_chunks: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Enrich insights with source references.

        Args:
            insights: Parsed insights
            retrieved_chunks: Original chunks

        Returns:
            Enriched insights
        """
        # Create a source map for quick lookup
        source_map = {}
        for chunk in retrieved_chunks:
            title = chunk.get('content_title') or chunk.get('source_title', '')
            if title and title not in source_map:
                source_map[title] = {
                    'title': title,
                    'author': chunk.get('content_author') or chunk.get('source_author', 'Unknown'),
                    'url': chunk.get('content_url') or chunk.get('source_url', ''),
                    'published_date': chunk.get('published_at') or chunk.get('created_at', ''),
                }

        # Enrich insights
        for insight in insights:
            # If source info is incomplete, try to fill from source map
            source = insight.get('source', {})
            source_title = source.get('title', '')

            if source_title and source_title in source_map:
                # Update with complete info
                insight['source'] = source_map[source_title]
            elif source_map:
                # Use first available source as fallback
                insight['source'] = next(iter(source_map.values()))

        return insights

    def validate_input(
        self,
        retrieved_chunks: List[Dict[str, Any]],
        learning_context: Dict[str, Any],
        query: str,
    ) -> bool:
        """
        Validate synthesis inputs.

        Args:
            retrieved_chunks: Chunks to validate
            learning_context: Learning context to validate
            query: Query to validate

        Returns:
            True if inputs are valid, False otherwise
        """
        if not retrieved_chunks:
            logger.error("Validation failed: No chunks provided")
            return False

        if not query or not isinstance(query, str):
            logger.error("Validation failed: Invalid query")
            return False

        if not learning_context or not isinstance(learning_context, dict):
            logger.error("Validation failed: Invalid learning context")
            return False

        return True

    def get_config(self) -> Dict[str, Any]:
        """
        Get current synthesizer configuration.

        Returns:
            Configuration dictionary
        """
        return {
            "model_info": self.llm_client.get_model_info(),
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
