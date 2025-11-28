# Agentic Learning Coach - Implementation Plan

## Executive Summary

**Goal:** Transform the AI Learning Coach from a fixed workflow MCP server into an autonomous agent that reasons, plans, acts, and reflects.

**Current State:**
- MCP server with 5 predefined tools
- Fixed workflow: User calls `generate_daily_digest()` → predetermined steps execute
- No adaptation, no visible reasoning, no personalization beyond basic RAG

**Target State (MVP):**
- Autonomous agent with SENSE → PLAN → ACT → OBSERVE → REFLECT loop
- LLM-driven decision making at each step
- Visible reasoning through detailed logging
- Adaptive behavior based on user context

**Key Constraint:** Build in phases, starting with MVP (Phase 1: Core Agent Loop)

---

## Phase 1: Core Agent Loop (MVP)

### 1.1 Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                   AGENT CONTROLLER                      │
│                                                         │
│  1. SENSE    → Query user context (progress, prefs)    │
│  2. PLAN     → LLM decides next action                  │
│  3. ACT      → Execute via existing MCP tools           │
│  4. OBSERVE  → Capture and log result                   │
│  5. REFLECT  → LLM evaluates if goal achieved           │
│  6. LOOP     → Repeat or complete                       │
│                                                         │
└─────────────────────────────────────────────────────────┘
          ↓ Uses existing tools ↓
┌─────────────────────────────────────────────────────────┐
│         EXISTING MCP TOOLS (Unchanged)                  │
│  • generate_daily_digest                                │
│  • manage_sources                                        │
│  • provide_feedback                                      │
│  • sync_bootcamp_progress                               │
│  • search_past_insights                                 │
└─────────────────────────────────────────────────────────┘
```

### 1.2 Components to Build

| Component | Location | Purpose | Lines of Code (Est.) |
|-----------|----------|---------|---------------------|
| Agent Controller | `learning-coach-mcp/src/agent/controller.py` | Main agent loop | ~250 |
| Tool Registry | `learning-coach-mcp/src/agent/tools.py` | Tool schemas for agent | ~150 |
| Planning Prompts | `learning-coach-mcp/src/agent/prompts/` | LLM prompts | ~200 |
| Logger | `learning-coach-mcp/src/agent/logger.py` | Audit logging | ~100 |
| Agent Tool (MCP) | `learning-coach-mcp/src/server.py` | New MCP tool | ~30 |
| Dashboard View | `dashboard/views/agent.py` | Agent UI | ~200 |
| Log Viewer Component | `dashboard/components/log_viewer.py` | Live log display | ~100 |

**Total: ~1030 lines of code**

---

## 1.3 Detailed Implementation Tasks

### Task 1: Create Agent Controller
**File:** `learning-coach-mcp/src/agent/controller.py`

**Implementation:**

```python
class AgentController:
    """
    Autonomous agent that executes SENSE → PLAN → ACT → OBSERVE → REFLECT loop.
    """

    def __init__(self, config: AgentConfig):
        self.config = config
        self.logger = AgentLogger()
        self.tools = ToolRegistry()
        self.llm_client = self._init_llm()

    async def run(self, goal: str, user_id: str) -> AgentResult:
        """
        Main entry point for agent execution.

        Args:
            goal: Natural language goal (e.g., "Generate my daily digest")
            user_id: UUID of the user

        Returns:
            AgentResult with output, logs, and metadata
        """
        session_id = uuid.uuid4()
        self.logger.start_session(session_id, goal, user_id)

        iteration = 0
        context = {}

        while iteration < self.config.max_iterations:
            iteration += 1

            # SENSE: Gather context
            context = await self._sense(user_id, context)

            # PLAN: Decide next action
            plan = await self._plan(goal, context, iteration)

            # Check if complete
            if plan.action_type == "COMPLETE":
                return self._complete(plan, context)

            # ACT: Execute the planned action
            result = await self._act(plan)

            # OBSERVE: Log the result
            self._observe(plan, result)

            # REFLECT: Evaluate quality and next steps
            reflection = await self._reflect(plan, result, goal, context)
            context['last_reflection'] = reflection

        # Max iterations reached
        return self._complete_with_timeout(context)
```

**Key Methods:**

1. `_sense()`: Query database for user context
   - Learning progress (week, topics, difficulty)
   - Learning preferences (if available)
   - Recent feedback patterns
   - Content already seen

2. `_plan()`: Call LLM to decide next action
   - Provide: Available tools, current context, goal, iteration history
   - Receive: JSON with action type, tool name, args, reasoning
   - Action types: TOOL_CALL, COMPLETE, CLARIFY

3. `_act()`: Execute the planned tool
   - Look up tool in registry
   - Call existing MCP tool functions
   - Handle errors gracefully

4. `_observe()`: Log execution
   - Record tool name, inputs, outputs
   - Track timing
   - Append to session logs

5. `_reflect()`: Call LLM to evaluate
   - Ask: "Did this help achieve the goal?"
   - Ask: "Is the quality sufficient?"
   - Ask: "Should we continue or complete?"
   - Return: Reflection string

**Dependencies:**
- OpenAI client for LLM calls
- Supabase client for context queries
- Existing MCP tool functions

---

### Task 2: Create Tool Registry
**File:** `learning-coach-mcp/src/agent/tools.py`

**Purpose:** Define tool schemas that the agent can call

**Implementation:**

```python
class ToolRegistry:
    """Registry of tools available to the agent."""

    def __init__(self):
        self.tools = {
            "get-user-context": self._get_user_context_schema(),
            "search-content": self._search_content_schema(),
            "generate-digest": self._generate_digest_schema(),
            "search-past-insights": self._search_past_insights_schema(),
            "sync-progress": self._sync_progress_schema(),
        }

    def get_tool_schemas_for_prompt(self) -> str:
        """Return formatted tool descriptions for LLM prompt."""
        # Format each tool as: name, description, input schema, output schema
        pass

    async def execute_tool(self, tool_name: str, args: dict) -> dict:
        """Execute a tool by name with given arguments."""
        # Import and call the corresponding MCP tool function
        pass
```

**Tools to Wrap:**

1. **get-user-context**
   - Maps to: DB query + sync_bootcamp_progress
   - Input: `{user_id}`
   - Output: `{week, topics, difficulty, preferences, recent_feedback}`

2. **search-content**
   - Maps to: RAG retriever
   - Input: `{query, k, filters}`
   - Output: `{results: [{title, snippet, source}]}`

3. **generate-digest**
   - Maps to: generate_daily_digest
   - Input: `{date, max_insights}`
   - Output: `{digest with insights, quiz, sources}`

4. **search-past-insights**
   - Maps to: search_past_insights
   - Input: `{query, date_range}`
   - Output: `{insights: [...]}`

5. **sync-progress**
   - Maps to: sync_bootcamp_progress
   - Input: `{user_id}`
   - Output: `{current_week, topics}`

---

### Task 3: Create Planning Prompts
**Files:**
- `learning-coach-mcp/src/agent/prompts/system.txt`
- `learning-coach-mcp/src/agent/prompts/planning.txt`
- `learning-coach-mcp/src/agent/prompts/reflection.txt`

**system.txt:**
```
You are an AI Learning Coach agent. Your role is to help students learn effectively by:

1. Understanding their current learning context (week, topics, struggles)
2. Finding relevant content from curated sources
3. Generating personalized learning digests
4. Adapting to their feedback and preferences

You work autonomously by deciding which tools to call and when. You reason about each action before taking it.

Always prioritize:
- Personalization (match user's level and preferences)
- Quality (verify content is relevant and accurate)
- Clarity (explain your reasoning)
```

**planning.txt:**
```
# Current Goal
{goal}

# User Context
{context}

# Available Tools
{tool_schemas}

# Your Task
Decide the NEXT action to take toward achieving the goal.

You must respond with valid JSON in this format:

{{
  "action_type": "TOOL_CALL" | "COMPLETE" | "CLARIFY",
  "tool": "tool-name" (if TOOL_CALL),
  "args": {{...}} (if TOOL_CALL),
  "reasoning": "Why you chose this action"
}}

Action Types:
- TOOL_CALL: You need to call a tool to gather information or perform an action
- COMPLETE: The goal has been achieved, return final output
- CLARIFY: You need more information from the user

Consider:
1. What information do you need?
2. Have you already gathered user context?
3. Is the quality sufficient?
4. Are you ready to complete the goal?

Respond with JSON only.
```

**reflection.txt:**
```
# Goal
{goal}

# Action Taken
Tool: {tool_name}
Arguments: {args}

# Result
{result}

# Your Task
Evaluate this result and determine next steps.

Consider:
1. Did this action help progress toward the goal?
2. Is the result quality sufficient?
3. Does it match the user's learning level and preferences?
4. Are we ready to complete, or do we need more steps?

Respond with your evaluation (2-3 sentences).
```

---

### Task 4: Create Logger
**File:** `learning-coach-mcp/src/agent/logger.py`

**Implementation:**

```python
class AgentLogger:
    """Logs agent execution for visibility and debugging."""

    def __init__(self):
        self.sessions = {}  # In-memory storage for MVP

    def start_session(self, session_id: UUID, goal: str, user_id: str):
        """Initialize a new agent session."""
        self.sessions[session_id] = {
            "id": session_id,
            "user_id": user_id,
            "goal": goal,
            "started_at": datetime.now(),
            "logs": [],
            "status": "running"
        }

    def log(self, session_id: UUID, phase: str, content: dict):
        """
        Log a phase execution.

        Args:
            session_id: UUID of the session
            phase: SENSE, PLAN, ACT, OBSERVE, REFLECT, COMPLETE
            content: Phase-specific data
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "phase": phase,
            "content": content
        }
        self.sessions[session_id]["logs"].append(log_entry)

    def get_logs(self, session_id: UUID) -> List[dict]:
        """Retrieve all logs for a session."""
        return self.sessions.get(session_id, {}).get("logs", [])

    def export_as_text(self, session_id: UUID) -> str:
        """Export logs as formatted text for UI display."""
        # Format logs with colors/emojis for terminal/UI
        pass
```

**Log Entry Structure:**
```json
{
  "timestamp": "2024-11-28T10:30:00",
  "phase": "PLAN",
  "content": {
    "iteration": 1,
    "action_type": "TOOL_CALL",
    "tool": "get-user-context",
    "reasoning": "Need to understand user's current learning context"
  }
}
```

---

### Task 5: Add Agent MCP Tool
**File:** `learning-coach-mcp/src/server.py` (modify)

**Add new tool:**

```python
@mcp.tool()
async def run_agent(
    goal: str,
    user_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Run the autonomous learning coach agent.

    Args:
        goal: Natural language goal (e.g., "Help me learn about attention mechanisms")
        user_id: UUID of the user (default: DEFAULT_USER_ID)

    Returns:
        Agent result with output and execution logs

    Example:
        >>> result = await run_agent(goal="Generate my daily digest")
        >>> print(result['output'])
        >>> print(result['logs'])
    """
    from .agent.controller import AgentController, AgentConfig

    config = AgentConfig(
        max_iterations=10,
        llm_model=os.getenv("AGENT_LLM_MODEL", "gpt-4o-mini"),
    )

    controller = AgentController(config)

    result = await controller.run(
        goal=goal,
        user_id=user_id or DEFAULT_USER_ID
    )

    return {
        "output": result.output,
        "logs": result.logs,
        "iterations": result.iteration_count,
        "status": result.status
    }
```

---

### Task 6: Create Dashboard Agent View
**File:** `dashboard/views/agent.py`

**Purpose:** UI for running agent and viewing logs

**Implementation:**

```python
import streamlit as st
from datetime import datetime

def show():
    """Agent interaction view."""

    st.title("🤖 Learning Coach Agent")
    st.markdown("Autonomous agent mode - watch the reasoning unfold")

    # Agent input
    with st.form("agent_form"):
        goal = st.text_area(
            "What do you want to learn?",
            placeholder="E.g., 'Help me understand attention mechanisms' or 'Generate my daily digest'",
            height=100
        )
        submit = st.form_submit_button("Run Agent", type="primary")

    if submit and goal:
        # Run agent
        with st.spinner("Agent is thinking..."):
            # Import agent controller
            from learning-coach-mcp.src.agent.controller import AgentController, AgentConfig

            config = AgentConfig(max_iterations=10)
            controller = AgentController(config)

            result = await controller.run(goal=goal, user_id=st.session_state.user_id)

        # Display results
        st.success("Agent completed!")

        # Output section
        st.markdown("### 📋 Result")
        st.markdown(result.output)

        # Logs section
        st.markdown("### 🔍 Agent Reasoning Logs")

        from components.log_viewer import render_logs
        render_logs(result.logs)
```

---

### Task 7: Create Log Viewer Component
**File:** `dashboard/components/log_viewer.py`

**Implementation:**

```python
import streamlit as st

def render_logs(logs: list):
    """Render agent logs with color coding."""

    phase_colors = {
        "SENSE": "🔵",
        "PLAN": "🟡",
        "ACT": "🟢",
        "OBSERVE": "🟣",
        "REFLECT": "🟠",
        "COMPLETE": "✅"
    }

    for i, log in enumerate(logs):
        phase = log["phase"]
        emoji = phase_colors.get(phase, "⚪")

        with st.expander(f"{emoji} {phase} - {log['timestamp']}", expanded=(i < 3)):
            st.json(log["content"])
```

---

### Task 8: Update Dashboard Navigation
**File:** `dashboard/app.py` (modify)

**Add agent page to navigation:**

```python
# In sidebar navigation
page = st.radio(
    "Navigation",
    ["📚 Today's Digest", "🤖 Agent Mode", "⚙️ Settings"],  # Added Agent Mode
    label_visibility="collapsed"
)

# In main content area
elif page == "🤖 Agent Mode":
    from views import agent
    agent.show()
```

---

## 1.4 Implementation Order

### Week 1: Core Infrastructure
1. **Day 1-2:** Agent Controller skeleton + Logger
   - Create files, set up basic structure
   - Implement logging functionality
   - Test in-memory log storage

2. **Day 3-4:** Tool Registry + Planning Prompts
   - Define all tool schemas
   - Write prompt templates
   - Test LLM prompt formatting

3. **Day 5-6:** Agent Loop Implementation
   - Implement SENSE, PLAN, ACT, OBSERVE, REFLECT methods
   - Integrate with existing MCP tools
   - Test end-to-end loop with simple goal

### Week 2: Integration & UI
4. **Day 1-2:** MCP Tool Integration
   - Add `run_agent` tool to server.py
   - Test via MCP protocol
   - Verify with Claude Desktop

5. **Day 3-4:** Dashboard Views
   - Create agent.py view
   - Create log_viewer.py component
   - Test UI rendering

6. **Day 5:** Testing & Refinement
   - End-to-end testing
   - Bug fixes
   - Documentation

---

## 1.5 Success Criteria (MVP)

### Functional Requirements
- [ ] Agent accepts natural language goals via MCP tool
- [ ] Agent executes SENSE → PLAN → ACT → OBSERVE → REFLECT loop
- [ ] Agent calls existing MCP tools based on LLM decisions
- [ ] Agent completes within max iterations (10)
- [ ] Agent returns structured output with logs

### Quality Requirements
- [ ] Logs show clear reasoning at each step
- [ ] Agent successfully generates daily digest
- [ ] Agent adapts based on REFLECT phase
- [ ] Dashboard displays logs in real-time
- [ ] No crashes or infinite loops

### Demo Scenario
**Input:** "Generate my daily digest"

**Expected Behavior:**
1. SENSE: Query user context → Week 7, Topics: Attention, Transformers
2. PLAN: Decision → Call get-user-context tool
3. ACT: Execute tool
4. OBSERVE: Log result
5. REFLECT: Evaluate → "Got user context, ready to search content"
6. PLAN: Decision → Call search-content with query about transformers
7. ACT: Execute search
8. OBSERVE: Log results
9. REFLECT: "Found 5 articles, quality looks good"
10. PLAN: Decision → Call generate-digest
11. ACT: Generate digest
12. OBSERVE: Log digest
13. REFLECT: "Digest generated successfully, goal achieved"
14. COMPLETE: Return digest + logs

---

## 1.6 Configuration

### Environment Variables
```bash
# Existing
SUPABASE_URL=...
SUPABASE_KEY=...
OPENAI_API_KEY=...
ANTHROPIC_API_KEY=...
DEFAULT_USER_ID=...

# New for Agent
AGENT_MAX_ITERATIONS=10
AGENT_LLM_MODEL=gpt-4o-mini
AGENT_LOG_LEVEL=INFO
```

### Agent Config Class
```python
@dataclass
class AgentConfig:
    max_iterations: int = 10
    llm_model: str = "gpt-4o-mini"
    temperature: float = 0.3
    log_level: str = "INFO"
```

---

## 1.7 Testing Strategy

### Unit Tests
- `test_agent_controller.py`: Test each method in isolation
- `test_tool_registry.py`: Verify tool schemas and execution
- `test_logger.py`: Check log formatting and storage

### Integration Tests
- `test_agent_e2e.py`: Full agent run with mock LLM
- `test_agent_with_real_llm.py`: Test with actual OpenAI API

### Manual Tests
- Run via MCP: Claude Desktop integration
- Run via Dashboard: Streamlit UI
- Verify logs are readable and useful

---

## 1.8 Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|---------|-----------|
| LLM returns invalid JSON | Medium | High | JSON validator with retry logic |
| Agent loops infinitely | Low | High | Max iterations + timeout |
| Tool execution fails | Medium | Medium | Graceful error handling + continue loop |
| Logs too verbose | Low | Low | Configurable log level |
| OpenAI rate limits | Medium | Medium | Exponential backoff + caching |

---

## 1.9 Future Phases (Post-MVP)

### Phase 2: Personalization
- Enhanced user context with preferences and struggles
- Reflection prompt evaluates fit for THIS user
- Agent rejects content and re-searches if needed

### Phase 3: Safety Gates
- Approval system for destructive actions
- Rate limiting
- Safety checks before tool execution

### Phase 4: Adaptive Difficulty (Student Lab)
- Quiz evaluation tool
- Difficulty adjustment logic
- Student-facing skeleton code

---

## 1.10 Files to Create/Modify

### New Files (8)
1. `learning-coach-mcp/src/agent/__init__.py`
2. `learning-coach-mcp/src/agent/controller.py`
3. `learning-coach-mcp/src/agent/tools.py`
4. `learning-coach-mcp/src/agent/logger.py`
5. `learning-coach-mcp/src/agent/prompts/system.txt`
6. `learning-coach-mcp/src/agent/prompts/planning.txt`
7. `learning-coach-mcp/src/agent/prompts/reflection.txt`
8. `dashboard/views/agent.py`
9. `dashboard/components/log_viewer.py`

### Modified Files (2)
1. `learning-coach-mcp/src/server.py` (add run_agent tool)
2. `dashboard/app.py` (add agent navigation)

---

## 1.11 Estimated Effort

| Task | Estimated Time |
|------|---------------|
| Agent Controller | 6 hours |
| Tool Registry | 3 hours |
| Planning Prompts | 2 hours |
| Logger | 2 hours |
| MCP Integration | 1 hour |
| Dashboard Views | 4 hours |
| Testing | 4 hours |
| Documentation | 2 hours |
| **Total** | **24 hours (3 days)** |

---

## Next Steps

1. **Get approval** on this plan
2. **Start with Day 1-2:** Agent Controller + Logger
3. **Test incrementally** after each component
4. **Document** as we build

---

## Appendix: Key Design Decisions

### Why MVP First?
- Validates core concept before investing in advanced features
- Delivers working demo quickly
- Reduces risk of over-engineering

### Why In-Memory Logs?
- Simpler for MVP
- No database migration needed yet
- Can add persistence in Phase 2

### Why gpt-4o-mini?
- Fast response times
- Low cost for iteration
- Sufficient for planning/reflection tasks
- Can upgrade to GPT-4 or Claude later

### Why Existing Tools?
- Reuses battle-tested MCP tools
- No need to rewrite RAG pipeline
- Faster development
- Easy to add new tools later
