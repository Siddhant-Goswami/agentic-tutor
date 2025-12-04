"""
Base Synthesizer Protocol

Defines the interface for all content synthesizers in the RAG system.
"""

from typing import Protocol, List, Dict, Any
from abc import abstractmethod


class BaseSynthesizer(Protocol):
    """Protocol for content synthesizers that generate insights from retrieved content."""

    @abstractmethod
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
                "insights": [
                    {
                        "title": str,
                        "explanation": str,
                        "practical_application": str,
                        "source_references": List[str],
                        ...
                    }
                ],
                "metadata": {
                    "num_insights": int,
                    "model_used": str,
                    ...
                }
            }
        """
        ...

    @abstractmethod
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
        ...
