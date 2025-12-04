"""
Backward Compatibility Layer

Provides backward-compatible wrappers for refactored RAG components.
This allows existing code to continue working while gradually migrating to the new architecture.
"""

import logging
from typing import List, Dict, Any, Optional

from src.rag.core.llm_client import LLMClient, LLMProvider
from src.rag.synthesis.synthesizer import EducationalSynthesizer
from src.rag.synthesis.prompt_builder import PromptBuilder
from src.rag.synthesis.parsers import InsightParser
from src.rag.evaluation.evaluator import InsightEvaluator
from src.rag.evaluation.metrics import RAGASMetrics

logger = logging.getLogger(__name__)


class LegacySynthesizerAdapter:
    """
    Backward-compatible adapter for EducationalSynthesizer.

    Provides the old API while using the new modular implementation internally.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o",
        use_openai: bool = True,
    ):
        """
        Initialize synthesizer with legacy API.

        Args:
            api_key: OpenAI or Anthropic API key
            model: Model to use
            use_openai: Whether to use OpenAI (True) or Anthropic (False)
        """
        # Map to new architecture
        provider = LLMProvider.OPENAI if use_openai else LLMProvider.ANTHROPIC

        # Create new components
        llm_client = LLMClient(
            provider=provider,
            model=model,
            api_key=api_key,
        )

        prompt_builder = PromptBuilder()
        parser = InsightParser()

        # Create new synthesizer
        self.synthesizer = EducationalSynthesizer(
            llm_client=llm_client,
            prompt_builder=prompt_builder,
            parser=parser,
        )

        logger.info("LegacySynthesizerAdapter initialized (using new architecture)")

    async def synthesize_insights(
        self,
        retrieved_chunks: List[Dict[str, Any]],
        learning_context: Dict[str, Any],
        query: str,
        num_insights: int = 7,
        stricter: bool = False,
    ) -> Dict[str, Any]:
        """
        Synthesize insights using legacy API.

        Delegates to new synthesizer implementation.
        """
        return await self.synthesizer.synthesize_insights(
            retrieved_chunks=retrieved_chunks,
            learning_context=learning_context,
            query=query,
            num_insights=num_insights,
            stricter=stricter,
        )


class LegacyEvaluatorAdapter:
    """
    Backward-compatible adapter for RAGASEvaluator.

    Provides the old API while using the new modular implementation internally.
    """

    def __init__(
        self,
        min_score: float = 0.70,
        openai_api_key: Optional[str] = None,
    ):
        """
        Initialize evaluator with legacy API.

        Args:
            min_score: Minimum acceptable score
            openai_api_key: OpenAI API key for LLM-based metrics
        """
        # Create new components
        metrics = RAGASMetrics(openai_api_key=openai_api_key)

        # Create new evaluator
        self.evaluator = InsightEvaluator(
            metrics=metrics,
            min_score=min_score,
        )

        logger.info("LegacyEvaluatorAdapter initialized (using new architecture)")

    async def evaluate_digest(
        self,
        query: str,
        insights: List[Dict[str, Any]],
        retrieved_chunks: List[Dict[str, Any]],
    ) -> Dict[str, float]:
        """
        Evaluate digest using legacy API.

        Delegates to new evaluator implementation.
        """
        return await self.evaluator.evaluate_digest(
            query=query,
            insights=insights,
            retrieved_chunks=retrieved_chunks,
        )

    def passes_quality_gate(self, scores: Dict[str, float]) -> bool:
        """Check if scores pass quality gate."""
        return self.evaluator.passes_quality_gate(scores)


def create_synthesizer(
    api_key: str,
    model: str = "gpt-4o",
    use_openai: bool = True,
) -> EducationalSynthesizer:
    """
    Factory function to create synthesizer with new architecture.

    Args:
        api_key: API key
        model: Model name
        use_openai: Whether to use OpenAI

    Returns:
        Configured EducationalSynthesizer
    """
    provider = LLMProvider.OPENAI if use_openai else LLMProvider.ANTHROPIC

    llm_client = LLMClient(
        provider=provider,
        model=model,
        api_key=api_key,
    )

    return EducationalSynthesizer(
        llm_client=llm_client,
        prompt_builder=PromptBuilder(),
        parser=InsightParser(),
    )


def create_evaluator(
    min_score: float = 0.70,
    openai_api_key: Optional[str] = None,
) -> InsightEvaluator:
    """
    Factory function to create evaluator with new architecture.

    Args:
        min_score: Minimum acceptable score
        openai_api_key: OpenAI API key

    Returns:
        Configured InsightEvaluator
    """
    metrics = RAGASMetrics(openai_api_key=openai_api_key)

    return InsightEvaluator(
        metrics=metrics,
        min_score=min_score,
    )
