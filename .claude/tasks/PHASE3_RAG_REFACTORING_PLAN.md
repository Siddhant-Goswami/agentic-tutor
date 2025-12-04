# Phase 3: RAG System Refactoring - Implementation Plan

**Date Created:** 2025-12-03
**Status:** 📋 PLANNED
**Priority:** HIGH
**Estimated Effort:** 2-3 days

---

## Overview

Refactor the RAG (Retrieval-Augmented Generation) system from monolithic files into a modular, testable architecture following Python best practices established in Phase 1 & 2.

---

## Current State Analysis

### Existing Files (2,218 lines total)

Located in: `learning-coach-mcp/src/rag/`

| File | Lines | Size | Status | Priority |
|------|-------|------|--------|----------|
| `synthesizer.py` | 468 | 15KB | Needs refactoring | HIGH |
| `digest_generator.py` | 417 | 14KB | Needs refactoring | HIGH |
| `evaluator.py` | 408 | 14KB | Needs refactoring | HIGH |
| `retriever.py` | 365 | 11KB | Needs refactoring | MEDIUM |
| `query_builder.py` | 324 | 9.6KB | Needs refactoring | MEDIUM |
| `insight_search.py` | 233 | 7.3KB | Needs refactoring | LOW |

### Key Issues to Address

1. **Prompts Embedded in Code** - Hard to modify and test
2. **Mixed Responsibilities** - Synthesis, evaluation, retrieval all tightly coupled
3. **LLM Client Duplication** - OpenAI/Anthropic clients created multiple times
4. **Limited Testability** - Hard to mock LLM calls
5. **Configuration Scattered** - RAG config spread across files
6. **No Separation of Concerns** - Template building, LLM calls, parsing all mixed

---

## Refactoring Strategy

### Phase 3 Architecture

```
src/rag/
├── __init__.py
│
├── core/                       # Core abstractions
│   ├── __init__.py
│   ├── base_synthesizer.py    # Abstract base for synthesizers
│   ├── base_evaluator.py      # Abstract base for evaluators
│   ├── base_retriever.py      # Abstract base for retrievers
│   └── llm_client.py           # Unified LLM client wrapper
│
├── synthesis/                  # Content synthesis
│   ├── __init__.py
│   ├── synthesizer.py          # Main synthesizer (refactored)
│   ├── prompt_builder.py       # Builds synthesis prompts
│   ├── templates/              # Prompt templates
│   │   ├── synthesis_system.txt
│   │   ├── synthesis_user.txt
│   │   └── synthesis_strict.txt
│   └── parsers.py              # Response parsing utilities
│
├── evaluation/                 # Quality evaluation
│   ├── __init__.py
│   ├── evaluator.py            # Main evaluator (refactored)
│   ├── ragas_evaluator.py      # RAGAS-based evaluation
│   ├── metrics.py              # Evaluation metrics
│   └── templates/              # Evaluation templates
│       ├── context_relevance.txt
│       ├── answer_correctness.txt
│       └── faithfulness.txt
│
├── retrieval/                  # Content retrieval
│   ├── __init__.py
│   ├── retriever.py            # Vector search retriever
│   ├── query_builder.py        # Query expansion & building
│   ├── insight_search.py       # Past insights search
│   └── reranker.py             # Result reranking (optional)
│
├── digest/                     # Digest generation
│   ├── __init__.py
│   ├── generator.py            # Main digest generator
│   ├── formatter.py            # Format digest output
│   └── templates/              # Digest templates
│       ├── daily_digest.txt
│       └── weekly_summary.txt
│
└── utils/                      # Shared utilities
    ├── __init__.py
    ├── embeddings.py           # Embedding generation
    ├── chunking.py             # Text chunking
    └── sanitization.py         # Input/output sanitization
```

---

## Implementation Tasks

### Task 1: Extract Core Abstractions

**Goal:** Create base classes and protocols for RAG components

**Files to Create:**
- `src/rag/core/base_synthesizer.py` (~150 lines)
- `src/rag/core/base_evaluator.py` (~100 lines)
- `src/rag/core/base_retriever.py` (~100 lines)
- `src/rag/core/llm_client.py` (~200 lines)

**Key Features:**
```python
# base_synthesizer.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from src.core.types import ToolResult

class BaseSynthesizer(ABC):
    """Abstract base for all synthesizers."""

    @abstractmethod
    async def synthesize(
        self,
        context: List[Dict[str, Any]],
        query: str,
        user_context: Dict[str, Any]
    ) -> ToolResult:
        """Synthesize insights from context."""
        pass

    @abstractmethod
    async def validate_input(
        self,
        context: List[Dict[str, Any]],
        query: str
    ) -> bool:
        """Validate synthesis inputs."""
        pass
```

**Benefits:**
- ✅ Consistent interface across synthesizers
- ✅ Easy to swap implementations
- ✅ Simplified testing with mocks

---

### Task 2: Extract Prompt Templates

**Goal:** Separate prompts from code for easier modification and versioning

**Files to Create:**
- `src/rag/synthesis/templates/synthesis_system.txt`
- `src/rag/synthesis/templates/synthesis_user.txt`
- `src/rag/synthesis/templates/synthesis_strict.txt`
- `src/rag/evaluation/templates/context_relevance.txt`
- `src/rag/evaluation/templates/answer_correctness.txt`
- `src/rag/evaluation/templates/faithfulness.txt`
- `src/rag/digest/templates/daily_digest.txt`

**Example Template:**
```
# synthesis_system.txt
You are an educational content synthesizer specializing in personalized learning.

Your role:
- Transform technical content into clear, actionable insights
- Apply first-principles thinking and the Feynman technique
- Adapt explanations to the learner's level and preferences
- Focus on practical takeaways and real-world applications

Guidelines:
1. Break complex concepts into fundamental building blocks
2. Use analogies and examples appropriate for the learner's level
3. Connect new concepts to previously learned material
4. Highlight practical applications and use cases
5. Include actionable next steps

Quality standards:
- Every insight must be grounded in provided source material
- Explanations must be technically accurate
- Examples must be concrete and relevant
- Takeaways must be immediately actionable
```

**Prompt Builder:**
```python
# src/rag/synthesis/prompt_builder.py
from pathlib import Path
from typing import Dict, Any

class PromptBuilder:
    """Builds prompts from templates."""

    def __init__(self, templates_dir: Path = None):
        self.templates_dir = templates_dir or Path(__file__).parent / "templates"
        self._cache = {}

    def build_synthesis_prompt(
        self,
        context_text: str,
        user_context: Dict[str, Any],
        query: str,
        num_insights: int = 3
    ) -> tuple[str, str]:
        """Build system and user prompts for synthesis."""
        system = self._load_template("synthesis_system")
        user_template = self._load_template("synthesis_user")

        user = user_template.format(
            context=context_text,
            week=user_context.get("week", "unknown"),
            topics=", ".join(user_context.get("topics", [])),
            difficulty=user_context.get("difficulty", "intermediate"),
            query=query,
            num_insights=num_insights
        )

        return system, user
```

**Benefits:**
- ✅ Easy to modify prompts without code changes
- ✅ Version control for prompts
- ✅ A/B testing different prompt versions
- ✅ Non-engineers can update prompts

---

### Task 3: Refactor Synthesizer

**Goal:** Modularize synthesis logic, separate concerns

**Current:** `learning-coach-mcp/src/rag/synthesizer.py` (468 lines)

**New Structure:**
- `src/rag/synthesis/synthesizer.py` (~250 lines) - Main logic
- `src/rag/synthesis/prompt_builder.py` (~150 lines) - Prompt building
- `src/rag/synthesis/parsers.py` (~100 lines) - Response parsing

**Key Improvements:**
```python
# src/rag/synthesis/synthesizer.py
from src.rag.core.base_synthesizer import BaseSynthesizer
from src.rag.core.llm_client import LLMClient
from src.rag.synthesis.prompt_builder import PromptBuilder
from src.rag.synthesis.parsers import InsightParser

class ContentSynthesizer(BaseSynthesizer):
    """Synthesizes educational content from retrieval results."""

    def __init__(
        self,
        llm_client: LLMClient,
        prompt_builder: PromptBuilder,
        parser: InsightParser,
        config: Dict[str, Any] = None
    ):
        self.llm = llm_client
        self.prompt_builder = prompt_builder
        self.parser = parser
        self.config = config or {}

    async def synthesize(
        self,
        context: List[Dict[str, Any]],
        query: str,
        user_context: Dict[str, Any]
    ) -> ToolResult:
        """Synthesize insights from context."""
        # Validate input
        if not await self.validate_input(context, query):
            return self._error_result("Invalid input")

        # Build prompts
        system_prompt, user_prompt = self.prompt_builder.build_synthesis_prompt(
            context_text=self._format_context(context),
            user_context=user_context,
            query=query,
            num_insights=self.config.get("num_insights", 3)
        )

        # Call LLM
        response = await self.llm.generate(
            system=system_prompt,
            user=user_prompt,
            temperature=self.config.get("temperature", 0.7)
        )

        # Parse response
        insights = self.parser.parse_insights(response)

        return self._success_result({"insights": insights})
```

**Benefits:**
- ✅ Clear separation: prompts, LLM calls, parsing
- ✅ Easy to test each component independently
- ✅ Flexible to swap prompt strategies
- ✅ Reusable LLM client

---

### Task 4: Refactor Evaluator

**Goal:** Modularize evaluation logic, add metrics abstraction

**Current:** `learning-coach-mcp/src/rag/evaluator.py` (408 lines)

**New Structure:**
- `src/rag/evaluation/evaluator.py` (~200 lines) - Main evaluator
- `src/rag/evaluation/ragas_evaluator.py` (~150 lines) - RAGAS integration
- `src/rag/evaluation/metrics.py` (~100 lines) - Metric definitions

**Key Improvements:**
```python
# src/rag/evaluation/evaluator.py
from src.rag.core.base_evaluator import BaseEvaluator
from src.rag.evaluation.metrics import EvaluationMetrics

class InsightEvaluator(BaseEvaluator):
    """Evaluates quality of synthesized insights."""

    def __init__(self, llm_client: LLMClient, metrics: EvaluationMetrics):
        self.llm = llm_client
        self.metrics = metrics

    async def evaluate(
        self,
        insight: Dict[str, Any],
        context: List[Dict[str, Any]],
        query: str
    ) -> Dict[str, float]:
        """Evaluate insight quality."""
        scores = {}

        # Context relevance
        scores["context_relevance"] = await self.metrics.context_relevance(
            insight, context
        )

        # Answer correctness
        scores["answer_correctness"] = await self.metrics.answer_correctness(
            insight, query
        )

        # Faithfulness (groundedness)
        scores["faithfulness"] = await self.metrics.faithfulness(
            insight, context
        )

        # Overall score
        scores["overall"] = self._compute_overall(scores)

        return scores
```

---

### Task 5: Refactor Retrieval System

**Goal:** Separate query building, vector search, reranking

**Current Files:**
- `learning-coach-mcp/src/rag/retriever.py` (365 lines)
- `learning-coach-mcp/src/rag/query_builder.py` (324 lines)
- `learning-coach-mcp/src/rag/insight_search.py` (233 lines)

**New Structure:**
- `src/rag/retrieval/retriever.py` (~200 lines) - Main retriever
- `src/rag/retrieval/query_builder.py` (~250 lines) - Query expansion
- `src/rag/retrieval/insight_search.py` (~180 lines) - Past insights
- `src/rag/retrieval/reranker.py` (~100 lines) - Result reranking

---

### Task 6: Refactor Digest Generator

**Goal:** Separate generation logic from formatting

**Current:** `learning-coach-mcp/src/rag/digest_generator.py` (417 lines)

**New Structure:**
- `src/rag/digest/generator.py` (~250 lines) - Main generator
- `src/rag/digest/formatter.py` (~150 lines) - Output formatting

---

### Task 7: Create Unified LLM Client

**Goal:** Single abstraction for OpenAI/Anthropic calls

**File:** `src/rag/core/llm_client.py` (~200 lines)

**Key Features:**
```python
from typing import Optional, Dict, Any
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic

class LLMClient:
    """Unified LLM client for OpenAI and Anthropic."""

    def __init__(
        self,
        provider: str = "openai",
        model: str = "gpt-4o-mini",
        api_key: str = None,
        **kwargs
    ):
        self.provider = provider
        self.model = model

        if provider == "openai":
            self.client = AsyncOpenAI(api_key=api_key)
        elif provider == "anthropic":
            self.client = AsyncAnthropic(api_key=api_key)
        else:
            raise ValueError(f"Unknown provider: {provider}")

    async def generate(
        self,
        system: str,
        user: str,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ) -> str:
        """Generate completion from LLM."""
        if self.provider == "openai":
            return await self._generate_openai(system, user, temperature, max_tokens)
        else:
            return await self._generate_anthropic(system, user, temperature, max_tokens)
```

**Benefits:**
- ✅ Single point for LLM configuration
- ✅ Easy to swap providers
- ✅ Centralized error handling
- ✅ Simplified testing with mocks

---

### Task 8: Create Shared Utilities

**Goal:** Extract common utility functions

**Files to Create:**
- `src/rag/utils/embeddings.py` (~100 lines)
- `src/rag/utils/chunking.py` (~150 lines)
- `src/rag/utils/sanitization.py` (~100 lines)

---

### Task 9: Write Comprehensive Tests

**Goal:** Achieve >80% test coverage for RAG system

**Test Files to Create:**
```
tests/unit/rag/
├── __init__.py
├── core/
│   ├── test_llm_client.py          (~150 lines, 10 tests)
│   └── test_base_classes.py        (~100 lines, 8 tests)
├── synthesis/
│   ├── test_synthesizer.py         (~200 lines, 15 tests)
│   ├── test_prompt_builder.py      (~150 lines, 12 tests)
│   └── test_parsers.py              (~100 lines, 8 tests)
├── evaluation/
│   ├── test_evaluator.py            (~200 lines, 15 tests)
│   └── test_metrics.py              (~150 lines, 12 tests)
├── retrieval/
│   ├── test_retriever.py            (~150 lines, 10 tests)
│   └── test_query_builder.py       (~150 lines, 10 tests)
└── digest/
    └── test_generator.py            (~150 lines, 10 tests)
```

**Estimated Tests:** ~100 tests total

---

## Success Criteria

### Functional Requirements
- ✅ All existing RAG functionality preserved
- ✅ Backward compatibility maintained
- ✅ Prompts extracted to template files
- ✅ Base classes for extensibility
- ✅ Unified LLM client

### Quality Requirements
- ✅ >80% test coverage for RAG system
- ✅ All new tests passing
- ✅ Type hints throughout
- ✅ Clear separation of concerns
- ✅ Comprehensive documentation

### Performance Requirements
- ✅ No regression in synthesis/evaluation speed
- ✅ Template caching for performance
- ✅ Efficient LLM client pooling

---

## Migration Strategy

### Gradual Migration Approach

**Phase 3a: Core & Templates (Week 1)**
1. Create base classes
2. Extract prompt templates
3. Create unified LLM client
4. Write core tests

**Phase 3b: Synthesis & Evaluation (Week 1-2)**
1. Refactor synthesizer
2. Refactor evaluator
3. Update tests
4. Verify functionality

**Phase 3c: Retrieval & Digest (Week 2)**
1. Refactor retrieval components
2. Refactor digest generator
3. Complete test coverage
4. Documentation

**Phase 3d: Integration & Verification (Week 2-3)**
1. Update imports across codebase
2. Run integration tests
3. Performance benchmarking
4. Migration guide

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Breaking RAG functionality | HIGH | Comprehensive tests before/after |
| Prompt changes affect quality | MEDIUM | A/B testing, gradual rollout |
| LLM client abstraction limits features | MEDIUM | Extensible design, fallback to direct calls |
| Template file management complexity | LOW | Clear naming convention, documentation |

---

## Estimated Effort

| Task | Effort | Priority |
|------|--------|----------|
| Core abstractions | 4 hours | HIGH |
| Extract templates | 3 hours | HIGH |
| Refactor synthesizer | 6 hours | HIGH |
| Refactor evaluator | 5 hours | HIGH |
| Refactor retrieval | 5 hours | MEDIUM |
| Refactor digest | 4 hours | MEDIUM |
| Create tests | 8 hours | HIGH |
| Documentation | 3 hours | MEDIUM |
| Integration & verification | 4 hours | HIGH |
| **TOTAL** | **42 hours (~1-2 weeks)** | |

---

## Dependencies

### Requires from Previous Phases
- ✅ Phase 1: Core infrastructure (config, exceptions, types)
- ✅ Phase 2: Agent system (models, controllers)

### Blocks Future Phases
- Phase 4: UI templates need RAG refactoring complete
- Phase 5: Repository pattern for RAG data access

---

## Next Steps

1. **Review this plan** with team
2. **Approve approach** and priorities
3. **Create detailed tickets** for each task
4. **Start with Phase 3a** (Core & Templates)
5. **Iterate and adjust** based on findings

---

## Success Metrics

After Phase 3 completion:
- ✅ RAG system fully modularized
- ✅ 2,218 lines → ~20 focused modules
- ✅ 100+ comprehensive tests
- ✅ Template-based prompt management
- ✅ Unified LLM abstraction
- ✅ >80% test coverage
- ✅ Complete documentation

---

**Status:** 🚧 IN PROGRESS (Phase 3a Complete, Phase 3b In Progress)
**Last Updated:** 2025-12-03
**Next:** Complete Phase 3b (Synthesizer refactoring)
