# Digest Generation - Complete Fix Plan

**Date:** 2025-11-29
**Status:** Planning Phase

## Executive Summary

Previous attempts fixed the agent workflow to call `generate-digest`, but the implementation still has critical issues:
1. **Wrong implementation called** - Using simplified `digest_api.py` instead of proper RAG pipeline
2. **Agent looping behavior** - Calls `generate-digest` 3 times then times out
3. **Query building too generic** - Doesn't adapt to specific learning questions
4. **No Q&A separation** - Learning questions need focused answers, not full daily digests

This plan addresses all issues comprehensively with architectural improvements.

---

## Root Cause Analysis

### Issue 1: Wrong Implementation (digest_api.py vs DigestGenerator)

**Current State:**
```python
# agent/tools.py:447
from digest_api import generate_digest_simple
result = await generate_digest_simple(...)
```

**What `digest_api.py` does:**
- Gets 10 most recent articles (NO semantic search!)
- Uses OpenAI GPT-4o-mini to generate generic insights
- Returns fake RAGAS scores (hardcoded to 0.80)
- **Not grounded in retrieved content**

**What it SHOULD do (DigestGenerator):**
1. **QueryBuilder** - Builds context-aware query from learning goals
2. **VectorRetriever** - Performs semantic search with embeddings
3. **EducationalSynthesizer** - Uses Claude with first-principles prompting
4. **RAGASEvaluator** - Validates quality with real scores
5. **QualityGate** - Can retry synthesis if scores too low

### Issue 2: Agent Looping

**Test output:**
```
Iteration 3: Call generate-digest
Iteration 4: Call generate-digest (AGAIN!)
Iteration 5: Call generate-digest (AGAIN!)
Status: timeout
```

**Root causes:**
1. `digest_api.py` likely returns empty insights or cached empty digest
2. Agent doesn't recognize this as success
3. Planning prompt says "retry if insights are empty"
4. No clear completion criteria

### Issue 3: Query Building is Generic

**Current query construction (query_builder.py:100-181):**
```
"I am in Week 7 of an AI bootcamp. I am learning about Model Context Protocol,
LLM Tool Calling. I have intermediate knowledge, so I need practical implementation
details. Find recent articles that explain these topics..."
```

**Problems:**
- Too verbose for semantic search
- Focused on "find articles" not "answer question"
- Doesn't use explicit user query effectively
- Generic structure doesn't leverage RAG

**What it should be for "Help me learn MCP":**
```
"What is Model Context Protocol and how do I use it?"
```

### Issue 4: No Separation Between Digest and Q&A

**Current behavior:**
- "Generate my daily digest" → Calls generate-digest ✓
- "Help me learn MCP" → Calls generate-digest ✗

**Should be:**
- "Generate my daily digest" → Full digest with 7 diverse insights
- "Help me learn MCP" → Focused answer with 2-3 targeted insights about MCP

---

## Proposed Solution

### Architecture Overview

```
User Query
    ↓
Goal Classification
    ↓
┌─────────────────────┬─────────────────────┐
│  Daily Digest Mode  │  Q&A Mode           │
├─────────────────────┼─────────────────────┤
│ - Full digest       │ - Focused answer    │
│ - 7 insights        │ - 2-3 insights      │
│ - Broad topics      │ - Specific topic    │
│ - Generic query     │ - Explicit query    │
└─────────────────────┴─────────────────────┘
    ↓                       ↓
DigestGenerator (Shared RAG Pipeline)
    ↓
VectorRetriever → EducationalSynthesizer → RAGASEvaluator
```

---

## Implementation Tasks

### Phase 1: Fix Tool Implementation (High Priority)

#### Task 1.1: Replace digest_api.py with DigestGenerator

**File:** `agent/tools.py`

**Current (lines 414-466):**
```python
from digest_api import generate_digest_simple
result = await generate_digest_simple(...)
```

**New implementation:**
```python
async def _execute_generate_digest(self, args: Dict[str, Any]) -> Dict[str, Any]:
    """Execute generate-digest using proper RAG pipeline."""
    import sys
    from pathlib import Path
    from datetime import datetime, date

    # Add MCP src to path
    mcp_src = Path(__file__).parent.parent / "learning-coach-mcp" / "src"
    if str(mcp_src) not in sys.path:
        sys.path.insert(0, str(mcp_src))

    from rag.digest_generator import DigestGenerator

    # Parse arguments
    date_str = args.get("date", "today")
    target_date = date.today() if date_str == "today" else datetime.fromisoformat(date_str).date()
    max_insights = args.get("max_insights", 7)
    force_refresh = args.get("force_refresh", True)  # Always force to avoid empty cache
    user_context = args.get("user_context", {})
    explicit_query = args.get("explicit_query")  # NEW: for Q&A mode

    # Get user_id from context
    user_id = user_context.get("user_id", "00000000-0000-0000-0000-000000000001")

    try:
        # Initialize proper DigestGenerator
        generator = DigestGenerator(
            supabase_url=self.supabase_url,
            supabase_key=self.supabase_key,
            openai_api_key=self.openai_api_key,
            anthropic_api_key=self.anthropic_api_key,
            ragas_min_score=0.70,
        )

        # Call actual RAG pipeline
        result = await generator.generate(
            user_id=user_id,
            date=target_date,
            max_insights=max_insights,
            force_refresh=force_refresh,
            explicit_query=explicit_query,  # Pass explicit query for Q&A mode
        )

        # Ensure proper format for agent
        if result.get("insights"):
            return {
                "success": True,
                "insights": result["insights"],
                "ragas_scores": result.get("ragas_scores", {}),
                "quality_badge": result.get("quality_badge", "✓"),
                "metadata": result.get("metadata", {}),
                "num_insights": len(result["insights"])
            }
        else:
            return {
                "success": False,
                "insights": [],
                "error": result.get("metadata", {}).get("error", "No insights generated"),
                "ragas_scores": {},
            }

    except Exception as e:
        logger.error(f"Error generating digest: {e}", exc_info=True)
        return {
            "success": False,
            "insights": [],
            "error": str(e),
            "ragas_scores": {},
        }
```

**Why this fixes the issue:**
- Uses proper RAG pipeline with semantic search
- Forces refresh to avoid empty cache
- Returns clear success/failure indicator
- Includes `explicit_query` parameter for Q&A mode

#### Task 1.2: Update Tool Schema

**File:** `agent/tools.py` (lines 121-154)

**Changes:**
```python
def _generate_digest_schema(self) -> Dict[str, Any]:
    """Schema for generate-digest tool."""
    return {
        "name": "generate-digest",
        "description": "Generate personalized learning digest using RAG pipeline. Retrieves relevant content via semantic search, synthesizes insights with Claude, and validates quality with RAGAS. Use for both daily digests and answering learning questions.",
        "input_schema": {
            "date": "string (ISO date or 'today', default: 'today')",
            "max_insights": "integer (2-10, default: 7 for digest, 3 for Q&A)",
            "force_refresh": "boolean (skip cache, default: true)",
            "user_context": "object (REQUIRED: user's learning context from get-user-context)",
            "explicit_query": "string (optional: for Q&A mode, e.g. 'What is MCP and how to use it?')",
        },
        "output_schema": {
            "success": "boolean",
            "insights": "array of insight objects",
            "ragas_scores": "object with faithfulness, precision, recall, average",
            "quality_badge": "string (✨/✓/⚠️)",
            "metadata": "object",
            "num_insights": "integer",
            "error": "string (only if success=false)"
        },
        # ... rest of schema
    }
```

---

### Phase 2: Improve Query Building

#### Task 2.1: Add Explicit Query Support

**File:** `learning-coach-mcp/src/rag/query_builder.py`

**Update `_construct_query_text` (lines 100-181):**

```python
def _construct_query_text(
    self,
    context: Dict[str, Any],
    explicit_query: Optional[str] = None,
) -> str:
    """Construct semantic query text from learning context."""

    # If user provided explicit query, use it directly for Q&A mode
    if explicit_query:
        # For Q&A mode: keep query focused and question-based
        query_parts = [explicit_query]

        # Add minimal context hints
        if context.get("difficulty_level"):
            level = context["difficulty_level"]
            query_parts.append(f"Explain at {level} level.")

        return " ".join(query_parts)

    # Otherwise, construct broader query for digest mode
    query_parts = []

    # Week and topics
    if context.get("current_week"):
        query_parts.append(f"Week {context['current_week']} of AI bootcamp.")

    if context.get("current_topics"):
        topics = context["current_topics"]
        topics_str = ", ".join(topics)
        query_parts.append(f"Learning: {topics_str}.")

    # Difficulty and request
    difficulty = context.get("difficulty_level", "intermediate")
    query_parts.append(
        f"Provide {difficulty}-level explanations with practical examples "
        f"and implementation details."
    )

    return " ".join(query_parts)
```

**Impact:** Queries become focused and effective for semantic search.

---

### Phase 3: Fix Agent Completion Logic

#### Task 3.1: Update Planning Prompt

**File:** `agent/prompts/planning.txt`

**Add after line 107 (after "Have I called generate-digest..."):**

```markdown
7. **Have I called generate-digest and received a result?**
   - Check if result has "success": true and "insights" is not empty
   - If YES and success=true → COMPLETE immediately with the digest output
   - If YES but success=false → Check error message, may need different approach
   - If NO → Call generate-digest to synthesize content

8. **Important: Do NOT retry generate-digest on success**
   - If generate-digest returned success=true with insights → COMPLETE
   - RAGAS scores of 0.7+ are acceptable - do not retry for improvements
   - Only retry if success=false or error occurred
```

**Add to "Important Guidelines" (line 131):**

```markdown
- **Complete after successful digest**: Once generate-digest returns success=true and insights (even with RAGAS ~0.7-0.8), COMPLETE immediately. Do NOT retry to improve scores. The digest is good enough.
- **Always force_refresh**: Set force_refresh=true to avoid cached empty digests
```

#### Task 3.2: Update Workflow Examples

**File:** `agent/prompts/planning.txt` (after line 349)

**Add example for Q&A mode:**

```markdown
### Scenario 3: User asks "Help me learn MCP" (Q&A mode)

**Iteration 1:** Get user context
```json
{"action_type": "TOOL_CALL", "tool": "get-user-context", "args": {"user_id": "current"}}
```
Result: `{"week": 7, "topics": ["Model Context Protocol", "LLM Tool Calling"], "difficulty": "intermediate"}`

**Iteration 2:** Generate focused answer (not full digest)
```json
{
  "action_type": "TOOL_CALL",
  "tool": "generate-digest",
  "args": {
    "max_insights": 3,
    "explicit_query": "What is Model Context Protocol and how do I use it?",
    "user_context": {"week": 7, "difficulty": "intermediate"},
    "force_refresh": true
  },
  "reasoning": "User wants to learn about MCP specifically. Using explicit_query for focused retrieval and fewer insights (3 instead of 7) for targeted answer."
}
```
Result: `{"success": true, "insights": [...3 insights...], "ragas_scores": {"average": 0.82}}`

**Iteration 3:** Complete immediately (do NOT retry!)
```json
{
  "action_type": "COMPLETE",
  "output": {
    "answer": {
      "insights": [...3 insights...],
      "topic": "Model Context Protocol",
      "ragas_scores": {"average": 0.82},
      "quality_badge": "✓"
    }
  },
  "reasoning": "Successfully generated focused answer with 3 insights and RAGAS score of 0.82. This is sufficient - completing now."
}
```

**CRITICAL:** Do NOT call generate-digest multiple times. Once you get success=true, COMPLETE immediately.
```

---

### Phase 4: Add Goal Classification

#### Task 4.1: Update Goal Type Detection

**File:** `agent/prompts/planning.txt` (lines 58-76)

**Replace with:**

```markdown
## Goal Type Detection

Before following the decision-making process, identify the goal type:

**Daily Digest Goals:**
- Keywords: "digest", "daily digest", "learning digest", "today's digest", "generate digest"
- Characteristics: No specific topic, wants broad overview
- Action: Call generate-digest with max_insights=7 (no explicit_query)

**Learning Question Goals (Q&A Mode):**
- Keywords: "help me learn", "teach me", "explain", "what is", "how does"
- Characteristics: Asking about specific topic
- Action: Call generate-digest with max_insights=3 and explicit_query parameter
- Example: "Help me learn MCP" → explicit_query="What is Model Context Protocol and how do I use it?"

**Content Search Goals:**
- Keywords: "search for", "find content about", "show me articles on"
- Action: Use search-content tool, return results

**Progress Sync Goals:**
- Keywords: "sync", "update progress", "refresh", "latest week"
- Action: Call sync-progress
```

---

## Testing Strategy

### Test 1: Daily Digest Generation

**Command:**
```bash
python test_digest_generation_simple.py
```

**Expected behavior:**
```
Iteration 1: get-user-context
Iteration 2: generate-digest (max_insights=7, no explicit_query)
Iteration 3: COMPLETE
Status: completed
Insights: 7
```

### Test 2: Learning Question (Q&A Mode)

**Command:**
```python
result = await controller.run(
    goal="Help me learn about Model Context Protocol",
    user_id="00000000-0000-0000-0000-000000000001"
)
```

**Expected behavior:**
```
Iteration 1: get-user-context
Iteration 2: generate-digest (max_insights=3, explicit_query="What is Model Context Protocol...")
Iteration 3: COMPLETE
Status: completed
Insights: 3 (focused on MCP)
```

### Test 3: Verify RAG Pipeline

**Check:**
- Vector retriever is called (semantic search, not just recent articles)
- Claude synthesizer is used (not OpenAI)
- Real RAGAS scores (not fake 0.80)
- Insights are grounded in retrieved chunks

### Test 4: Agent Doesn't Loop

**Check:**
- Agent calls generate-digest exactly ONCE
- Completes on success=true
- No retries unless error

---

## Success Criteria

| Metric | Target | How to Verify |
|--------|--------|---------------|
| Uses DigestGenerator | ✅ | Check imports in tools.py |
| Semantic search works | ✅ | Check retriever logs, similarity scores |
| Claude synthesis | ✅ | Check synthesizer logs, quality of insights |
| Real RAGAS scores | ✅ | Scores vary, not always 0.80 |
| Agent completes in 3 iterations | ✅ | Test output shows 3 iterations |
| No looping | ✅ | generate-digest called exactly once |
| Q&A mode works | ✅ | Focused insights for learning questions |
| Full digest works | ✅ | 7 diverse insights for digest request |

---

## Risks and Mitigation

### Risk 1: Import Issues

**Problem:** DigestGenerator uses relative imports that may fail

**Mitigation:**
- Add MCP src to sys.path explicitly
- Wrap in try/except with clear error messages
- Test imports before running full implementation

### Risk 2: RAGAS Evaluation Slow

**Problem:** RAGAS evaluation can take 30-60 seconds

**Mitigation:**
- Set reasonable timeouts (120s)
- Make RAGAS optional (fallback to placeholder scores)
- Consider caching evaluation results

### Risk 3: Empty Database

**Problem:** If database has no content, retrieval fails

**Mitigation:**
- Check content availability before retrieval
- Return helpful error message
- Suggest running ingestion

---

## Implementation Order

1. **Task 1.1** - Replace digest_api.py (30 min)
2. **Task 1.2** - Update tool schema (10 min)
3. **Test** - Verify RAG pipeline works (15 min)
4. **Task 3.1** - Fix completion logic (15 min)
5. **Task 4.1** - Update goal detection (10 min)
6. **Task 3.2** - Add workflow examples (10 min)
7. **Task 2.1** - Improve query building (15 min)
8. **Test** - Full integration testing (20 min)

**Total estimated time: ~2 hours**

---

## Rollback Plan

If issues arise:
1. Revert `agent/tools.py` to use digest_api.py
2. Keep planning prompt changes (they're improvements)
3. Test individual components separately
4. Can disable RAGAS evaluation if too slow

---

## Future Enhancements (Not in This Plan)

1. **Streaming insights** - Show insights as they're generated
2. **Insight caching** - Cache individual insights, not just full digests
3. **Multi-turn conversations** - Allow follow-up questions
4. **Source diversity** - Ensure insights from different sources
5. **User feedback loop** - Incorporate ratings into future digests

---

## Key Insights

1. **Root cause was dual:** Both wrong implementation (digest_api.py) AND agent looping
2. **Import complexity:** Python package structure makes imports challenging
3. **Q&A is not digest:** Need separate modes for different use cases
4. **Completion criteria unclear:** Agent needs explicit success indicators
5. **Query building matters:** Generic queries get generic results

---

## Deliverables

1. ✅ Updated `agent/tools.py` with DigestGenerator integration
2. ✅ Updated `agent/prompts/planning.txt` with completion logic
3. ✅ Updated `learning-coach-mcp/src/rag/query_builder.py` with explicit query support
4. ✅ Test results showing 3-iteration completion
5. ✅ Documentation of changes

---

## Next Steps After Approval

1. Implement Task 1.1 (DigestGenerator integration)
2. Run initial tests
3. Iterate on remaining tasks based on test results
4. Document any issues discovered
5. Update this plan with actual implementation notes
