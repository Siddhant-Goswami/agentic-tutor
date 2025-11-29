# Digest Generation Architectural Review

## Executive Summary

The system is **NOT generating digests** because of multiple architectural gaps and misalignments between the agent's decision-making logic and the digest generation implementation.

**Root Cause:** The agent's planning prompt teaches it that generating a digest requires manually searching for content first, but then the agent never actually calls the digest generation tool—it gets stuck in a search loop and hits max iterations.

---

## Critical Logical Gaps

### 1. **Planning Prompt Teaches Wrong Workflow**

**Location:** `agent/prompts/planning.txt:79`

```
5. **What information or action is needed next?**
   - To generate a digest → Need to search for relevant content
   - To search content → Need to know what topics/query
   - To answer a question → May need to search past insights
```

**Problem:** This teaches the agent that before calling `generate-digest`, it must first call `search-content`. This is fundamentally wrong because:

- The `DigestGenerator.generate()` method (in `learning-coach-mcp/src/rag/digest_generator.py:87-202`) **already handles content retrieval internally** via `retriever.retrieve()`
- The agent ends up in a loop: search → web-search → analyze-coverage → search again → timeout
- It **never calls** `generate-digest` because it thinks it needs more content first

**Expected Flow:**
```
User: "Generate my daily digest"
  → Iteration 1: get-user-context
  → Iteration 2: generate-digest (which internally retrieves content + synthesizes)
  → Iteration 3: COMPLETE with digest
```

**Actual Flow:**
```
User: "Generate my daily digest"
  → Iteration 1: get-user-context
  → Iteration 2: analyze-content-coverage
  → Iteration 3: PLAN_APPROVAL for web search
  → Iteration 4: web-search (after approval)
  → Iteration 5: search-content (database)
  → Iteration 6: search-content again (refined query)
  → ...
  → Iteration 15: TIMEOUT (never called generate-digest)
```

---

### 2. **Agent's generate-digest Tool Doesn't Use DigestGenerator**

**Location:** `agent/tools.py:404-448` (`_execute_generate_digest`)

**Current Implementation:**
```python
async def _execute_generate_digest(self, args: Dict[str, Any]) -> Dict[str, Any]:
    """Execute generate-digest tool."""
    from utils.db import get_supabase_client

    max_insights = args.get("max_insights", 5)
    db = get_supabase_client(self.supabase_url, self.supabase_key)

    # Simplified digest generation using direct DB access
    content_result = (
        db.table("content")
        .select("title, author, url, published_at")
        .order("published_at", desc=True)
        .limit(max_insights)
        .execute()
    )

    # Format as insights
    insights = []
    for item in content_result.data:
        insights.append({
            "title": item.get("title", "Untitled"),
            "content": f"Article by {item.get('author', 'Unknown')}...",
            "source": {...}
        })

    return {
        "insights": insights,
        "ragas_scores": {"average": 0.85},  # Fake score!
        "message": f"Generated {len(insights)} insights"
    }
```

**Problems:**

1. **Doesn't use the actual RAG pipeline:**
   - The sophisticated `DigestGenerator` with vector search, quality gates, RAGAS evaluation exists in `learning-coach-mcp/src/rag/digest_generator.py`
   - But the agent's tool completely bypasses it
   - Instead, it just queries the content table by `published_at` (most recent)

2. **No semantic search:**
   - Doesn't use embeddings or similarity thresholds
   - Doesn't match user's learning context (week, topics, difficulty)
   - Just grabs the 5 most recent articles regardless of relevance

3. **No synthesis:**
   - Doesn't use Claude (Anthropic API) to generate insights
   - Just formats raw content metadata as "insights"
   - No actual learning value added

4. **Fake quality scores:**
   - Returns hardcoded `ragas_scores: {"average": 0.85}`
   - No actual RAGAS evaluation happening
   - Misleading quality indicators

5. **Missing cache check:**
   - Doesn't check if a digest was already generated today
   - No cache_expires_at logic

**Expected Implementation:**
```python
async def _execute_generate_digest(self, args: Dict[str, Any]) -> Dict[str, Any]:
    """Execute generate-digest tool using the actual DigestGenerator."""
    from rag.digest_generator import DigestGenerator

    # Initialize the proper DigestGenerator with all dependencies
    generator = DigestGenerator(
        supabase_url=self.supabase_url,
        supabase_key=self.supabase_key,
        openai_api_key=self.openai_api_key,
        anthropic_api_key=self.anthropic_api_key,
    )

    # Parse date and call the real generate() method
    date_obj = parse_date(args.get("date", "today"))
    max_insights = args.get("max_insights", 7)
    force_refresh = args.get("force_refresh", False)

    # This handles everything: cache check, retrieval, synthesis, quality gate
    result = generator.generate(
        target_date=date_obj,
        num_insights=max_insights,
        force_refresh=force_refresh,
    )

    return result  # Real digest with real quality scores
```

---

### 3. **Workflow Example Shows Manual Search Before Digest**

**Location:** `agent/prompts/planning.txt:203-240`

The "Complete Workflow Example" teaches:

```
Iteration 1: Get user context
Iteration 2: Check database coverage
Iteration 3: Request approval (if needed)
Iteration 4: Search database content
Iteration 5: Generate digest combining DB and web sources
Iteration 6: Complete
```

**Problem:** This reinforces the wrong mental model that:
- Searching must happen BEFORE digest generation
- The digest tool needs pre-fetched results passed to it

**Reality:** The `generate-digest` tool should be called IMMEDIATELY after getting user context. It handles retrieval internally.

**Corrected Workflow:**
```
Iteration 1: Get user context
Iteration 2: Generate digest (internally retrieves + synthesizes)
Iteration 3: COMPLETE with digest

OR (if web search needed):

Iteration 1: Get user context
Iteration 2: analyze-content-coverage (check if DB has enough)
Iteration 3: PLAN_APPROVAL (if needs_web_search: true)
[User approves, system re-runs with SKIP_WEB_SEARCH_APPROVAL=true]
Iteration 4: web-search (fetch additional sources)
Iteration 5: Generate digest (now includes web results)
Iteration 6: COMPLETE
```

---

### 4. **Missing Integration Between Agent Tools and MCP DigestGenerator**

**Gap:** The agent's `generate-digest` tool and the MCP server's `DigestGenerator` are completely disconnected.

**Evidence:**

1. **MCP Server Tool:** `learning-coach-mcp/src/server.py:43-103`
   - Properly instantiates `DigestGenerator`
   - Calls `generator.generate()`
   - Returns full digest with real RAGAS scores

2. **Agent Tool:** `agent/tools.py:404-448`
   - Doesn't import or use `DigestGenerator`
   - Implements a naive "simplified" version
   - Doesn't leverage any of the RAG infrastructure

**Why This Happened:**

Looking at the imports in `tools.py:1-18`:
```python
import sys
from pathlib import Path

# Add MCP src to path for accessing shared utilities
project_root = Path(__file__).parent.parent
mcp_src_path = project_root / "learning-coach-mcp" / "src"
sys.path.insert(0, str(mcp_src_path))
```

The path is added, but then the code never actually imports from it!

**Missing Import:**
```python
from rag.digest_generator import DigestGenerator  # This is never imported!
```

---

### 5. **No Clear Signal for When to Call generate-digest**

**Problem:** The planning prompt doesn't explicitly tell the agent:
> "If the user's goal is to generate a digest, call the generate-digest tool directly after getting user context"

Instead, it has a vague guideline (line 79):
> "To generate a digest → Need to search for relevant content"

**What's Needed:**

Add explicit decision tree to `planning.txt`:

```markdown
## Special Case: Digest Generation Goals

If user's goal contains keywords like:
- "generate digest"
- "daily digest"
- "learning digest"
- "show me my digest"

Follow this workflow:

1. **Iteration 1:** Call get-user-context
2. **Iteration 2:** Call generate-digest directly
3. **Iteration 3:** COMPLETE with digest

Do NOT call search-content or analyze-content-coverage first.
The generate-digest tool handles all retrieval internally.
```

---

### 6. **Test Results Confirm the Gap**

From `test_approval_ui_workflow.py` output:

```
================================================================================
TEST 5: Complete Approval Workflow with Digest
================================================================================

Step 1: Running agent (should request approval)...
✅ Step 1 passed: Agent requested approval

Step 2: Simulating approval granted (setting SKIP_WEB_SEARCH_APPROVAL=true)...

Step 3: Re-running agent with approval granted...

Step 3 result status: timeout
Iterations: 15
⚠️  Agent didn't complete (status: timeout)
```

**Analysis:**
- Agent correctly requests approval (Step 1) ✅
- Approval is granted via `SKIP_WEB_SEARCH_APPROVAL=true` ✅
- Agent re-runs but **hits 15 iterations without completing** ❌
- This confirms: Agent is stuck in a loop and never calls generate-digest

---

## Additional Observations

### 7. **Partial Result Generation Doesn't Help**

**Location:** `agent/controller.py:542-672` (`_generate_partial_result`)

When the agent hits max iterations, it generates a "partial result" with:
- Warning about timeout
- Any insights from gathered sources
- Recommendations

**Problem:** This is a fallback for when the agent fails, but it shouldn't be hitting this fallback at all for digest generation! The digest should complete in 2-3 iterations.

**Current Behavior:** The partial result synthesizes search results, but it's not using the `DigestGenerator`—just formatting whatever search results were found.

---

### 8. **Missing User Context Integration**

**Location:** `learning-coach-mcp/src/rag/digest_generator.py:126-133`

```python
# Get user context (if available)
user_context = learning_context or self._get_default_context()

# If learning_context is None, use defaults
if learning_context is None:
    user_context = {
        "current_week": 1,
        "current_topics": ["AI", "Machine Learning"],
        "difficulty_level": "intermediate",
    }
```

**Problem:** The agent retrieves user context in Iteration 1, but when it (theoretically) calls `generate-digest`, it **doesn't pass the user context as a parameter**.

**Looking at the tool schema** (`agent/tools.py:121-144`):

```python
"input_schema": {
    "date": "string (ISO date or 'today', default: 'today')",
    "max_insights": "integer (3-10, default: 7)",
    "force_refresh": "boolean (skip cache, default: false)",
}
```

**Missing:** No `user_context` parameter!

**What Should Happen:**
```python
"input_schema": {
    "date": "string",
    "max_insights": "integer",
    "force_refresh": "boolean",
    "user_context": "object (optional, from get-user-context tool)",  # ADD THIS
}
```

Then in `_execute_generate_digest`:
```python
user_context = args.get("user_context")
result = generator.generate(
    target_date=date_obj,
    num_insights=max_insights,
    force_refresh=force_refresh,
    learning_context=user_context,  # Pass it through
)
```

---

## Root Cause Summary

| Issue | Impact | Severity |
|-------|--------|----------|
| Planning prompt teaches wrong workflow (search before digest) | Agent never calls generate-digest | 🔴 CRITICAL |
| Agent's generate-digest tool doesn't use DigestGenerator | No RAG, no synthesis, fake quality scores | 🔴 CRITICAL |
| Workflow example reinforces manual search pattern | Agent stuck in search loop | 🔴 CRITICAL |
| No clear decision rule for digest goals | Agent doesn't know when to call tool | 🟠 HIGH |
| Missing user_context parameter in tool schema | Digest not personalized | 🟡 MEDIUM |
| Partial result fallback masks the problem | Hides that agent is failing | 🟡 MEDIUM |

---

## Recommended Fixes (Priority Order)

### **FIX 1: Update Planning Prompt** (CRITICAL)

**File:** `agent/prompts/planning.txt`

**Change Line 79:**

**Current:**
```
- To generate a digest → Need to search for relevant content
```

**New:**
```
- To generate a digest → Call generate-digest tool directly (it handles retrieval internally)
```

**Add New Section After Line 101:**

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

---

### **FIX 2: Reimplement Agent's generate-digest Tool** (CRITICAL)

**File:** `agent/tools.py:404-448`

**Replace entire `_execute_generate_digest` method:**

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
    user_context = args.get("user_context")  # Get from args

    try:
        # Initialize DigestGenerator with proper credentials
        generator = DigestGenerator(
            supabase_url=self.supabase_url,
            supabase_key=self.supabase_key,
            openai_api_key=self.openai_api_key,
            anthropic_api_key=self.anthropic_api_key,
        )

        # Call the actual generate method with all the RAG pipeline
        result = generator.generate(
            target_date=target_date,
            num_insights=max_insights,
            force_refresh=force_refresh,
            learning_context=user_context,  # Pass user context
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

**Also Update Schema (`_generate_digest_schema` at line 121-144):**

```python
def _generate_digest_schema(self) -> Dict[str, Any]:
    """Schema for generate-digest tool."""
    return {
        "name": "generate-digest",
        "description": "Generate a complete personalized learning digest with insights and quality scores. This tool handles all content retrieval, synthesis, and evaluation internally - do NOT search for content before calling this tool.",
        "input_schema": {
            "date": "string (ISO date or 'today', default: 'today')",
            "max_insights": "integer (3-10, default: 7)",
            "force_refresh": "boolean (skip cache, default: false)",
            "user_context": "object (optional, user's learning context from get-user-context)",  # ADD
        },
        "output_schema": {
            "insights": "array of insight objects with title, explanation, practical_takeaway, source",
            "ragas_scores": "object with faithfulness, context_precision, context_recall, average",
            "quality_badge": "string (✨ high / ✓ good / ⚠️ low)",
            "metadata": "object with query, learning_context, sources, etc.",
        },
        "example": {
            "input": {
                "date": "today",
                "max_insights": 5,
                "user_context": {
                    "week": 7,
                    "topics": ["Transformers", "Attention"],
                    "difficulty": "intermediate",
                }
            },
            "output": {
                "insights": [{"title": "...", "explanation": "...", "source": {...}}],
                "ragas_scores": {"average": 0.85, "faithfulness": 0.88},
                "quality_badge": "✨",
            },
        },
    }
```

---

### **FIX 3: Update Workflow Example in Planning Prompt** (HIGH)

**File:** `agent/prompts/planning.txt:203-240`

**Replace "Complete Workflow Example" section:**

```markdown
## Complete Workflow Example

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
Result: Full digest with insights, sources, RAGAS scores

**Iteration 3:** Complete
```json
{
  "action_type": "COMPLETE",
  "output": {"digest": {...}},
  "reasoning": "Successfully generated personalized digest with verified quality scores."
}
```

---

### Scenario 2: User asks "Help me learn quantum computing" (requires web search)

**Iteration 1:** Get user context
```json
{"action_type": "TOOL_CALL", "tool": "get-user-context", "args": {"user_id": "current"}}
```

**Iteration 2:** Check database coverage
```json
{
  "action_type": "TOOL_CALL",
  "tool": "analyze-content-coverage",
  "args": {"query": "quantum computing", "user_id": "current"}
}
```
Result: `{"needs_web_search": true, "coverage_gaps": ["quantum gates", "entanglement"]}`

**Iteration 3:** Request approval (because needs_web_search: true)
```json
{
  "action_type": "PLAN_APPROVAL",
  "research_plan": {...gaps and proposed searches...}
}
```

[User approves → System re-runs with SKIP_WEB_SEARCH_APPROVAL=true]

**Iteration 4:** Call web-search (approval already granted)
```json
{
  "action_type": "TOOL_CALL",
  "tool": "web-search",
  "args": {"query": "quantum computing basics tutorial", "max_results": 5},
  "reasoning": "SKIP_WEB_SEARCH_APPROVAL is true, proceeding with web search"
}
```

**Iteration 5:** Generate digest (will use DB + web results)
```json
{
  "action_type": "TOOL_CALL",
  "tool": "generate-digest",
  "args": {"date": "today", "max_insights": 7, "user_context": {...}}
}
```

**Iteration 6:** Complete
```json
{"action_type": "COMPLETE", "output": {"digest": {...}}}
```
```

---

### **FIX 4: Add Explicit Goal Detection** (MEDIUM)

**File:** `agent/prompts/planning.txt`

**Add after line 58 (before "Decision-Making Process"):**

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
- Action: Use search-content or search-past-insights as appropriate

**Progress Sync Goals:**
- Keywords: "sync", "update progress", "refresh", "latest week"
- Action: Call sync-progress
```

---

## Testing Plan

After implementing fixes, verify:

1. **Test 1: Direct Digest Request**
   ```
   User: "Generate my daily digest"
   Expected: 2-3 iterations max, returns complete digest
   ```

2. **Test 2: Digest with User Context**
   ```
   User: "Generate my daily digest"
   Expected: Digest is personalized to user's week, topics, difficulty
   ```

3. **Test 3: Digest Quality**
   ```
   Verify: insights have real RAGAS scores (not hardcoded 0.85)
   Verify: insights are synthesized (not just raw content metadata)
   ```

4. **Test 4: Digest with Web Search Approval**
   ```
   User: "Help me learn quantum computing basics"
   Expected: Agent analyzes coverage, requests approval, executes web search, generates digest
   ```

5. **Test 5: No Timeout**
   ```
   User: "Generate my daily digest"
   Expected: Never hits max_iterations (15)
   ```

---

## Conclusion

The digest generation system has all the right components:
- ✅ Sophisticated DigestGenerator with RAG pipeline
- ✅ Quality gates with RAGAS evaluation
- ✅ Vector search and semantic retrieval
- ✅ User context personalization

But they're **disconnected** from the agent's decision-making:
- ❌ Agent doesn't know when to call generate-digest
- ❌ Agent's generate-digest tool doesn't use DigestGenerator
- ❌ Planning prompt teaches the wrong workflow

**Fix the 4 critical issues above and the system will work as designed.**
