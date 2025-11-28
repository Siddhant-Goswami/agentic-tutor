# Agent-MCP Separation Refactoring Plan

## Problem Statement

Currently, the **agent controller module is located inside the MCP source directory** (`learning-coach-mcp/src/agent/`), creating architectural confusion and tight coupling:

1. The agent is physically nested inside MCP but is being imported directly by dashboard and tests
2. The agent controller logic is conceptually separate from MCP but not architecturally separate
3. Import paths are confusing: `from agent.controller import AgentController` works from different contexts
4. The MCP server exposes agent as a tool, creating circular dependency concerns

## Desired Architecture

The agent controller should be a **completely separate, standalone module** that:

1. Lives at the top level of the project structure
2. Has NO dependency on MCP
3. Can be used independently by dashboard, tests, and other clients
4. MCP server is just ONE client that can optionally invoke the agent

```
┌─────────────────────────────────────────────────────────────┐
│                   DESIRED ARCHITECTURE                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────────┐         ┌──────────────────┐         │
│  │   Dashboard      │         │   MCP Server     │         │
│  │   (Streamlit)    │         │   (FastMCP)      │         │
│  └────────┬─────────┘         └────────┬─────────┘         │
│           │                            │                   │
│           │         ┌──────────────────┘                   │
│           │         │                                      │
│           ▼         ▼                                      │
│  ┌─────────────────────────────────┐                      │
│  │   Agent Controller (Standalone)  │                      │
│  │   - controller.py                │                      │
│  │   - tools.py (registry)          │                      │
│  │   - logger.py                    │                      │
│  │   - prompts/                     │                      │
│  └─────────────────┬────────────────┘                      │
│                    │                                       │
│                    ▼                                       │
│  ┌─────────────────────────────────┐                      │
│  │   Shared Services                │                      │
│  │   - Database (utils/db.py)       │                      │
│  │   - RAG Pipeline                 │                      │
│  │   - LLM Clients                  │                      │
│  └─────────────────────────────────┘                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘

KEY PRINCIPLE: Agent has NO knowledge of MCP. MCP knows about Agent.
```

## Refactoring Steps

### Phase 1: Create Standalone Agent Module

**Action**: Move agent from `learning-coach-mcp/src/agent/` to `agent/`

**New Structure**:
```
agentic-tutor/
├── agent/                          # NEW: Standalone agent module
│   ├── __init__.py
│   ├── controller.py               # Moved from learning-coach-mcp/src/agent/
│   ├── tools.py                    # Moved from learning-coach-mcp/src/agent/
│   ├── logger.py                   # Moved from learning-coach-mcp/src/agent/
│   ├── prompts/                    # Moved from learning-coach-mcp/src/agent/prompts/
│   │   ├── planning.txt
│   │   ├── reflection.txt
│   │   └── system.txt
│   └── README.md                   # NEW: Document the agent module
│
├── learning-coach-mcp/             # MCP Server (no agent inside)
│   ├── src/
│   │   ├── server.py               # MCP tools (can optionally call agent)
│   │   ├── rag/                    # RAG pipeline
│   │   ├── ingestion/              # Content ingestion
│   │   ├── tools/                  # Source manager, feedback handler
│   │   └── utils/                  # Database utilities
│   └── pyproject.toml
│
├── dashboard/                      # Streamlit dashboard
│   ├── app.py
│   ├── views/
│   │   └── agent.py                # Imports from top-level agent module
│   └── components/
│
└── shared/                         # NEW: Shared utilities (optional)
    └── utils/
        └── db.py                   # Shared database client
```

**Files to Move**:
1. `learning-coach-mcp/src/agent/controller.py` → `agent/controller.py`
2. `learning-coach-mcp/src/agent/tools.py` → `agent/tools.py`
3. `learning-coach-mcp/src/agent/logger.py` → `agent/logger.py`
4. `learning-coach-mcp/src/agent/prompts/` → `agent/prompts/`

**Reasoning**:
- Agent becomes a first-class module at the project root
- Clear ownership: agent/ is independent, learning-coach-mcp/ is MCP-specific
- No nested dependencies

### Phase 2: Update Import Paths

**Action**: Update all imports to reference the new standalone agent module

**Files to Update**:

1. **dashboard/views/agent.py** (line 177)
   ```python
   # OLD
   from agent.controller import AgentController, AgentConfig

   # NEW
   import sys
   from pathlib import Path
   project_root = Path(__file__).parent.parent.parent
   sys.path.insert(0, str(project_root))

   from agent.controller import AgentController, AgentConfig
   ```

2. **test_agent.py** (line 26)
   ```python
   # OLD
   sys.path.insert(0, str(src_path))
   sys.path.insert(0, str(learning_coach_path))
   from agent.controller import AgentController, AgentConfig

   # NEW
   sys.path.insert(0, str(project_root))
   from agent.controller import AgentController, AgentConfig
   ```

3. **learning-coach-mcp/src/server.py** (line 336)
   ```python
   # OLD
   from agent.controller import AgentController, AgentConfig

   # NEW
   import sys
   from pathlib import Path
   project_root = Path(__file__).parent.parent.parent
   sys.path.insert(0, str(project_root))

   from agent.controller import AgentController, AgentConfig
   ```

4. **agent/controller.py** (lines 15-16)
   ```python
   # OLD
   from .logger import AgentLogger
   from .tools import ToolRegistry

   # NEW (no change needed - relative imports still work)
   from .logger import AgentLogger
   from .tools import ToolRegistry
   ```

5. **agent/tools.py** (lines 219, 263, 302, etc.)
   ```python
   # OLD
   from utils.db import get_supabase_client

   # NEW
   import sys
   from pathlib import Path
   project_root = Path(__file__).parent.parent
   sys.path.insert(0, str(project_root / "learning-coach-mcp" / "src"))

   from utils.db import get_supabase_client
   ```

**Reasoning**:
- All imports point to the standalone agent module
- Clear dependency hierarchy: Dashboard → Agent → Shared Utils

### Phase 3: Clean Up MCP Server

**Action**: Update MCP server to be a clean client of the agent

**File**: `learning-coach-mcp/src/server.py`

**Changes**:

1. Make the `run_agent` tool import explicit and document it as optional
   ```python
   @mcp.tool()
   async def run_agent(
       goal: str,
       user_id: Optional[str] = None,
   ) -> Dict[str, Any]:
       """
       Run the autonomous learning coach agent.

       NOTE: This tool invokes the standalone agent module.
       The agent is NOT part of MCP - MCP just provides a convenient
       way to call the agent from Claude.

       ...
       """
       try:
           # Import from standalone agent module
           import sys
           from pathlib import Path
           project_root = Path(__file__).parent.parent.parent
           sys.path.insert(0, str(project_root))

           from agent.controller import AgentController, AgentConfig

           # ... rest of implementation
   ```

2. Add clear documentation that MCP can work WITHOUT agent
   ```python
   # ============================================================================
   # MCP TOOLS
   # ============================================================================

   # NOTE: The agent-related tool (run_agent) is OPTIONAL and imports
   # the standalone agent module. All other MCP tools work independently.
   ```

**Reasoning**:
- Makes it explicit that agent is external to MCP
- MCP server documents its dependency on agent
- Clear separation of concerns

### Phase 4: Update Agent Module to Remove MCP Dependencies

**Action**: Ensure agent has NO imports or references to MCP

**File**: `agent/tools.py`

**Current Issue**: ToolRegistry directly imports and uses services that might be considered "MCP utilities"

**Solution**: Make ToolRegistry accept injected dependencies

```python
class ToolRegistry:
    """
    Registry of tools available to the autonomous agent.

    The registry wraps existing functionality (RAG, database, integrations)
    and exposes them as tools the agent can call.

    NOTE: This is NOT an MCP tool registry. This is the agent's internal
    tool abstraction layer.
    """

    def __init__(
        self,
        supabase_url: str,
        supabase_key: str,
        openai_api_key: str,
        anthropic_api_key: Optional[str] = None,
    ):
        """
        Initialize tool registry.

        Args:
            supabase_url: Supabase project URL
            supabase_key: Supabase API key
            openai_api_key: OpenAI API key
            anthropic_api_key: Anthropic API key (optional)
        """
        # Store credentials
        self.supabase_url = supabase_url
        self.supabase_key = supabase_key
        self.openai_api_key = openai_api_key
        self.anthropic_api_key = anthropic_api_key

        # Initialize tool definitions
        self.tools = {
            "get-user-context": self._get_user_context_schema(),
            # ... other tools
        }
```

**Reasoning**:
- Agent module is completely standalone
- No references to MCP anywhere in agent code
- Clean dependency injection pattern

### Phase 5: Update Documentation

**Action**: Create clear documentation for the separation

**New File**: `agent/README.md`

```markdown
# Autonomous Learning Coach Agent

This is a **standalone autonomous agent module** that implements the SENSE → PLAN → ACT → OBSERVE → REFLECT loop for personalized learning coaching.

## Architecture Principles

1. **Standalone**: This module has NO dependency on MCP or any other part of the system
2. **Reusable**: Can be imported and used by dashboard, tests, CLI, or any other client
3. **Self-contained**: Contains all agent logic, prompts, and tool registry

## Components

- `controller.py` - Main agent loop implementation
- `tools.py` - Tool registry and execution
- `logger.py` - Agent audit logging
- `prompts/` - LLM prompts for planning and reflection

## Usage

```python
from agent.controller import AgentController, AgentConfig

# Configure agent
config = AgentConfig(
    max_iterations=10,
    llm_model="gpt-4o-mini",
    temperature=0.3,
)

# Initialize controller
controller = AgentController(
    config=config,
    supabase_url="https://your-project.supabase.co",
    supabase_key="your-key",
    openai_api_key="your-key",
)

# Run agent
result = await controller.run(
    goal="Generate my daily learning digest",
    user_id="user-uuid",
)

print(result.output)
print(result.logs)
```

## Clients

This agent module is used by:
- **Dashboard** (`dashboard/views/agent.py`) - Interactive UI
- **MCP Server** (`learning-coach-mcp/src/server.py`) - Optional MCP tool wrapper
- **Tests** (`test_agent.py`) - Automated testing
- **CLI** (future) - Command-line interface

## NOT Part of MCP

**Important**: This agent module is NOT part of the MCP server implementation.
The MCP server (`learning-coach-mcp/`) is just ONE client that happens to
expose the agent as a tool. The agent can be used completely independently
of MCP.
```

**File**: Update `learning-coach-mcp/README.md` or main `README.md`

Add section:
```markdown
## Architecture

This project consists of several independent modules:

### 1. Agent Module (`agent/`)
Autonomous learning coach agent with SENSE → PLAN → ACT → OBSERVE → REFLECT loop.
**Standalone module** - no dependencies on other project components.

### 2. MCP Server (`learning-coach-mcp/`)
FastMCP server providing tools for:
- Daily digest generation
- Source management
- Feedback handling
- Bootcamp progress sync
- (Optional) Agent invocation via `run_agent` tool

### 3. Dashboard (`dashboard/`)
Streamlit web UI for interacting with the learning coach.
Can use agent directly OR through MCP.

### 4. Database (`database/`)
Supabase schema and migrations.

### Dependency Flow

```
Dashboard ──────┐
                ├──→ Agent Module ──→ Shared Utils (DB, RAG)
MCP Server ─────┘
```

**Key Principle**: Agent is independent. Dashboard and MCP are both clients of Agent.
```

**Reasoning**:
- Clear documentation of architecture
- Explicit statement that agent is standalone
- Usage examples for different clients

### Phase 6: Update Implementation Plan

**Action**: Update the main implementation plan to reflect the new architecture

**File**: `.claude/tasks/agentic-learning-coach-implementation-plan.md`

**Changes Needed**:

1. Update **Section 1.3: Component Mapping** (line 85-94)
   ```markdown
   | Current Component | Transformation | New Role |
   |------------------|----------------|----------|
   | server.py (MCP tools) | Keep as-is | MCP tool endpoints |
   | rag/ pipeline | Keep as-is | Called by agent via tools |
   | Supabase vector store | Extend | Add agent memory tables |
   | Streamlit dashboard | Extend | Add agent view (direct import) |
   | — (new) | Create | **Standalone Agent Module** |
   | — (new) | Create | Agent Controller |
   | — (new) | Create | Planning Prompts |
   | — (new) | Create | Safety Gates (future) |
   | — (new) | Create | Logger/Audit System |
   ```

2. Update **Section 2.1: Agent Controller** (line 99)
   ```markdown
   **Location:** `agent/controller.py` (top-level module, NOT inside MCP)
   ```

3. Update **Section 2.2: Planning Prompt System** (line 128)
   ```markdown
   **Location:** `agent/prompts/` (top-level module)
   ```

4. Update **Section 2.3: Tool Registry Extension** (line 169)
   ```markdown
   **Location:** `agent/tools.py` (top-level module)

   **Important**: This is NOT an MCP tool registry. This is the agent's
   internal abstraction layer for calling various services (RAG, database, etc.)
   ```

5. Update **Section 6: File Structure** (line 524)
   ```markdown
   ### Final Project Structure
   ```
   ai-learning-coach/
   ├── README.md
   │
   ├── agent/                          # NEW: Standalone agent module
   │   ├── __init__.py
   │   ├── controller.py               # Main agent loop
   │   ├── tools.py                    # Tool registry for agent
   │   ├── logger.py                   # Audit logging
   │   ├── prompts/
   │   │   ├── planning.txt
   │   │   ├── reflection.txt
   │   │   └── system.txt
   │   └── README.md
   │
   ├── learning-coach-mcp/             # MCP server (agent-free)
   │   ├── src/
   │   │   ├── server.py               # MCP tools (can call agent)
   │   │   ├── rag/                    # RAG pipeline
   │   │   ├── ingestion/              # Content ingestion
   │   │   ├── tools/                  # Source manager, feedback
   │   │   └── utils/                  # Database utilities
   │   │
   │   ├── tests/
   │   └── pyproject.toml
   │
   ├── dashboard/
   │   ├── app.py
   │   ├── views/
   │   │   ├── home.py
   │   │   ├── settings.py
   │   │   └── agent.py                # Imports from agent/
   │   └── components/
   │       └── log_viewer.py
   │
   ├── database/
   │   └── migrations/
   │
   ├── test_agent.py                   # Tests agent module
   └── test_e2e.py                     # End-to-end tests
   ```

**Reasoning**:
- Implementation plan now reflects clean architecture
- No confusion about where agent lives
- Clear that MCP is just one client

## Testing Strategy

After refactoring, verify:

1. **Agent works standalone**
   ```bash
   python test_agent.py
   ```
   Should run without errors using new import paths

2. **Dashboard can use agent**
   ```bash
   cd dashboard && streamlit run app.py
   ```
   Navigate to Agent view, run a goal

3. **MCP can call agent (optional)**
   ```bash
   # Test MCP server with run_agent tool
   ```

4. **No circular dependencies**
   ```bash
   # Verify clean dependency tree
   # Agent should NOT import from MCP
   # MCP CAN import from Agent
   ```

## Migration Checklist

- [ ] Create `agent/` directory at project root
- [ ] Move `controller.py` to `agent/`
- [ ] Move `tools.py` to `agent/`
- [ ] Move `logger.py` to `agent/`
- [ ] Move `prompts/` directory to `agent/`
- [ ] Create `agent/__init__.py`
- [ ] Create `agent/README.md`
- [ ] Update imports in `dashboard/views/agent.py`
- [ ] Update imports in `test_agent.py`
- [ ] Update imports in `learning-coach-mcp/src/server.py`
- [ ] Update imports in `agent/tools.py` for utils
- [ ] Remove old `learning-coach-mcp/src/agent/` directory
- [ ] Update `.claude/tasks/agentic-learning-coach-implementation-plan.md`
- [ ] Update main `README.md` with architecture diagram
- [ ] Test: `python test_agent.py` works
- [ ] Test: Dashboard agent view works
- [ ] Test: MCP `run_agent` tool works (if needed)
- [ ] Commit changes with clear message

## Benefits of This Refactoring

1. **Clear Separation of Concerns**
   - Agent logic is completely separate from MCP
   - MCP is just one way to invoke the agent
   - Dashboard can use agent without MCP

2. **Better Maintainability**
   - Agent module can be developed independently
   - Changes to MCP don't affect agent
   - Clear ownership of each module

3. **Improved Testability**
   - Agent can be tested in isolation
   - No need to start MCP server to test agent
   - Mocking is easier with clean boundaries

4. **Flexibility**
   - Agent can be used by CLI, API, or any other client
   - MCP becomes optional, not required
   - Easier to add new clients in the future

5. **Clearer Mental Model**
   - Agent is a standalone autonomous system
   - MCP provides tools (source management, etc.)
   - Dashboard provides UI
   - All three are peers, not nested

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| Import path issues | Test thoroughly after each move |
| Circular dependencies | Verify agent has NO MCP imports |
| Breaking existing code | Update all import paths systematically |
| Confusion about structure | Document clearly in README files |

## Timeline

- **Phase 1-2** (Move and update imports): 30 minutes
- **Phase 3-4** (Clean up MCP, remove dependencies): 20 minutes
- **Phase 5-6** (Documentation updates): 20 minutes
- **Testing**: 20 minutes

**Total**: ~90 minutes

## Success Criteria

- [ ] Agent module lives at `agent/` (not inside MCP)
- [ ] All imports reference `agent/` correctly
- [ ] Agent has ZERO imports from MCP
- [ ] MCP server clearly documents agent as optional dependency
- [ ] Tests pass: `python test_agent.py`
- [ ] Dashboard works: `streamlit run dashboard/app.py`
- [ ] Documentation clearly explains architecture
- [ ] No circular dependencies between modules
