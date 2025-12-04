"""
Base Retriever Protocol

Defines the interface for all content retrievers in the RAG system.
"""

from typing import Protocol, List, Dict, Any
from abc import abstractmethod


class BaseRetriever(Protocol):
    """Protocol for content retrievers that fetch relevant chunks."""

    @abstractmethod
    async def retrieve(
        self,
        query: str,
        user_id: str,
        top_k: int = 15,
        similarity_threshold: float = 0.40,
        **kwargs,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant content chunks.

        Args:
            query: Search query text
            user_id: User ID for filtering sources
            top_k: Number of top results to return (default: 15)
            similarity_threshold: Minimum similarity score (default: 0.40)
            **kwargs: Additional retriever-specific parameters

        Returns:
            List of chunk dictionaries with content and metadata
            Format: [
                {
                    "content": str,
                    "chunk_index": int,
                    "source_title": str,
                    "source_url": str,
                    "similarity_score": float,
                    "created_at": str,
                    ...
                }
            ]
        """
        ...

    @abstractmethod
    async def generate_embedding(
        self,
        text: str,
    ) -> List[float]:
        """
        Generate embedding vector for text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector as list of floats
        """
        ...

    @abstractmethod
    def validate_chunks(
        self,
        chunks: List[Dict[str, Any]],
    ) -> bool:
        """
        Validate retrieved chunks have required fields.

        Args:
            chunks: Chunks to validate

        Returns:
            True if chunks are valid, False otherwise
        """
        ...
