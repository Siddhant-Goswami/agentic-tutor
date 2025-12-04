"""
Tool System Demo

Demonstrates how to use the new refactored tool system.

This example shows:
1. Creating a custom tool
2. Registering tools in the registry
3. Executing tools
4. Error handling
5. Filtering tools by tags
"""

import asyncio
from src.agent.tools.base import BaseToolImpl, ToolSchema
from src.agent.tools.registry import ToolRegistry
from src.agent.tools.schemas import get_all_schemas
from src.core.types import ToolResult


# =============================================================================
# Example 1: Create a Simple Tool
# =============================================================================

class GreetingTool(BaseToolImpl):
    """A simple greeting tool."""

    def __init__(self):
        super().__init__()
        self._schema = ToolSchema(
            name="greet",
            description="Greets a person by name",
            input_schema={"name": "string"},
            output_schema={"greeting": "string"},
            tags=["example", "simple"],
        )

    async def execute(self, **kwargs) -> ToolResult:
        """Execute greeting."""
        name = kwargs.get("name", "World")
        greeting = f"Hello, {name}!"
        return self._create_success_result({"greeting": greeting})

    async def validate_input(self, **kwargs) -> bool:
        """Validate that name is provided."""
        return "name" in kwargs and isinstance(kwargs["name"], str)


# =============================================================================
# Example 2: Create a Calculator Tool
# =============================================================================

class CalculatorTool(BaseToolImpl):
    """A simple calculator tool."""

    def __init__(self):
        super().__init__()
        self._schema = ToolSchema(
            name="calculate",
            description="Performs basic arithmetic operations",
            input_schema={
                "operation": "string (add, subtract, multiply, divide)",
                "a": "number",
                "b": "number",
            },
            output_schema={"result": "number"},
            tags=["example", "math"],
        )

    async def execute(self, **kwargs) -> ToolResult:
        """Execute calculation."""
        operation = kwargs.get("operation")
        a = kwargs.get("a")
        b = kwargs.get("b")

        operations = {
            "add": lambda x, y: x + y,
            "subtract": lambda x, y: x - y,
            "multiply": lambda x, y: x * y,
            "divide": lambda x, y: x / y if y != 0 else None,
        }

        if operation not in operations:
            return self._create_error_result(f"Unknown operation: {operation}")

        result = operations[operation](a, b)

        if result is None:
            return self._create_error_result("Division by zero")

        return self._create_success_result({"result": result})

    async def validate_input(self, **kwargs) -> bool:
        """Validate calculator inputs."""
        required = ["operation", "a", "b"]
        if not all(k in kwargs for k in required):
            return False

        # Check types
        if not isinstance(kwargs["operation"], str):
            return False
        if not isinstance(kwargs["a"], (int, float)):
            return False
        if not isinstance(kwargs["b"], (int, float)):
            return False

        return True


# =============================================================================
# Demo Functions
# =============================================================================

async def demo_basic_usage():
    """Demonstrate basic tool registration and execution."""
    print("\n" + "=" * 60)
    print("DEMO 1: Basic Tool Usage")
    print("=" * 60)

    # Create registry
    registry = ToolRegistry()
    print(f"✓ Created registry: {registry}")

    # Register tools
    greeting_tool = GreetingTool()
    calculator_tool = CalculatorTool()

    registry.register(greeting_tool)
    registry.register(calculator_tool)
    print(f"✓ Registered 2 tools: {registry.list_tools()}")

    # Execute greeting tool
    print("\n--- Executing greeting tool ---")
    result = await registry.execute("greet", name="Alice")
    print(f"Success: {result['success']}")
    print(f"Greeting: {result['data']['greeting']}")

    # Execute calculator tool
    print("\n--- Executing calculator tool ---")
    result = await registry.execute("calculate", operation="add", a=10, b=5)
    print(f"Success: {result['success']}")
    print(f"10 + 5 = {result['data']['result']}")

    result = await registry.execute("calculate", operation="multiply", a=7, b=6)
    print(f"7 * 6 = {result['data']['result']}")


async def demo_error_handling():
    """Demonstrate error handling."""
    print("\n" + "=" * 60)
    print("DEMO 2: Error Handling")
    print("=" * 60)

    registry = ToolRegistry()
    registry.register(CalculatorTool())

    # Test validation error
    print("\n--- Testing validation error (missing argument) ---")
    try:
        await registry.execute("calculate", operation="add", a=10)
    except Exception as e:
        print(f"✓ Caught expected error: {type(e).__name__}: {e}")

    # Test execution error
    print("\n--- Testing execution error (division by zero) ---")
    result = await registry.execute("calculate", operation="divide", a=10, b=0)
    print(f"Success: {result['success']}")
    print(f"Error: {result['error']}")


async def demo_tool_discovery():
    """Demonstrate tool discovery features."""
    print("\n" + "=" * 60)
    print("DEMO 3: Tool Discovery")
    print("=" * 60)

    registry = ToolRegistry()
    registry.register(GreetingTool())
    registry.register(CalculatorTool())

    # List all tools
    print("\n--- All Tools ---")
    for tool_name in registry.list_tools():
        schema = registry.get_schema(tool_name)
        print(f"  • {tool_name}: {schema.description}")

    # Filter by tag
    print("\n--- Tools with 'math' tag ---")
    math_tools = registry.get_tools_by_tag("math")
    print(f"  {math_tools}")

    # Get tool schemas
    print("\n--- Tool Schemas ---")
    schemas = registry.list_schemas()
    for name, schema in schemas.items():
        print(f"  • {name}")
        print(f"    Input: {schema.input_schema}")
        print(f"    Output: {schema.output_schema}")
        print(f"    Tags: {schema.tags}")


async def demo_all_built_in_schemas():
    """Demonstrate accessing built-in tool schemas."""
    print("\n" + "=" * 60)
    print("DEMO 4: Built-in Tool Schemas")
    print("=" * 60)

    schemas = get_all_schemas()
    print(f"\n✓ Found {len(schemas)} built-in tool schemas:")

    for name, schema in schemas.items():
        approval_marker = " [REQUIRES APPROVAL]" if schema.requires_approval else ""
        print(f"\n  {name}{approval_marker}")
        print(f"    {schema.description[:80]}...")
        print(f"    Tags: {', '.join(schema.tags)}")


# =============================================================================
# Main
# =============================================================================

async def main():
    """Run all demos."""
    print("\n" + "=" * 60)
    print("TOOL SYSTEM DEMO")
    print("Demonstrating the new refactored tool system")
    print("=" * 60)

    await demo_basic_usage()
    await demo_error_handling()
    await demo_tool_discovery()
    await demo_all_built_in_schemas()

    print("\n" + "=" * 60)
    print("DEMO COMPLETE!")
    print("=" * 60)
    print("\nKey Takeaways:")
    print("  • Tools implement BaseToolImpl or BaseTool protocol")
    print("  • Registry manages tool registration and execution")
    print("  • Built-in validation and error handling")
    print("  • Schemas separated from implementation")
    print("  • Easy to discover and filter tools by tags")


if __name__ == "__main__":
    asyncio.run(main())
