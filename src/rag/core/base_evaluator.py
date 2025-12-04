"""
Base Evaluator Protocol

Defines the interface for all quality evaluators in the RAG system.
"""

from typing import Protocol, List, Dict, Any
from abc import abstractmethod


class BaseEvaluator(Protocol):
    """Protocol for quality evaluators that assess generated insights."""

    @abstractmethod
    async def evaluate_digest(
        self,
        query: str,
        insights: List[Dict[str, Any]],
        retrieved_chunks: List[Dict[str, Any]],
    ) -> Dict[str, float]:
        """
        Evaluate digest quality using various metrics.

        Args:
            query: Original search query
            insights: Generated insights to evaluate
            retrieved_chunks: Source chunks used for generation

        Returns:
            Dictionary with quality scores
            Format: {
                "faithfulness": float (0.0-1.0),
                "context_precision": float (0.0-1.0),
                "context_recall": float (0.0-1.0),
                "overall": float (0.0-1.0),
                ...
            }
        """
        ...

    @abstractmethod
    def passes_quality_gate(
        self,
        scores: Dict[str, float],
        min_score: float = 0.70,
    ) -> bool:
        """
        Check if quality scores meet minimum threshold.

        Args:
            scores: Dictionary of quality scores
            min_score: Minimum acceptable score (default: 0.70)

        Returns:
            True if quality gate passed, False otherwise
        """
        ...

    @abstractmethod
    def get_quality_badge(
        self,
        scores: Dict[str, float],
    ) -> str:
        """
        Get quality badge based on scores.

        Args:
            scores: Dictionary of quality scores

        Returns:
            Quality badge string (e.g., "🟢 Excellent", "🟡 Good", "🔴 Needs Review")
        """
        ...
