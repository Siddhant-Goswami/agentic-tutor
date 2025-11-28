# Autonomous Learning Coach Agent

This is a **standalone autonomous agent module** that implements the SENSE → PLAN → ACT → OBSERVE → REFLECT loop for personalized learning coaching.

## Architecture Principles

1. **Standalone**: This module has NO dependency on MCP or any other part of the system
2. **Reusable**: Can be imported and used by dashboard, tests, CLI, or any other client
3. **Self-contained**: Contains all agent logic, prompts, and tool registry

## Components

- `controller.py` - Main agent loop implementation (SENSE → PLAN → ACT → OBSERVE → REFLECT)
- `tools.py` - Tool registry and execution (wraps RAG, database, integrations)
- `logger.py` - Agent audit logging and session tracking
- `prompts/` - LLM prompts for planning, reflection, and system instructions

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

# Access results
print(result.output)        # Final output
print(result.logs)          # Execution logs
print(result.status)        # "completed", "timeout", "failed", etc.
print(result.iteration_count)  # Number of iterations
```

## Agent Loop

The agent executes an autonomous reasoning loop:

1. **SENSE** - Gather user context (learning progress, preferences, history)
2. **PLAN** - LLM decides next action based on goal and context
3. **ACT** - Execute the planned action (call tool, search content, etc.)
4. **OBSERVE** - Capture and log the execution result
5. **REFLECT** - LLM evaluates quality and determines if goal is achieved
6. **Repeat** until goal is achieved or max iterations reached

## Available Tools

The agent can call these tools during execution:

- `get-user-context` - Fetch user's learning progress, topics, difficulty, preferences
- `search-content` - Semantic search for relevant learning content
- `generate-digest` - Create personalized learning digest with insights and quiz
- `search-past-insights` - Search through previously delivered content
- `sync-progress` - Sync latest learning context from bootcamp platform

## Clients Using This Module

This agent module is used by:

- **Dashboard** (`dashboard/views/agent.py`) - Interactive Streamlit UI
- **MCP Server** (`learning-coach-mcp/src/server.py`) - Optional MCP tool wrapper
- **Tests** (`test_agent.py`) - Automated testing
- **CLI** (future) - Command-line interface

## NOT Part of MCP

**Important**: This agent module is **NOT part of the MCP server implementation**.

The MCP server (`learning-coach-mcp/`) is just **ONE client** that happens to expose the agent as a tool via the `run_agent` MCP tool. The agent can be used completely independently of MCP.

## Architecture Diagram

```
┌──────────────┐         ┌──────────────┐
│  Dashboard   │         │  MCP Server  │
│ (Streamlit)  │         │  (FastMCP)   │
└──────┬───────┘         └──────┬───────┘
       │                        │
       │         ┌──────────────┘
       │         │
       ▼         ▼
┌─────────────────────────────┐
│   Agent Controller          │  ← You are here
│   (Standalone Module)       │
└──────────┬──────────────────┘
           │
           ▼
┌─────────────────────────────┐
│   Shared Services           │
│   - Database (Supabase)     │
│   - RAG Pipeline            │
│   - LLM Clients             │
└─────────────────────────────┘
```

## Dependencies

This module depends on:

- `openai` - For LLM planning and reflection
- `supabase` (via utils) - For database access
- Shared utilities from `learning-coach-mcp/src/utils/`

The agent does **NOT** depend on:

- MCP server
- Dashboard
- Any MCP-specific code

## Development

To modify the agent:

1. **Controller logic**: Edit `controller.py`
2. **Tool definitions**: Edit `tools.py`
3. **Planning behavior**: Edit `prompts/planning.txt`
4. **Reflection behavior**: Edit `prompts/reflection.txt`
5. **Agent persona**: Edit `prompts/system.txt`

## Testing

Run the agent test:

```bash
python test_agent.py
```

This will execute the agent with test goals and display the reasoning logs.

## Future Enhancements

Planned improvements:

- Safety gates for destructive operations
- Adaptive difficulty based on quiz performance
- Multi-turn conversations with clarification
- Memory persistence across sessions
- Tool approval workflow for sensitive operations
