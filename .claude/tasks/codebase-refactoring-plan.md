# Codebase Refactoring Plan: Python Best Practices 2025

**Project:** Agentic Learning Coach
**Created:** 2025-12-02
**Status:** Draft - Awaiting Approval

## Executive Summary

This plan outlines a comprehensive refactoring strategy to transform the Agentic Learning Coach codebase into a modular, maintainable, and scalable Python application following 2025 best practices. The refactoring will address code organization, reduce file sizes, improve reusability, add type safety, and implement proper design patterns.

**Key Objectives:**
- Break down monolithic files (>400 lines) into focused modules
- Implement proper separation of concerns
- Add comprehensive type hints
- Introduce dependency injection
- Create reusable abstractions
- Improve testability and error handling
- Reorganize project structure

---

## Current State Analysis

### Files Requiring Refactoring (By Priority)

| File | Lines | Issues | Priority |
|------|-------|--------|----------|
| `agent/tools.py` | 754 | Monolithic tool registry, mixed schemas and execution | **HIGH** |
| `agent/controller.py` | 736 | Long agent loop, multiple responsibilities | **HIGH** |
| `learning-coach-mcp/src/ui/daily_digest.py` | 630 | Inline HTML generation, should use templates | **HIGH** |
| `dashboard/views/agent.py` | 567 | Mixed UI and business logic | **MEDIUM** |
| `agent/research_planner.py` | 508 | Complex planning logic, needs breakdown | **MEDIUM** |
| `learning-coach-mcp/src/rag/synthesizer.py` | 468 | Prompt generation mixed with LLM calls | **MEDIUM** |
| `learning-coach-mcp/src/server.py` | 446 | Multiple MCP tools in one file | **MEDIUM** |
| `learning-coach-mcp/src/rag/digest_generator.py` | 417 | Complex orchestration logic | **MEDIUM** |
| `learning-coach-mcp/src/tools/source_manager.py` | 409 | Source management mixed concerns | **LOW** |
| `learning-coach-mcp/src/rag/evaluator.py` | 408 | Evaluation logic + prompt handling | **LOW** |

### Key Problems Identified

1. **Monolithic Files**
   - Single files handling multiple responsibilities
   - 754-line tool registry with schemas + execution
   - 630-line HTML generation file

2. **Missing Abstractions**
   - No base classes for tools, prompts, or UI components
   - Repeated patterns (error handling, logging, validation)
   - Direct instantiation everywhere (tight coupling)

3. **Type Safety Issues**
   - Inconsistent or missing type hints
   - Heavy use of `Dict[str, Any]` instead of typed models
   - No runtime validation

4. **Poor Separation of Concerns**
   - UI logic mixed with business logic
   - Data access mixed with business rules
   - Prompts hardcoded in business logic files

5. **Testing Challenges**
   - Test files scattered at project root (20+ files)
   - Difficult to mock due to tight coupling
   - No clear test organization

6. **Configuration Management**
   - Environment variables accessed directly
   - No centralized configuration
   - Hard to test different configurations

---

## Target Architecture

### New Directory Structure

```
agentic-tutor/
├── src/                                    # All application source code
│   ├── __init__.py
│   │
│   ├── core/                               # Shared core functionality
│   │   ├── __init__.py
│   │   ├── config.py                       # Centralized configuration
│   │   ├── exceptions.py                   # Base exception hierarchy
│   │   ├── logging.py                      # Logging configuration
│   │   ├── types.py                        # Shared type definitions
│   │   └── dependencies.py                 # Dependency injection container
│   │
│   ├── agent/                              # Agent domain (refactored)
│   │   ├── __init__.py
│   │   ├── models/                         # Agent data models
│   │   │   ├── __init__.py
│   │   │   ├── agent_config.py
│   │   │   ├── agent_result.py
│   │   │   ├── plan.py
│   │   │   └── context.py
│   │   │
│   │   ├── controllers/                    # Agent control logic
│   │   │   ├── __init__.py
│   │   │   ├── base_controller.py          # Abstract base
│   │   │   ├── agent_controller.py         # Main controller
│   │   │   ├── step_executor.py            # Step execution
│   │   │   └── workflow_manager.py         # Workflow coordination
│   │   │
│   │   ├── tools/                          # Tool implementations
│   │   │   ├── __init__.py
│   │   │   ├── base.py                     # Tool protocol/interface
│   │   │   ├── registry.py                 # Tool registration
│   │   │   ├── schemas.py                  # Tool schemas (separate!)
│   │   │   ├── user_context_tool.py
│   │   │   ├── search_tool.py
│   │   │   ├── digest_tool.py
│   │   │   ├── web_search_tool.py
│   │   │   └── coverage_analysis_tool.py
│   │   │
│   │   ├── planning/                       # Planning components
│   │   │   ├── __init__.py
│   │   │   ├── planner.py                  # Main planner
│   │   │   ├── research_planner.py
│   │   │   ├── strategies/                 # Planning strategies
│   │   │   │   ├── __init__.py
│   │   │   │   ├── base_strategy.py
│   │   │   │   ├── research_strategy.py
│   │   │   │   └── digest_strategy.py
│   │   │   └── templates/                  # Prompt templates (text files)
│   │   │       ├── planning.txt
│   │   │       ├── reflection.txt
│   │   │       └── system.txt
│   │   │
│   │   ├── logger.py                       # Agent-specific logging
│   │   ├── exceptions.py                   # Agent exceptions
│   │   └── services.py                     # Agent business logic
│   │
│   ├── rag/                                # RAG domain (refactored)
│   │   ├── __init__.py
│   │   ├── models/                         # RAG data models
│   │   │   ├── __init__.py
│   │   │   ├── chunk.py
│   │   │   ├── insight.py
│   │   │   ├── digest.py
│   │   │   └── evaluation_result.py
│   │   │
│   │   ├── retrieval/                      # Retrieval components
│   │   │   ├── __init__.py
│   │   │   ├── retriever.py
│   │   │   ├── query_builder.py
│   │   │   └── ranking.py
│   │   │
│   │   ├── synthesis/                      # Synthesis components
│   │   │   ├── __init__.py
│   │   │   ├── base_synthesizer.py
│   │   │   ├── openai_synthesizer.py       # OpenAI implementation
│   │   │   ├── anthropic_synthesizer.py    # Anthropic implementation
│   │   │   ├── prompt_builder.py           # Prompt construction
│   │   │   └── templates/                  # Prompt templates
│   │   │       ├── synthesis_system.txt
│   │   │       ├── synthesis_user.txt
│   │   │       └── stricter_system.txt
│   │   │
│   │   ├── evaluation/                     # Evaluation components
│   │   │   ├── __init__.py
│   │   │   ├── evaluator.py
│   │   │   ├── ragas_evaluator.py
│   │   │   └── metrics.py
│   │   │
│   │   ├── orchestration/                  # Digest generation
│   │   │   ├── __init__.py
│   │   │   ├── digest_generator.py
│   │   │   └── pipeline.py
│   │   │
│   │   ├── exceptions.py                   # RAG exceptions
│   │   └── services.py                     # RAG business logic
│   │
│   ├── ingestion/                          # Content ingestion (refactored)
│   │   ├── __init__.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── source.py
│   │   │   └── content.py
│   │   ├── extractors/                     # Content extraction
│   │   │   ├── __init__.py
│   │   │   ├── base_extractor.py
│   │   │   ├── rss_extractor.py
│   │   │   └── web_extractor.py
│   │   ├── processors/                     # Content processing
│   │   │   ├── __init__.py
│   │   │   ├── chunker.py
│   │   │   ├── embedder.py
│   │   │   └── cleaner.py
│   │   ├── orchestrator.py                 # Ingestion orchestration
│   │   └── exceptions.py
│   │
│   ├── database/                           # Data access layer
│   │   ├── __init__.py
│   │   ├── models/                         # Database models
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── session.py
│   │   │   ├── insight.py
│   │   │   └── source.py
│   │   │
│   │   ├── repositories/                   # Repository pattern
│   │   │   ├── __init__.py
│   │   │   ├── base_repository.py          # Abstract base
│   │   │   ├── user_repository.py
│   │   │   ├── session_repository.py
│   │   │   ├── insight_repository.py
│   │   │   └── source_repository.py
│   │   │
│   │   ├── client.py                       # Supabase client wrapper
│   │   ├── migrations/                     # SQL migrations
│   │   └── exceptions.py
│   │
│   ├── ui/                                 # UI components (refactored)
│   │   ├── __init__.py
│   │   ├── models/                         # UI data models
│   │   │   ├── __init__.py
│   │   │   └── view_models.py
│   │   │
│   │   ├── components/                     # Reusable UI components
│   │   │   ├── __init__.py
│   │   │   ├── base_component.py
│   │   │   ├── digest_viewer.py
│   │   │   ├── log_viewer.py
│   │   │   └── approval_modal.py
│   │   │
│   │   ├── templates/                      # HTML templates (Jinja2)
│   │   │   ├── daily_digest.html
│   │   │   ├── weekly_summary.html
│   │   │   ├── components/
│   │   │   │   ├── insight_card.html
│   │   │   │   ├── quality_badge.html
│   │   │   │   └── source_citation.html
│   │   │   └── base.html
│   │   │
│   │   ├── renderers/                      # Template renderers
│   │   │   ├── __init__.py
│   │   │   ├── base_renderer.py
│   │   │   ├── digest_renderer.py
│   │   │   └── summary_renderer.py
│   │   │
│   │   └── exceptions.py
│   │
│   ├── mcp/                                # MCP server (refactored)
│   │   ├── __init__.py
│   │   ├── server.py                       # Main server
│   │   ├── tools/                          # MCP tool endpoints
│   │   │   ├── __init__.py
│   │   │   ├── digest_tools.py
│   │   │   ├── search_tools.py
│   │   │   └── source_tools.py
│   │   ├── resources/                      # MCP resources
│   │   │   ├── __init__.py
│   │   │   └── ui_resources.py
│   │   └── exceptions.py
│   │
│   └── integrations/                       # External integrations
│       ├── __init__.py
│       ├── bootcamp.py                     # Bootcamp API
│       ├── tavily.py                       # Web search
│       └── exceptions.py
│
├── dashboard/                              # Streamlit dashboard
│   ├── __init__.py
│   ├── app.py                              # Main Streamlit app
│   ├── pages/                              # Dashboard pages
│   │   ├── __init__.py
│   │   ├── home.py
│   │   ├── agent.py
│   │   └── settings.py
│   ├── components/                         # Dashboard components
│   │   ├── __init__.py
│   │   ├── sidebar.py
│   │   ├── log_viewer.py
│   │   └── research_planner_ui.py
│   └── utils.py
│
├── tests/                                  # All tests organized
│   ├── __init__.py
│   ├── conftest.py                         # Pytest fixtures
│   │
│   ├── unit/                               # Unit tests
│   │   ├── __init__.py
│   │   ├── agent/
│   │   │   ├── test_controller.py
│   │   │   ├── test_tools.py
│   │   │   └── test_planner.py
│   │   ├── rag/
│   │   │   ├── test_retriever.py
│   │   │   ├── test_synthesizer.py
│   │   │   └── test_evaluator.py
│   │   └── database/
│   │       ├── test_repositories.py
│   │       └── test_models.py
│   │
│   ├── integration/                        # Integration tests
│   │   ├── __init__.py
│   │   ├── test_agent_workflow.py
│   │   ├── test_digest_generation.py
│   │   ├── test_rag_pipeline.py
│   │   └── test_approval_workflow.py
│   │
│   └── e2e/                                # End-to-end tests
│       ├── __init__.py
│       └── test_full_workflow.py
│
├── scripts/                                # Utility scripts
│   ├── run_ingestion.py
│   ├── run_migration.py
│   └── setup_test_data.py
│
├── config/                                 # Configuration files
│   ├── __init__.py
│   ├── default.py                          # Default config
│   ├── development.py                      # Dev config
│   ├── production.py                       # Prod config
│   └── test.py                             # Test config
│
├── .env.example                            # Example environment vars
├── pyproject.toml                          # Project config (Poetry/setuptools)
├── requirements.txt                        # Dependencies
├── requirements-dev.txt                    # Dev dependencies
├── mypy.ini                                # Type checking config
├── pytest.ini                              # Pytest config
└── README.md
```

---

## Phase 1: Foundation & Core Infrastructure (Week 1)

### Priority: CRITICAL
**Goal:** Establish foundation for all future refactoring

### Tasks

#### 1.1 Create Core Module Structure

**File:** `src/core/config.py`

```python
"""Centralized configuration management."""
from dataclasses import dataclass
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

@dataclass
class DatabaseConfig:
    """Database configuration."""
    url: str
    key: str
    connection_pool_size: int = 10

@dataclass
class LLMConfig:
    """LLM configuration."""
    openai_api_key: str
    anthropic_api_key: Optional[str] = None
    default_model: str = "gpt-4o-mini"
    temperature: float = 0.3
    max_tokens: int = 8000

@dataclass
class AgentConfig:
    """Agent configuration."""
    max_iterations: int = 10
    log_level: str = "INFO"
    enable_safety: bool = True

@dataclass
class AppConfig:
    """Application configuration."""
    database: DatabaseConfig
    llm: LLMConfig
    agent: AgentConfig
    default_user_id: str

    @classmethod
    def from_env(cls) -> "AppConfig":
        """Load configuration from environment variables."""
        return cls(
            database=DatabaseConfig(
                url=os.getenv("SUPABASE_URL"),
                key=os.getenv("SUPABASE_KEY"),
            ),
            llm=LLMConfig(
                openai_api_key=os.getenv("OPENAI_API_KEY"),
                anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
            ),
            agent=AgentConfig(
                max_iterations=int(os.getenv("AGENT_MAX_ITERATIONS", "10")),
                log_level=os.getenv("AGENT_LOG_LEVEL", "INFO"),
            ),
            default_user_id=os.getenv("DEFAULT_USER_ID", "00000000-0000-0000-0000-000000000001"),
        )
```

**File:** `src/core/exceptions.py`

```python
"""Base exception hierarchy for the application."""

class AgenticTutorError(Exception):
    """Base exception for all application errors."""
    pass

class ConfigurationError(AgenticTutorError):
    """Configuration-related errors."""
    pass

class DatabaseError(AgenticTutorError):
    """Database-related errors."""
    pass

class AgentError(AgenticTutorError):
    """Agent-related errors."""
    pass

class AgentExecutionError(AgentError):
    """Agent execution failed."""
    pass

class AgentTimeoutError(AgentError):
    """Agent exceeded max iterations."""
    pass

class ToolError(AgentError):
    """Tool execution error."""
    pass

class ToolNotFoundError(ToolError):
    """Tool not found in registry."""
    pass

class RAGError(AgenticTutorError):
    """RAG pipeline errors."""
    pass

class RetrievalError(RAGError):
    """Content retrieval failed."""
    pass

class SynthesisError(RAGError):
    """Insight synthesis failed."""
    pass

class EvaluationError(RAGError):
    """Quality evaluation failed."""
    pass

class IngestionError(AgenticTutorError):
    """Content ingestion errors."""
    pass

class UIError(AgenticTutorError):
    """UI rendering errors."""
    pass
```

**File:** `src/core/types.py`

```python
"""Shared type definitions."""
from typing import Dict, Any, List, Optional, Protocol, TypedDict
from datetime import datetime
from uuid import UUID

# Type aliases for clarity
UserId = str  # UUID string
SessionId = str  # UUID string
ToolName = str
JsonDict = Dict[str, Any]

# Typed dictionaries for structured data
class UserContext(TypedDict, total=False):
    """User learning context."""
    user_id: UserId
    week: int
    topics: List[str]
    difficulty: str
    preferences: Dict[str, Any]
    recent_feedback: List[Dict[str, Any]]

class ToolResult(TypedDict):
    """Result from tool execution."""
    success: bool
    data: JsonDict
    error: Optional[str]

class AgentPlan(TypedDict):
    """Agent action plan."""
    action_type: str  # "TOOL_CALL", "COMPLETE", "CLARIFY"
    tool: Optional[ToolName]
    args: Optional[JsonDict]
    reasoning: str
    output: Optional[JsonDict]

# Protocols for interfaces
class Tool(Protocol):
    """Protocol for tool implementations."""

    @property
    def name(self) -> str:
        """Tool name."""
        ...

    @property
    def description(self) -> str:
        """Tool description."""
        ...

    async def execute(self, **kwargs) -> ToolResult:
        """Execute the tool."""
        ...

class Repository(Protocol):
    """Protocol for repository implementations."""

    async def get(self, id: str) -> Optional[Any]:
        """Get entity by ID."""
        ...

    async def save(self, entity: Any) -> str:
        """Save entity and return ID."""
        ...

    async def delete(self, id: str) -> bool:
        """Delete entity."""
        ...
```

#### 1.2 Setup Type Checking

**File:** `mypy.ini`

```ini
[mypy]
python_version = 3.11
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = True
disallow_any_unimported = False
no_implicit_optional = True
warn_redundant_casts = True
warn_unused_ignores = True
warn_no_return = True
check_untyped_defs = True

# Per-module options for gradual adoption
[mypy-src.agent.*]
disallow_untyped_defs = True

[mypy-src.rag.*]
disallow_untyped_defs = False  # Enable later

[mypy-tests.*]
disallow_untyped_defs = False
```

#### 1.3 Test Infrastructure

**File:** `tests/conftest.py`

```python
"""Pytest configuration and shared fixtures."""
import pytest
import asyncio
from typing import AsyncGenerator
from src.core.config import AppConfig, DatabaseConfig, LLMConfig, AgentConfig

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def test_config() -> AppConfig:
    """Test configuration."""
    return AppConfig(
        database=DatabaseConfig(
            url="http://test-supabase.local",
            key="test-key",
        ),
        llm=LLMConfig(
            openai_api_key="test-openai-key",
            default_model="gpt-4o-mini",
        ),
        agent=AgentConfig(
            max_iterations=5,
            log_level="DEBUG",
        ),
        default_user_id="test-user-id",
    )

@pytest.fixture
def mock_supabase_client():
    """Mock Supabase client."""
    from unittest.mock import MagicMock
    return MagicMock()

@pytest.fixture
def mock_llm_client():
    """Mock LLM client."""
    from unittest.mock import AsyncMock
    return AsyncMock()
```

**Deliverables:**
- [ ] `src/core/config.py` - Centralized configuration
- [ ] `src/core/exceptions.py` - Exception hierarchy
- [ ] `src/core/types.py` - Shared type definitions
- [ ] `mypy.ini` - Type checking configuration
- [ ] `tests/conftest.py` - Test fixtures
- [ ] `pytest.ini` - Pytest configuration

**Validation:**
```bash
# Type checking works
mypy src/core/

# Tests can import core modules
pytest tests/ -v
```

---

## Phase 2: Agent System Refactoring (Week 2)

### Priority: HIGH
**Goal:** Break down monolithic agent files into focused modules

### Tasks

#### 2.1 Extract Tool Schemas

**Current:** `agent/tools.py` (754 lines) - Everything in one file

**New Structure:**

**File:** `src/agent/tools/base.py`

```python
"""Base tool interface and abstractions."""
from typing import Protocol, Dict, Any
from dataclasses import dataclass
from src.core.types import ToolResult, ToolName

@dataclass
class ToolSchema:
    """Tool schema definition."""
    name: ToolName
    description: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    requires_approval: bool = False
    example: Dict[str, Any] = None

class BaseTool(Protocol):
    """Base protocol for all tools."""

    @property
    def schema(self) -> ToolSchema:
        """Get tool schema."""
        ...

    async def execute(self, **kwargs) -> ToolResult:
        """Execute the tool."""
        ...

    async def validate_input(self, **kwargs) -> bool:
        """Validate input arguments."""
        ...
```

**File:** `src/agent/tools/schemas.py`

```python
"""Tool schema definitions (separate from execution)."""
from typing import Dict, Any
from .base import ToolSchema

def get_user_context_schema() -> ToolSchema:
    """Schema for get-user-context tool."""
    return ToolSchema(
        name="get-user-context",
        description="Get complete user learning context",
        input_schema={"user_id": "string (UUID)"},
        output_schema={
            "week": "integer (1-24)",
            "topics": "array of strings",
            "difficulty": "string",
        },
        requires_approval=False,
        example={
            "input": {"user_id": "00000000-0000-0000-0000-000000000001"},
            "output": {"week": 7, "topics": ["Attention"]},
        },
    )

# Similar functions for each tool schema
def search_content_schema() -> ToolSchema: ...
def generate_digest_schema() -> ToolSchema: ...
def web_search_schema() -> ToolSchema: ...
```

**File:** `src/agent/tools/user_context_tool.py`

```python
"""User context retrieval tool."""
import logging
from typing import Dict, Any
from .base import BaseTool, ToolSchema
from .schemas import get_user_context_schema
from src.core.types import ToolResult, UserId
from src.database.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)

class UserContextTool:
    """Tool for retrieving user learning context."""

    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    @property
    def schema(self) -> ToolSchema:
        return get_user_context_schema()

    async def execute(self, user_id: UserId) -> ToolResult:
        """Execute user context retrieval."""
        try:
            # Get user from repository
            user = await self.user_repo.get(user_id)
            if not user:
                return ToolResult(
                    success=False,
                    data={},
                    error=f"User {user_id} not found"
                )

            # Get learning context
            context = await self.user_repo.get_learning_context(user_id)

            return ToolResult(
                success=True,
                data=context,
                error=None
            )

        except Exception as e:
            logger.error(f"Error executing user-context tool: {e}")
            return ToolResult(
                success=False,
                data={},
                error=str(e)
            )

    async def validate_input(self, **kwargs) -> bool:
        """Validate input arguments."""
        return "user_id" in kwargs
```

**File:** `src/agent/tools/registry.py`

```python
"""Tool registry for managing available tools."""
import logging
from typing import Dict, Optional
from .base import BaseTool, ToolSchema
from src.core.types import ToolName, ToolResult
from src.core.exceptions import ToolNotFoundError

logger = logging.getLogger(__name__)

class ToolRegistry:
    """Registry of available tools."""

    def __init__(self):
        self._tools: Dict[ToolName, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        """Register a tool."""
        schema = tool.schema
        logger.info(f"Registering tool: {schema.name}")
        self._tools[schema.name] = tool

    def get(self, name: ToolName) -> BaseTool:
        """Get a tool by name."""
        tool = self._tools.get(name)
        if not tool:
            raise ToolNotFoundError(f"Tool not found: {name}")
        return tool

    def list_schemas(self) -> Dict[ToolName, ToolSchema]:
        """List all tool schemas."""
        return {
            name: tool.schema
            for name, tool in self._tools.items()
        }

    async def execute(self, name: ToolName, **kwargs) -> ToolResult:
        """Execute a tool by name."""
        tool = self.get(name)

        # Validate input
        if not await tool.validate_input(**kwargs):
            return ToolResult(
                success=False,
                data={},
                error=f"Invalid input for tool: {name}"
            )

        # Execute
        return await tool.execute(**kwargs)
```

#### 2.2 Refactor Agent Controller

**Current:** `agent/controller.py` (736 lines) - Single class with all logic

**New Structure:**

**File:** `src/agent/models/agent_result.py`

```python
"""Agent execution result model."""
from dataclasses import dataclass
from typing import List, Dict, Any
from src.core.types import SessionId

@dataclass
class AgentResult:
    """Result from agent execution."""
    output: Dict[str, Any]
    logs: List[Dict[str, Any]]
    iteration_count: int
    status: str  # "completed", "timeout", "failed", "needs_approval"
    session_id: SessionId

    def is_successful(self) -> bool:
        """Check if execution was successful."""
        return self.status == "completed"

    def needs_user_action(self) -> bool:
        """Check if user action is needed."""
        return self.status in ("needs_approval", "needs_clarification")
```

**File:** `src/agent/controllers/step_executor.py`

```python
"""Executes individual agent steps (SENSE, PLAN, ACT, etc.)."""
import logging
from typing import Dict, Any
from uuid import UUID

from src.core.types import UserId, AgentPlan, ToolResult
from src.agent.tools.registry import ToolRegistry
from src.agent.logger import AgentLogger

logger = logging.getLogger(__name__)

class StepExecutor:
    """Executes individual steps in the agent loop."""

    def __init__(self, tools: ToolRegistry, agent_logger: AgentLogger):
        self.tools = tools
        self.agent_logger = agent_logger

    async def sense(
        self,
        user_id: UserId,
        context: Dict[str, Any],
        session_id: UUID,
        iteration: int
    ) -> Dict[str, Any]:
        """SENSE: Gather user context."""
        logger.info("SENSE: Gathering user context")

        try:
            result = await self.tools.execute("get-user-context", user_id=user_id)

            if result["success"]:
                context["user_context"] = result["data"]
                self.agent_logger.log(
                    session_id,
                    "SENSE",
                    {"user_context": result["data"]},
                    iteration
                )
            else:
                logger.error(f"SENSE failed: {result['error']}")
                context["user_context"] = {}

            return context

        except Exception as e:
            logger.error(f"Error in SENSE: {e}", exc_info=True)
            context["user_context"] = {}
            return context

    async def act(
        self,
        plan: AgentPlan,
        session_id: UUID,
        iteration: int
    ) -> ToolResult:
        """ACT: Execute planned tool."""
        tool_name = plan.get("tool")
        args = plan.get("args", {})

        logger.info(f"ACT: Executing tool {tool_name}")

        try:
            result = await self.tools.execute(tool_name, **args)

            self.agent_logger.log(
                session_id,
                "ACT",
                {
                    "tool": tool_name,
                    "args": args,
                    "result_preview": str(result)[:200]
                },
                iteration
            )

            return result

        except Exception as e:
            logger.error(f"Error in ACT: {e}", exc_info=True)
            return ToolResult(success=False, data={}, error=str(e))

    def observe(
        self,
        plan: AgentPlan,
        result: ToolResult,
        session_id: UUID,
        iteration: int
    ) -> None:
        """OBSERVE: Log result."""
        self.agent_logger.log(
            session_id,
            "OBSERVE",
            {
                "tool": plan.get("tool"),
                "success": result["success"],
                "result_summary": str(result)[:200]
            },
            iteration
        )
```

**File:** `src/agent/controllers/agent_controller.py`

```python
"""Main agent controller (simplified)."""
import logging
import uuid
from typing import Dict, Any

from src.core.config import AgentConfig
from src.core.types import UserId
from src.agent.models.agent_result import AgentResult
from src.agent.tools.registry import ToolRegistry
from src.agent.logger import AgentLogger
from src.agent.controllers.step_executor import StepExecutor
from src.agent.planning.planner import AgentPlanner

logger = logging.getLogger(__name__)

class AgentController:
    """Autonomous agent controller."""

    def __init__(
        self,
        config: AgentConfig,
        tools: ToolRegistry,
        planner: AgentPlanner,
        agent_logger: AgentLogger
    ):
        self.config = config
        self.tools = tools
        self.planner = planner
        self.logger = agent_logger
        self.executor = StepExecutor(tools, agent_logger)

    async def run(self, goal: str, user_id: UserId) -> AgentResult:
        """
        Main agent execution loop.

        Orchestrates: SENSE → PLAN → ACT → OBSERVE → REFLECT
        """
        session_id = uuid.uuid4()
        self.logger.start_session(session_id, goal, user_id)

        iteration = 0
        context = {"user_id": user_id, "iteration_history": []}

        try:
            while iteration < self.config.max_iterations:
                iteration += 1

                # SENSE (first iteration only)
                if iteration == 1:
                    context = await self.executor.sense(
                        user_id, context, session_id, iteration
                    )

                # PLAN
                plan = await self.planner.plan(goal, context, session_id, iteration)

                # Check completion conditions
                if plan["action_type"] == "COMPLETE":
                    return self._complete_successfully(
                        plan, session_id, iteration
                    )

                if plan["action_type"] == "CLARIFY":
                    return self._request_clarification(
                        plan, session_id, iteration
                    )

                # ACT
                result = await self.executor.act(plan, session_id, iteration)

                # OBSERVE
                self.executor.observe(plan, result, session_id, iteration)

                # REFLECT
                reflection = await self.planner.reflect(
                    plan, result, goal, context, session_id, iteration
                )

                # Update context
                context["last_reflection"] = reflection
                context["iteration_history"].append({
                    "iteration": iteration,
                    "plan": plan,
                    "reflection": reflection
                })

            # Max iterations reached
            return self._timeout(context, session_id, iteration)

        except Exception as e:
            logger.error(f"Agent execution failed: {e}", exc_info=True)
            return self._fail(e, session_id, iteration)

    def _complete_successfully(
        self, plan: Dict[str, Any], session_id: uuid.UUID, iteration: int
    ) -> AgentResult:
        """Handle successful completion."""
        output = plan.get("output", {})
        self.logger.complete_session(session_id, "completed", output)

        return AgentResult(
            output=output,
            logs=self.logger.get_logs(session_id),
            iteration_count=iteration,
            status="completed",
            session_id=str(session_id)
        )

    # Similar methods for other exit conditions...
```

**Deliverables:**
- [x] `src/agent/tools/base.py` - Tool protocol (170 lines)
- [x] `src/agent/tools/schemas.py` - Schema definitions (290 lines, 7 schemas)
- [x] `src/agent/tools/registry.py` - Tool registry (240 lines)
- [ ] `src/agent/tools/user_context_tool.py` - Example tool (pending migration)
- [ ] `src/agent/tools/search_tool.py` - Search tool (pending migration)
- [ ] `src/agent/tools/digest_tool.py` - Digest tool (pending migration)
- [x] `src/agent/models/agent_result.py` - Result model (90 lines)
- [x] `src/agent/models/agent_config.py` - Agent config (65 lines)
- [ ] `src/agent/controllers/step_executor.py` - Step execution (pending)
- [ ] `src/agent/controllers/agent_controller.py` - Main controller (pending)
- [x] Migration guide created (`.claude/tasks/MIGRATION_GUIDE.md`)

**Validation:**
```bash
# New structure works ✓
python -c "from src.agent.tools.registry import ToolRegistry; print('OK')"

# Tests pass ✓
pytest tests/unit/agent/tools/test_registry.py -v
# Result: 17 passed in 0.03s
```

### PHASE 2 IMPLEMENTATION STATUS: 🟢 CORE REFACTORING COMPLETE

**What was completed:**

1. **Tool System Foundation (700 lines)**
   - Created modular tool system with protocol-based design
   - Separated schemas from implementation
   - Built tool registry with registration, discovery, validation
   - 17 comprehensive unit tests (all passing)
   - Working demo (`examples/tool_system_demo.py`)
   - Detailed migration guide (`.claude/tasks/MIGRATION_GUIDE.md`)

2. **Agent Models (155 lines)**
   - AgentConfig with validation and helpers
   - AgentResult with status tracking

3. **Controller Refactoring (860 lines)**
   - ✅ Refactored agent/controller.py (736 lines) into modular structure
   - ✅ Created StepExecutor (468 lines) - SENSE/PLAN/ACT/OBSERVE/REFLECT phases
   - ✅ Created AgentController (285 lines) - Clean orchestration logic
   - ✅ Created response_parser utilities (107 lines)
   - ✅ Separated concerns: phases, orchestration, utilities
   - ✅ Improved maintainability and testability

4. **Key Features Delivered:**
   - ✅ Protocol-based tool interface (BaseTool)
   - ✅ Tool schema separation
   - ✅ Centralized tool registry
   - ✅ Input validation framework
   - ✅ Tool discovery by tags
   - ✅ Approval-required tool tracking
   - ✅ Comprehensive error handling
   - ✅ Type-safe interfaces
   - ✅ Modular agent phases
   - ✅ Clean separation of orchestration and execution

**What remains for Phase 2:**
- Migrate 7 built-in tools from old system to new (user_context, search, digest, etc.)
- Update imports across codebase to use new structure
- Add tests for controller and step executor

**Files created:** 12 new files, ~1,715 lines of well-structured, modular code

**Date completed:** 2025-12-03

---

## Phase 3: RAG System Refactoring (Week 3)

### Priority: HIGH
**Status:** 📋 PLANNED - See detailed plan: `.claude/tasks/PHASE3_RAG_REFACTORING_PLAN.md`
**Goal:** Modularize RAG pipeline components

**📄 Detailed Implementation Plan:** [PHASE3_RAG_REFACTORING_PLAN.md](./PHASE3_RAG_REFACTORING_PLAN.md)

### Current State

**Files to Refactor (2,218 lines total):**
- `learning-coach-mcp/src/rag/synthesizer.py` (468 lines)
- `learning-coach-mcp/src/rag/digest_generator.py` (417 lines)
- `learning-coach-mcp/src/rag/evaluator.py` (408 lines)
- `learning-coach-mcp/src/rag/retriever.py` (365 lines)
- `learning-coach-mcp/src/rag/query_builder.py` (324 lines)
- `learning-coach-mcp/src/rag/insight_search.py` (233 lines)

### Quick Overview

#### 3.1 Extract Prompt Templates

**Current:** Prompts are inline strings in synthesizer and evaluator

**New:** `src/rag/synthesis/templates/synthesis_system.txt`

```
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

**File:** `src/rag/synthesis/prompt_builder.py`

```python
"""Builds prompts for synthesis."""
from typing import Dict, Any, List
from pathlib import Path

class PromptBuilder:
    """Builds synthesis prompts from templates."""

    def __init__(self, templates_dir: Path = None):
        if templates_dir is None:
            templates_dir = Path(__file__).parent / "templates"
        self.templates_dir = templates_dir
        self._cache = {}

    def _load_template(self, name: str) -> str:
        """Load template from file with caching."""
        if name not in self._cache:
            path = self.templates_dir / f"{name}.txt"
            with open(path, "r") as f:
                self._cache[name] = f.read()
        return self._cache[name]

    def build_system_prompt(self, stricter: bool = False) -> str:
        """Build system prompt."""
        if stricter:
            return self._load_template("synthesis_system_strict")
        return self._load_template("synthesis_system")

    def build_user_prompt(
        self,
        context_text: str,
        learning_context: Dict[str, Any],
        query: str,
        num_insights: int
    ) -> str:
        """Build user prompt."""
        template = self._load_template("synthesis_user")

        return template.format(
            context_text=context_text,
            week=learning_context.get("week", "unknown"),
            topics=", ".join(learning_context.get("topics", [])),
            difficulty=learning_context.get("difficulty", "intermediate"),
            query=query,
            num_insights=num_insights
        )
```

#### 3.2 Abstract LLM Clients

**File:** `src/rag/synthesis/base_synthesizer.py`

```python
"""Base synthesizer interface."""
from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BaseSynthesizer(ABC):
    """Abstract base for synthesizers."""

    @abstractmethod
    async def synthesize_insights(
        self,
        retrieved_chunks: List[Dict[str, Any]],
        learning_context: Dict[str, Any],
        query: str,
        num_insights: int = 7
    ) -> Dict[str, Any]:
        """Synthesize insights from chunks."""
        pass
```

**File:** `src/rag/synthesis/openai_synthesizer.py`

```python
"""OpenAI-based synthesizer."""
import logging
from typing import List, Dict, Any
from openai import AsyncOpenAI

from .base_synthesizer import BaseSynthesizer
from .prompt_builder import PromptBuilder
from src.core.exceptions import SynthesisError

logger = logging.getLogger(__name__)

class OpenAISynthesizer(BaseSynthesizer):
    """Synthesizer using OpenAI models."""

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o",
        prompt_builder: PromptBuilder = None
    ):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model
        self.prompt_builder = prompt_builder or PromptBuilder()

    async def synthesize_insights(
        self,
        retrieved_chunks: List[Dict[str, Any]],
        learning_context: Dict[str, Any],
        query: str,
        num_insights: int = 7
    ) -> Dict[str, Any]:
        """Synthesize insights using OpenAI."""
        logger.info(f"Synthesizing {num_insights} insights via OpenAI")

        try:
            # Build prompts
            system_prompt = self.prompt_builder.build_system_prompt()
            user_prompt = self.prompt_builder.build_user_prompt(
                context_text=self._format_chunks(retrieved_chunks),
                learning_context=learning_context,
                query=query,
                num_insights=num_insights
            )

            # Call OpenAI
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=8000
            )

            # Parse response
            insights = self._parse_response(response.choices[0].message.content)

            return {
                "insights": insights,
                "metadata": {
                    "model": self.model,
                    "num_chunks": len(retrieved_chunks)
                }
            }

        except Exception as e:
            logger.error(f"Synthesis failed: {e}", exc_info=True)
            raise SynthesisError(f"Failed to synthesize insights: {e}")

    def _format_chunks(self, chunks: List[Dict[str, Any]]) -> str:
        """Format chunks for prompt."""
        # Implementation...
        pass

    def _parse_response(self, text: str) -> List[Dict[str, Any]]:
        """Parse LLM response into structured insights."""
        # Implementation...
        pass
```

**Deliverables:**
- [ ] `src/rag/synthesis/templates/` - Prompt templates as files
- [ ] `src/rag/synthesis/prompt_builder.py` - Prompt builder
- [ ] `src/rag/synthesis/base_synthesizer.py` - Abstract base
- [ ] `src/rag/synthesis/openai_synthesizer.py` - OpenAI implementation
- [ ] `src/rag/synthesis/anthropic_synthesizer.py` - Anthropic implementation
- [ ] Migration from inline prompts to templates

---

## Phase 4: UI & Template System (Week 4)

### Priority: MEDIUM
**Goal:** Separate HTML from Python using templates

### Tasks

#### 4.1 Setup Jinja2 Templates

**File:** `src/ui/templates/daily_digest.html`

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Learning Digest - {{ date }}</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='css/digest.css') }}">
</head>
<body>
    <div class="digest-container">
        {% include 'components/header.html' %}

        <div class="insights-grid">
            {% for insight in insights %}
                {% include 'components/insight_card.html' %}
            {% endfor %}
        </div>

        {% include 'components/quality_badge.html' %}
    </div>
</body>
</html>
```

**File:** `src/ui/renderers/digest_renderer.py`

```python
"""Digest HTML renderer using Jinja2."""
import logging
from typing import Dict, Any
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

logger = logging.getLogger(__name__)

class DigestRenderer:
    """Renders digest as HTML using templates."""

    def __init__(self, templates_dir: Path = None):
        if templates_dir is None:
            templates_dir = Path(__file__).parent.parent / "templates"

        self.env = Environment(
            loader=FileSystemLoader(str(templates_dir)),
            autoescape=True
        )

    def render(self, digest: Dict[str, Any]) -> str:
        """Render digest to HTML."""
        logger.info("Rendering digest HTML")

        try:
            template = self.env.get_template("daily_digest.html")
            return template.render(**digest)

        except Exception as e:
            logger.error(f"Rendering failed: {e}", exc_info=True)
            return self._render_error(str(e))

    def _render_error(self, error: str) -> str:
        """Render error page."""
        template = self.env.get_template("error.html")
        return template.render(error=error)
```

**Deliverables:**
- [ ] `src/ui/templates/` - All HTML templates
- [ ] `src/ui/renderers/digest_renderer.py` - Digest renderer
- [ ] `src/ui/renderers/summary_renderer.py` - Summary renderer
- [ ] Static CSS files extracted
- [ ] Migration from inline HTML to templates

---

## Phase 5: Database & Repository Pattern (Week 5)

### Priority: MEDIUM
**Goal:** Abstract data access behind repositories

### Tasks

#### 5.1 Create Repository Layer

**File:** `src/database/repositories/base_repository.py`

```python
"""Base repository with common operations."""
from abc import ABC, abstractmethod
from typing import Optional, List, Any, TypeVar, Generic
from uuid import UUID

T = TypeVar('T')

class BaseRepository(ABC, Generic[T]):
    """Abstract base repository."""

    @abstractmethod
    async def get(self, id: str) -> Optional[T]:
        """Get entity by ID."""
        pass

    @abstractmethod
    async def save(self, entity: T) -> str:
        """Save entity and return ID."""
        pass

    @abstractmethod
    async def delete(self, id: str) -> bool:
        """Delete entity."""
        pass

    @abstractmethod
    async def list(
        self,
        offset: int = 0,
        limit: int = 100,
        filters: dict = None
    ) -> List[T]:
        """List entities with pagination."""
        pass
```

**File:** `src/database/repositories/user_repository.py`

```python
"""User repository."""
from typing import Optional, Dict, Any
from src.database.repositories.base_repository import BaseRepository
from src.database.models.user import User
from src.database.client import SupabaseClient

class UserRepository(BaseRepository[User]):
    """Repository for user data."""

    def __init__(self, client: SupabaseClient):
        self.client = client

    async def get(self, id: str) -> Optional[User]:
        """Get user by ID."""
        result = await self.client.table("users").select("*").eq("id", id).single().execute()
        if result.data:
            return User(**result.data)
        return None

    async def get_learning_context(self, user_id: str) -> Dict[str, Any]:
        """Get user's learning context."""
        # Implementation...
        pass

    async def update_preferences(
        self,
        user_id: str,
        preferences: Dict[str, Any]
    ) -> bool:
        """Update user preferences."""
        # Implementation...
        pass
```

**Deliverables:**
- [ ] `src/database/repositories/base_repository.py` - Base repository
- [ ] `src/database/repositories/user_repository.py` - User repository
- [ ] `src/database/repositories/session_repository.py` - Session repository
- [ ] `src/database/repositories/insight_repository.py` - Insight repository
- [ ] `src/database/models/` - Typed database models
- [ ] Replace direct Supabase calls with repository calls

---

## Phase 6: Testing & Documentation (Week 6)

### Priority: MEDIUM
**Goal:** Comprehensive test coverage and documentation

### Tasks

#### 6.1 Organize Tests

**Move all root test files to `tests/` directory:**

```bash
# Move unit tests
tests/
├── unit/
│   ├── agent/
│   │   ├── test_controller.py (from test_agent.py)
│   │   ├── test_tools.py (from test_agent_comprehensive.py)
│   │   └── test_planner.py (from test_agent_digest.py)
│   └── rag/
│       ├── test_retriever.py (from test_rag_search.py)
│       ├── test_synthesizer.py
│       └── test_evaluator.py (from test_ragas_eval_simple.py)
│
├── integration/
│   ├── test_digest_generation.py (from test_digest_generation_simple.py)
│   ├── test_approval_workflow.py (from test_approval_ui_workflow.py)
│   └── test_web_search.py (from test_web_search.py)
│
└── e2e/
    └── test_full_workflow.py (from test_e2e.py)
```

#### 6.2 Add Docstrings

**Template for modules:**

```python
"""
Module: src.agent.tools.registry

This module provides the ToolRegistry class for managing and executing
agent tools. The registry acts as a central point for tool discovery,
validation, and execution.

Usage:
    >>> from src.agent.tools.registry import ToolRegistry
    >>> registry = ToolRegistry()
    >>> registry.register(UserContextTool(user_repo))
    >>> result = await registry.execute("get-user-context", user_id="123")

See Also:
    - src.agent.tools.base: Base tool protocol
    - src.agent.tools.schemas: Tool schema definitions
"""
```

**Deliverables:**
- [ ] All test files moved to `tests/` directory
- [ ] Test organization (unit/integration/e2e)
- [ ] Module docstrings added to all files
- [ ] Function docstrings for public APIs
- [ ] README updates with new structure

---

## Phase 7: Final Cleanup & Migration (Week 7)

### Priority: LOW
**Goal:** Complete migration and remove old structure

### Tasks

#### 7.1 Create Compatibility Layer

**File:** `agent/tools.py` (legacy compatibility)

```python
"""
Legacy compatibility layer for agent.tools module.

DEPRECATED: This module is deprecated. Use src.agent.tools instead.
This module will be removed in version 2.0.

New imports:
    from src.agent.tools.registry import ToolRegistry
    from src.agent.tools.user_context_tool import UserContextTool
"""
import warnings
from src.agent.tools.registry import ToolRegistry  # noqa
from src.agent.tools.user_context_tool import UserContextTool  # noqa

warnings.warn(
    "agent.tools is deprecated. Use src.agent.tools instead.",
    DeprecationWarning,
    stacklevel=2
)
```

#### 7.2 Update All Imports

**Create migration script:**

```python
"""
Script to update imports from old to new structure.
"""
import os
import re
from pathlib import Path

OLD_TO_NEW = {
    "from agent.tools import": "from src.agent.tools.registry import",
    "from agent.controller import": "from src.agent.controllers.agent_controller import",
    "from learning-coach-mcp.src.rag.synthesizer import": "from src.rag.synthesis.openai_synthesizer import",
    # Add more mappings...
}

def migrate_imports(file_path: Path):
    """Migrate imports in a single file."""
    content = file_path.read_text()

    for old, new in OLD_TO_NEW.items():
        content = content.replace(old, new)

    file_path.write_text(content)

def main():
    """Migrate all Python files."""
    for file_path in Path(".").rglob("*.py"):
        if "venv" not in str(file_path):
            migrate_imports(file_path)

if __name__ == "__main__":
    main()
```

#### 7.3 Remove Old Structure

**After verification:**

```bash
# Verify new structure works
pytest tests/ -v
python -c "from src.agent.tools.registry import ToolRegistry; print('OK')"

# Remove old files (after backup)
rm -rf agent/  # Keep agent/ with compatibility layer for now
rm -rf learning-coach-mcp/src/rag/  # Moved to src/rag/
# etc...
```

**Deliverables:**
- [ ] Compatibility layers for gradual migration
- [ ] Import migration script
- [ ] Updated documentation
- [ ] All tests passing with new structure
- [ ] Old structure marked as deprecated

---

## Implementation Guidelines

### Priority Order

1. **Phase 1 (Week 1)**: Foundation - **MUST DO FIRST**
   - Core modules, config, types, exceptions
   - Test infrastructure
   - Type checking setup

2. **Phase 2 (Week 2)**: Agent System - **HIGH PRIORITY**
   - Largest files, most complex
   - Blocks other refactoring

3. **Phase 3 (Week 3)**: RAG System - **HIGH PRIORITY**
   - Core business logic
   - Affects digest generation

4. **Phase 4-7**: Can be done in parallel or as needed

### Migration Strategy

**Gradual Migration:**
- Keep old structure working during migration
- Add new structure alongside
- Create compatibility layers
- Update imports gradually
- Remove old structure last

**No Breaking Changes:**
- Maintain backwards compatibility
- Use deprecation warnings
- Provide migration guides

### Testing Strategy

**For Each Phase:**
1. Write tests for new structure first
2. Migrate code
3. Ensure old tests still pass
4. Add new tests for new features
5. Update integration tests

**Test Coverage Goals:**
- Unit tests: >80% coverage
- Integration tests: All major workflows
- E2E tests: Happy path + error cases

### Code Review Checkpoints

**After Each Phase:**
- [ ] All tests passing
- [ ] Type checking passing (mypy)
- [ ] No breaking changes
- [ ] Documentation updated
- [ ] Performance not degraded

---

## Success Metrics

### Code Quality

| Metric | Current | Target |
|--------|---------|--------|
| Average file size | 350 lines | <250 lines |
| Files >400 lines | 10 | 0 |
| Type hint coverage | ~30% | >90% |
| Test coverage | ~40% | >80% |
| Cyclomatic complexity | High | <10 per function |

### Maintainability

| Metric | Current | Target |
|--------|---------|--------|
| Coupling | High | Low (DI used) |
| Cohesion | Low | High (SRP followed) |
| Code duplication | ~15% | <5% |
| Documentation | Sparse | Comprehensive |

### Performance

| Metric | Current | Target |
|--------|---------|--------|
| Import time | Baseline | <10% increase |
| Test execution | Baseline | <20% increase |
| Memory usage | Baseline | <5% increase |

---

## Risks & Mitigations

### Risk 1: Breaking Changes

**Impact:** High
**Likelihood:** Medium

**Mitigation:**
- Gradual migration with compatibility layers
- Comprehensive testing at each phase
- Deprecation warnings before removal

### Risk 2: Performance Degradation

**Impact:** Medium
**Likelihood:** Low

**Mitigation:**
- Benchmark critical paths before/after
- Profile import times
- Optimize if needed (lazy loading)

### Risk 3: Scope Creep

**Impact:** High
**Likelihood:** High

**Mitigation:**
- Strict phase boundaries
- No new features during refactoring
- Focus on structural improvements only

### Risk 4: Timeline Overrun

**Impact:** Medium
**Likelihood:** Medium

**Mitigation:**
- Phases are independent
- Can pause between phases
- Core phases (1-2) are mandatory, rest optional

---

## Approval Checklist

Before proceeding with implementation:

- [ ] Review target architecture
- [ ] Confirm phase priorities
- [ ] Agree on timeline (7 weeks estimated)
- [ ] Allocate resources
- [ ] Approve breaking compatibility plan
- [ ] Review success metrics

---

## References

- [Python Best Practices 2025 Summary](.claude/tasks/python-best-practices-2025-summary.md)
- [Current Implementation Plan](.claude/tasks/agentic-learning-coach-implementation-plan.md)
- [The Hitchhiker's Guide to Python - Code Structure](https://docs.python-guide.org/writing/structure/)
- [Dagster - Python Project Best Practices](https://dagster.io/blog/python-project-best-practices)
- [Real Python - Dependency Injection](https://realpython.com/dependency-injection-python/)

---

**Next Steps:**

1. Review this plan
2. Provide feedback and approval
3. Begin Phase 1: Foundation & Core Infrastructure

---

## Implementation Progress

### Phase 1: Foundation & Core Infrastructure ✅ COMPLETED

**Date Completed:** 2025-12-02

**Deliverables Completed:**
- ✅ `src/core/config.py` - Centralized configuration with validation
- ✅ `src/core/exceptions.py` - Comprehensive exception hierarchy
- ✅ `src/core/types.py` - Type definitions, protocols, and type guards
- ✅ `mypy.ini` - Type checking configuration with gradual adoption
- ✅ `pytest.ini` - Pytest configuration with markers
- ✅ `tests/conftest.py` - Test fixtures and mocks
- ✅ `tests/unit/core/test_config.py` - 19 passing tests

**Validation Results:**
```
✓ Config module works
✓ Exceptions module works  
✓ Types module works
✓ 19/19 tests passing
```

**Next Steps:** Phase 2 - Agent System Refactoring


### Phase 2: Agent System Refactoring 🚧 IN PROGRESS

**Started:** 2025-12-02

**Goal:** Break down monolithic agent files into focused, reusable modules

**Progress:**

#### Completed:
1. **Module Structure** ✅
   - Created `src/agent/` with subdirectories: models/, controllers/, tools/, planning/
   
2. **Tool System Refactoring** ✅
   - **base.py** (170 lines): Tool protocol, ToolSchema dataclass, BaseToolImpl helper
   - **schemas.py** (290 lines): All 7 tool schemas extracted and organized
   - **registry.py** (240 lines): Tool registration, discovery, and execution management

**Breakdown Achievement:**
- Original `agent/tools.py`: **754 lines** (monolithic)
- Refactored into **3 focused modules**: **~700 lines total**
- Schemas now separate from implementation (better maintainability)
- Protocol-based design enables easy tool addition

**Tool Schemas Extracted:**
1. get-user-context
2. search-content
3. generate-digest
4. search-past-insights
5. sync-progress
6. web-search (requires_approval=True)
7. analyze-content-coverage

**Validation:**
```
✓ 7 tool schemas created
✓ Tool registry functional
✓ Protocol-based design working
✓ All modules import successfully
```

#### Next Steps:
- Create individual tool implementations
- Refactor agent/controller.py into smaller modules
- Add tests for tool system
- Create migration path from old ToolRegistry

