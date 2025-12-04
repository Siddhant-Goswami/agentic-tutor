"""
Edge case tests for Educational Synthesizer.

Tests for edge cases like invalid inputs, all insights filtered, etc.
"""

import pytest
from unittest.mock import Mock, AsyncMock
from src.rag.synthesis.synthesizer import EducationalSynthesizer


class TestEducationalSynthesizerEdgeCases:
    """Test edge cases in educational synthesizer."""

    @pytest.mark.asyncio
    async def test_synthesize_insights_empty_chunks(self):
        """Test synthesis with empty chunks list."""
        # Create mock LLM client (won't be called)
        mock_llm = Mock()
        mock_llm.get_model_info.return_value = {"model": "test-model"}

        synthesizer = EducationalSynthesizer(llm_client=mock_llm)

        result = await synthesizer.synthesize_insights(
            retrieved_chunks=[],  # Empty
            learning_context={"week": 1},
            query="test query",
        )

        # Should return error
        assert result["insights"] == []
        assert "error" in result["metadata"]
        assert result["metadata"]["error"] == "Invalid inputs"

    @pytest.mark.asyncio
    async def test_synthesize_insights_invalid_query(self):
        """Test synthesis with invalid query."""
        mock_llm = Mock()
        mock_llm.get_model_info.return_value = {"model": "test-model"}
        synthesizer = EducationalSynthesizer(llm_client=mock_llm)

        result = await synthesizer.synthesize_insights(
            retrieved_chunks=[{"chunk_text": "test"}],
            learning_context={"week": 1},
            query="",  # Empty query
        )

        # Should return error
        assert result["insights"] == []
        assert "error" in result["metadata"]

    @pytest.mark.asyncio
    async def test_synthesize_insights_invalid_context(self):
        """Test synthesis with invalid learning context."""
        mock_llm = Mock()
        mock_llm.get_model_info.return_value = {"model": "test-model"}
        synthesizer = EducationalSynthesizer(llm_client=mock_llm)

        result = await synthesizer.synthesize_insights(
            retrieved_chunks=[{"chunk_text": "test"}],
            learning_context=None,  # Invalid
            query="test query",
        )

        # Should return error
        assert result["insights"] == []
        assert "error" in result["metadata"]

    @pytest.mark.asyncio
    async def test_synthesize_insights_llm_error(self):
        """Test synthesis when LLM raises error."""
        # Mock LLM that raises error
        mock_llm = Mock()
        mock_llm.generate = AsyncMock(side_effect=Exception("LLM API error"))
        mock_llm.model = "gpt-4o"
        mock_llm.get_model_info.return_value = {"model": "gpt-4o"}

        synthesizer = EducationalSynthesizer(llm_client=mock_llm)

        result = await synthesizer.synthesize_insights(
            retrieved_chunks=[{"chunk_text": "test content"}],
            learning_context={"week": 1, "topics": ["test"]},
            query="test query",
        )

        # Should return error gracefully
        assert result["insights"] == []
        assert "error" in result["metadata"]
        assert "LLM API error" in result["metadata"]["error"]

    @pytest.mark.asyncio
    async def test_synthesize_insights_parse_error(self):
        """Test synthesis when parser fails."""
        # Mock LLM that returns unparseable response
        mock_llm = Mock()
        mock_llm.generate = AsyncMock(return_value="Not JSON at all!")
        mock_llm.model = "gpt-4o"
        mock_llm.get_model_info.return_value = {"model": "gpt-4o"}

        synthesizer = EducationalSynthesizer(llm_client=mock_llm)

        result = await synthesizer.synthesize_insights(
            retrieved_chunks=[{"chunk_text": "test content"}],
            learning_context={"week": 1, "topics": ["test"]},
            query="test query",
        )

        # Should return error gracefully
        assert result["insights"] == []
        assert "error" in result["metadata"]

    def test_validate_input_valid(self):
        """Test validate_input with valid inputs."""
        mock_llm = Mock()
        mock_llm.get_model_info.return_value = {"model": "test-model"}
        synthesizer = EducationalSynthesizer(llm_client=mock_llm)

        result = synthesizer.validate_input(
            retrieved_chunks=[{"chunk_text": "test"}],
            learning_context={"week": 1},
            query="test query",
        )

        assert result is True

    def test_validate_input_empty_chunks(self):
        """Test validate_input with empty chunks."""
        mock_llm = Mock()
        mock_llm.get_model_info.return_value = {"model": "test-model"}
        synthesizer = EducationalSynthesizer(llm_client=mock_llm)

        result = synthesizer.validate_input(
            retrieved_chunks=[],
            learning_context={"week": 1},
            query="test query",
        )

        assert result is False

    def test_validate_input_invalid_query(self):
        """Test validate_input with invalid query."""
        mock_llm = Mock()
        mock_llm.get_model_info.return_value = {"model": "test-model"}
        synthesizer = EducationalSynthesizer(llm_client=mock_llm)

        result = synthesizer.validate_input(
            retrieved_chunks=[{"chunk_text": "test"}],
            learning_context={"week": 1},
            query="",  # Empty
        )

        assert result is False

    def test_validate_input_none_query(self):
        """Test validate_input with None query."""
        mock_llm = Mock()
        mock_llm.get_model_info.return_value = {"model": "test-model"}
        synthesizer = EducationalSynthesizer(llm_client=mock_llm)

        result = synthesizer.validate_input(
            retrieved_chunks=[{"chunk_text": "test"}],
            learning_context={"week": 1},
            query=None,  # None
        )

        assert result is False

    def test_validate_input_invalid_context(self):
        """Test validate_input with invalid context."""
        mock_llm = Mock()
        mock_llm.get_model_info.return_value = {"model": "test-model"}
        synthesizer = EducationalSynthesizer(llm_client=mock_llm)

        result = synthesizer.validate_input(
            retrieved_chunks=[{"chunk_text": "test"}],
            learning_context=None,  # Invalid
            query="test query",
        )

        assert result is False

    def test_validate_input_non_dict_context(self):
        """Test validate_input with non-dict context."""
        mock_llm = Mock()
        mock_llm.get_model_info.return_value = {"model": "test-model"}
        synthesizer = EducationalSynthesizer(llm_client=mock_llm)

        result = synthesizer.validate_input(
            retrieved_chunks=[{"chunk_text": "test"}],
            learning_context="not a dict",  # Wrong type
            query="test query",
        )

        assert result is False
