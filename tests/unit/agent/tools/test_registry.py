"""
Tests for Tool Registry

Tests tool registration, discovery, and execution.
"""

import pytest
from src.agent.tools.registry import ToolRegistry
from src.agent.tools.base import ToolSchema, BaseToolImpl
from src.core.exceptions import ToolNotFoundError, ToolValidationError
from src.core.types import ToolResult


class MockTool(BaseToolImpl):
    """Mock tool for testing."""

    def __init__(self, name: str = "mock-tool", requires_approval: bool = False):
        super().__init__()
        self._schema = ToolSchema(
            name=name,
            description="A mock tool for testing",
            input_schema={"arg1": "string", "arg2": "integer"},
            output_schema={"result": "string"},
            requires_approval=requires_approval,
            tags=["test", "mock"],
        )

    async def execute(self, **kwargs) -> ToolResult:
        """Execute mock tool."""
        return self._create_success_result({"result": "success", "args": kwargs})

    async def validate_input(self, **kwargs) -> bool:
        """Validate that arg1 is present."""
        return "arg1" in kwargs


class FailingTool(BaseToolImpl):
    """Tool that always fails for testing."""

    def __init__(self):
        super().__init__()
        self._schema = ToolSchema(
            name="failing-tool",
            description="Tool that fails",
            input_schema={"arg": "string"},
            output_schema={"result": "string"},
        )

    async def execute(self, **kwargs) -> ToolResult:
        """Always fail."""
        raise RuntimeError("Tool execution failed")

    async def validate_input(self, **kwargs) -> bool:
        """Always valid."""
        return True


class TestToolRegistry:
    """Tests for ToolRegistry."""

    def test_init(self):
        """Test registry initialization."""
        registry = ToolRegistry()
        assert len(registry) == 0
        assert registry.list_tools() == []

    def test_register_tool(self):
        """Test tool registration."""
        registry = ToolRegistry()
        tool = MockTool()

        registry.register(tool)

        assert len(registry) == 1
        assert "mock-tool" in registry
        assert registry.has_tool("mock-tool")

    def test_register_duplicate_tool_overwrites(self):
        """Test that registering same tool twice overwrites."""
        registry = ToolRegistry()
        tool1 = MockTool("duplicate")
        tool2 = MockTool("duplicate")

        registry.register(tool1)
        registry.register(tool2)

        assert len(registry) == 1

    def test_unregister_tool(self):
        """Test tool unregistration."""
        registry = ToolRegistry()
        tool = MockTool()

        registry.register(tool)
        assert registry.has_tool("mock-tool")

        result = registry.unregister("mock-tool")
        assert result is True
        assert not registry.has_tool("mock-tool")

    def test_unregister_nonexistent_tool(self):
        """Test unregistering tool that doesn't exist."""
        registry = ToolRegistry()
        result = registry.unregister("nonexistent")
        assert result is False

    def test_get_tool(self):
        """Test getting tool by name."""
        registry = ToolRegistry()
        tool = MockTool()
        registry.register(tool)

        retrieved = registry.get("mock-tool")
        assert retrieved is tool

    def test_get_nonexistent_tool_raises_error(self):
        """Test that getting nonexistent tool raises error."""
        registry = ToolRegistry()

        with pytest.raises(ToolNotFoundError, match="mock-tool.*not found"):
            registry.get("mock-tool")

    def test_list_tools(self):
        """Test listing all tools."""
        registry = ToolRegistry()
        tool1 = MockTool("tool1")
        tool2 = MockTool("tool2")

        registry.register(tool1)
        registry.register(tool2)

        tools = registry.list_tools()
        assert len(tools) == 2
        assert "tool1" in tools
        assert "tool2" in tools

    def test_list_schemas(self):
        """Test listing all tool schemas."""
        registry = ToolRegistry()
        tool = MockTool()
        registry.register(tool)

        schemas = registry.list_schemas()
        assert len(schemas) == 1
        assert "mock-tool" in schemas
        assert schemas["mock-tool"].name == "mock-tool"

    def test_get_schema(self):
        """Test getting specific tool schema."""
        registry = ToolRegistry()
        tool = MockTool()
        registry.register(tool)

        schema = registry.get_schema("mock-tool")
        assert schema.name == "mock-tool"
        assert schema.description == "A mock tool for testing"

    @pytest.mark.asyncio
    async def test_execute_tool_success(self):
        """Test successful tool execution."""
        registry = ToolRegistry()
        tool = MockTool()
        registry.register(tool)

        result = await registry.execute("mock-tool", arg1="test", arg2=42)

        assert result["success"] is True
        assert result["data"]["result"] == "success"
        assert result["data"]["args"]["arg1"] == "test"

    @pytest.mark.asyncio
    async def test_execute_nonexistent_tool_raises_error(self):
        """Test executing nonexistent tool raises error."""
        registry = ToolRegistry()

        with pytest.raises(ToolNotFoundError):
            await registry.execute("nonexistent")

    @pytest.mark.asyncio
    async def test_execute_with_invalid_input_raises_error(self):
        """Test that invalid input raises validation error."""
        registry = ToolRegistry()
        tool = MockTool()
        registry.register(tool)

        # Missing required arg1
        with pytest.raises(ToolValidationError):
            await registry.execute("mock-tool", arg2=42)

    def test_get_tools_by_tag(self):
        """Test filtering tools by tag."""
        registry = ToolRegistry()
        tool1 = MockTool("tool1")
        tool2 = MockTool("tool2")

        registry.register(tool1)
        registry.register(tool2)

        test_tools = registry.get_tools_by_tag("test")
        assert len(test_tools) == 2

        mock_tools = registry.get_tools_by_tag("mock")
        assert len(mock_tools) == 2

    def test_get_approval_required_tools(self):
        """Test getting tools that require approval."""
        registry = ToolRegistry()
        tool1 = MockTool("normal", requires_approval=False)
        tool2 = MockTool("sensitive", requires_approval=True)

        registry.register(tool1)
        registry.register(tool2)

        approval_required = registry.get_approval_required_tools()
        assert len(approval_required) == 1
        assert "sensitive" in approval_required

    def test_clear(self):
        """Test clearing all tools."""
        registry = ToolRegistry()
        registry.register(MockTool("tool1"))
        registry.register(MockTool("tool2"))

        assert len(registry) == 2

        registry.clear()

        assert len(registry) == 0
        assert registry.list_tools() == []

    def test_repr(self):
        """Test string representation."""
        registry = ToolRegistry()
        registry.register(MockTool())

        repr_str = repr(registry)
        assert "ToolRegistry" in repr_str
        assert "1 tools" in repr_str
        assert "mock-tool" in repr_str
