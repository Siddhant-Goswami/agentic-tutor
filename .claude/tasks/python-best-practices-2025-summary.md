# Python Best Practices 2025: Comprehensive Guide for Agentic Learning Coach

A detailed research-backed guide on Python best practices tailored for your system architecture involving agent controllers, RAG pipelines, Streamlit dashboards, and MCP server implementations.

---

## Table of Contents

1. [Code Organization & Modular Architecture](#1-code-organization--modular-architecture)
2. [Breaking Down Large Files & Functions](#2-breaking-down-large-files--functions)
3. [Reusability Patterns & DRY Principle](#3-reusability-patterns--dry-principle)
4. [Type Hints & Type Safety](#4-type-hints--type-safety)
5. [Error Handling Patterns](#5-error-handling-patterns)
6. [Testing Best Practices](#6-testing-best-practices)
7. [Documentation Standards](#7-documentation-standards)
8. [Dependency Injection & Configuration](#8-dependency-injection--configuration)
9. [Async/Await Patterns](#9-asyncawait-patterns)
10. [Design Patterns for Maintainability](#10-design-patterns-for-maintainability)

---

## 1. Code Organization & Modular Architecture

### Current Structure Considerations

Your project has multiple domains:
- **Agent System** (`/agent`) - Controllers, tools, workflow logic
- **RAG Pipeline** - Vector search, retrieval components
- **Dashboard** (`/dashboard`) - Streamlit UI
- **Database** (`/database`) - Supabase interactions
- **MCP Server** (`/learning-coach-mcp`) - Protocol server

### Recommended Approach

#### 1.1 Adopt Domain-Driven Design (DDD)

Organize code by business domains/features rather than technical layers:

```
agentic-tutor/
├── src/                           # All application code
│   ├── agent_system/              # Agent domain
│   │   ├── __init__.py
│   │   ├── controllers/
│   │   │   ├── agent_controller.py
│   │   │   ├── step_executor.py
│   │   │   └── workflow_manager.py
│   │   ├── tools/
│   │   │   ├── base.py           # Tool interface
│   │   │   ├── web_search_tool.py
│   │   │   ├── research_tool.py
│   │   │   └── __init__.py
│   │   ├── models.py              # Domain models
│   │   ├── exceptions.py          # Agent-specific exceptions
│   │   └── services.py            # Business logic
│   │
│   ├── rag_system/                # RAG domain
│   │   ├── __init__.py
│   │   ├── retrieval/
│   │   │   ├── vector_search.py
│   │   │   ├── ranking.py
│   │   │   └── __init__.py
│   │   ├── indexing/
│   │   │   ├── document_processor.py
│   │   │   ├── chunk_manager.py
│   │   │   └── __init__.py
│   │   ├── models.py
│   │   ├── exceptions.py
│   │   └── services.py
│   │
│   ├── database/                  # Data access domain
│   │   ├── __init__.py
│   │   ├── repositories/          # Repository pattern
│   │   │   ├── user_repository.py
│   │   │   ├── session_repository.py
│   │   │   └── __init__.py
│   │   ├── migrations/
│   │   ├── client.py              # Supabase client wrapper
│   │   ├── models.py              # ORM/table models
│   │   └── exceptions.py
│   │
│   ├── dashboard/                 # UI domain
│   │   ├── __init__.py
│   │   ├── pages/
│   │   │   ├── home.py
│   │   │   ├── chat.py
│   │   │   └── analytics.py
│   │   ├── components/
│   │   │   ├── sidebar.py
│   │   │   ├── message_display.py
│   │   │   └── __init__.py
│   │   ├── app.py                 # Main Streamlit app
│   │   └── utils.py               # Dashboard utilities
│   │
│   ├── mcp_server/                # MCP domain
│   │   ├── __init__.py
│   │   ├── protocol.py            # Protocol implementation
│   │   ├── handlers.py            # Message handlers
│   │   └── exceptions.py
│   │
│   ├── shared/                    # Shared utilities
│   │   ├── __init__.py
│   │   ├── config.py              # Configuration management
│   │   ├── logging.py             # Logging setup
│   │   ├── constants.py           # Application constants
│   │   ├── exceptions.py          # Base exceptions
│   │   ├── types.py               # Shared type definitions
│   │   └── utils.py               # General utilities
│   │
│   └── __init__.py
│
├── tests/                         # Parallel test structure
│   ├── unit/
│   │   ├── agent_system/
│   │   ├── rag_system/
│   │   ├── database/
│   │   └── shared/
│   ├── integration/
│   │   ├── agent_rag_flow.py
│   │   └── end_to_end.py
│   ├── conftest.py               # Pytest fixtures
│   └── fixtures/
│
├── docs/                         # Documentation
│   ├── architecture.md
│   ├── api.md
│   └── deployment.md
│
├── scripts/                      # Utility scripts
│   ├── setup_db.py
│   ├── run_ingestion.py
│   └── seed_data.py
│
├── pyproject.toml               # Project configuration
├── README.md
├── .env.example
└── requirements.txt
```

#### 1.2 Single Responsibility Principle (SRP)

Each module should have **one reason to change**:

```python
# ❌ Bad: Too many responsibilities
class AgentController:
    def run_agent(self, request):
        # Validate input
        if not request.query:
            raise ValueError("Missing query")

        # Process agent logic
        tools = [WebSearchTool(), RAGTool()]

        # Call tools
        results = []
        for tool in tools:
            results.append(tool.execute(request.query))

        # Log results
        print(f"Results: {results}")

        # Save to database
        db.save(results)

        return results

# ✅ Good: Separated concerns
class AgentController:
    def __init__(self,
                 validator: RequestValidator,
                 agent_service: AgentService,
                 logger: Logger):
        self.validator = validator
        self.agent_service = agent_service
        self.logger = logger

    async def run_agent(self, request: AgentRequest) -> AgentResponse:
        """Execute agent workflow."""
        self.validator.validate(request)
        response = await self.agent_service.process(request)
        self.logger.info(f"Agent completed: {response.id}")
        return response

class AgentService:
    """Business logic for agent execution."""
    def __init__(self,
                 tool_factory: ToolFactory,
                 state_manager: StateManager):
        self.tool_factory = tool_factory
        self.state_manager = state_manager

    async def process(self, request: AgentRequest) -> AgentResponse:
        """Core agent processing logic."""
        tools = await self.tool_factory.create_tools(request)
        results = await asyncio.gather(*[
            tool.execute(request.query) for tool in tools
        ])
        return AgentResponse(query=request.query, results=results)

class StateManager:
    """Handle state persistence."""
    def __init__(self, repository: AgentStateRepository):
        self.repository = repository

    async def save_state(self, state: AgentState) -> None:
        await self.repository.save(state)
```

#### 1.3 Cohesion Guidelines

Keep related functionality together:

```python
# ❌ Bad: Scattered related logic
# In controller.py
def validate_query(query):
    return len(query) > 3

# In utils.py
def check_query_length(q):
    return len(q) > 3

# In service.py
def is_valid_query(text):
    return len(text) > 3

# ✅ Good: Cohesive validation module
# src/shared/validation.py
class QueryValidator:
    """Centralized query validation logic."""

    MIN_LENGTH = 3
    MAX_LENGTH = 2000
    FORBIDDEN_CHARS = {'<', '>', '$', ';'}

    @classmethod
    def validate(cls, query: str) -> ValidationResult:
        """Validate query meets requirements."""
        if not query or len(query) < cls.MIN_LENGTH:
            return ValidationResult(
                is_valid=False,
                error="Query too short"
            )

        if len(query) > cls.MAX_LENGTH:
            return ValidationResult(
                is_valid=False,
                error="Query too long"
            )

        if any(char in query for char in cls.FORBIDDEN_CHARS):
            return ValidationResult(
                is_valid=False,
                error="Query contains invalid characters"
            )

        return ValidationResult(is_valid=True)
```

### References

- [Structuring Your Project — The Hitchhiker's Guide to Python](https://docs.python-guide.org/writing/structure/)
- [Best Practices in Structuring Python Projects](https://dagster.io/blog/python-project-best-practices)
- [Organizing Python Code into Modules](https://llego.dev/posts/organizing-python-code-modules-better-organization-reusability/)
- [Best Practices for Structuring a Python Project Like a Pro](https://medium.com/the-pythonworld/best-practices-for-structuring-a-python-project-like-a-pro-1265363836f9)

---

## 2. Breaking Down Large Files & Functions

### The Problem

Large files become:
- Hard to test individually
- Difficult to maintain
- Prone to naming conflicts
- Impossible to reuse components

### 2.1 File Size Guidelines

- **Ideal**: 200-400 lines per file
- **Maximum**: 600 lines before refactoring
- **Sweet spot**: 250-350 lines (one primary class/module per file)

### 2.2 Function Size Guidelines

```python
# ❌ Bad: 150 lines in one function
async def execute_agent_workflow(request):
    # 30 lines: validate input
    if not request.query:
        raise ValueError(...)
    if not request.session_id:
        raise ValueError(...)
    # ... more validation

    # 40 lines: initialize tools
    web_search = WebSearchTool(...)
    rag_tool = RAGTool(...)
    # ... more tool setup

    # 50 lines: run tools concurrently
    tasks = [...]
    results = await asyncio.gather(*tasks)
    # ... process results

    # 30 lines: save state
    state = AgentState(...)
    await db.save(state)
    # ...

# ✅ Good: Extracted into smaller, focused functions
async def execute_agent_workflow(
    request: AgentRequest,
    service: AgentService
) -> AgentResponse:
    """Orchestrate the agent workflow."""
    service.validator.validate(request)

    tools = await service.tool_manager.initialize_tools(request)
    results = await service.executor.run_tools(tools, request.query)

    await service.state_manager.save_workflow_state(
        request.session_id,
        results
    )

    return AgentResponse(query=request.query, results=results)

async def run_tools(tools: List[Tool], query: str) -> List[ToolResult]:
    """Execute all tools concurrently."""
    return await asyncio.gather(*[
        tool.execute(query) for tool in tools
    ])

async def save_workflow_state(
    session_id: str,
    results: List[ToolResult]
) -> None:
    """Persist workflow state to database."""
    state = AgentState(
        session_id=session_id,
        results=results,
        timestamp=datetime.now()
    )
    await repository.save(state)
```

### 2.3 Refactoring Techniques

#### Extract Method

```python
# ❌ Before
class AgentController:
    async def handle_request(self, request):
        # Complex query processing - 30 lines
        query = request.text.lower().strip()
        words = query.split()
        # ... processing logic

        # Run agent - 20 lines
        # ... agent logic

        # Format response - 15 lines
        # ... formatting

        return response

# ✅ After
class AgentController:
    async def handle_request(self, request):
        processed_query = self._preprocess_query(request.text)
        agent_result = await self._run_agent(processed_query)
        response = self._format_response(agent_result)
        return response

    def _preprocess_query(self, text: str) -> str:
        return text.lower().strip()

    async def _run_agent(self, query: str) -> AgentResult:
        # Agent logic here
        pass

    def _format_response(self, result: AgentResult) -> Response:
        # Formatting logic here
        pass
```

#### Extract Class

```python
# ❌ Before: Too many responsibilities
class RAGPipeline:
    def __init__(self, db_client, embedding_model):
        self.db = db_client
        self.embedding = embedding_model

    async def search(self, query: str):
        # Preprocessing - 20 lines
        # Embedding - 15 lines
        # Vector search - 20 lines
        # Ranking - 25 lines
        # Response formatting - 15 lines
        pass

# ✅ After: Separated concerns
class RAGPipeline:
    def __init__(self,
                 preprocessor: QueryPreprocessor,
                 embedder: EmbeddingService,
                 retriever: VectorRetriever,
                 ranker: ResultRanker):
        self.preprocessor = preprocessor
        self.embedder = embedder
        self.retriever = retriever
        self.ranker = ranker

    async def search(self, query: str) -> SearchResult:
        processed = self.preprocessor.process(query)
        embedding = await self.embedder.embed(processed)
        candidates = await self.retriever.retrieve(embedding)
        ranked = self.ranker.rank(candidates)
        return SearchResult(results=ranked)

# Each class has single responsibility
class QueryPreprocessor:
    """Handle query normalization and validation."""
    pass

class VectorRetriever:
    """Handle vector database operations."""
    pass

class ResultRanker:
    """Handle result ranking/reordering."""
    pass
```

### 2.4 Complexity Metrics

Use tools to identify refactoring candidates:

```bash
# Install radon for code metrics
pip install radon

# Check cyclomatic complexity
radon cc src/ -a -nb

# Check maintainability index
radon mi src/ -nb
```

### References

- [Best Practices for Structuring Python Code for Optimal Organization](https://medium.com/@austinoblow97/best-practices-for-structuring-python-code-for-optimal-organization-ba58f2f1e87b)

---

## 3. Reusability Patterns & DRY Principle

### 3.1 Identify Duplication

Common duplication patterns:
- **Validation logic** repeated across functions
- **Tool initialization** in multiple places
- **Error handling** patterns duplicated
- **Configuration parsing** in multiple modules

```python
# ❌ Bad: Duplication across agent tools
class WebSearchTool:
    async def execute(self, query: str):
        # Validation - 10 lines duplicated in every tool
        if not query:
            raise ValueError("Empty query")
        if len(query) > 2000:
            raise ValueError("Query too long")

        # Execute search
        results = await self.search_api.query(query)

        # Formatting - 10 lines duplicated
        return {
            "tool": "web_search",
            "query": query,
            "results": results,
            "timestamp": datetime.now().isoformat()
        }

class RAGTool:
    async def execute(self, query: str):
        # Same validation - 10 lines
        if not query:
            raise ValueError("Empty query")
        if len(query) > 2000:
            raise ValueError("Query too long")

        # Execute search
        results = await self.rag_index.search(query)

        # Same formatting - 10 lines
        return {
            "tool": "rag_search",
            "query": query,
            "results": results,
            "timestamp": datetime.now().isoformat()
        }

# ✅ Good: Extract common behavior into base class
from abc import ABC, abstractmethod
from datetime import datetime

class BaseTool(ABC):
    """Base class for all agent tools."""

    MAX_QUERY_LENGTH = 2000

    async def execute(self, query: str) -> ToolResult:
        """Execute tool with common validation/formatting."""
        self._validate_query(query)
        result = await self._execute_impl(query)
        return self._format_result(result, query)

    def _validate_query(self, query: str) -> None:
        """Validate query input."""
        if not query or not query.strip():
            raise QueryValidationError("Query cannot be empty")
        if len(query) > self.MAX_QUERY_LENGTH:
            raise QueryValidationError(
                f"Query exceeds {self.MAX_QUERY_LENGTH} characters"
            )

    @abstractmethod
    async def _execute_impl(self, query: str) -> List[Any]:
        """Implement tool-specific logic. Subclasses override this."""
        pass

    def _format_result(self, data: List[Any], query: str) -> ToolResult:
        """Format result uniformly across all tools."""
        return ToolResult(
            tool_name=self.__class__.__name__,
            query=query,
            results=data,
            timestamp=datetime.now().isoformat()
        )

class WebSearchTool(BaseTool):
    def __init__(self, api_client):
        self.api_client = api_client

    async def _execute_impl(self, query: str) -> List[Any]:
        """Only implement tool-specific logic."""
        return await self.api_client.search(query)

class RAGTool(BaseTool):
    def __init__(self, index):
        self.index = index

    async def _execute_impl(self, query: str) -> List[Any]:
        """Only implement tool-specific logic."""
        return await self.index.search(query)
```

### 3.2 Configuration Management (DRY for Settings)

```python
# ❌ Bad: Magic numbers scattered everywhere
class AgentService:
    async def run_step(self, step):
        if step.retry_count > 3:  # Magic number!
            raise MaxRetriesExceeded()

        response = await self.call_api(
            timeout=30,  # Magic number!
            max_tokens=2000  # Magic number!
        )

class RAGPipeline:
    def search(self, query):
        results = self.index.search(
            query,
            top_k=10  # Different default than agent uses!
        )

# ✅ Good: Centralized configuration
# src/shared/config.py
from dataclasses import dataclass
from typing import Optional

@dataclass
class AgentConfig:
    """Configuration for agent execution."""
    max_retries: int = 3
    api_timeout: int = 30
    max_tokens: int = 2000
    model: str = "gpt-4"

@dataclass
class RAGConfig:
    """Configuration for RAG pipeline."""
    top_k: int = 10
    similarity_threshold: float = 0.7
    embedding_model: str = "text-embedding-3-small"
    max_chunk_size: int = 512

@dataclass
class AppConfig:
    """Global application configuration."""
    agent: AgentConfig = AgentConfig()
    rag: RAGConfig = RAGConfig()

    @classmethod
    def from_env(cls) -> "AppConfig":
        """Load configuration from environment."""
        return cls(
            agent=AgentConfig(
                max_retries=int(os.getenv("AGENT_MAX_RETRIES", 3)),
                api_timeout=int(os.getenv("AGENT_TIMEOUT", 30)),
            ),
            rag=RAGConfig(
                top_k=int(os.getenv("RAG_TOP_K", 10)),
                similarity_threshold=float(
                    os.getenv("RAG_SIMILARITY_THRESHOLD", 0.7)
                ),
            )
        )

# Usage
config = AppConfig.from_env()

class AgentService:
    def __init__(self, config: AgentConfig):
        self.config = config

    async def run_step(self, step):
        if step.retry_count > self.config.max_retries:
            raise MaxRetriesExceeded()

        response = await self.call_api(
            timeout=self.config.api_timeout,
            max_tokens=self.config.max_tokens
        )

class RAGPipeline:
    def __init__(self, config: RAGConfig):
        self.config = config

    def search(self, query):
        return self.index.search(
            query,
            top_k=self.config.top_k
        )
```

### 3.3 Template Method Pattern (for DRY in workflows)

```python
# ❌ Bad: Duplicate workflow structure in multiple tools
class WebSearchTool:
    async def execute(self, query):
        logger.info(f"Starting web search: {query}")
        try:
            result = await self._search(query)
            logger.info(f"Web search succeeded")
            return result
        except Exception as e:
            logger.error(f"Web search failed: {e}")
            raise

class RAGTool:
    async def execute(self, query):
        logger.info(f"Starting RAG search: {query}")
        try:
            result = await self._search(query)
            logger.info(f"RAG search succeeded")
            return result
        except Exception as e:
            logger.error(f"RAG search failed: {e}")
            raise

# ✅ Good: Template method pattern
class ExecutableToolBase(ABC):
    """Template for tool execution workflow."""

    async def execute(self, query: str) -> ToolResult:
        """Template method defining execution workflow."""
        self._log_start(query)
        try:
            result = await self._do_execute(query)
            self._log_success()
            return result
        except Exception as e:
            self._log_error(e)
            raise

    @abstractmethod
    async def _do_execute(self, query: str) -> ToolResult:
        """Subclasses implement their specific logic."""
        pass

    def _log_start(self, query: str) -> None:
        logger.info(f"Executing {self.__class__.__name__}: {query}")

    def _log_success(self) -> None:
        logger.info(f"{self.__class__.__name__} succeeded")

    def _log_error(self, error: Exception) -> None:
        logger.error(f"{self.__class__.__name__} failed: {error}")

class WebSearchTool(ExecutableToolBase):
    async def _do_execute(self, query: str) -> ToolResult:
        return await self.search_api.query(query)

class RAGTool(ExecutableToolBase):
    async def _do_execute(self, query: str) -> ToolResult:
        return await self.rag_index.search(query)
```

### 3.4 Utility Functions for Common Operations

```python
# src/shared/utils.py
"""Common utility functions shared across domains."""

from typing import List, Dict, Any
import asyncio

async def run_concurrent(
    coroutines: List,
    timeout: Optional[int] = None,
    return_exceptions: bool = False
) -> List[Any]:
    """
    Run multiple coroutines concurrently with optional timeout.

    Args:
        coroutines: List of coroutines to run
        timeout: Optional timeout in seconds
        return_exceptions: If True, exceptions are returned as results

    Returns:
        List of results from coroutines
    """
    try:
        return await asyncio.wait_for(
            asyncio.gather(*coroutines, return_exceptions=return_exceptions),
            timeout=timeout
        )
    except asyncio.TimeoutError:
        raise ExecutionTimeoutError(
            f"Operations timed out after {timeout}s"
        )

def batch_items(items: List[Any], batch_size: int) -> List[List[Any]]:
    """Split items into batches."""
    return [
        items[i:i + batch_size]
        for i in range(0, len(items), batch_size)
    ]

def flatten_dict(nested: Dict, parent_key: str = '') -> Dict:
    """Flatten nested dictionary."""
    items = []
    for k, v in nested.items():
        new_key = f"{parent_key}.{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key).items())
        else:
            items.append((new_key, v))
    return dict(items)
```

### References

- [Applying the DRY Principle in Python](https://codesignal.com/learn/courses/applying-clean-code-principles-in-python/lessons/applying-the-dry-principle-in-python/)
- [Best Practices for Writing DRY Code](https://blog.pixelfreestudio.com/best-practices-for-writing-dry-dont-repeat-yourself-code/)
- [DRY Principle in Software Development](https://www.geeksforgeeks.org/dont-repeat-yourselfdry-in-software-development/)

---

## 4. Type Hints & Type Safety

### 4.1 Adopt Gradual Type Hints

Start with critical paths, expand gradually:

```python
# Phase 1: Type hint critical functions
# src/agent/controller.py
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

@dataclass
class AgentRequest:
    """Type-safe request object."""
    query: str
    session_id: str
    user_id: str
    parameters: Optional[Dict[str, Any]] = None

@dataclass
class AgentResponse:
    """Type-safe response object."""
    query: str
    results: List[Dict[str, Any]]
    execution_time: float
    status: str

class AgentController:
    async def run_agent(self, request: AgentRequest) -> AgentResponse:
        """Execute agent with type-safe interface."""
        # Type hints catch errors early
        pass

# Phase 2: Add return types and parameter types
# src/rag/retriever.py
class VectorRetriever:
    def __init__(self, client: SupabaseClient, model_name: str) -> None:
        self.client = client
        self.model_name = model_name

    async def retrieve(
        self,
        query_embedding: List[float],
        top_k: int = 10
    ) -> List[Document]:
        """Retrieve documents similar to query."""
        results = await self.client.vector_search(
            query_embedding,
            limit=top_k
        )
        return [Document.from_db_row(row) for row in results]

# Phase 3: Add generic types for flexibility
from typing import TypeVar, Generic

T = TypeVar('T')

class Repository(Generic[T]):
    """Generic repository pattern with types."""

    async def get_by_id(self, id: str) -> Optional[T]:
        pass

    async def list_all(self) -> List[T]:
        pass

    async def save(self, item: T) -> T:
        pass

class UserRepository(Repository[User]):
    """Type-safe user repository."""
    async def get_by_email(self, email: str) -> Optional[User]:
        pass
```

### 4.2 Using Protocols for Interface Definition

```python
# ✅ Good: Define interfaces with Protocol
from typing import Protocol, runtime_checkable

@runtime_checkable
class SearchTool(Protocol):
    """Protocol defining search tool interface."""

    async def execute(self, query: str) -> SearchResult:
        """Execute search."""
        ...

    @property
    def name(self) -> str:
        """Tool name."""
        ...

# Any class implementing these methods matches the protocol
class WebSearchTool:
    async def execute(self, query: str) -> SearchResult:
        return await self.api.search(query)

    @property
    def name(self) -> str:
        return "web_search"

class RAGTool:
    async def execute(self, query: str) -> SearchResult:
        return await self.index.search(query)

    @property
    def name(self) -> str:
        return "rag_search"

# Type-safe usage
async def run_tools(
    tools: List[SearchTool],
    query: str
) -> List[SearchResult]:
    """Run multiple tools - all must implement SearchTool protocol."""
    return await asyncio.gather(*[
        tool.execute(query) for tool in tools
    ])
```

### 4.3 Type Safety with Pydantic

```python
# ✅ Good: Use Pydantic for runtime validation + type safety
from pydantic import BaseModel, Field, validator

class SearchRequest(BaseModel):
    """Type-safe with runtime validation."""
    query: str = Field(..., min_length=1, max_length=2000)
    session_id: str
    max_results: int = Field(default=10, ge=1, le=100)

    @validator('query')
    def query_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Query cannot be whitespace only')
        return v.strip()

class SearchResult(BaseModel):
    """Type-safe result with validation."""
    tool_name: str
    query: str
    results: List[Dict[str, Any]]
    score: float = Field(..., ge=0.0, le=1.0)

# Automatic validation
request = SearchRequest(
    query="What is AI?",
    session_id="session_123"
)

# This would raise validation error
invalid = SearchRequest(query="")  # Raises: Query cannot be empty
```

### 4.4 Type Checking Setup

```bash
# Install type checker
pip install mypy

# Create mypy.ini
[mypy]
python_version = 3.10
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = False  # Gradual adoption
disallow_untyped_calls = False
check_untyped_defs = True
no_implicit_optional = True
warn_redundant_casts = True
warn_unused_ignores = True
warn_no_return = True
strict_equality = True

# Run type checking
mypy src/
```

### References

- [Python Typing in 2025: A Comprehensive Guide](https://khaled-jallouli.medium.com/python-typing-in-2025-a-comprehensive-guide-d61b4f562b99)
- [A Complete Guide to Python Type Hints](https://betterstack.com/community/guides/scaling-python/python-type-hints/)
- [typing — Support for type hints](https://docs.python.org/3/library/typing.html)

---

## 5. Error Handling Patterns

### 5.1 Custom Exception Hierarchy

```python
# src/shared/exceptions.py
"""Application-wide exception hierarchy."""

class AgenticTutorError(Exception):
    """Base exception for entire application."""
    pass

class ValidationError(AgenticTutorError):
    """Raised when validation fails."""
    pass

class QueryValidationError(ValidationError):
    """Raised when query validation fails."""
    pass

class ConfigurationError(AgenticTutorError):
    """Raised when configuration is invalid."""
    pass

# Agent-specific exceptions
class AgentError(AgenticTutorError):
    """Base for agent system errors."""
    pass

class AgentExecutionError(AgentError):
    """Raised when agent execution fails."""
    pass

class MaxRetriesExceeded(AgentError):
    """Raised when max retries exceeded."""
    pass

class ToolExecutionError(AgentError):
    """Raised when tool execution fails."""
    pass

# RAG-specific exceptions
class RAGError(AgenticTutorError):
    """Base for RAG system errors."""
    pass

class RetrievalError(RAGError):
    """Raised when document retrieval fails."""
    pass

class IndexingError(RAGError):
    """Raised when indexing fails."""
    pass

# Database exceptions
class DatabaseError(AgenticTutorError):
    """Base for database errors."""
    pass

class RepositoryError(DatabaseError):
    """Raised when repository operations fail."""
    pass
```

### 5.2 Specific Exception Handling (Not Broad Except)

```python
# ❌ Bad: Too broad
async def execute_tool(tool: Tool, query: str):
    try:
        result = await tool.execute(query)
        return result
    except:  # Catches everything!
        return {"error": "Unknown error"}
    except Exception:  # Still too broad
        logger.error("Error")
        raise

# ✅ Good: Specific exception handling
async def execute_tool(tool: Tool, query: str) -> ToolResult:
    """Execute tool with specific error handling."""
    try:
        result = await tool.execute(query)
        return result
    except asyncio.TimeoutError:
        logger.warning(f"Tool timeout: {tool.name}")
        raise ToolExecutionError(
            f"Tool {tool.name} timed out",
            cause="timeout"
        ) from None
    except QueryValidationError as e:
        logger.warning(f"Invalid query: {e}")
        raise  # Re-raise validation errors
    except ToolExecutionError:
        raise  # Re-raise known tool errors
    except Exception as e:
        logger.error(f"Unexpected error in {tool.name}: {e}", exc_info=True)
        raise ToolExecutionError(
            f"Unexpected error in {tool.name}: {str(e)}",
            cause="unexpected"
        ) from e
```

### 5.3 EAFP Pattern (Easier to Ask Forgiveness than Permission)

```python
# ❌ Bad: LBYL (Look Before You Leap)
def get_user_data(user_id: str) -> Dict:
    if user_id is not None and len(user_id) > 0:
        if user_id in cache:
            return cache[user_id]
        else:
            # Query database
            pass

# ✅ Good: EAFP pattern
async def get_user_data(user_id: str) -> Dict:
    """Use EAFP - try first, handle errors."""
    try:
        # Try cache first
        return cache[user_id]
    except KeyError:
        # Cache miss, query database
        try:
            user = await db.get_user(user_id)
            return user.to_dict()
        except RepositoryError as e:
            logger.error(f"Database error: {e}")
            raise UserNotFoundError(f"User {user_id} not found") from e
```

### 5.4 Context Managers for Resource Management

```python
# ✅ Good: Automatic resource cleanup
from contextlib import asynccontextmanager

class DatabaseConnection:
    """Database connection with automatic cleanup."""

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()

@asynccontextmanager
async def database_transaction():
    """Context manager for database transactions."""
    async with db.transaction() as txn:
        try:
            yield txn
        except Exception as e:
            await txn.rollback()
            logger.error(f"Transaction rolled back: {e}")
            raise
        else:
            await txn.commit()

# Usage
async with database_transaction() as txn:
    await txn.save(user)  # Auto-commits on success
    # Auto-rollback on exception
```

### 5.5 Exception Groups (Python 3.11+)

```python
# ✅ Good: Handle multiple exceptions
async def run_tools_with_error_collection(
    tools: List[Tool],
    query: str
) -> Tuple[List[ToolResult], List[Exception]]:
    """Run all tools, collecting errors."""
    results = []
    errors = []

    for tool in tools:
        try:
            result = await tool.execute(query)
            results.append(result)
        except Exception as e:
            logger.warning(f"Tool {tool.name} failed: {e}")
            errors.append(e)

    if errors:
        logger.error(f"{len(errors)} tools failed")

    return results, errors

# Python 3.11+ ExceptionGroup
import traceback

async def run_tools_concurrent(
    tools: List[Tool],
    query: str
) -> List[ToolResult]:
    """Run tools concurrently with error handling."""
    tasks = [tool.execute(query) for tool in tools]

    try:
        return await asyncio.gather(*tasks, return_exceptions=False)
    except ExceptionGroup as eg:
        # Handle multiple exceptions that occurred
        for exc in eg.exceptions:
            logger.error(f"Tool execution error: {exc}")
        raise ToolExecutionError(
            f"{len(eg.exceptions)} tools failed"
        ) from eg
```

### References

- [6 Best practices for Python exception handling](https://www.qodo.ai/blog/6-best-practices-for-python-exception-handling/)
- [The Ultimate Guide to Error Handling in Python](https://blog.miguelgrinberg.com/post/the-ultimate-guide-to-error-handling-in-python)
- [5 Error Handling Patterns in Python (Beyond Try-Except)](https://www.kdnuggets.com/5-error-handling-patterns-in-python-beyond-try-except)

---

## 6. Testing Best Practices

### 6.1 Test Organization

```
tests/
├── conftest.py                 # Shared fixtures
├── unit/
│   ├── agent_system/
│   │   ├── test_agent_controller.py
│   │   ├── test_tools.py
│   │   └── __init__.py
│   ├── rag_system/
│   │   ├── test_retrieval.py
│   │   ├── test_indexing.py
│   │   └── __init__.py
│   └── database/
│       ├── test_repositories.py
│       └── __init__.py
├── integration/
│   ├── test_agent_rag_flow.py
│   ├── test_dashboard_agent.py
│   └── __init__.py
└── e2e/
    └── test_full_workflow.py
```

### 6.2 Pytest Fixtures for DI

```python
# tests/conftest.py
"""Shared test fixtures."""

import pytest
from unittest.mock import AsyncMock, Mock
from src.agent.controller import AgentController
from src.agent.tools import WebSearchTool, RAGTool
from src.rag.retriever import VectorRetriever
from src.database.client import SupabaseClient

@pytest.fixture
def mock_supabase_client() -> Mock:
    """Mock Supabase client."""
    client = Mock(spec=SupabaseClient)
    client.vector_search = AsyncMock(return_value=[])
    return client

@pytest.fixture
def vector_retriever(mock_supabase_client) -> VectorRetriever:
    """VectorRetriever with mocked dependencies."""
    return VectorRetriever(
        client=mock_supabase_client,
        model_name="test-model"
    )

@pytest.fixture
def mock_web_search() -> AsyncMock:
    """Mock web search API."""
    return AsyncMock(return_value=[
        {"title": "Result 1", "url": "https://example.com"}
    ])

@pytest.fixture
def web_search_tool(mock_web_search) -> WebSearchTool:
    """Web search tool with mocked API."""
    tool = WebSearchTool()
    tool.api = mock_web_search
    return tool

@pytest.fixture
def agent_controller(
    vector_retriever,
    web_search_tool
) -> AgentController:
    """Agent controller with mocked dependencies."""
    return AgentController(
        tools=[web_search_tool],
        rag_retriever=vector_retriever
    )
```

### 6.3 Unit Test Example - AAA Pattern

```python
# tests/unit/agent_system/test_agent_controller.py
"""Test agent controller."""

import pytest
from src.agent.controller import AgentController, AgentRequest, AgentResponse
from src.shared.exceptions import QueryValidationError

class TestAgentController:
    """Test suite for AgentController."""

    @pytest.mark.asyncio
    async def test_run_agent_success(self, agent_controller, web_search_tool):
        """Test successful agent execution.

        AAA Pattern:
        - Arrange: Set up test data
        - Act: Execute function under test
        - Assert: Verify results
        """
        # Arrange
        request = AgentRequest(
            query="What is AI?",
            session_id="test_session_123",
            user_id="user_456"
        )

        # Act
        response = await agent_controller.run_agent(request)

        # Assert
        assert response.query == "What is AI?"
        assert len(response.results) > 0
        assert response.status == "success"

    @pytest.mark.asyncio
    async def test_run_agent_empty_query(self, agent_controller):
        """Test agent rejects empty query."""
        # Arrange
        request = AgentRequest(
            query="",
            session_id="test_session_123",
            user_id="user_456"
        )

        # Act & Assert
        with pytest.raises(QueryValidationError):
            await agent_controller.run_agent(request)

    @pytest.mark.asyncio
    async def test_run_agent_timeout(self, agent_controller, mocker):
        """Test agent timeout handling."""
        # Arrange
        request = AgentRequest(
            query="What is AI?",
            session_id="test_session_123",
            user_id="user_456"
        )

        # Mock timeout
        mocker.patch.object(
            agent_controller,
            '_run_tools',
            side_effect=asyncio.TimeoutError()
        )

        # Act & Assert
        with pytest.raises(ToolExecutionError):
            await agent_controller.run_agent(request)
```

### 6.4 Parametrized Tests

```python
# tests/unit/shared/test_query_validator.py
"""Test query validation."""

import pytest
from src.shared.validation import QueryValidator, ValidationResult

class TestQueryValidator:
    """Test query validation."""

    @pytest.mark.parametrize("query,expected_valid", [
        ("What is AI?", True),
        ("Valid query with spaces", True),
        ("", False),
        ("  ", False),  # Whitespace only
        ("a" * 2001, False),  # Too long
    ])
    def test_validate_query(self, query, expected_valid):
        """Test query validation with multiple cases."""
        result = QueryValidator.validate(query)
        assert result.is_valid == expected_valid

    @pytest.mark.parametrize("forbidden_char", ['<', '>', '$', ';'])
    def test_reject_forbidden_chars(self, forbidden_char):
        """Test that forbidden characters are rejected."""
        query = f"test{forbidden_char}query"
        result = QueryValidator.validate(query)
        assert not result.is_valid
        assert "invalid characters" in result.error.lower()
```

### 6.5 Mocking Dependencies

```python
# tests/unit/agent_system/test_tools.py
"""Test agent tools."""

import pytest
from unittest.mock import AsyncMock, patch
from src.agent.tools import WebSearchTool, RAGTool

class TestWebSearchTool:
    """Test web search tool."""

    @pytest.mark.asyncio
    async def test_web_search_success(self):
        """Test successful web search."""
        # Arrange
        tool = WebSearchTool()
        expected_results = [
            {"title": "Result 1", "url": "https://example.com"}
        ]

        # Mock the API call
        tool.api_client.search = AsyncMock(return_value=expected_results)

        # Act
        result = await tool.execute("test query")

        # Assert
        assert result.tool_name == "WebSearchTool"
        assert result.results == expected_results
        tool.api_client.search.assert_called_once_with("test query")

    @pytest.mark.asyncio
    async def test_web_search_api_error(self):
        """Test handling of API errors."""
        # Arrange
        tool = WebSearchTool()
        tool.api_client.search = AsyncMock(
            side_effect=Exception("API Error")
        )

        # Act & Assert
        with pytest.raises(ToolExecutionError):
            await tool.execute("test query")
```

### 6.6 Integration Tests

```python
# tests/integration/test_agent_rag_flow.py
"""Test integrated agent + RAG flow."""

import pytest
from src.agent.controller import AgentController
from src.rag.retriever import VectorRetriever
from src.database.client import SupabaseClient

@pytest.mark.asyncio
class TestAgentRAGFlow:
    """Test agent with RAG integration."""

    async def test_agent_uses_rag_for_context(
        self,
        agent_controller,
        vector_retriever,
        mock_documents
    ):
        """Test that agent uses RAG for context."""
        # Arrange
        request = AgentRequest(
            query="What is machine learning?",
            session_id="test_123",
            user_id="user_456"
        )

        # Mock RAG retrieval
        vector_retriever.retrieve = AsyncMock(
            return_value=mock_documents
        )

        # Act
        response = await agent_controller.run_agent(request)

        # Assert - verify RAG was called
        vector_retriever.retrieve.assert_called()

        # Verify response includes RAG-sourced information
        assert any(doc.source in str(response) for doc in mock_documents)
```

### References

- [Effective Python Testing With pytest](https://realpython.com/pytest-python-testing/)
- [Good Integration Practices - pytest documentation](https://docs.pytest.org/en/stable/explanation/goodpractices/)
- [Python Unit Testing Best Practices For Building Reliable Applications](https://pytest-with-eric.com/introduction/python-unit-testing-best-practices/)

---

## 7. Documentation Standards

### 7.1 Docstring Format (Google Style)

```python
# ✅ Good: Comprehensive Google-style docstrings
from typing import List, Dict, Optional, Any
from datetime import datetime

class AgentController:
    """
    Main controller for agent execution and orchestration.

    Handles the orchestration of agent workflow including tool
    initialization, execution, and result aggregation.

    Attributes:
        tools: List of tools available to the agent
        validator: Request validator instance
        logger: Logger for recording execution
        state_manager: Manager for agent state persistence

    Example:
        >>> controller = AgentController(
        ...     tools=[web_search_tool, rag_tool],
        ...     validator=validator,
        ...     logger=logger
        ... )
        >>> request = AgentRequest(
        ...     query="What is AI?",
        ...     session_id="session_123"
        ... )
        >>> response = await controller.run_agent(request)
    """

    async def run_agent(
        self,
        request: 'AgentRequest',
        timeout: Optional[int] = None
    ) -> 'AgentResponse':
        """
        Execute agent workflow for given request.

        Orchestrates the complete agent workflow including validation,
        tool execution, and response generation. Supports optional
        timeout to prevent hanging operations.

        Args:
            request: Agent request with query and metadata
            timeout: Optional timeout in seconds for the entire workflow

        Returns:
            AgentResponse containing query, results, and metadata

        Raises:
            QueryValidationError: If request validation fails
            ToolExecutionError: If any tool execution fails
            ExecutionTimeoutError: If execution exceeds timeout

        Example:
            >>> request = AgentRequest(
            ...     query="Explain quantum computing",
            ...     session_id="sess_1"
            ... )
            >>> response = await controller.run_agent(request)
            >>> print(f"Results: {response.results}")

        Note:
            If timeout is None, no timeout is enforced.
            Timeout applies to the entire workflow, not individual tools.
        """
        pass

    def _validate_request(self, request: 'AgentRequest') -> None:
        """
        Validate incoming request.

        Performs syntactic and semantic validation on the request.

        Args:
            request: Request to validate

        Raises:
            QueryValidationError: If validation fails with details
        """
        pass
```

### 7.2 Module-Level Documentation

```python
# src/agent/tools.py
"""
Agent tools for information retrieval and processing.

This module provides the base Tool class and implementations for
specific tools like web search and RAG retrieval. Tools can be
composed and executed by the agent controller.

Classes:
    BaseTool: Abstract base class for all tools
    WebSearchTool: Performs web searches via external API
    RAGTool: Performs semantic search over indexed documents
    ToolResult: Dataclass for tool execution results

Example:
    >>> from src.agent.tools import WebSearchTool
    >>> tool = WebSearchTool(api_client)
    >>> result = await tool.execute("AI trends 2025")
    >>> print(result.results)

Note:
    All tools support async execution via the execute() method.
    Tools should validate inputs before execution.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
```

### 7.3 Complex Function Documentation

```python
@dataclass
class SearchResult:
    """
    Result from a search operation.

    Attributes:
        query (str): The original search query
        results (List[Dict[str, Any]]): List of search results
        total_count (int): Total number of results found
        execution_time (float): Time taken to execute search in seconds
        relevance_scores (Optional[List[float]]): Optional relevance scores

    Example:
        >>> result = SearchResult(
        ...     query="machine learning",
        ...     results=[{"title": "ML Guide", "url": "..."}],
        ...     total_count=1,
        ...     execution_time=0.45,
        ...     relevance_scores=[0.95]
        ... )
    """
    query: str
    results: List[Dict[str, Any]]
    total_count: int
    execution_time: float
    relevance_scores: Optional[List[float]] = None
```

### 7.4 Configuration File Documentation

```yaml
# config/agent_config.yaml
"""
Agent System Configuration

Defines behavior of the agent system including retry policies,
timeouts, and model parameters.

Environment overrides:
  AGENT_MAX_RETRIES - Maximum retries for failed operations
  AGENT_TIMEOUT - Request timeout in seconds
  AGENT_MODEL - LLM model to use
"""

agent:
  max_retries: 3           # Max retries for failed tool calls
  timeout: 30              # Timeout in seconds for tool execution
  api_timeout: 30          # HTTP request timeout
  max_tokens: 2000         # Max tokens in LLM response
  model: "gpt-4"           # LLM model name
  temperature: 0.7         # Model temperature for creativity

logging:
  level: "INFO"            # Logging level
  format: "json"           # Log format (json or text)
```

### 7.5 README Documentation

```markdown
# Agentic Learning Coach - Architecture Guide

## Quick Start

```python
from src.agent.controller import AgentController
from src.agent.tools import WebSearchTool, RAGTool

controller = AgentController(
    tools=[WebSearchTool(), RAGTool()],
    config=AppConfig.from_env()
)

response = await controller.run_agent(
    AgentRequest(query="What is AI?", session_id="123")
)
```

## System Architecture

### Components

1. **Agent System** - Orchestrates execution of multiple tools
2. **RAG Pipeline** - Semantic search over indexed documents
3. **Tool System** - Pluggable tools for various operations
4. **Database Layer** - Supabase integration via repositories

See [Architecture Documentation](docs/architecture.md) for details.

## Configuration

Environment variables:

- `AGENT_MAX_RETRIES` - Max retries (default: 3)
- `AGENT_TIMEOUT` - Timeout in seconds (default: 30)
- `SUPABASE_URL` - Supabase project URL
- `SUPABASE_KEY` - Supabase API key

## Testing

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/unit/agent_system/test_controller.py

# Run with coverage
pytest --cov=src tests/
```
```

### References

- [Documenting Python Code: A Complete Guide](https://realpython.com/documenting-python-code/)
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- [PEP 257 – Docstring Conventions](https://peps.python.org/pep-0257/)
- [Python Docstrings Tutorial](https://www.datacamp.com/tutorial/docstrings-python)

---

## 8. Dependency Injection & Configuration Management

### 8.1 Container Pattern with Dependency Injector

```python
# src/shared/container.py
"""Application dependency injection container."""

from dependency_injector import containers, providers
from src.shared.config import AppConfig
from src.agent.controller import AgentController
from src.agent.tools import WebSearchTool, RAGTool
from src.rag.retriever import VectorRetriever
from src.database.client import SupabaseClient

class AppContainer(containers.DeclarativeContainer):
    """Main application container."""

    # Configuration
    config = providers.Singleton(AppConfig.from_env)

    # Database layer
    supabase_client = providers.Singleton(
        SupabaseClient,
        url=config.provided.supabase_url,
        api_key=config.provided.supabase_key
    )

    # RAG system
    embedding_service = providers.Singleton(
        EmbeddingService,
        model_name=config.provided.rag.embedding_model
    )

    vector_retriever = providers.Singleton(
        VectorRetriever,
        client=supabase_client,
        embedding_service=embedding_service,
        config=config.provided.rag
    )

    # Tools
    web_search_tool = providers.Factory(
        WebSearchTool,
        api_key=config.provided.web_search_api_key
    )

    rag_tool = providers.Factory(
        RAGTool,
        retriever=vector_retriever
    )

    # Agent system
    tool_factory = providers.Singleton(
        ToolFactory,
        web_search=web_search_tool,
        rag=rag_tool
    )

    agent_controller = providers.Singleton(
        AgentController,
        tools=[web_search_tool, rag_tool],
        config=config.provided.agent,
        state_manager=providers.Factory(StateManager, db=supabase_client)
    )

# Usage
container = AppContainer()
controller = container.agent_controller()  # Dependency injection!
```

### 8.2 Configuration Management

```python
# src/shared/config.py
"""Application configuration with environment support."""

import os
from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path

@dataclass
class AgentConfig:
    """Agent system configuration."""
    max_retries: int = 3
    timeout: int = 30
    api_timeout: int = 30
    max_tokens: int = 2000
    model: str = "gpt-4"
    temperature: float = 0.7

    @classmethod
    def from_env(cls) -> "AgentConfig":
        """Load from environment variables."""
        return cls(
            max_retries=int(os.getenv("AGENT_MAX_RETRIES", 3)),
            timeout=int(os.getenv("AGENT_TIMEOUT", 30)),
            api_timeout=int(os.getenv("AGENT_API_TIMEOUT", 30)),
            max_tokens=int(os.getenv("AGENT_MAX_TOKENS", 2000)),
            model=os.getenv("AGENT_MODEL", "gpt-4"),
            temperature=float(os.getenv("AGENT_TEMPERATURE", 0.7)),
        )

@dataclass
class RAGConfig:
    """RAG system configuration."""
    top_k: int = 10
    similarity_threshold: float = 0.7
    embedding_model: str = "text-embedding-3-small"
    max_chunk_size: int = 512
    chunk_overlap: int = 100

    @classmethod
    def from_env(cls) -> "RAGConfig":
        """Load from environment variables."""
        return cls(
            top_k=int(os.getenv("RAG_TOP_K", 10)),
            similarity_threshold=float(os.getenv("RAG_THRESHOLD", 0.7)),
            embedding_model=os.getenv(
                "RAG_EMBEDDING_MODEL",
                "text-embedding-3-small"
            ),
            max_chunk_size=int(os.getenv("RAG_CHUNK_SIZE", 512)),
            chunk_overlap=int(os.getenv("RAG_CHUNK_OVERLAP", 100)),
        )

@dataclass
class DatabaseConfig:
    """Database configuration."""
    url: str = ""
    api_key: str = ""

    @classmethod
    def from_env(cls) -> "DatabaseConfig":
        """Load from environment variables."""
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")

        if not url or not key:
            raise ConfigurationError(
                "SUPABASE_URL and SUPABASE_KEY required"
            )

        return cls(url=url, api_key=key)

@dataclass
class AppConfig:
    """Global application configuration."""
    agent: AgentConfig = field(default_factory=AgentConfig.from_env)
    rag: RAGConfig = field(default_factory=RAGConfig.from_env)
    database: DatabaseConfig = field(default_factory=DatabaseConfig.from_env)
    debug: bool = False
    log_level: str = "INFO"

    @classmethod
    def from_env(cls) -> "AppConfig":
        """Load complete configuration from environment."""
        return cls(
            agent=AgentConfig.from_env(),
            rag=RAGConfig.from_env(),
            database=DatabaseConfig.from_env(),
            debug=os.getenv("DEBUG", "false").lower() == "true",
            log_level=os.getenv("LOG_LEVEL", "INFO"),
        )
```

### 8.3 Simple Manual DI (Without Framework)

```python
# src/shared/factories.py
"""Factory functions for dependency creation."""

from typing import List
from src.agent.controller import AgentController
from src.agent.tools import Tool, WebSearchTool, RAGTool
from src.rag.retriever import VectorRetriever
from src.shared.config import AppConfig

class ServiceFactory:
    """Factory for creating service instances with dependencies."""

    def __init__(self, config: AppConfig):
        self.config = config

    def create_tools(self) -> List[Tool]:
        """Create all available tools."""
        tools = []

        if self.config.enable_web_search:
            tools.append(WebSearchTool(
                api_key=self.config.web_search_api_key,
                timeout=self.config.agent.api_timeout
            ))

        if self.config.enable_rag:
            retriever = self.create_vector_retriever()
            tools.append(RAGTool(
                retriever=retriever,
                config=self.config.rag
            ))

        return tools

    def create_vector_retriever(self) -> VectorRetriever:
        """Create vector retriever with dependencies."""
        client = SupabaseClient(
            url=self.config.database.url,
            api_key=self.config.database.api_key
        )

        embedding_service = EmbeddingService(
            model=self.config.rag.embedding_model
        )

        return VectorRetriever(
            client=client,
            embedding_service=embedding_service,
            config=self.config.rag
        )

    def create_agent_controller(self) -> AgentController:
        """Create agent controller with all dependencies."""
        tools = self.create_tools()

        return AgentController(
            tools=tools,
            config=self.config.agent,
            state_manager=StateManager(
                repository=AgentStateRepository(
                    client=SupabaseClient(
                        url=self.config.database.url,
                        api_key=self.config.database.api_key
                    )
                )
            )
        )

# Usage
config = AppConfig.from_env()
factory = ServiceFactory(config)
controller = factory.create_agent_controller()
```

### References

- [Dependency injection and inversion of control in Python](https://python-dependency-injector.ets-labs.org/introduction/di_in_python.html)
- [Dependency Injection in Python with Pydantic and Hydra - PyCon US 2025](https://us.pycon.org/2025/schedule/presentation/128/)
- [FastAPI Dependency Injection](https://fastapi.tiangolo.com/tutorial/dependencies/)

---

## 9. Async/Await Patterns

### 9.1 Concurrent Tool Execution

```python
# ✅ Good: Run multiple tools concurrently
import asyncio
from typing import List

class AgentService:
    """Execute agent with concurrent tool execution."""

    async def run_tools_concurrent(
        self,
        tools: List[Tool],
        query: str,
        timeout: Optional[int] = 30
    ) -> List[ToolResult]:
        """
        Execute multiple tools concurrently.

        Uses asyncio.gather to run all tools in parallel,
        with optional timeout protection.

        Args:
            tools: Tools to execute
            query: Query to pass to each tool
            timeout: Optional timeout in seconds

        Returns:
            List of tool results

        Raises:
            ExecutionTimeoutError: If execution exceeds timeout
        """
        try:
            # Create tasks for all tools
            tasks = [
                tool.execute(query) for tool in tools
            ]

            # Run concurrently with timeout
            results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=False),
                timeout=timeout
            )

            return results
        except asyncio.TimeoutError:
            raise ExecutionTimeoutError(
                f"Tool execution timed out after {timeout}s"
            )

# Alternative: Limited concurrency with semaphore
class RateLimitedAgentService:
    """Execute tools with rate limiting."""

    async def run_tools_limited(
        self,
        tools: List[Tool],
        query: str,
        max_concurrent: int = 3
    ) -> List[ToolResult]:
        """Run tools with concurrency limit."""
        semaphore = asyncio.Semaphore(max_concurrent)

        async def run_with_limit(tool: Tool) -> ToolResult:
            async with semaphore:
                return await tool.execute(query)

        return await asyncio.gather(*[
            run_with_limit(tool) for tool in tools
        ])
```

### 9.2 Async Context Managers for Resources

```python
# ✅ Good: Async context managers for automatic cleanup
from contextlib import asynccontextmanager

@asynccontextmanager
async def database_session():
    """Context manager for database sessions."""
    session = await create_session()
    try:
        yield session
    finally:
        await session.close()

@asynccontextmanager
async def tool_execution_context(tool: Tool):
    """Context manager for tool execution with logging."""
    logger.info(f"Starting {tool.name}")
    start_time = time.time()

    try:
        yield tool
    except Exception as e:
        logger.error(f"{tool.name} failed: {e}")
        raise
    finally:
        duration = time.time() - start_time
        logger.info(f"{tool.name} completed in {duration:.2f}s")

# Usage
async def run_tool_safe(tool: Tool, query: str):
    async with tool_execution_context(tool):
        return await tool.execute(query)
```

### 9.3 Avoid Blocking Operations

```python
# ❌ Bad: Blocking operations in async code
async def process_data_bad(query: str):
    # This blocks the event loop!
    time.sleep(1)  # Never use time.sleep in async

    # File I/O blocks
    data = open("file.txt").read()

    # CPU-intensive work blocks
    result = expensive_computation(query)

# ✅ Good: Use async equivalents and run_in_executor for blocking
async def process_data_good(query: str):
    # Use async sleep
    await asyncio.sleep(1)

    # Use async file I/O
    async with aiofiles.open("file.txt") as f:
        data = await f.read()

    # Use run_in_executor for CPU work
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None,  # Use default executor
        expensive_computation,
        query
    )

    return result
```

### 9.4 Error Handling in Concurrent Operations

```python
# ✅ Good: Collect errors from concurrent operations
async def run_tools_with_error_handling(
    tools: List[Tool],
    query: str
) -> Tuple[List[ToolResult], List[ToolError]]:
    """Run tools and collect both results and errors."""

    async def safe_execute(tool: Tool) -> Tuple[Optional[ToolResult], Optional[ToolError]]:
        try:
            result = await tool.execute(query)
            return result, None
        except Exception as e:
            error = ToolError(tool=tool.name, error=e)
            logger.warning(f"Tool {tool.name} failed: {e}")
            return None, error

    # Execute all tools
    all_results = await asyncio.gather(*[
        safe_execute(tool) for tool in tools
    ])

    # Separate results and errors
    results = [r for r, e in all_results if r is not None]
    errors = [e for r, e in all_results if e is not None]

    if errors:
        logger.warning(f"{len(errors)} tools failed")

    return results, errors
```

### 9.5 Graceful Shutdown

```python
# ✅ Good: Handle graceful shutdown
class AsyncServiceManager:
    """Manage async service lifecycle."""

    def __init__(self):
        self.tasks: Set[asyncio.Task] = set()

    async def create_task(self, coro):
        """Create task and track it."""
        task = asyncio.create_task(coro)
        self.tasks.add(task)
        task.add_done_callback(self.tasks.discard)
        return task

    async def shutdown(self, timeout: int = 5):
        """Gracefully shutdown all tasks."""
        logger.info("Shutting down services...")

        # Cancel all remaining tasks
        for task in self.tasks:
            task.cancel()

        # Wait for cancellation with timeout
        try:
            await asyncio.wait_for(
                asyncio.gather(*self.tasks, return_exceptions=True),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            logger.warning("Shutdown timeout - forcing closure")

        logger.info("Services shut down")

# Usage in main
async def main():
    manager = AsyncServiceManager()

    # Start background tasks
    await manager.create_task(background_worker())

    try:
        # Main logic
        await run_application()
    except KeyboardInterrupt:
        await manager.shutdown()
```

### References

- [Python's asyncio: A Hands-On Walkthrough](https://realpython.com/async-io-python/)
- [3 essential async patterns for building a Python service](https://www.elastic.co/blog/async-patterns-building-python-service)
- [Asyncio in Python — The Essential Guide for 2025](https://medium.com/@shweta.trrev/asyncio-in-python-the-essential-guide-for-2025-a006074ee2d1)

---

## 10. Design Patterns for Maintainability

### 10.1 Repository Pattern for Data Access

```python
# src/database/repositories/base.py
"""Base repository for data access."""

from abc import ABC, abstractmethod
from typing import TypeVar, Generic, List, Optional

T = TypeVar('T')

class Repository(ABC, Generic[T]):
    """Generic repository interface."""

    @abstractmethod
    async def get_by_id(self, id: str) -> Optional[T]:
        """Get entity by ID."""
        pass

    @abstractmethod
    async def list_all(self, limit: int = 100, offset: int = 0) -> List[T]:
        """List all entities."""
        pass

    @abstractmethod
    async def create(self, entity: T) -> T:
        """Create new entity."""
        pass

    @abstractmethod
    async def update(self, id: str, entity: T) -> T:
        """Update entity."""
        pass

    @abstractmethod
    async def delete(self, id: str) -> bool:
        """Delete entity."""
        pass

# src/database/repositories/user_repository.py
"""User data access."""

class UserRepository(Repository[User]):
    """Repository for user data access."""

    def __init__(self, client: SupabaseClient):
        self.client = client
        self.table = "users"

    async def get_by_id(self, id: str) -> Optional[User]:
        """Get user by ID."""
        data = await self.client.from_(self.table).select("*").eq("id", id).single().execute()
        return User.from_db(data) if data else None

    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        data = await self.client.from_(self.table).select("*").eq("email", email).single().execute()
        return User.from_db(data) if data else None

    async def list_all(self, limit: int = 100, offset: int = 0) -> List[User]:
        """List all users."""
        data = await self.client.from_(self.table).select("*").limit(limit).offset(offset).execute()
        return [User.from_db(row) for row in data.data]

    async def create(self, user: User) -> User:
        """Create new user."""
        data = await self.client.from_(self.table).insert(user.to_db()).execute()
        return User.from_db(data.data[0])
```

### 10.2 Factory Pattern for Tool Creation

```python
# src/agent/tool_factory.py
"""Factory for creating agent tools."""

from typing import List, Dict, Type
from src.agent.tools import Tool, WebSearchTool, RAGTool
from src.shared.config import AppConfig

class ToolFactory:
    """Factory for creating tool instances."""

    AVAILABLE_TOOLS: Dict[str, Type[Tool]] = {
        "web_search": WebSearchTool,
        "rag": RAGTool,
    }

    def __init__(self, config: AppConfig):
        self.config = config
        self._instances: Dict[str, Tool] = {}

    def create_tool(self, name: str, **kwargs) -> Tool:
        """Create a tool instance."""
        if name not in self.AVAILABLE_TOOLS:
            raise ValueError(f"Unknown tool: {name}")

        tool_class = self.AVAILABLE_TOOLS[name]
        return tool_class(**kwargs)

    def get_enabled_tools(self) -> List[Tool]:
        """Get all enabled tools."""
        tools = []

        if self.config.enable_web_search:
            tools.append(self.create_tool("web_search"))

        if self.config.enable_rag:
            tools.append(self.create_tool("rag"))

        return tools
```

### 10.3 Strategy Pattern for Different Search Strategies

```python
# src/rag/search_strategies.py
"""Different search strategies for RAG."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any

class SearchStrategy(ABC):
    """Interface for different search strategies."""

    @abstractmethod
    async def search(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """Execute search."""
        pass

class VectorSearchStrategy(SearchStrategy):
    """Vector similarity search."""

    def __init__(self, index):
        self.index = index

    async def search(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """Search using vector similarity."""
        embedding = await self.embedding_service.embed(query)
        return await self.index.similarity_search(embedding, top_k)

class BM25SearchStrategy(SearchStrategy):
    """Full-text BM25 search."""

    def __init__(self, index):
        self.index = index

    async def search(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """Search using BM25."""
        return await self.index.bm25_search(query, top_k)

class HybridSearchStrategy(SearchStrategy):
    """Hybrid vector + BM25 search."""

    def __init__(self, vector_index, bm25_index):
        self.vector_strategy = VectorSearchStrategy(vector_index)
        self.bm25_strategy = BM25SearchStrategy(bm25_index)

    async def search(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """Combine vector and BM25 results."""
        vector_results = await self.vector_strategy.search(query, top_k)
        bm25_results = await self.bm25_strategy.search(query, top_k)

        # Combine and rank results
        combined = self._merge_and_rank(vector_results, bm25_results)
        return combined[:top_k]
```

### 10.4 Observer Pattern for Event Handling

```python
# src/shared/events.py
"""Event system for application events."""

from abc import ABC, abstractmethod
from typing import List, Callable, Any
from dataclasses import dataclass

@dataclass
class Event:
    """Base event class."""
    source: str
    timestamp: str

class EventListener(ABC):
    """Base listener interface."""

    @abstractmethod
    async def handle(self, event: Event) -> None:
        pass

class EventBus:
    """Central event bus."""

    def __init__(self):
        self._listeners: Dict[str, List[EventListener]] = {}

    def subscribe(self, event_type: str, listener: EventListener) -> None:
        """Subscribe to events."""
        if event_type not in self._listeners:
            self._listeners[event_type] = []
        self._listeners[event_type].append(listener)

    async def publish(self, event: Event) -> None:
        """Publish event."""
        event_type = type(event).__name__
        listeners = self._listeners.get(event_type, [])

        # Notify all listeners
        await asyncio.gather(*[
            listener.handle(event) for listener in listeners
        ])

# Usage
@dataclass
class AgentExecutionStarted(Event):
    """Agent execution started."""
    session_id: str
    query: str

class LoggingListener(EventListener):
    async def handle(self, event: Event) -> None:
        if isinstance(event, AgentExecutionStarted):
            logger.info(f"Agent started for query: {event.query}")

# In agent
bus = EventBus()
bus.subscribe("AgentExecutionStarted", LoggingListener())

await bus.publish(AgentExecutionStarted(
    source="agent",
    timestamp=datetime.now().isoformat(),
    session_id="session_123",
    query="What is AI?"
))
```

### References

- [Python Design Patterns - Basics to Advanced (2025 Guide)](https://www.scholarhat.com/tutorial/python/python-design-patterns)
- [Design Patterns in Python](https://refactoring.guru/design-patterns/python)
- [7 Python Patterns That Helped Me Write Maintainable Code in 2025](https://medium.com/codrift/7-python-patterns-that-helped-me-write-maintainable-code-in-2025-c6c488d00f7e)

---

## Summary: Implementation Priorities

Based on your agentic learning coach architecture, prioritize implementation in this order:

### Phase 1 (Immediate)
1. **Restructure directories** - Organize by domain (agent, rag, database, dashboard)
2. **Add type hints** - Start with critical paths (controllers, main services)
3. **Create base exceptions** - Centralize exception hierarchy
4. **Extract validation** - Move validation logic to shared modules

### Phase 2 (Short term)
1. **Implement repositories** - Add database abstraction layer
2. **Create dependency injection** - Use either manual factory or Dependency Injector
3. **Add comprehensive tests** - Unit tests for controllers, services, tools
4. **Improve documentation** - Add docstrings following Google style

### Phase 3 (Medium term)
1. **Refactor large functions** - Break down complex workflows
2. **Add async patterns** - Optimize concurrent tool execution
3. **Configuration management** - Centralize all settings
4. **Event bus** - Decouple components with events

### Phase 4 (Long term)
1. **Design patterns** - Implement factory, strategy, repository patterns
2. **Performance optimization** - Add caching, rate limiting
3. **Monitoring & observability** - Comprehensive logging and metrics

---

## Key Takeaways

1. **Modularity First** - Organize by domain/responsibility, not technical layers
2. **Type Everything** - Gradual adoption of type hints improves code quality
3. **Small & Focused** - Functions <30 lines, files <400 lines
4. **DRY Consistently** - Extract common patterns into shared modules/base classes
5. **Test Everything** - Unit tests, integration tests, fixtures for DI
6. **Document Thoroughly** - Google-style docstrings for all public APIs
7. **Async Correctly** - Concurrent execution with proper error handling
8. **Inject Dependencies** - Decouple components, improve testability
9. **Handle Errors Gracefully** - Specific exceptions, proper logging
10. **Configure Externally** - Environment-based configuration, not magic numbers

