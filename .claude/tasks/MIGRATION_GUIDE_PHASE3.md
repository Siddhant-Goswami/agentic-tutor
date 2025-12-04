# Phase 3 RAG Refactoring - Migration Guide

**Version:** 1.0
**Date:** 2025-12-03
**Status:** Complete

---

## Overview

This guide helps you migrate from the old monolithic RAG system to the new modular architecture introduced in Phase 3.

**Key Benefits:**
- 🎯 Modular, testable components
- 📝 Template-based prompt management
- 🔄 Easy LLM provider switching
- ✅ Comprehensive test coverage
- 🚀 Better performance with caching

---

## Quick Start

### Option 1: Use Backward Compatibility Layer (Easiest)

If you have existing code using the old API, use the compatibility layer:

```python
# Old code (still works!)
from learning_coach_mcp.src.rag.synthesizer import EducationalSynthesizer
from learning_coach_mcp.src.rag.evaluator import RAGASEvaluator

# New code (drop-in replacement)
from src.rag.compat import LegacySynthesizerAdapter as EducationalSynthesizer
from src.rag.compat import LegacyEvaluatorAdapter as RAGASEvaluator

# Everything else stays the same!
synthesizer = EducationalSynthesizer(api_key=key, model="gpt-4o", use_openai=True)
result = await synthesizer.synthesize_insights(chunks, context, query)
```

### Option 2: Use New Architecture (Recommended)

For new code or when refactoring, use the new modular components:

```python
from src.rag.core.llm_client import LLMClient, LLMProvider
from src.rag.synthesis import EducationalSynthesizer, PromptBuilder, InsightParser

# Create components
llm_client = LLMClient(
    provider=LLMProvider.OPENAI,
    model="gpt-4o",
    api_key=api_key,
)

synthesizer = EducationalSynthesizer(
    llm_client=llm_client,
    prompt_builder=PromptBuilder(),
    parser=InsightParser(),
)

# Use it
result = await synthesizer.synthesize_insights(
    retrieved_chunks=chunks,
    learning_context=context,
    query=query,
    num_insights=7,
)
```

### Option 3: Use Factory Functions (Simplest New API)

Use convenience factory functions:

```python
from src.rag.compat import create_synthesizer, create_evaluator

# Create synthesizer
synthesizer = create_synthesizer(
    api_key=api_key,
    model="gpt-4o",
    use_openai=True,
)

# Create evaluator
evaluator = create_evaluator(
    min_score=0.70,
    openai_api_key=api_key,
)
```

---

## Component Migration

### 1. Synthesizer

#### Old API
```python
from learning_coach_mcp.src.rag.synthesizer import EducationalSynthesizer

synthesizer = EducationalSynthesizer(
    api_key="sk-...",
    model="gpt-4o",
    use_openai=True,
)

result = await synthesizer.synthesize_insights(
    retrieved_chunks=chunks,
    learning_context=context,
    query=query,
    num_insights=7,
    stricter=False,
)
```

#### New API
```python
from src.rag.core.llm_client import LLMClient, LLMProvider
from src.rag.synthesis import EducationalSynthesizer

# Create LLM client (reusable!)
llm_client = LLMClient(
    provider=LLMProvider.OPENAI,
    model="gpt-4o",
    api_key="sk-...",
)

# Create synthesizer (dependency injection)
synthesizer = EducationalSynthesizer(llm_client=llm_client)

# Use it (same API)
result = await synthesizer.synthesize_insights(
    retrieved_chunks=chunks,
    learning_context=context,
    query=query,
    num_insights=7,
    stricter=False,
)
```

#### Benefits
- ✅ LLM client can be shared across components
- ✅ Easy to mock for testing
- ✅ Simple to swap providers
- ✅ Prompts in template files (easy to modify)

---

### 2. Evaluator

#### Old API
```python
from learning_coach_mcp.src.rag.evaluator import RAGASEvaluator

evaluator = RAGASEvaluator(
    min_score=0.70,
    openai_api_key="sk-...",
)

scores = await evaluator.evaluate_digest(
    query=query,
    insights=insights,
    retrieved_chunks=chunks,
)

passed = evaluator.passes_quality_gate(scores)
```

#### New API
```python
from src.rag.evaluation import InsightEvaluator, RAGASMetrics

# Create metrics (reusable!)
metrics = RAGASMetrics(openai_api_key="sk-...")

# Create evaluator
evaluator = InsightEvaluator(
    metrics=metrics,
    min_score=0.70,
)

# Use it (same API)
scores = await evaluator.evaluate_digest(
    query=query,
    insights=insights,
    retrieved_chunks=chunks,
)

passed = evaluator.passes_quality_gate(scores)

# NEW: Get quality badge
badge = evaluator.get_quality_badge(scores)  # "🟢 Excellent"
```

#### Benefits
- ✅ Metrics module is reusable
- ✅ Easy to add custom metrics
- ✅ Quality badges and detailed analysis
- ✅ Better testability

---

### 3. Retriever (No Changes Needed)

The retriever was already well-structured, so it just moved locations:

#### Import Update
```python
# Old
from learning_coach_mcp.src.rag.retriever import VectorRetriever
from learning_coach_mcp.src.rag.query_builder import QueryBuilder

# New
from src.rag.retrieval import VectorRetriever, QueryBuilder

# API stays exactly the same!
retriever = VectorRetriever(supabase_url, supabase_key, openai_key)
chunks = await retriever.retrieve(query, user_id)
```

---

## Prompt Template Management

### Old Way (Prompts in Code)
Prompts were embedded in Python code. To modify them, you had to:
1. Edit Python files
2. Understand the code
3. Risk breaking functionality
4. Redeploy the application

### New Way (Template Files)

Prompts are in separate `.txt` files:

```
src/rag/synthesis/templates/
├── synthesis_system.txt       # Base system prompt
├── synthesis_system_strict.txt # Strict mode additions
└── synthesis_user.txt          # User prompt template
```

**To modify prompts:**
1. Edit the `.txt` file
2. No code changes needed
3. Changes take effect immediately (cached templates)
4. Version control tracks changes

**Example: Editing System Prompt**

```bash
# Edit the system prompt
vim src/rag/synthesis/templates/synthesis_system.txt

# That's it! Next synthesis will use the new prompt
```

---

## Switching LLM Providers

### Old Way
```python
# OpenAI
synthesizer_openai = EducationalSynthesizer(
    api_key=openai_key,
    model="gpt-4o",
    use_openai=True,  # Flag to switch
)

# Anthropic
synthesizer_anthropic = EducationalSynthesizer(
    api_key=anthropic_key,
    model="claude-sonnet-4-5-20250929",
    use_openai=False,  # Different flag
)
```

### New Way
```python
from src.rag.core.llm_client import LLMClient, LLMProvider

# OpenAI
llm_openai = LLMClient(
    provider=LLMProvider.OPENAI,  # Enum for type safety
    model="gpt-4o",
    api_key=openai_key,
)

# Anthropic
llm_anthropic = LLMClient(
    provider=LLMProvider.ANTHROPIC,
    model="claude-sonnet-4-5-20250929",
    api_key=anthropic_key,
)

# Both have the same API!
synthesizer_openai = EducationalSynthesizer(llm_client=llm_openai)
synthesizer_anthropic = EducationalSynthesizer(llm_client=llm_anthropic)
```

**Benefits:**
- Type-safe provider selection
- Same API for both providers
- Easy A/B testing
- Unified error handling

---

## Testing

### Old Way (Hard to Test)
```python
# Hard to test because synthesizer directly calls OpenAI
async def test_synthesis():
    synthesizer = EducationalSynthesizer(api_key="real_key")
    # This actually calls OpenAI API!
    result = await synthesizer.synthesize_insights(...)
```

### New Way (Easy to Test)
```python
from unittest.mock import Mock, AsyncMock
from src.rag.synthesis import EducationalSynthesizer

async def test_synthesis():
    # Mock the LLM client
    mock_llm = Mock()
    mock_llm.generate = AsyncMock(return_value='{"insights": [...]}')

    # Inject mock
    synthesizer = EducationalSynthesizer(llm_client=mock_llm)

    # Test without calling actual API
    result = await synthesizer.synthesize_insights(...)

    # Verify behavior
    mock_llm.generate.assert_called_once()
```

**Benefits:**
- Fast tests (no API calls)
- Predictable results
- Easy to test edge cases
- No API costs during testing

---

## Advanced Usage

### Custom Prompt Templates

Create your own prompt templates:

```python
from pathlib import Path
from src.rag.synthesis import PromptBuilder

# Use custom templates directory
custom_templates = Path("/path/to/custom/templates")
prompt_builder = PromptBuilder(templates_dir=custom_templates)

# Use in synthesizer
synthesizer = EducationalSynthesizer(
    llm_client=llm_client,
    prompt_builder=prompt_builder,  # Custom templates!
)
```

### Custom Metrics

Add your own evaluation metrics:

```python
from src.rag.evaluation.metrics import RAGASMetrics

class CustomMetrics(RAGASMetrics):
    async def evaluate_custom_metric(self, ...):
        # Your custom metric logic
        return score

# Use custom metrics
metrics = CustomMetrics(openai_api_key=key)
evaluator = InsightEvaluator(metrics=metrics)
```

### Configuration

Configure components:

```python
# Synthesizer with custom settings
synthesizer = EducationalSynthesizer(
    llm_client=llm_client,
    temperature=0.5,  # Custom temperature
    max_tokens=4000,  # Custom max tokens
)

# Get current config
config = synthesizer.get_config()
print(config)  # {"model_info": {...}, "temperature": 0.5, ...}
```

---

## Troubleshooting

### Issue: Import Errors

**Problem:**
```python
ImportError: cannot import name 'EducationalSynthesizer' from 'src.rag.synthesis'
```

**Solution:**
Make sure `src/` is in your Python path:
```python
import sys
sys.path.insert(0, '/path/to/project')
```

Or use relative imports if within the project.

---

### Issue: Template Not Found

**Problem:**
```python
FileNotFoundError: Template not found: synthesis_system.txt
```

**Solution:**
Check template directory path:
```python
from pathlib import Path
templates_dir = Path(__file__).parent / "templates"
print(templates_dir.exists())  # Should be True
```

---

### Issue: Tests Failing

**Problem:**
Tests that worked before are now failing.

**Solution:**
1. Update imports to new modules
2. Use factory functions or compat layer
3. Check that old components still exist in `learning-coach-mcp/src/rag/`

---

## Migration Checklist

### Phase 1: Preparation
- [ ] Read this migration guide
- [ ] Review new architecture in `src/rag/`
- [ ] Identify files using old RAG components
- [ ] Create branch for migration

### Phase 2: Gradual Migration
- [ ] Use compat layer for existing code
- [ ] Write new code using new components
- [ ] Update tests to use new architecture
- [ ] Test thoroughly

### Phase 3: Complete Migration
- [ ] Replace all old imports with new ones
- [ ] Remove compatibility layer usage
- [ ] Update documentation
- [ ] Deploy and monitor

---

## FAQ

**Q: Do I have to migrate immediately?**
A: No! The old code still works. Use the compatibility layer for a smooth transition.

**Q: What if I find a bug in the new code?**
A: The old code in `learning-coach-mcp/src/rag/` is unchanged and still works. You can fall back to it anytime.

**Q: Can I use both old and new components together?**
A: Yes! They're compatible. You can migrate incrementally.

**Q: How do I modify prompts now?**
A: Edit the `.txt` files in `src/rag/synthesis/templates/`. No code changes needed!

**Q: Will this break existing functionality?**
A: No! The refactor maintains backward compatibility. Old code continues to work.

**Q: Are there performance improvements?**
A: Yes! Template caching and better architecture improve performance.

---

## Support

**Documentation:**
- Phase 3 Plan: `.claude/tasks/PHASE3_RAG_REFACTORING_PLAN.md`
- Progress Report: `.claude/tasks/PHASE3_PROGRESS.md`
- Final Summary: `.claude/tasks/PHASE3_FINAL_SUMMARY.md`

**Examples:**
- Factory functions: `src/rag/compat.py`
- Tests: `tests/unit/rag/`

---

**Happy Migrating!** 🚀

The new architecture provides significant benefits while maintaining full backward compatibility. Take your time migrating, and enjoy the improved code quality and maintainability!
