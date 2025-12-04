# Codebase Guide for AI Learning Coach

**Welcome to the codebase!** 👋

This guide will walk you through the entire codebase, explaining how everything works together. Perfect for new contributors or anyone wanting to understand the system.

---

## 📚 Table of Contents

- [Project Overview](#project-overview)
- [Directory Structure](#directory-structure)
- [Core Components](#core-components)
- [RAG Pipeline Deep Dive](#rag-pipeline-deep-dive)
- [Autonomous Agent](#autonomous-agent)
- [Data Flow](#data-flow)
- [Key Files Explained](#key-files-explained)
- [Common Tasks](#common-tasks)

---

## 🎯 Project Overview

### What Does This Project Do?

The AI Learning Coach is an **autonomous agent** that:
1. **Retrieves** relevant learning content from a vector database
2. **Generates** personalized insights using LLMs
3. **Evaluates** quality using RAGAS metrics
4. **Delivers** content through multiple interfaces (dashboard, MCP, API)

### The Big Picture

```
User Request
    ↓
Agent (thinks & plans)
    ↓
RAG Pipeline (search & synthesize)
    ↓
Database (vector search)
    ↓
LLM (generate insights)
    ↓
RAGAS (evaluate quality)
    ↓
Result to User
```

---

## 📁 Directory Structure

```
agentic-tutor/
├── agent/                          # 🤖 Autonomous agent
│   ├── controller.py              # Main SENSE-PLAN-ACT loop
│   ├── tools.py                   # Tool registry (wraps RAG, DB)
│   ├── logger.py                  # Execution logging
│   └── prompts/                   # LLM prompts for planning
│
├── learning-coach-mcp/            # 🧠 RAG & MCP Server
│   └── src/
│       ├── rag/                   # RAG System (Phase 3 refactored!)
│       │   ├── core/             # Base classes & LLM client
│       │   │   ├── llm_client.py        # Unified OpenAI/Anthropic client
│       │   │   ├── base_synthesizer.py  # Protocol for synthesizers
│       │   │   └── base_evaluator.py    # Protocol for evaluators
│       │   │
│       │   ├── synthesis/        # Content synthesis
│       │   │   ├── synthesizer.py       # Main synthesis logic
│       │   │   ├── prompt_builder.py    # Template-based prompts
│       │   │   ├── parsers.py           # JSON parsing & validation
│       │   │   └── templates/           # Prompt templates (.txt)
│       │   │
│       │   ├── evaluation/       # Quality evaluation
│       │   │   ├── evaluator.py         # RAGAS integration
│       │   │   └── metrics.py           # Quality metrics
│       │   │
│       │   └── retrieval/        # Content retrieval
│       │       ├── retriever.py         # Vector search
│       │       ├── query_builder.py     # Query enhancement
│       │       └── insight_search.py    # Past insights search
│       │
│       ├── server.py             # MCP server (FastMCP)
│       └── utils/                # Shared utilities
│           └── supabase_client.py   # Database client
│
├── dashboard/                     # 🖥️ Streamlit UI
│   ├── app.py                    # Main app entry point
│   ├── views/                    # Pages
│   │   ├── home.py              # Today's digest
│   │   ├── agent.py             # Agent playground
│   │   └── settings.py          # Configuration
│   └── digest_api.py            # RAG API wrapper
│
├── database/                      # 🗄️ Database
│   └── migrations/               # SQL migrations
│       ├── 001_initial_schema.sql
│       ├── 003_insert_test_data_with_rls_bypass.sql
│       └── 004_add_test_user_rls_policies.sql
│
├── tests/                         # 🧪 Tests (64 tests!)
│   └── unit/rag/                # RAG unit tests
│       ├── core/                # LLM client tests
│       ├── synthesis/           # Synthesis tests
│       └── evaluation/          # Evaluation tests
│
└── docs/                          # 📖 Documentation
    ├── CODEBASE_GUIDE.md        # This file!
    ├── ARCHITECTURE.md
    └── USER_GUIDE.md
```

---

## 🧩 Core Components

### 1. Autonomous Agent (`agent/`)

**What it does:** Implements the SENSE → PLAN → ACT → OBSERVE → REFLECT loop

**Key File:** `agent/controller.py`

```python
# High-level flow
async def run(goal: str, user_id: str):
    while not goal_achieved and iterations < max_iterations:
        # SENSE: Gather context
        context = await self._sense(user_id, goal)

        # PLAN: Decide next action
        plan = await self._plan(context, goal)

        # ACT: Execute the action
        result = await self._act(plan)

        # OBSERVE: Log the result
        await self._observe(result)

        # REFLECT: Evaluate progress
        achieved = await self._reflect(goal, result)

    return final_result
```

**Read this first if:** You want to understand the autonomous behavior

**Key Concepts:**
- **Tool Registry**: Available actions (search, generate, etc.)
- **LLM Planning**: GPT-4 decides next steps
- **Reflection**: Quality checks and progress evaluation

---

### 2. RAG Pipeline (`learning-coach-mcp/src/rag/`)

**What it does:** Retrieves and synthesizes personalized learning content

#### 2a. Core Module (`rag/core/`)

**Purpose:** Base classes and LLM abstraction

**Key File:** `llm_client.py`

```python
# Unified LLM client - works with OpenAI or Anthropic
class LLMClient:
    def __init__(self, provider: LLMProvider, model: str, api_key: str):
        if provider == LLMProvider.OPENAI:
            self.client = AsyncOpenAI(api_key=api_key)
        elif provider == LLMProvider.ANTHROPIC:
            self.client = AsyncAnthropic(api_key=api_key)

    async def generate(self, system: str, user: str) -> str:
        """Generate completion (same API for both providers!)"""
        if self.provider == LLMProvider.OPENAI:
            return await self._generate_openai(system, user)
        else:
            return await self._generate_anthropic(system, user)
```

**Why this matters:**
- Switch between OpenAI/Anthropic with 2 lines of code
- Single interface for all LLM operations
- Easy to test (just mock the client!)

#### 2b. Synthesis Module (`rag/synthesis/`)

**Purpose:** Generate insights from retrieved content

**Key Files:**
1. **`prompt_builder.py`** - Builds prompts from templates
2. **`parsers.py`** - Parses and validates LLM responses
3. **`synthesizer.py`** - Main synthesis logic

**Flow:**

```python
# 1. Build prompts from templates
system_prompt, user_prompt = prompt_builder.build_synthesis_prompt(
    context_text=chunks,
    user_context={"week": 7, "topics": ["transformers"]},
    query="Explain attention mechanisms",
)

# 2. Call LLM
response = await llm_client.generate(system_prompt, user_prompt)

# 3. Parse response
insights = parser.parse_insights(response)

# 4. Enrich with source info
insights = enrich_insights(insights, chunks)
```

**Template Example:** (`templates/synthesis_user.txt`)
```txt
You are teaching a student in week {current_week} of their AI bootcamp.
Current topics: {topics}
Difficulty level: {difficulty}

Query: {query}

Context:
{context_text}

Generate {num_insights} educational insights...
```

**Why templates?** Non-engineers can improve prompts without touching code!

#### 2c. Evaluation Module (`rag/evaluation/`)

**Purpose:** Measure quality using RAGAS

**Key Files:**
1. **`metrics.py`** - RAGAS integration
2. **`evaluator.py`** - Quality gates

```python
# Evaluate generated insights
scores = await evaluator.evaluate_digest(
    query="Explain attention",
    insights=[...],
    retrieved_chunks=[...],
)

# Returns:
{
    "faithfulness": 0.87,      # Factually accurate?
    "context_precision": 0.82,  # Relevant chunks used?
    "context_recall": 0.78,     # All important info included?
    "average": 0.82
}

# Check quality gate
if evaluator.passes_quality_gate(scores):
    print("✅ High quality!")
```

#### 2d. Retrieval Module (`rag/retrieval/`)

**Purpose:** Semantic search using vector embeddings

**Key File:** `retriever.py`

```python
# Vector search flow
class VectorRetriever:
    async def retrieve(self, query: str, user_id: str, limit: int = 10):
        # 1. Generate query embedding
        embedding = await self.embed_query(query)  # OpenAI

        # 2. Search vector database (Supabase pgvector)
        results = await self.supabase.rpc(
            "match_content_embeddings",
            {
                "query_embedding": embedding,
                "match_threshold": 0.7,  # Similarity threshold
                "match_count": limit,
            }
        )

        # 3. Return relevant chunks
        return self._format_results(results)
```

**How vector search works:**
1. **Ingestion**: Content → Chunks → Embeddings → Store in DB
2. **Query**: User question → Embedding → Find similar embeddings
3. **Results**: Most similar chunks returned

---

### 3. MCP Server (`learning-coach-mcp/src/server.py`)

**What it does:** Exposes agent as MCP tools for Claude Desktop

```python
# FastMCP tool definition
@mcp.tool()
async def run_agent(
    goal: str,
    user_id: str = DEFAULT_USER_ID,
    max_iterations: int = 10,
) -> str:
    """
    Run autonomous learning coach agent.

    Args:
        goal: What the user wants to achieve
        user_id: User identifier
        max_iterations: Max agent iterations

    Returns:
        Agent execution result with logs
    """
    controller = AgentController(...)
    result = await controller.run(goal, user_id)
    return format_result(result)
```

**What's MCP?** Model Context Protocol - lets Claude Desktop use external tools

---

### 4. Dashboard (`dashboard/`)

**What it does:** Web UI for the learning coach

**Key Files:**
1. **`app.py`** - Main Streamlit app
2. **`views/home.py`** - Today's digest page
3. **`views/agent.py`** - Agent playground
4. **`views/settings.py`** - Configuration

**Flow:**
```python
# In dashboard/views/agent.py
if st.button("Run Agent"):
    # 1. Create agent controller
    controller = AgentController(...)

    # 2. Run agent (streaming logs to UI)
    with st.container():
        for log in controller.run_streaming(goal, user_id):
            st.write(log)  # Real-time updates!

    # 3. Show final result
    st.success(result.output)
```

---

## 🔄 Data Flow

### End-to-End Example: "Generate my daily digest"

```
1. USER INPUT
   └─ Dashboard: User clicks "Generate Digest"
   └─ Agent receives goal: "Generate daily learning digest"

2. AGENT SENSE
   └─ Calls tool: get-user-context(user_id)
   └─ Fetches: {week: 7, topics: ["transformers"], difficulty: "intermediate"}

3. AGENT PLAN (LLM)
   └─ GPT-4: "I need to search for relevant content about transformers"
   └─ Next action: search-content

4. AGENT ACT: SEARCH
   └─ Query Builder: Enhances "transformers" → "transformer attention mechanisms week 7"
   └─ Vector Retriever: Generates embedding, searches pgvector
   └─ Returns: 10 most relevant content chunks

5. AGENT PLAN (LLM)
   └─ GPT-4: "Now I have content, I should generate insights"
   └─ Next action: generate-digest

6. AGENT ACT: SYNTHESIZE
   └─ Prompt Builder: Loads templates, builds prompts
   └─ LLM Client: Calls OpenAI GPT-4o-mini
   └─ Parser: Extracts and validates 7 insights
   └─ Enricher: Adds source attribution

7. AGENT ACT: EVALUATE
   └─ RAGAS Evaluator: Measures quality
   └─ Scores: {faithfulness: 0.87, precision: 0.82, recall: 0.78}
   └─ Quality gate: PASS ✅

8. AGENT REFLECT (LLM)
   └─ GPT-4: "Goal achieved! Generated 7 high-quality insights"
   └─ Final state: COMPLETED

9. AGENT OBSERVE
   └─ Logger: Saves execution log to database
   └─ Returns: Final digest with insights + quality scores

10. USER OUTPUT
    └─ Dashboard: Displays 7 insights with quality badge
    └─ User can read, provide feedback, save to history
```

---

## 📄 Key Files Explained

### Must-Read Files

#### 1. `agent/controller.py` (500 lines)

**Purpose:** Main agent loop

**Key Methods:**
- `run()` - Execute agent with goal
- `_sense()` - Gather context
- `_plan()` - LLM decides next action
- `_act()` - Execute tool
- `_reflect()` - Evaluate progress

**When to modify:** Adding new agent capabilities

#### 2. `src/rag/core/llm_client.py` (200 lines)

**Purpose:** Unified LLM interface

**Key Methods:**
- `generate()` - Text completion
- `generate_structured()` - JSON mode (OpenAI only)
- `get_model_info()` - Configuration details

**When to modify:** Adding new LLM provider

#### 3. `src/rag/synthesis/synthesizer.py` (230 lines)

**Purpose:** Core synthesis logic

**Key Methods:**
- `synthesize_insights()` - Main synthesis
- `validate_input()` - Input validation
- `_enrich_insights()` - Add source info

**When to modify:** Changing how insights are generated

#### 4. `src/rag/retrieval/retriever.py` (365 lines)

**Purpose:** Vector search

**Key Methods:**
- `retrieve()` - Semantic search
- `embed_query()` - Generate embeddings
- `_format_results()` - Process results

**When to modify:** Changing search behavior

---

## 🛠️ Common Tasks

### Task 1: Add a New Agent Tool

```python
# 1. Define tool in agent/tools.py
class AgentTools:
    async def my_new_tool(self, arg1: str, arg2: int) -> Dict[str, Any]:
        """
        Description of what this tool does.

        Args:
            arg1: First argument
            arg2: Second argument

        Returns:
            Result dictionary
        """
        # Implementation
        return {"result": "success"}

# 2. Register in AVAILABLE_TOOLS
AVAILABLE_TOOLS = [
    {
        "name": "my-new-tool",
        "description": "What it does",
        "parameters": {
            "arg1": {"type": "string", "description": "..."},
            "arg2": {"type": "integer", "description": "..."},
        },
    },
    # ... other tools
]

# 3. Add to tool execution in controller.py
async def _act(self, plan):
    if plan.tool == "my-new-tool":
        return await self.tools.my_new_tool(plan.args["arg1"], plan.args["arg2"])
```

### Task 2: Modify Synthesis Prompts

```bash
# 1. Edit template file (NO code changes needed!)
vim src/rag/synthesis/templates/synthesis_user.txt

# 2. Test changes
cd learning-coach-mcp
python -m src.rag.synthesis.synthesizer  # If you have a test script

# 3. Templates are cached, clear cache if needed
# Restart the application
```

### Task 3: Add RAGAS Metric

```python
# In src/rag/evaluation/metrics.py
async def _evaluate_custom_metric(self, sample):
    """Add your custom metric."""
    try:
        score = await self.custom_metric.single_turn_ascore(sample)
        return float(score)
    except Exception as e:
        logger.warning(f"Custom metric failed: {e}")
        return 0.75  # Fallback

# Add to evaluate_all()
async def evaluate_all(self, query, response, contexts):
    tasks = [
        self._evaluate_faithfulness(sample),
        self._evaluate_context_precision(sample),
        self._evaluate_custom_metric(sample),  # NEW!
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    return {
        "faithfulness": results[0],
        "context_precision": results[1],
        "custom": results[2],  # NEW!
        "average": sum(results) / len(results),
    }
```

### Task 4: Add Test

```python
# tests/unit/rag/synthesis/test_synthesizer.py
@pytest.mark.asyncio
async def test_my_new_feature():
    """Test description."""
    # Arrange
    mock_llm = Mock()
    mock_llm.get_model_info.return_value = {"model": "test"}

    synthesizer = EducationalSynthesizer(llm_client=mock_llm)

    # Act
    result = await synthesizer.my_new_method()

    # Assert
    assert result is not None
    assert result["status"] == "success"
```

---

## 🎓 Learning Path

### If You're New to the Codebase:

**Day 1: Understand the Flow**
1. Read README.md
2. Run the dashboard, try generating a digest
3. Watch the agent logs to see the steps

**Day 2: Explore RAG**
1. Read `src/rag/README.md` (if exists)
2. Trace through `synthesizer.py`
3. Look at prompt templates

**Day 3: Understand Agent**
1. Read `agent/README.md`
2. Trace through `controller.py`
3. Try modifying a prompt

**Day 4: Run Tests**
1. Run test suite: `pytest`
2. Read test files to understand behavior
3. Try adding a simple test

**Day 5: Make a Small Change**
1. Fix a typo in documentation
2. Add a comment to clarify code
3. Submit your first PR!

---

## 🔍 Where to Find Things

**Looking for:**
- **How synthesis works?** → `src/rag/synthesis/synthesizer.py`
- **How agent plans?** → `agent/controller.py` → `_plan()`
- **Prompt templates?** → `src/rag/synthesis/templates/`
- **How to add tools?** → `agent/tools.py`
- **Database schema?** → `database/migrations/001_initial_schema.sql`
- **How to evaluate quality?** → `src/rag/evaluation/evaluator.py`
- **Tests?** → `tests/unit/rag/`
- **Dashboard pages?** → `dashboard/views/`

---

## 🆘 Still Confused?

**Don't worry!** This is a complex system. Here's what to do:

1. **Start small** - Pick one component to understand first
2. **Use debugger** - Step through code with breakpoints
3. **Add print statements** - See what data looks like
4. **Read tests** - They show how code is meant to be used
5. **Ask questions** - Open an issue or discussion

**Remember:** Everyone was a beginner once. Take your time, and don't hesitate to ask for help!

---

**Happy coding! 🚀**
