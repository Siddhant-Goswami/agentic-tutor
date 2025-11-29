# Fix Digest Generation - Implementation Plan

## Overview

Implementing the 4 critical fixes identified in the architectural review to enable proper digest generation.

**Goal:** Agent should generate digests in 2-3 iterations instead of timing out at 15 iterations.

---

## Implementation Tasks

### Task 1: Fix Planning Prompt - Correct Digest Workflow

**File:** `agent/prompts/planning.txt`

**Changes:**

1. **Line 79** - Change the decision-making guideline:
   - **Current:** "To generate a digest → Need to search for relevant content"
   - **New:** "To generate a digest → Call generate-digest tool directly (it handles retrieval internally)"

2. **After Line 101** - Add new section "Special Workflows":
   ```markdown
   ## Special Workflows

   ### Digest Generation

   If the user's goal is to generate a digest:

   1. **Iteration 1:** Call get-user-context to get current week, topics, difficulty
   2. **Iteration 2:** Call generate-digest with user_context parameter
      - Do NOT call search-content first
      - Do NOT call analyze-content-coverage first
      - The generate-digest tool handles all retrieval, synthesis, and quality evaluation internally
   3. **Iteration 3:** COMPLETE with the digest output

   Only use search-content or web-search if the user explicitly asks to search for specific content separately.
   ```

**Reasoning:** The planning prompt currently teaches the agent the wrong workflow. This corrects the mental model.

---

### Task 2: Reimplement Agent's generate-digest Tool

**File:** `agent/tools.py`

**Changes:**

1. **Update `_generate_digest_schema()` method (lines 121-144):**
   - Add `user_context` to input_schema
   - Update description to clarify tool handles retrieval internally
   - Update output_schema to match DigestGenerator output
   - Update example to show proper usage

2. **Replace `_execute_generate_digest()` method (lines 404-448):**
   - Import `DigestGenerator` from `rag.digest_generator`
   - Parse date parameter (support "today" and ISO format)
   - Initialize DigestGenerator with proper credentials
   - Call `generator.generate()` with all parameters including user_context
   - Return the actual result with real RAGAS scores

**Code to implement:**

```python
async def _execute_generate_digest(self, args: Dict[str, Any]) -> Dict[str, Any]:
    """Execute generate-digest tool using the actual DigestGenerator."""
    from rag.digest_generator import DigestGenerator
    from datetime import datetime, date

    # Parse date
    date_str = args.get("date", "today")
    if date_str == "today":
        target_date = date.today()
    else:
        target_date = datetime.fromisoformat(date_str).date()

    max_insights = args.get("max_insights", 7)
    force_refresh = args.get("force_refresh", False)
    user_context = args.get("user_context")

    try:
        # Initialize DigestGenerator with proper credentials
        generator = DigestGenerator(
            supabase_url=self.supabase_url,
            supabase_key=self.supabase_key,
            openai_api_key=self.openai_api_key,
            anthropic_api_key=self.anthropic_api_key,
        )

        # Call the actual generate method
        result = generator.generate(
            target_date=target_date,
            num_insights=max_insights,
            force_refresh=force_refresh,
            learning_context=user_context,
        )

        return result

    except Exception as e:
        logger.error(f"Error generating digest: {e}", exc_info=True)
        return {
            "insights": [],
            "error": str(e),
            "message": "Failed to generate digest",
            "ragas_scores": {},
        }
```

**Reasoning:** Current implementation is a stub that doesn't use the real DigestGenerator. This integrates the actual RAG pipeline.

---

### Task 3: Update Workflow Examples

**File:** `agent/prompts/planning.txt`

**Changes:**

**Replace lines 203-240** (Complete Workflow Example section) with two scenarios:

1. **Scenario 1: Direct digest generation** (2-3 iterations)
2. **Scenario 2: Digest with web search approval** (5-6 iterations)

**New content:**

```markdown
## Complete Workflow Examples

### Scenario 1: User asks "Generate my daily digest"

**Iteration 1:** Get user context
```json
{"action_type": "TOOL_CALL", "tool": "get-user-context", "args": {"user_id": "current"}}
```
Result: `{"week": 7, "topics": ["Transformers"], "difficulty": "intermediate"}`

**Iteration 2:** Generate digest (internally retrieves + synthesizes)
```json
{
  "action_type": "TOOL_CALL",
  "tool": "generate-digest",
  "args": {
    "date": "today",
    "max_insights": 7,
    "user_context": {"week": 7, "topics": ["Transformers"], "difficulty": "intermediate"}
  },
  "reasoning": "User wants a digest. The generate-digest tool will retrieve relevant content for Week 7/Transformers, synthesize insights, and evaluate quality."
}
```

**Iteration 3:** Complete
```json
{
  "action_type": "COMPLETE",
  "output": {"digest": {...}},
  "reasoning": "Successfully generated personalized digest with verified quality scores."
}
```

---

### Scenario 2: User asks "Help me learn quantum computing" (database lacks content)

**Iteration 1:** Get user context

**Iteration 2:** Check database coverage
```json
{"action_type": "TOOL_CALL", "tool": "analyze-content-coverage", "args": {...}}
```
Result: `{"needs_web_search": true, "coverage_gaps": [...]}`

**Iteration 3:** Request approval
```json
{"action_type": "PLAN_APPROVAL", "research_plan": {...}}
```

[User approves → System re-runs with SKIP_WEB_SEARCH_APPROVAL=true]

**Iteration 4:** Execute web search
```json
{"action_type": "TOOL_CALL", "tool": "web-search", "args": {...}}
```

**Iteration 5:** Generate digest (uses DB + web results)
```json
{"action_type": "TOOL_CALL", "tool": "generate-digest", "args": {...}}
```

**Iteration 6:** Complete
```

**Reasoning:** Current examples reinforce the wrong pattern. New examples show correct workflows.

---

### Task 4: Add Explicit Goal Detection

**File:** `agent/prompts/planning.txt`

**Changes:**

**Insert after line 58** (before "Decision-Making Process"):

```markdown
## Goal Type Detection

Before following the decision-making process, identify the goal type:

**Digest Generation Goals:**
- Keywords: "digest", "daily digest", "learning digest", "today's digest", "generate digest"
- Action: Call generate-digest after getting user context (skip search steps)

**Search Goals:**
- Keywords: "search for", "find content about", "show me articles on"
- Action: Use search-content or web-search as appropriate

**Question Goals:**
- Keywords: "what is", "how does", "explain", "help me understand"
- Action: Use search-content or search-past-insights to find answers

**Progress Sync Goals:**
- Keywords: "sync", "update progress", "refresh", "latest week"
- Action: Call sync-progress
```

**Reasoning:** Helps the agent immediately recognize digest generation goals and follow the correct workflow.

---

## Testing Plan

After implementation, run these tests:

### Test 1: Direct Digest Request
```bash
python -c "from agent.controller import AgentController, AgentConfig; ..."
# Goal: "Generate my daily digest"
# Expected: 2-3 iterations, complete status, real digest
```

### Test 2: Verify Integration
- Check that DigestGenerator is imported
- Check that real RAGAS scores are returned (not 0.85)
- Check that insights are synthesized (not just content metadata)

### Test 3: User Context Personalization
- Verify digest includes user's week and topics
- Check that difficulty level affects content selection

### Test 4: Run Existing Test Suite
```bash
python test_approval_ui_workflow.py
```
- Test 5 should now complete successfully
- Agent should generate digest within iteration limit

---

## Success Criteria

✅ Agent completes digest generation in ≤ 5 iterations (not 15)
✅ `generate-digest` tool uses actual `DigestGenerator` class
✅ Real RAGAS scores returned (not hardcoded)
✅ Insights are synthesized (not raw metadata)
✅ User context is used for personalization
✅ No timeout errors
✅ Test suite passes

---

## Rollback Plan

If issues occur:
1. Keep original files as `.bak` backups
2. Can revert each file independently
3. Test after each fix to isolate issues

---

## Estimated Completion

- Task 1: 5 minutes (prompt updates)
- Task 2: 15 minutes (code rewrite + schema update)
- Task 3: 5 minutes (workflow examples)
- Task 4: 3 minutes (goal detection)
- Testing: 10 minutes

**Total: ~40 minutes**

---

## Implementation Status

### ✅ Completed Tasks

**Task 1: Fixed Planning Prompt** (`agent/prompts/planning.txt`)
- ✅ Updated line 99 to correct the workflow: "Call generate-digest tool directly"
- ✅ Added "Goal Type Detection" section (lines 58-76) to help agent recognize digest goals
- ✅ Added "Special Workflows" section (lines 123-136) with explicit digest generation steps

**Task 2: Reimplemented generate-digest Tool** (`agent/tools.py`)
- ✅ Updated `_generate_digest_schema()` with proper description and user_context parameter
- ✅ Replaced `_execute_generate_digest()` with subprocess-based approach to call MCP server
  - **Note:** Used subprocess to avoid Python import issues with relative imports in MCP package
  - Calls `server.generate_daily_digest()` function directly
  - Properly async with 120s timeout

**Task 3: Updated Workflow Examples** (`agent/prompts/planning.txt`)
- ✅ Replaced lines 238-316 with two new scenarios:
  - Scenario 1: Direct digest generation (3 iterations)
  - Scenario 2: Digest with web search approval (6 iterations)
- ✅ Examples now show correct tool call sequence

**Task 4: Added Goal Detection** (`agent/prompts/planning.txt`)
- ✅ Added explicit goal type detection section (lines 58-76)
- ✅ Includes keywords for digest, search, question, and progress goals
- ✅ Provides clear action mappings for each goal type

### 🔄 Current Status

**Testing in progress:**
- Running `test_approval_ui_workflow.py` to verify fixes
- Checking if agent now completes digest generation within iteration limit

---

## Technical Decisions Made

### Import Approach

**Problem:** Direct import of `DigestGenerator` from `learning-coach-mcp/src/rag/digest_generator.py` failed due to relative import issues:
```
from ..utils.db import get_supabase_client
ImportError: attempted relative import beyond top-level package
```

**Solution:** Used subprocess to call MCP server's `generate_daily_digest()` function:
- Avoids Python package import complexities
- Reuses existing tested MCP server code
- Clean separation of concerns
- 120s timeout for digest generation

**Future Improvement:** Consider:
1. Installing MCP package properly with setup.py
2. Restructuring imports to avoid relative import issues
3. Creating a shared library package

---

## Notes

- All fixes are backward compatible
- No database schema changes needed
- No new dependencies required
- Preserves existing DigestGenerator functionality
- Subprocess approach is pragmatic but could be optimized in future
