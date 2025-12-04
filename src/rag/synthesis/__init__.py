"""
Synthesis Module

Content synthesis components for the RAG system.
"""

from src.rag.synthesis.prompt_builder import PromptBuilder
from src.rag.synthesis.parsers import InsightParser
from src.rag.synthesis.synthesizer import EducationalSynthesizer

__all__ = [
    "PromptBuilder",
    "InsightParser",
    "EducationalSynthesizer",
]
