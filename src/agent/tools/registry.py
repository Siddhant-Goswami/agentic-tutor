"""
Tool Registry

Manages registration, discovery, and execution of agent tools.
The registry acts as a central point for tool management.

Usage:
    >>> from src.agent.tools.registry import ToolRegistry
    >>> from src.agent.tools.user_context_tool import UserContextTool
    >>>
    >>> registry = ToolRegistry()
    >>> registry.register(UserContextTool(user_repo))
    >>> result = await registry.execute("get-user-context", user_id="123")
"""

import logging
from typing import Dict, List, Optional
from src.core.types import ToolName, ToolResult
from src.core.exceptions import ToolNotFoundError, ToolExecutionError, ToolValidationError
from src.agent.tools.base import BaseTool, ToolSchema, is_tool

logger = logging.getLogger(__name__)


class ToolRegistry:
    """
    Registry for managing agent tools.

    Provides methods to register tools, list available tools,
    and execute tools by name.
    """

    def __init__(self):
        """Initialize empty tool registry."""
        self._tools: Dict[ToolName, BaseTool] = {}
        logger.info("Tool registry initialized")

    def register(self, tool: BaseTool) -> None:
        """
        Register a tool in the registry.

        Args:
            tool: Tool instance implementing BaseTool protocol

        Raises:
            TypeError: If tool doesn't implement BaseTool protocol
            ValueError: If tool with same name already registered
        """
        if not is_tool(tool):
            raise TypeError(
                f"Object {tool} does not implement BaseTool protocol"
            )

        schema = tool.schema
        tool_name = schema.name

        if tool_name in self._tools:
            logger.warning(f"Overwriting existing tool: {tool_name}")

        self._tools[tool_name] = tool
        logger.info(
            f"Registered tool: {tool_name} (approval_required={schema.requires_approval})"
        )

    def unregister(self, tool_name: ToolName) -> bool:
        """
        Unregister a tool from the registry.

        Args:
            tool_name: Name of tool to unregister

        Returns:
            True if tool was unregistered, False if not found
        """
        if tool_name in self._tools:
            del self._tools[tool_name]
            logger.info(f"Unregistered tool: {tool_name}")
            return True
        return False

    def get(self, tool_name: ToolName) -> BaseTool:
        """
        Get a tool by name.

        Args:
            tool_name: Name of the tool

        Returns:
            Tool instance

        Raises:
            ToolNotFoundError: If tool not found
        """
        tool = self._tools.get(tool_name)
        if not tool:
            available = list(self._tools.keys())
            raise ToolNotFoundError(
                f"Tool '{tool_name}' not found. Available: {available}"
            )
        return tool

    def has_tool(self, tool_name: ToolName) -> bool:
        """
        Check if tool is registered.

        Args:
            tool_name: Name of the tool

        Returns:
            True if tool is registered
        """
        return tool_name in self._tools

    def list_tools(self) -> List[ToolName]:
        """
        List all registered tool names.

        Returns:
            List of tool names
        """
        return list(self._tools.keys())

    def list_schemas(self) -> Dict[ToolName, ToolSchema]:
        """
        List all tool schemas.

        Returns:
            Dictionary mapping tool names to schemas
        """
        return {name: tool.schema for name, tool in self._tools.items()}

    def get_schema(self, tool_name: ToolName) -> ToolSchema:
        """
        Get schema for a specific tool.

        Args:
            tool_name: Name of the tool

        Returns:
            Tool schema

        Raises:
            ToolNotFoundError: If tool not found
        """
        tool = self.get(tool_name)
        return tool.schema

    async def execute(self, tool_name: ToolName, **kwargs) -> ToolResult:
        """
        Execute a tool by name with given arguments.

        Args:
            tool_name: Name of tool to execute
            **kwargs: Tool-specific arguments

        Returns:
            ToolResult with success status and data

        Raises:
            ToolNotFoundError: If tool not found
            ToolValidationError: If input validation fails
            ToolExecutionError: If execution fails
        """
        logger.info(f"Executing tool: {tool_name}")
        logger.debug(f"Tool arguments: {kwargs}")

        # Get tool
        try:
            tool = self.get(tool_name)
        except ToolNotFoundError:
            logger.error(f"Tool not found: {tool_name}")
            raise

        # Validate input
        try:
            is_valid = await tool.validate_input(**kwargs)
            if not is_valid:
                error_msg = f"Invalid input for tool: {tool_name}"
                logger.error(error_msg)
                raise ToolValidationError(
                    tool_name, {"error": "Input validation failed"}
                )
        except Exception as e:
            if isinstance(e, ToolValidationError):
                raise
            logger.error(f"Validation error for {tool_name}: {e}")
            raise ToolValidationError(
                tool_name, {"error": str(e), "validation_exception": type(e).__name__}
            )

        # Execute tool
        try:
            result = await tool.execute(**kwargs)
            logger.info(
                f"Tool {tool_name} executed: success={result.get('success', False)}"
            )
            return result
        except Exception as e:
            logger.error(f"Execution error for {tool_name}: {e}", exc_info=True)
            raise ToolExecutionError(
                tool_name, str(e)
            )

    def get_tools_by_tag(self, tag: str) -> List[ToolName]:
        """
        Get tools that have a specific tag.

        Args:
            tag: Tag to filter by

        Returns:
            List of tool names with the tag
        """
        return [
            name
            for name, tool in self._tools.items()
            if tag in tool.schema.tags
        ]

    def get_approval_required_tools(self) -> List[ToolName]:
        """
        Get tools that require user approval before execution.

        Returns:
            List of tool names requiring approval
        """
        return [
            name
            for name, tool in self._tools.items()
            if tool.schema.requires_approval
        ]

    def clear(self) -> None:
        """Clear all registered tools."""
        count = len(self._tools)
        self._tools.clear()
        logger.info(f"Cleared {count} tools from registry")

    def __len__(self) -> int:
        """Get number of registered tools."""
        return len(self._tools)

    def __contains__(self, tool_name: ToolName) -> bool:
        """Check if tool is in registry."""
        return tool_name in self._tools

    def __repr__(self) -> str:
        """String representation of registry."""
        tools = ", ".join(self._tools.keys())
        return f"ToolRegistry({len(self._tools)} tools: {tools})"
