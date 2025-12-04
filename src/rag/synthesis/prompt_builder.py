"""
Prompt Builder for Synthesis

Builds prompts from templates for synthesis operations.
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class PromptBuilder:
    """Builds prompts from templates for synthesis."""

    def __init__(self, templates_dir: Optional[Path] = None):
        """
        Initialize prompt builder.

        Args:
            templates_dir: Directory containing prompt templates
                          (defaults to templates/ in this module)
        """
        if templates_dir is None:
            templates_dir = Path(__file__).parent / "templates"

        self.templates_dir = templates_dir
        self._cache: Dict[str, str] = {}

        logger.info(f"PromptBuilder initialized with templates from: {templates_dir}")

    def build_synthesis_prompt(
        self,
        context_text: str,
        user_context: Dict[str, Any],
        query: str,
        num_insights: int = 7,
        stricter: bool = False,
    ) -> tuple[str, str]:
        """
        Build system and user prompts for synthesis.

        Args:
            context_text: Formatted context from retrieved chunks
            user_context: User's learning context (week, topics, difficulty, goals)
            query: Original search query
            num_insights: Number of insights to generate (default: 7)
            stricter: Whether to use stricter mode (default: False)

        Returns:
            Tuple of (system_prompt, user_prompt)
        """
        # Build system prompt
        system_prompt = self._load_template("synthesis_system")

        if stricter:
            strict_addition = self._load_template("synthesis_system_strict")
            system_prompt += strict_addition

        # Build user prompt
        user_template = self._load_template("synthesis_user")

        # Extract user context with defaults
        current_week = user_context.get("current_week") or user_context.get("week", "N/A")
        topics = user_context.get("current_topics") or user_context.get("topics", [])
        difficulty = user_context.get("difficulty_level") or user_context.get("difficulty", "intermediate")
        goal = user_context.get("learning_goals") or user_context.get("goal", "General AI/ML learning")

        # Format topics
        topics_str = ", ".join(topics) if topics else "AI and Machine Learning"

        # Format user prompt
        user_prompt = user_template.format(
            current_week=current_week,
            topics=topics_str,
            difficulty=difficulty,
            goal=goal,
            query=query,
            context_text=context_text,
            num_insights=num_insights,
        )

        return system_prompt, user_prompt

    def build_context_text(self, chunks: List[Dict[str, Any]]) -> str:
        """
        Format retrieved chunks into context text.

        Args:
            chunks: Retrieved chunks with metadata

        Returns:
            Formatted context string
        """
        context_parts = []

        for i, chunk in enumerate(chunks, 1):
            # Extract chunk metadata with fallbacks
            title = chunk.get('content_title') or chunk.get('source_title', 'Untitled')
            author = chunk.get('content_author') or chunk.get('source_author', 'Unknown')
            url = chunk.get('content_url') or chunk.get('source_url', 'N/A')
            published = chunk.get('published_at') or chunk.get('created_at', 'N/A')
            similarity = chunk.get('similarity') or chunk.get('similarity_score', 0)
            content = chunk.get('chunk_text') or chunk.get('content', '')

            # Format chunk as numbered source
            source_block = f"""## Source {i}: {title}

**Author**: {author}
**URL**: {url}
**Published**: {published}
**Relevance Score**: {similarity:.3f}

### Content:
{content}

---
"""
            context_parts.append(source_block)

        return "\n".join(context_parts)

    def _load_template(self, template_name: str) -> str:
        """
        Load a template file, with caching.

        Args:
            template_name: Name of template (without .txt extension)

        Returns:
            Template content as string

        Raises:
            FileNotFoundError: If template file doesn't exist
        """
        # Check cache first
        if template_name in self._cache:
            return self._cache[template_name]

        # Load from file
        template_path = self.templates_dir / f"{template_name}.txt"

        if not template_path.exists():
            raise FileNotFoundError(f"Template not found: {template_path}")

        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Cache for future use
        self._cache[template_name] = content

        logger.debug(f"Loaded template: {template_name}")

        return content

    def clear_cache(self):
        """Clear the template cache."""
        self._cache.clear()
        logger.debug("Template cache cleared")
