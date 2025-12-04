"""
Tests for Prompt Builder
"""

import pytest
from pathlib import Path
from src.rag.synthesis.prompt_builder import PromptBuilder


class TestPromptBuilder:
    """Test cases for PromptBuilder."""

    def test_init_default_templates_dir(self):
        """Test initialization with default templates directory."""
        builder = PromptBuilder()

        expected_dir = Path(__file__).parent.parent.parent.parent.parent / "src" / "rag" / "synthesis" / "templates"
        assert builder.templates_dir == expected_dir
        assert builder._cache == {}

    def test_init_custom_templates_dir(self):
        """Test initialization with custom templates directory."""
        custom_dir = Path("/custom/path")
        builder = PromptBuilder(templates_dir=custom_dir)

        assert builder.templates_dir == custom_dir

    def test_build_context_text(self):
        """Test building context text from chunks."""
        builder = PromptBuilder()

        chunks = [
            {
                "content_title": "Test Article 1",
                "content_author": "John Doe",
                "content_url": "https://example.com/1",
                "published_at": "2024-01-01",
                "similarity": 0.95,
                "chunk_text": "This is test content 1",
            },
            {
                "source_title": "Test Article 2",  # Different field names
                "source_author": "Jane Smith",
                "source_url": "https://example.com/2",
                "created_at": "2024-01-02",
                "similarity_score": 0.85,
                "content": "This is test content 2",
            },
        ]

        context = builder.build_context_text(chunks)

        # Check that both chunks are included
        assert "Test Article 1" in context
        assert "Test Article 2" in context
        assert "John Doe" in context
        assert "Jane Smith" in context
        assert "This is test content 1" in context
        assert "This is test content 2" in context
        assert "0.950" in context  # Similarity score formatted
        assert "0.850" in context

    def test_build_context_text_empty_chunks(self):
        """Test building context text with empty chunks list."""
        builder = PromptBuilder()

        context = builder.build_context_text([])

        assert context == ""

    def test_build_synthesis_prompt(self):
        """Test building synthesis prompts."""
        builder = PromptBuilder()

        user_context = {
            "current_week": 5,
            "current_topics": ["Machine Learning", "Neural Networks"],
            "difficulty_level": "intermediate",
            "learning_goals": "Understand deep learning basics",
        }

        system_prompt, user_prompt = builder.build_synthesis_prompt(
            context_text="Test context",
            user_context=user_context,
            query="Explain backpropagation",
            num_insights=3,
            stricter=False,
        )

        # Check system prompt contains key phrases
        assert "first-principles thinking" in system_prompt.lower()
        assert "feynman" in system_prompt.lower()

        # Check user prompt contains context
        assert "Test context" in user_prompt
        assert "Explain backpropagation" in user_prompt
        assert "5" in user_prompt  # Week
        assert "Machine Learning, Neural Networks" in user_prompt
        assert "intermediate" in user_prompt
        assert "3" in user_prompt  # num_insights

    def test_build_synthesis_prompt_strict_mode(self):
        """Test building synthesis prompts with strict mode."""
        builder = PromptBuilder()

        user_context = {
            "week": 3,
            "topics": ["Python"],
            "difficulty": "beginner",
            "goal": "Learn Python basics",
        }

        system_prompt, user_prompt = builder.build_synthesis_prompt(
            context_text="Context",
            user_context=user_context,
            query="Query",
            stricter=True,
        )

        # Check strict mode additions
        assert "STRICT MODE" in system_prompt
        assert "precise and accurate" in system_prompt.lower()

    def test_build_synthesis_prompt_handles_alternative_fields(self):
        """Test prompt building handles alternative field names in user context."""
        builder = PromptBuilder()

        # Use alternative field names
        user_context = {
            "week": 7,
            "topics": ["AI"],
            "difficulty": "advanced",
            "goal": "Master AI",
        }

        system_prompt, user_prompt = builder.build_synthesis_prompt(
            context_text="Context",
            user_context=user_context,
            query="Query",
        )

        assert "7" in user_prompt
        assert "AI" in user_prompt
        assert "advanced" in user_prompt
        assert "Master AI" in user_prompt

    def test_template_caching(self):
        """Test that templates are cached after first load."""
        builder = PromptBuilder()

        # Load template twice
        template1 = builder._load_template("synthesis_system")
        template2 = builder._load_template("synthesis_system")

        # Should be the same object from cache
        assert template1 is template2
        assert "synthesis_system" in builder._cache

    def test_clear_cache(self):
        """Test clearing template cache."""
        builder = PromptBuilder()

        # Load template to populate cache
        builder._load_template("synthesis_system")
        assert len(builder._cache) > 0

        # Clear cache
        builder.clear_cache()
        assert len(builder._cache) == 0

    def test_load_template_not_found(self):
        """Test loading non-existent template raises error."""
        builder = PromptBuilder()

        with pytest.raises(FileNotFoundError):
            builder._load_template("nonexistent_template")

    def test_build_context_text_missing_fields(self):
        """Test building context text with chunks missing some fields."""
        builder = PromptBuilder()

        chunks = [
            {
                "content_title": "Title Only",
                # Missing other fields
            }
        ]

        context = builder.build_context_text(chunks)

        # Should handle missing fields gracefully
        assert "Title Only" in context
        assert "Unknown" in context  # Default author
        assert "N/A" in context  # Default URL/date
