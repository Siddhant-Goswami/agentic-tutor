"""
RAG (Retrieval-Augmented Generation) Module

Modular RAG system for personalized learning digest generation.

Includes:
- Core: Base classes and LLM client
- Synthesis: Insight synthesis and prompt building
- Evaluation: Quality evaluation with RAGAS metrics
- Retrieval: Vector search and query building
- Digest: Complete digest generation pipeline
"""

# Core components
from src.rag.core.llm_client import LLMClient, LLMProvider
from src.rag.core.base_synthesizer import BaseSynthesizer
from src.rag.core.base_evaluator import BaseEvaluator
from src.rag.core.base_retriever import BaseRetriever

# Synthesis
from src.rag.synthesis.synthesizer import EducationalSynthesizer
from src.rag.synthesis.prompt_builder import PromptBuilder
from src.rag.synthesis.parsers import InsightParser

# Evaluation
from src.rag.evaluation.evaluator import InsightEvaluator
from src.rag.evaluation.metrics import RAGASMetrics, QualityBadge

# Retrieval
from src.rag.retrieval.retriever import VectorRetriever
from src.rag.retrieval.query_builder import QueryBuilder
from src.rag.retrieval.insight_search import InsightSearch

# Digest generation
from src.rag.digest import DigestGenerator, QualityGate

# Backward compatibility
from src.rag.compat import (
    LegacySynthesizerAdapter,
    LegacyEvaluatorAdapter,
    create_synthesizer,
    create_evaluator,
)

__all__ = [
    # Core
    "LLMClient",
    "LLMProvider",
    "BaseSynthesizer",
    "BaseEvaluator",
    "BaseRetriever",
    # Synthesis
    "EducationalSynthesizer",
    "PromptBuilder",
    "InsightParser",
    # Evaluation
    "InsightEvaluator",
    "RAGASMetrics",
    "QualityBadge",
    # Retrieval
    "VectorRetriever",
    "QueryBuilder",
    "InsightSearch",
    # Digest
    "DigestGenerator",
    "QualityGate",
    # Compat
    "LegacySynthesizerAdapter",
    "LegacyEvaluatorAdapter",
    "create_synthesizer",
    "create_evaluator",
]
