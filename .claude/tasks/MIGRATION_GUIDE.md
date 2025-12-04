# Migration Guide: Old to New Tool System

**Date:** 2025-12-02
**Version:** 1.0
**Status:** Phase 2 Refactoring Complete

This guide helps you migrate from the old monolithic tool system to the new modular architecture.

---

## Overview of Changes

### What Changed

| Aspect | Old Structure | New Structure |
|--------|--------------|---------------|
| **Location** | `agent/tools.py` (754 lines) | `src/agent/tools/` (3 modules, ~700 lines) |
| **Tool Schemas** | Mixed with implementation | Separate `schemas.py` file |
| **Tool Registration** | Hardcoded dictionary | Protocol-based registry |
| **Tool Interface** | Implicit | Explicit `BaseTool` protocol |
| **Validation** | Manual in each tool | Built into registry |
| **Error Handling** | Custom per tool | Centralized exceptions |

### Why We Changed It

✅ **Modularity** - Easier to understand and maintain
✅ **Extensibility** - Simple to add new tools
✅ **Testability** - Each component tested independently
✅ **Type Safety** - Protocol-based design with type hints
✅ **Reusability** - Shared base classes and utilities

---

## Migration Path

### Phase 1: Update Imports ✅

**Old Code:**
```python
from agent.tools import ToolRegistry
```

**New Code:**
```python
from src.agent.tools.registry import ToolRegistry
from src.agent.tools.schemas import get_all_schemas
from src.agent.tools.base import BaseTool, BaseToolImpl
```

### Phase 2: Create New Tools

**Old Way (agent/tools.py):**
```python
class ToolRegistry:
    def __init__(self):
        # Schemas hardcoded in methods
        self.tools = {
            "my-tool": self._my_tool_schema()
        }

    def _my_tool_schema(self):
        return {...}  # Schema dict

    async def execute_tool(self, name, args):
        if name == "my-tool":
            # Implementation here
            pass
```

**New Way (Clean Separation):**

**Step 1: Define Schema** (`src/agent/tools/schemas.py`):
```python
from src.agent.tools.base import ToolSchema

def my_tool_schema() -> ToolSchema:
    return ToolSchema(
        name="my-tool",
        description="Does something useful",
        input_schema={"arg1": "string"},
        output_schema={"result": "string"},
        tags=["category", "feature"],
    )
```

**Step 2: Implement Tool** (`src/agent/tools/my_tool.py`):
```python
from src.agent.tools.base import BaseToolImpl
from src.agent.tools.schemas import my_tool_schema
from src.core.types import ToolResult

class MyTool(BaseToolImpl):
    def __init__(self, dependencies):
        super().__init__()
        self._schema = my_tool_schema()
        self.dependencies = dependencies

    async def execute(self, **kwargs) -> ToolResult:
        """Execute the tool."""
        try:
            result = self._do_work(kwargs)
            return self._create_success_result({"result": result})
        except Exception as e:
            return self._create_error_result(str(e))

    async def validate_input(self, **kwargs) -> bool:
        """Validate inputs."""
        return "arg1" in kwargs
```

**Step 3: Register Tool**:
```python
from src.agent.tools.registry import ToolRegistry
from src.agent.tools.my_tool import MyTool

registry = ToolRegistry()
registry.register(MyTool(dependencies))
```

### Phase 3: Update Tool Execution

**Old:**
```python
result = await old_registry.execute_tool("my-tool", args={"arg1": "value"})
```

**New:**
```python
result = await registry.execute("my-tool", arg1="value")
```

---

## Detailed Migration Examples

### Example 1: Simple Tool Migration

**Before (agent/tools.py):**
```python
def _greet_schema(self):
    return {
        "name": "greet",
        "description": "Greets user",
        "input_schema": {"name": "string"},
        "output_schema": {"greeting": "string"}
    }

async def execute_tool(self, name, args):
    if name == "greet":
        return {"greeting": f"Hello, {args['name']}!"}
```

**After (src/agent/tools/greet_tool.py):**
```python
from src.agent.tools.base import BaseToolImpl, ToolSchema

class GreetTool(BaseToolImpl):
    def __init__(self):
        super().__init__()
        self._schema = ToolSchema(
            name="greet",
            description="Greets user",
            input_schema={"name": "string"},
            output_schema={"greeting": "string"},
            tags=["greeting", "simple"],
        )

    async def execute(self, **kwargs) -> ToolResult:
        name = kwargs.get("name", "World")
        return self._create_success_result({
            "greeting": f"Hello, {name}!"
        })

    async def validate_input(self, **kwargs) -> bool:
        return "name" in kwargs
```

### Example 2: Tool with Dependencies

**Before:**
```python
class ToolRegistry:
    def __init__(self, supabase_client, openai_client):
        self.supabase = supabase_client
        self.openai = openai_client
```

**After:**
```python
class SearchTool(BaseToolImpl):
    """Tool with external dependencies."""

    def __init__(self, supabase_client, openai_client):
        super().__init__()
        self._schema = search_tool_schema()
        self.supabase = supabase_client
        self.openai = openai_client

    async def execute(self, **kwargs) -> ToolResult:
        # Use self.supabase and self.openai
        results = await self.supabase.query(...)
        return self._create_success_result({"results": results})
```

### Example 3: Tool Requiring Approval

**Schema:**
```python
def dangerous_tool_schema() -> ToolSchema:
    return ToolSchema(
        name="delete-data",
        description="Deletes user data",
        input_schema={"user_id": "string"},
        output_schema={"deleted": "boolean"},
        requires_approval=True,  # ← Mark as requiring approval
        tags=["dangerous", "destructive"],
    )
```

**Usage:**
```python
# Check if tool requires approval
schema = registry.get_schema("delete-data")
if schema.requires_approval:
    # Show approval UI to user
    user_approved = await show_approval_dialog(schema)
    if not user_approved:
        return
```

---

## Configuration Migration

### Old Configuration
```python
# agent/tools.py
class ToolRegistry:
    def __init__(
        self,
        supabase_url: str,
        supabase_key: str,
        openai_api_key: str,
    ):
        self.supabase_url = supabase_url
        # ...
```

### New Configuration
```python
# Use centralized config
from src.core.config import AppConfig

config = AppConfig.from_env()

# Create tools with config
from src.agent.tools.registry import ToolRegistry
registry = ToolRegistry()

# Register tools with dependencies from config
from src.agent.tools.search_tool import SearchTool
search_tool = SearchTool(
    supabase_url=config.database.url,
    supabase_key=config.database.key,
)
registry.register(search_tool)
```

---

## Testing Migration

### Old Tests
```python
# Hard to test - everything coupled
def test_tool():
    registry = ToolRegistry(url, key, api_key)
    result = await registry.execute_tool("search", args={...})
    assert result["success"]
```

### New Tests
```python
# Easy to test - use mocks
from src.agent.tools.registry import ToolRegistry

def test_tool():
    # Create mock tool
    mock_tool = MockTool()

    # Test registry
    registry = ToolRegistry()
    registry.register(mock_tool)

    # Test execution
    result = await registry.execute("mock-tool", arg="value")
    assert result["success"]
```

**Example Mock:**
```python
class MockTool(BaseToolImpl):
    def __init__(self):
        super().__init__()
        self._schema = ToolSchema(name="mock", ...)

    async def execute(self, **kwargs):
        return self._create_success_result({"test": "data"})
```

---

## Common Migration Issues

### Issue 1: Import Errors

**Problem:**
```python
ModuleNotFoundError: No module named 'src'
```

**Solution:**
```python
# Add project root to PYTHONPATH
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Or use relative imports from src/
from src.agent.tools.registry import ToolRegistry
```

### Issue 2: Schema Format Changed

**Problem:** Old schemas used plain dictionaries

**Solution:** Use `ToolSchema` dataclass
```python
# Old
schema = {"name": "tool", "description": "...", ...}

# New
from src.agent.tools.base import ToolSchema
schema = ToolSchema(name="tool", description="...", ...)
```

### Issue 3: Tool Execution Changed

**Problem:** Args passed differently

**Solution:**
```python
# Old
await registry.execute_tool("tool", args={"key": "value"})

# New (args as kwargs)
await registry.execute("tool", key="value")
```

---

## Gradual Migration Strategy

You can migrate gradually without breaking existing code:

### Step 1: Both Systems Coexist
```python
# Keep old system running
from agent.tools import ToolRegistry as OldRegistry

# Add new system alongside
from src.agent.tools.registry import ToolRegistry as NewRegistry

old_registry = OldRegistry(...)
new_registry = NewRegistry()
```

### Step 2: Migrate One Tool at a Time
```python
# Migrate "greet" tool first
new_registry.register(GreetTool())

# Use new registry for migrated tools
if tool_name in new_registry:
    result = await new_registry.execute(tool_name, **args)
else:
    result = await old_registry.execute_tool(tool_name, args)
```

### Step 3: Deprecate Old System
Once all tools migrated, remove old registry.

---

## Benefits After Migration

✅ **Cleaner Code** - Schemas separated from implementation
✅ **Easier Testing** - Mock tools, test registry independently
✅ **Better Type Safety** - Protocol-based with type hints
✅ **Simpler Extension** - Just implement BaseTool protocol
✅ **Centralized Validation** - Registry handles validation
✅ **Better Error Handling** - Consistent exceptions
✅ **Tool Discovery** - Filter by tags, check approval status

---

## Quick Reference

### Old → New Mapping

| Old | New | Location |
|-----|-----|----------|
| `agent/tools.py` | `src/agent/tools/` | Multiple files |
| `ToolRegistry.__init__()` | `ToolRegistry.register()` | `registry.py` |
| `_tool_schema()` methods | `tool_schema()` functions | `schemas.py` |
| `execute_tool(name, args)` | `execute(name, **kwargs)` | `registry.py` |
| Schema dict | `ToolSchema` dataclass | `base.py` |

### Import Cheat Sheet

```python
# Core
from src.core.config import AppConfig
from src.core.exceptions import ToolNotFoundError, ToolExecutionError
from src.core.types import ToolResult

# Tool System
from src.agent.tools.base import BaseTool, BaseToolImpl, ToolSchema
from src.agent.tools.registry import ToolRegistry
from src.agent.tools.schemas import get_all_schemas, get_schema

# Specific Tools (after migration)
from src.agent.tools.search_tool import SearchTool
from src.agent.tools.user_context_tool import UserContextTool
```

---

## Need Help?

1. **Check examples:** `examples/tool_system_demo.py`
2. **Read tests:** `tests/unit/agent/tools/test_registry.py`
3. **Review plan:** `.claude/tasks/codebase-refactoring-plan.md`

---

**Migration Status:** ✅ Tool system foundation complete
**Next:** Migrate remaining 7 built-in tools from old to new system
