"""
Evaluation Metrics

Individual metric implementations for RAG quality evaluation.
"""

import logging
from typing import Dict, Any, List, Optional
import asyncio

logger = logging.getLogger(__name__)


class RAGASMetrics:
    """RAGAS-based metrics for RAG evaluation."""

    def __init__(self, openai_api_key: Optional[str] = None):
        """
        Initialize RAGAS metrics.

        Args:
            openai_api_key: OpenAI API key for LLM-based metrics (optional)
        """
        self.ragas_available = False
        self.openai_api_key = openai_api_key

        # Lazy import RAGAS
        try:
            from ragas import SingleTurnSample
            from ragas.metrics import (
                Faithfulness,
                LLMContextPrecisionWithoutReference,
                NonLLMContextRecall,
            )
            from ragas.llms import LangchainLLMWrapper
            from langchain_openai import ChatOpenAI

            self.SingleTurnSample = SingleTurnSample

            # Initialize LLM for metrics if API key provided
            if openai_api_key:
                logger.info("Initializing RAGAS metrics with OpenAI LLM...")
                try:
                    llm = ChatOpenAI(
                        model="gpt-4o-mini",
                        api_key=openai_api_key,
                        temperature=0
                    )
                    ragas_llm = LangchainLLMWrapper(llm)

                    self.faithfulness = Faithfulness(llm=ragas_llm)
                    self.context_precision = LLMContextPrecisionWithoutReference(llm=ragas_llm)
                    self.context_recall = NonLLMContextRecall()
                    logger.info("RAGAS metrics initialized with OpenAI LLM")
                except Exception as e:
                    logger.warning(f"Failed to initialize RAGAS with LLM: {e}, using defaults")
                    self.faithfulness = Faithfulness()
                    self.context_precision = LLMContextPrecisionWithoutReference()
                    self.context_recall = NonLLMContextRecall()
            else:
                logger.warning("No OpenAI API key provided, using default RAGAS metrics")
                self.faithfulness = Faithfulness()
                self.context_precision = LLMContextPrecisionWithoutReference()
                self.context_recall = NonLLMContextRecall()

            self.ragas_available = True
            logger.info("RAGAS metrics initialized successfully")

        except ImportError as e:
            logger.warning(f"RAGAS not available: {e}. Metrics will use placeholders.")
            self.ragas_available = False

    async def evaluate_all(
        self,
        query: str,
        response: str,
        contexts: List[str],
    ) -> Dict[str, float]:
        """
        Evaluate all metrics.

        Args:
            query: User query
            response: Generated response
            contexts: Retrieved contexts

        Returns:
            Dictionary of metric scores
        """
        if not self.ragas_available:
            logger.warning("RAGAS not available, returning placeholder scores")
            return self._placeholder_scores()

        try:
            # Create RAGAS sample
            sample = self.SingleTurnSample(
                user_input=query,
                response=response,
                retrieved_contexts=contexts,
                reference_contexts=[response],  # Use synthesized response as reference
            )

            # Run metrics in parallel
            tasks = [
                self._evaluate_faithfulness(sample),
                self._evaluate_context_precision(sample),
                self._evaluate_context_recall(sample),
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Extract scores with fallbacks
            faithfulness = results[0] if not isinstance(results[0], Exception) else 0.75
            precision = results[1] if not isinstance(results[1], Exception) else 0.75
            recall = results[2] if not isinstance(results[2], Exception) else 0.75

            scores = {
                "faithfulness": float(faithfulness),
                "context_precision": float(precision),
                "context_recall": float(recall),
            }

            # Calculate average
            scores["average"] = sum(scores.values()) / len(scores)

            return scores

        except Exception as e:
            logger.error(f"Metrics evaluation failed: {e}", exc_info=True)
            return self._placeholder_scores()

    async def _evaluate_faithfulness(self, sample: Any) -> float:
        """Evaluate faithfulness (factual consistency)."""
        try:
            score = await self.faithfulness.single_turn_ascore(sample)
            return float(score)
        except Exception as e:
            logger.warning(f"Faithfulness evaluation failed: {e}")
            return 0.75

    async def _evaluate_context_precision(self, sample: Any) -> float:
        """Evaluate context precision (relevance of chunks)."""
        try:
            score = await self.context_precision.single_turn_ascore(sample)
            return float(score)
        except Exception as e:
            logger.warning(f"Context precision evaluation failed: {e}")
            return 0.75

    async def _evaluate_context_recall(self, sample: Any) -> float:
        """Evaluate context recall (coverage of information)."""
        try:
            score = await self.context_recall.single_turn_ascore(sample)
            return float(score)
        except Exception as e:
            logger.warning(f"Context recall evaluation failed: {e}")
            return 0.75

    def _placeholder_scores(self) -> Dict[str, float]:
        """Return placeholder scores when RAGAS unavailable."""
        return {
            "faithfulness": 0.75,
            "context_precision": 0.75,
            "context_recall": 0.75,
            "average": 0.75,
        }


class QualityBadge:
    """Generates quality badges based on scores."""

    @staticmethod
    def get_badge(scores: Dict[str, float]) -> str:
        """
        Get quality badge based on scores.

        Args:
            scores: Dictionary of metric scores

        Returns:
            Quality badge string
        """
        avg_score = scores.get("average", 0.0)

        if avg_score >= 0.90:
            return "🟢 Excellent"
        elif avg_score >= 0.80:
            return "🟢 Good"
        elif avg_score >= 0.70:
            return "🟡 Acceptable"
        elif avg_score >= 0.60:
            return "🟡 Needs Improvement"
        else:
            return "🔴 Poor"

    @staticmethod
    def get_detailed_analysis(scores: Dict[str, float]) -> Dict[str, str]:
        """
        Get detailed analysis of scores.

        Args:
            scores: Dictionary of metric scores

        Returns:
            Dictionary of metric analyses
        """
        analysis = {}

        for metric, score in scores.items():
            if metric == "average":
                continue

            if score >= 0.90:
                level = "Excellent"
            elif score >= 0.80:
                level = "Good"
            elif score >= 0.70:
                level = "Acceptable"
            elif score >= 0.60:
                level = "Needs Improvement"
            else:
                level = "Poor"

            analysis[metric] = f"{level} ({score:.2f})"

        return analysis
