"""
Edge case tests for Insight Evaluator.

Tests for edge cases like empty insights, empty contexts, etc.
"""

import pytest
from src.rag.evaluation.evaluator import InsightEvaluator


class TestInsightEvaluatorEdgeCases:
    """Test edge cases in insight evaluator."""

    @pytest.mark.asyncio
    async def test_evaluate_digest_empty_insights(self):
        """Test evaluation with empty insights list."""
        evaluator = InsightEvaluator(min_score=0.70)

        result = await evaluator.evaluate_digest(
            query="test query",
            insights=[],  # Empty insights
            retrieved_chunks=[{"chunk_text": "test"}],
        )

        # Should return error scores
        assert result["faithfulness"] == 0.0
        assert result["context_precision"] == 0.0
        assert result["context_recall"] == 0.0
        assert result["average"] == 0.0
        assert result["error"] == "No insights provided"

    @pytest.mark.asyncio
    async def test_evaluate_digest_empty_contexts(self):
        """Test evaluation with empty retrieved chunks."""
        evaluator = InsightEvaluator(min_score=0.70)

        result = await evaluator.evaluate_digest(
            query="test query",
            insights=[{"title": "Test", "explanation": "Test explanation"}],
            retrieved_chunks=[],  # Empty chunks
        )

        # Should return error scores
        assert result["faithfulness"] == 0.0
        assert result["context_precision"] == 0.0
        assert result["context_recall"] == 0.0
        assert result["average"] == 0.0
        assert result["error"] == "No contexts provided"

    @pytest.mark.asyncio
    async def test_evaluate_digest_both_empty(self):
        """Test evaluation with both empty insights and contexts."""
        evaluator = InsightEvaluator(min_score=0.70)

        result = await evaluator.evaluate_digest(
            query="test query",
            insights=[],
            retrieved_chunks=[],
        )

        # Should return error for insights (checked first)
        assert result["error"] == "No insights provided"

    def test_passes_quality_gate_empty_insights(self):
        """Test quality gate with empty insights scores."""
        evaluator = InsightEvaluator(min_score=0.70)

        scores = {
            "faithfulness": 0.0,
            "context_precision": 0.0,
            "context_recall": 0.0,
            "average": 0.0,
            "error": "No insights provided",
        }

        # Should fail quality gate
        assert not evaluator.passes_quality_gate(scores)

    def test_get_quality_badge_zero_scores(self):
        """Test quality badge for zero scores."""
        evaluator = InsightEvaluator(min_score=0.70)

        scores = {
            "faithfulness": 0.0,
            "context_precision": 0.0,
            "context_recall": 0.0,
            "average": 0.0,
        }

        badge = evaluator.get_quality_badge(scores)
        assert badge == "🔴 Poor"

    def test_format_insights_empty(self):
        """Test formatting empty insights list."""
        evaluator = InsightEvaluator(min_score=0.70)

        result = evaluator._format_insights([])
        assert result == ""

    def test_extract_contexts_empty(self):
        """Test extracting contexts from empty chunks."""
        evaluator = InsightEvaluator(min_score=0.70)

        result = evaluator._extract_contexts([])
        assert result == []

    def test_extract_contexts_missing_fields(self):
        """Test extracting contexts when chunks have no text fields."""
        evaluator = InsightEvaluator(min_score=0.70)

        chunks = [
            {"title": "test"},  # No text fields
            {"metadata": "test"},  # No text fields
        ]

        result = evaluator._extract_contexts(chunks)
        assert result == []
