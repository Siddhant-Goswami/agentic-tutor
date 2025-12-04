"""
Insight Evaluator - Refactored

Evaluates quality of synthesized insights using RAGAS metrics.
"""

import logging
from typing import Dict, Any, List, Optional

from src.rag.evaluation.metrics import RAGASMetrics, QualityBadge

logger = logging.getLogger(__name__)


class InsightEvaluator:
    """
    Evaluates quality of synthesized insights.

    This is a refactored version that uses:
    - RAGASMetrics for metric evaluation
    - QualityBadge for badge generation
    """

    def __init__(
        self,
        metrics: Optional[RAGASMetrics] = None,
        min_score: float = 0.70,
    ):
        """
        Initialize evaluator.

        Args:
            metrics: RAGAS metrics instance (creates default if not provided)
            min_score: Minimum acceptable score (default: 0.70)
        """
        self.metrics = metrics or RAGASMetrics()
        self.min_score = min_score

        logger.info(f"InsightEvaluator initialized with min_score={min_score}")

    async def evaluate_digest(
        self,
        query: str,
        insights: List[Dict[str, Any]],
        retrieved_chunks: List[Dict[str, Any]],
    ) -> Dict[str, float]:
        """
        Evaluate digest quality using RAGAS metrics.

        Args:
            query: Original search query
            insights: Generated insights
            retrieved_chunks: Retrieved content chunks

        Returns:
            Dictionary with RAGAS scores
        """
        logger.info("Evaluating digest with RAGAS")

        # Validate inputs
        if not insights:
            logger.warning("No insights to evaluate")
            return {
                "faithfulness": 0.0,
                "context_precision": 0.0,
                "context_recall": 0.0,
                "average": 0.0,
                "error": "No insights provided",
            }

        if not retrieved_chunks:
            logger.warning("No contexts to evaluate against")
            return {
                "faithfulness": 0.0,
                "context_precision": 0.0,
                "context_recall": 0.0,
                "average": 0.0,
                "error": "No contexts provided",
            }

        try:
            # Format insights for evaluation
            response = self._format_insights(insights)

            # Extract contexts
            contexts = self._extract_contexts(retrieved_chunks)

            # Evaluate using metrics
            scores = await self.metrics.evaluate_all(
                query=query,
                response=response,
                contexts=contexts,
            )

            logger.info(
                f"RAGAS evaluation complete: "
                f"faithfulness={scores['faithfulness']:.3f}, "
                f"precision={scores['context_precision']:.3f}, "
                f"recall={scores['context_recall']:.3f}, "
                f"avg={scores['average']:.3f}"
            )

            return scores

        except Exception as e:
            logger.error(f"Evaluation failed: {e}", exc_info=True)
            return {
                "faithfulness": 0.0,
                "context_precision": 0.0,
                "context_recall": 0.0,
                "average": 0.0,
                "error": str(e),
            }

    def passes_quality_gate(
        self,
        scores: Dict[str, float],
        min_score: Optional[float] = None,
    ) -> bool:
        """
        Check if quality scores meet minimum threshold.

        Args:
            scores: Dictionary of quality scores
            min_score: Minimum acceptable score (uses instance default if not provided)

        Returns:
            True if quality gate passed, False otherwise
        """
        threshold = min_score if min_score is not None else self.min_score
        required_metrics = ["faithfulness", "context_precision", "context_recall"]

        for metric in required_metrics:
            score = scores.get(metric, 0.0)
            if score < threshold:
                logger.info(
                    f"Failed quality gate: {metric}={score:.3f} < {threshold:.3f}"
                )
                return False

        logger.info("✓ Quality gate passed")
        return True

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
        return QualityBadge.get_badge(scores)

    def get_detailed_analysis(
        self,
        scores: Dict[str, float],
    ) -> Dict[str, str]:
        """
        Get detailed analysis of each metric.

        Args:
            scores: Dictionary of quality scores

        Returns:
            Dictionary of metric analyses
        """
        return QualityBadge.get_detailed_analysis(scores)

    def _format_insights(self, insights: List[Dict[str, Any]]) -> str:
        """
        Format insights into single text for evaluation.

        Args:
            insights: List of insight dictionaries

        Returns:
            Concatenated insight text
        """
        texts = []
        for insight in insights:
            title = insight.get("title", "")
            explanation = insight.get("explanation", "")
            texts.append(f"{title}\n\n{explanation}")

        return "\n\n---\n\n".join(texts)

    def _extract_contexts(self, chunks: List[Dict[str, Any]]) -> List[str]:
        """
        Extract context texts from chunks.

        Args:
            chunks: Retrieved chunks

        Returns:
            List of context strings
        """
        contexts = []
        for chunk in chunks:
            # Try different field names
            text = (
                chunk.get("chunk_text") or
                chunk.get("content") or
                chunk.get("text") or
                ""
            )
            if text:
                contexts.append(text)

        return contexts

    def get_config(self) -> Dict[str, Any]:
        """
        Get current evaluator configuration.

        Returns:
            Configuration dictionary
        """
        return {
            "min_score": self.min_score,
            "ragas_available": self.metrics.ragas_available,
        }
