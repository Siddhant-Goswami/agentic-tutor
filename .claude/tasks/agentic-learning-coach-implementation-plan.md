# Implementation Plan: AI Learning Coach → Agentic Learning Coach
Converting the MCP Workflow into an Autonomous Agent System

## Executive Summary
**Current State:** MCP server with 5 predefined tools, Streamlit dashboard, RAG pipeline, Supabase vector store. User or Claude explicitly calls each tool—the system follows a fixed workflow.

**Target State:** Autonomous agent that receives a learning goal, reasons about the user's context, decides which tools to call, reflects on results, and adapts its approach—all visible through detailed logging.

**Key Constraint:** Must be implementable by students in a 45-60 minute lab with ≤3 files to modify.

## Part 1: Architecture Transformation

### 1.1 Current Architecture (Workflow)
```
┌─────────────────────────────────────────────────────────────┐
│                     CURRENT FLOW                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  User/Claude: "Generate my daily digest"                    │
│       │                                                     │
│       ▼                                                     │
│  MCP Server receives tool call                              │
│       │                                                     │
│       ▼                                                     │
│  generate_daily_digest() executes:                          │
│       │                                                     │
│       ├── fetch_learning_context()      ← Fixed Step 1      │
│       ├── retrieve_relevant_content()   ← Fixed Step 2      │
│       ├── synthesize_insights()         ← Fixed Step 3      │
│       ├── evaluate_quality()            ← Fixed Step 4      │
│       └── store_and_return()            ← Fixed Step 5      │
│                                                             │
│  PATH IS PREDETERMINED BY CODE                              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Limitations:**
- Cannot adapt to user's stated struggles
- Cannot reject and re-search if content doesn't fit
- Cannot personalize based on learning preferences
- No reasoning visible—just input → output

### 1.2 Target Architecture (Agent)
```
┌─────────────────────────────────────────────────────────────┐
│                     TARGET FLOW                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  User: "Help me understand attention mechanisms.            │
│         I've read the basics but the math confuses me."     │
│       │                                                     │
│       ▼                                                     │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              AGENT CONTROLLER                        │   │
│  │                                                      │   │
│  │  SENSE: Query user history, preferences, struggles   │   │
│  │    → "User prefers visual content, struggles with    │   │
│  │       matrix notation"                               │   │
│  │                                                      │   │
│  │  PLAN: LLM decides next action                       │   │
│  │    → "Search for visual explanations of attention"   │   │
│  │                                                      │   │
│  │  ACT: Execute via existing MCP tools                 │   │
│  │    → search_content(query="attention visual...")     │   │
│  │                                                      │   │
│  │  OBSERVE: Capture result                             │   │
│  │    → "Found 5 articles, but 2 are math-heavy papers" │   │
│  │                                                      │   │
│  │  REFLECT: LLM evaluates for THIS user                │   │
│  │    → "Papers won't work for this user. Search again" │   │
│  │                                                      │   │
│  │  [LOOP until goal achieved or max iterations]        │   │
│  │                                                      │   │
│  │  COMPLETE: Return personalized digest + quiz         │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  PATH IS DETERMINED BY LLM REASONING                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 1.3 Component Mapping

| Current Component | Transformation | New Role |
|------------------|----------------|----------|
| server.py (MCP tools) | Keep as-is | MCP tool endpoints (can optionally call agent) |
| rag/ pipeline | Keep as-is | Called by agent via tools |
| Supabase vector store | Extend | Add agent memory tables |
| Streamlit dashboard | Extend | Add agent view (imports agent directly) |
| — (new) | Create | **Standalone Agent Module** (top-level) |
| — (new) | Create | Agent Controller |
| — (new) | Create | Planning Prompts |
| — (new) | Create | Safety Gates |
| — (new) | Create | Logger/Audit System |

## Part 2: New Components Specification

### 2.1 Agent Controller
**Location:** `agent/controller.py` (top-level module, NOT inside MCP)

**Purpose:** Orchestrate the Sense → Plan → Act → Observe → Reflect loop

**Responsibilities:**
- Accept user goal and user_id
- Initialize context from user history
- Run reasoning loop until completion or max iterations
- Manage safety gates for dangerous operations
- Return structured result with full audit trail

**Key Methods:**

| Method | Input | Output | Purpose |
|--------|-------|--------|---------|
| run(goal, user_id) | Goal string, user ID | AgentResult | Main entry point |
| _sense() | — | Context dict | Gather user history, preferences |
| _plan() | — | Plan object | LLM decides next action |
| _act(plan) | Plan | Tool result | Execute via MCP |
| _observe(result) | Tool result | — | Append to context |
| _reflect(plan, result) | Plan + result | Reflection string | LLM evaluates quality |
| _requires_approval(plan) | Plan | Boolean | Safety check |

**Configuration:**
- `max_iterations`: 10 (prevents infinite loops)
- `approval_required_tools`: List of tools needing human confirmation
- `llm_model`: Model for planning/reflection (configurable)

### 2.2 Planning Prompt System
**Location:** `agent/prompts/` (top-level module)

**Files:**

| File | Purpose |
|------|---------|
| planning.txt | Main prompt for deciding next action |
| reflection.txt | Prompt for evaluating tool results |
| system.txt | Agent persona and constraints |

**Planning Prompt Requirements:**

The planning prompt must:
- Describe agent's role (personalized learning coach)
- List available tools with schemas
- Define output format (JSON with action type)
- Include current context (user history, conversation so far)
- Emphasize personalization considerations:
  - User's current knowledge level
  - User's stated struggles
  - User's learning preferences
  - Content user has already seen

**Action Types:**

| Action | Schema | When Used |
|--------|--------|-----------|
| TOOL_CALL | {tool, args, reasoning} | Need to call a tool |
| COMPLETE | {output: {digest, quiz, note}, reasoning} | Goal achieved |
| CLARIFY | {question, reasoning} | Need more info from user |

**Reflection Prompt Requirements:**

The reflection prompt must ask:
- Does this result match the user's level?
- Does it fit their stated preferences?
- Does it avoid content they've seen?
- Is quality sufficient, or should we search differently?
- Are we ready to complete?

### 2.3 Tool Registry Extension
**Location:** `agent/tools.py` (top-level module)

**Purpose:** Define tools available to the agent with schemas

**Important:** This is NOT an MCP tool registry. This is the agent's internal abstraction layer for calling various services (RAG, database, etc.)

**Tools to Expose (wrapping existing MCP tools):**

| Tool Name | Maps To | Input Schema | Output Schema |
|-----------|---------|--------------|---------------|
| get-user-context | sync_bootcamp_progress + DB query | {user_id} | {week, topics, difficulty, preferences, struggles, history} |
| search-content | RAG pipeline query | {query, k, filters} | {results: [{title, snippet, source, difficulty}]} |
| search-past-insights | search_past_insights | {query, limit, date_range} | {insights: [...]} |
| write-journal | New DB write | {user_id, title, content} | {entry_id, success} |
| generate-quiz | Extract from generate_daily_digest | {topic, difficulty, num_questions} | {questions: [...]} |
| evaluate-quiz | New | {user_answers, correct_answers, topics} | {score, weak_topics, adjustment} |
| update-user-profile | DB write | {user_id, updates} | {success} |

**New Tool: evaluate-quiz**

**Purpose:** Enable adaptive difficulty (core lab exercise)

**Input:**
- user_answers: List of user's answers
- correct_answers: List of correct answers
- question_topics: List of topics per question

**Output:**
- score: Float 0-1
- weak_topics: Topics user got wrong
- strong_topics: Topics user got right
- difficulty_adjustment: "easier" | "same" | "harder"
- recommendation: Personalized next-step suggestion

### 2.4 Safety Gate System
**Location:** `learning-coach-mcp/src/agent/safety.py`

**Purpose:** Prevent destructive actions without human approval

**Dangerous Operations:**
- Bulk delete (journal entries, progress, sources)
- Reset user profile/progress
- Share data externally
- Modify difficulty by more than 1 level at once

**Safety Check Flow:**
1. Before executing any tool, check if it requires approval
2. If yes, pause agent and return approval request
3. Wait for human confirmation
4. If denied, add "action denied" to context and continue loop
5. If approved, execute and continue

**Rate Limiting:**
- Max 10 tool calls per session
- If exceeded, return partial result with explanation

### 2.5 Logger/Audit System
**Location:** `learning-coach-mcp/src/agent/logger.py`

**Purpose:** Record every step for visibility and debugging

**Log Entry Schema:**

| Field | Type | Description |
|-------|------|-------------|
| timestamp | ISO datetime | When it happened |
| session_id | UUID | Groups entries for one run |
| iteration | Integer | Loop iteration number |
| phase | Enum | SENSE, PLAN, ACT, OBSERVE, REFLECT, COMPLETE |
| content | Object | Phase-specific data |
| duration_ms | Integer | How long this step took |

**Storage:**
- In-memory for demo (list of entries)
- Optional: Supabase table for persistence

**Export Formats:**
- JSON (for programmatic access)
- Formatted text (for UI display)
- Markdown (for sharing/reports)

### 2.6 Database Extensions
**Location:** `database/migrations/005_agent_tables.sql`

**New Tables:**

**Table: agent_sessions**

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| user_id | UUID | FK to users |
| goal | TEXT | Original user request |
| started_at | TIMESTAMP | Session start |
| completed_at | TIMESTAMP | Session end (null if running) |
| status | ENUM | running, completed, failed, cancelled |
| result | JSONB | Final output |
| tool_call_count | INTEGER | Total tools called |

**Table: agent_logs**

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| session_id | UUID | FK to agent_sessions |
| iteration | INTEGER | Loop iteration |
| phase | TEXT | SENSE, PLAN, ACT, etc. |
| content | JSONB | Phase-specific data |
| timestamp | TIMESTAMP | When logged |

**Table: user_difficulty_history**

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| user_id | UUID | FK to users |
| topic | TEXT | Topic area |
| old_level | TEXT | Previous difficulty |
| new_level | TEXT | New difficulty |
| reason | TEXT | Why changed |
| quiz_score | FLOAT | Score that triggered change |
| changed_at | TIMESTAMP | When changed |

### 2.7 Streamlit Dashboard Extensions
**Location:** `dashboard/views/agent.py`

**New UI Components:**

1. **Agent Mode Toggle:**
   - Switch between "Workflow Mode" (current) and "Agent Mode" (new)
   - Default to Agent Mode for lecture

2. **Agent Input Panel:**
   - Text area for natural language goal
   - "Run Agent" button
   - Status indicator (idle, running, waiting for approval)

3. **Live Logs Panel:**
   - Real-time display of agent reasoning
   - Color-coded by phase (SENSE=blue, PLAN=yellow, ACT=green, etc.)
   - Expandable detail for each entry
   - Timestamp and duration for each step

4. **Approval Modal:**
   - Appears when agent needs human confirmation
   - Shows: What action, why it's flagged, consequences
   - Buttons: Approve, Deny, Cancel Session

5. **Result Panel:**
   - Final digest display
   - Quiz display with answer submission
   - Personalization notes
   - Quality metrics

## Part 3: Implementation Phases

### Phase 1: Core Agent Loop (Pre-Lecture Preparation)
**Goal:** Working agent controller that students can observe

**Deliverables:**
- controller.py with full loop implementation
- prompts/ directory with planning and reflection prompts
- logger.py with in-memory logging
- tools.py wrapping existing MCP tools
- Basic Streamlit integration showing logs

**Verification:**
- Agent can accept: "Generate my learning digest"
- Agent logs show: SENSE → PLAN → ACT → OBSERVE → REFLECT → COMPLETE
- Result matches or exceeds workflow version quality

### Phase 2: Personalization Logic (Pre-Lecture Preparation)
**Goal:** Agent actually personalizes based on user context

**Deliverables:**
- Enhanced get-user-context tool returning preferences and struggles
- Planning prompt that considers personalization
- Reflection prompt that evaluates fit for THIS user
- Demo showing agent rejecting content and re-searching

**Verification:**
- User with "struggles with math" gets visual content prioritized
- User who has seen content X doesn't get X again
- Logs show reflection: "This content is too advanced for this user"

### Phase 3: Safety Gates (Pre-Lecture Preparation)
**Goal:** Demonstrate responsible agent design

**Deliverables:**
- safety.py with approval checks
- Streamlit approval modal
- Rate limiting logic
- Demo scenario: user asks to "clear all my progress"

**Verification:**
- Destructive request triggers approval modal
- Denied action continues gracefully
- Max iterations enforced

### Phase 4: Quiz Evaluation Skeleton (Lab Preparation)
**Goal:** Provide skeleton for students to complete

**Deliverables:**
- tools/quiz_evaluator.py with function signature and docstring
- Empty implementation with TODO markers
- Test data for verification
- Updated planning prompt mentioning new tool

**Verification:**
- File exists and imports without error
- Students can fill in logic
- When complete, agent calls tool and updates difficulty

## Part 4: Lab Exercise Specification

### Lab Goal
Add adaptive difficulty to the Learning Coach agent.

### Pre-Lab State (What Students Receive)
```
Files provided:
├── controller.py          ✓ Complete - agent loop works
├── prompts/
│   ├── planning.txt       ✓ Complete - but missing quiz-evaluator
│   └── reflection.txt     ✓ Complete
├── tools/
│   └── quiz_evaluator.py  ◐ Skeleton - students complete this
├── logger.py              ✓ Complete
└── safety.py              ✓ Complete
```

### Student Tasks

**Task 1: Implement Quiz Evaluator (15 min)**

File: `tools/quiz_evaluator.py`

Students implement:
- Compare user answers to correct answers
- Identify which topics were wrong
- Calculate score
- Determine difficulty adjustment based on score thresholds
- Generate personalized recommendation

Scoring logic to implement:
- Score < 0.4 → "easier"
- Score 0.4-0.7 → "same"
- Score > 0.7 → "harder"

**Task 2: Update Planning Prompt (10 min)**

File: `prompts/planning.txt`

Students add:
- New tool definition for quiz-evaluator
- Instructions for when to call it (after quiz answers received)
- Instructions to update user profile based on result

**Task 3: Add Post-Quiz Flow (15 min)**

File: `controller.py` (specific section marked)

Students add:
- Detection of quiz answer submission in user input
- Logic to trigger quiz evaluation
- Memory update with new difficulty level
- Logging of difficulty adjustment

### Success Criteria
Students verify success by:
1. Running agent with: "Help me learn about attention"
2. Agent generates quiz
3. Submitting answers: "My answers: A, C, B"
4. Observing in logs: [REFLECT] User scored 0.33, adjusting difficulty to easier
5. Running agent again
6. Observing: Agent searches for easier content

### Test Script Provided
```python
# test_adaptive_difficulty.py
# Runs the following sequence automatically:

Request 1: "Help me learn about transformers at intermediate level"
→ Expect: Digest + Quiz generated

Request 2: "My quiz answers: A, C, B" (intentionally 1/3 correct)
→ Expect: quiz-evaluator called, difficulty adjustment logged

Request 3: "Continue helping me learn"
→ Expect: Agent searches for easier content, logs show awareness of weak topics
```

## Part 5: Demo Scenarios

### Demo 1: Basic Agent Flow (Opening Demo)
**Input:** "Update me on tool calling this week at intermediate level"

**Expected Behavior:**
1. SENSE: Query user context
2. PLAN: Search for tool calling content
3. ACT: Call search-content
4. OBSERVE: Got 5 results
5. REFLECT: Results look good for intermediate
6. PLAN: Generate digest
7. COMPLETE: Return digest + quiz

**Teaching Point:** Show the loop, explain each phase

### Demo 2: Personalization in Action
**Input:** "Help me understand attention mechanisms. I've read the basics but the math confuses me."

**Expected Behavior:**
1. SENSE: User prefers visual, struggles with math
2. PLAN: Search for visual attention explanations
3. ACT: Call search-content
4. OBSERVE: Got results including math-heavy paper
5. REFLECT: "Paper won't work for this user, need more visual content"
6. PLAN: Search again with visual focus
7. ACT: Call search-content (refined query)
8. OBSERVE: Got visual explanations
9. REFLECT: "These match user preferences"
10. COMPLETE: Return personalized digest

**Teaching Point:** Agent adapted based on user context—workflow wouldn't

### Demo 3: Safety Gate (Danger Zone Demo)
**Input:** "I want to start fresh. Clear all my learning history and progress."

**Expected Behavior:**
1. SENSE: Query user context (has 12 weeks of progress)
2. PLAN: Call clear-user-progress
3. SAFETY GATE TRIGGERED
4. Display: "This will delete 47 journal entries and 12 weeks of progress. Confirm?"
5. If denied: OBSERVE: "Action denied by user"
6. REFLECT: "User didn't want full clear. Should I ask what they meant?"
7. PLAN: Ask clarifying question
8. COMPLETE: "Did you want to reset just one topic, or start fresh on this week's content?"

**Teaching Point:** Agents need guardrails—autonomy requires wisdom

### Demo 4: Adaptive Difficulty (Post-Lab Demo)
**Input Sequence:**
1. "Generate a quiz on attention mechanisms"
2. "My answers: A, C, B" (1/3 correct)
3. "What should I learn next?"

**Expected Behavior:**
1. Quiz generated at current difficulty
2. Quiz evaluated: score 0.33, weak topics identified
3. Difficulty adjusted to "easier"
4. Next request: Agent searches for easier content on weak topics

**Teaching Point:** Students just built this—celebrate their work

## Part 6: File Structure

### Final Project Structure
```
ai-learning-coach/
├── README.md
│
├── agent/                               # NEW: Standalone agent module
│   ├── __init__.py
│   ├── controller.py                    # Main agent loop
│   ├── tools.py                         # Tool registry for agent
│   ├── logger.py                        # Audit logging
│   ├── prompts/
│   │   ├── planning.txt                 # Planning prompt
│   │   ├── reflection.txt               # Reflection prompt
│   │   └── system.txt                   # Agent persona
│   └── README.md                        # Agent documentation
│
├── learning-coach-mcp/                  # MCP server (agent-free)
│   ├── src/
│   │   ├── server.py                    # MCP tools (can call agent)
│   │   ├── rag/                         # RAG pipeline
│   │   ├── ingestion/                   # Content ingestion
│   │   ├── tools/                       # Source manager, feedback
│   │   └── utils/                       # Database utilities
│   │
│   ├── tests/
│   │   └── test_agent/                  # Agent tests (optional)
│   │       ├── test_controller.py
│   │       ├── test_adaptive_difficulty.py
│   │       └── test_safety.py
│   │
│   └── pyproject.toml
│
├── dashboard/
│   ├── app.py
│   ├── views/
│   │   ├── home.py
│   │   ├── settings.py
│   │   └── agent.py                     # Imports from agent/
│   └── components/
│       └── log_viewer.py                # Live log display
│
├── database/
│   └── migrations/
│       ├── 001_initial_schema.sql
│       ├── 003_insert_test_data...
│       ├── 004_add_test_user_rls...
│       └── 005_agent_tables.sql         # NEW: Agent tables
│
├── test_agent.py                        # Tests agent module
└── test_e2e.py                          # End-to-end tests
```

## Part 7: Dependencies

### New Python Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| — | — | No new dependencies required |

**Note:** The agent system uses existing dependencies:
- OpenAI/Anthropic SDK for LLM calls
- Supabase client for database
- Streamlit for UI
- Existing MCP framework

### Configuration Additions

**New Environment Variables:**

| Variable | Default | Purpose |
|----------|---------|---------|
| AGENT_MAX_ITERATIONS | 10 | Max loop iterations |
| AGENT_LLM_MODEL | gpt-4o-mini | Model for planning/reflection |
| AGENT_ENABLE_SAFETY | true | Enable safety gates |
| AGENT_LOG_LEVEL | INFO | Logging verbosity |

## Part 8: Success Metrics

### Technical Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Agent completes basic request | 100% | Automated test |
| Agent calls ≤6 tools per request | 90% | Log analysis |
| Personalization visible in logs | 100% | Manual review |
| Safety gates trigger on dangerous input | 100% | Automated test |
| Quiz evaluator adjusts difficulty | 100% | Lab test script |

### Lecture Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Demo runs without errors | 100% | Pre-lecture testing |
| Students understand workflow→agent distinction | 80% | Poll after breakpoint exercise |
| Students complete lab exercise | 80% | Working test output |
| Students can explain agent loop | 70% | Closing discussion |

### Student Lab Metrics

| Metric | Target | Verification |
|--------|--------|--------------|
| Quiz evaluator implemented correctly | 80% | Test script passes |
| Planning prompt updated | 90% | Tool appears in agent plan |
| Difficulty adjustment logged | 80% | Log contains adjustment entry |
| End-to-end adaptive flow works | 70% | Three-request test passes |

## Part 9: Risk Mitigation

### Technical Risks

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| LLM returns invalid JSON | Medium | JSON validator with retry + fallback |
| Agent loops infinitely | Low | Max iterations + timeout |
| Database connection issues | Low | Graceful fallback to in-memory |
| OpenAI rate limits | Medium | Exponential backoff + caching |

### Lecture Risks

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Demo fails during lecture | Low | Pre-tested scenarios, backup recordings |
| Students can't complete lab | Medium | Solution branch available, pair programming |
| Lab takes longer than expected | Medium | Stretch goals are optional, core task scoped tight |
| Students don't understand agent vs workflow | Low | Multiple touch points, breakpoint exercise |

## Part 10: Timeline

### Pre-Lecture Preparation (Instructor)

| Task | Time Required | Deadline |
|------|--------------|----------|
| Implement agent controller | 4 hours | Lecture - 7 days |
| Implement prompts and tools | 2 hours | Lecture - 6 days |
| Implement safety gates | 2 hours | Lecture - 5 days |
| Implement Streamlit extensions | 3 hours | Lecture - 4 days |
| Create quiz evaluator skeleton | 1 hour | Lecture - 3 days |
| Write lab instructions | 2 hours | Lecture - 3 days |
| End-to-end testing | 2 hours | Lecture - 2 days |
| Dry run demos | 1 hour | Lecture - 1 day |

### During Lecture

| Phase | Duration | Materials |
|-------|----------|-----------|
| Hook + Definition | 20 min | Study plan exercise, slides |
| Demo + Deconstruction | 15 min | Running agent, logs visible |
| Breakpoint Exercise | 12 min | Current workflow code |
| Danger Zone | 8 min | Safety demo scenario |
| Connection + Build | 35 min | Architecture diagram, code walkthrough |
| Lab | 45 min | Skeleton files, test script |
| Closing | 5 min | — |

## Appendix: Lab Handout

### AI Learning Coach Agent Lab

**Goal:** Make the Learning Coach agent adapt quiz difficulty based on user performance.

#### Setup (5 min)
```bash
cd ai-learning-coach
git checkout agent-lab-start
./start-demo.sh
```

Verify: Streamlit opens, agent mode available

#### Your Task

**Step 1: Implement Quiz Evaluator (15 min)**

Open: `learning-coach-mcp/src/agent/tools/quiz_evaluator.py`

Find the function `evaluate_quiz_performance()` and implement:
- Compare answers
- Identify weak/strong topics
- Calculate score
- Determine adjustment

**Step 2: Update Planning Prompt (10 min)**

Open: `learning-coach-mcp/src/agent/prompts/planning.txt`

Add the quiz-evaluator tool definition and instructions for when to use it.

**Step 3: Test (15 min)**

Run: `python tests/test_adaptive_difficulty.py`

Observe logs. Verify difficulty adjustment appears.

#### Success Criteria
- [ ] Test script passes
- [ ] Logs show: [REFLECT] User scored X, adjusting to Y
- [ ] Second request shows agent searching for adjusted difficulty content

#### Stretch Goals
- Track difficulty history over time
- Add "struggling" detector that triggers encouragement
- Make adjustment gradual (5 levels instead of 3)
