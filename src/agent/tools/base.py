"""
Base Tool Protocol and Schema Definitions

This module defines the base protocol that all agent tools must implement,
along with the ToolSchema dataclass for tool metadata.

Usage:
    >>> from src.agent.tools.base import BaseTool, ToolSchema
    >>> class MyTool(BaseTool):
    ...     @property
    ...     def schema(self) -> ToolSchema:
    ...         return ToolSchema(name="my-tool", ...)
"""

from dataclasses import dataclass, field
from typing import Protocol, Dict, Any, Optional
from src.core.types import ToolName, ToolResult


@dataclass
class ToolSchema:
    """
    Tool schema definition.

    Describes a tool's metadata, inputs, outputs, and usage.
    """

    name: ToolName
    description: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    requires_approval: bool = False
    example: Optional[Dict[str, Any]] = None
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert schema to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
            "output_schema": self.output_schema,
            "requires_approval": self.requires_approval,
            "example": self.example,
            "tags": self.tags,
        }


class BaseTool(Protocol):
    """
    Protocol for tool implementations.

    Any class implementing this protocol can be registered and used
    as a tool in the agent system.

    Example:
        >>> class SearchTool:
        ...     @property
        ...     def schema(self) -> ToolSchema:
        ...         return ToolSchema(
        ...             name="search",
        ...             description="Search for content",
        ...             input_schema={"query": "string"},
        ...             output_schema={"results": "array"}
        ...         )
        ...
        ...     async def execute(self, **kwargs) -> ToolResult:
        ...         query = kwargs.get("query")
        ...         # Perform search...
        ...         return {"success": True, "data": {...}}
        ...
        ...     async def validate_input(self, **kwargs) -> bool:
        ...         return "query" in kwargs
    """

    @property
    def schema(self) -> ToolSchema:
        """
        Get tool schema.

        Returns:
            ToolSchema describing this tool
        """
        ...

    async def execute(self, **kwargs: Any) -> ToolResult:
        """
        Execute the tool with given arguments.

        Args:
            **kwargs: Tool-specific arguments

        Returns:
            ToolResult with success status and data

        Raises:
            ToolExecutionError: If execution fails
        """
        ...

    async def validate_input(self, **kwargs: Any) -> bool:
        """
        Validate input arguments before execution.

        Args:
            **kwargs: Arguments to validate

        Returns:
            True if valid, False otherwise
        """
        ...


class BaseToolImpl:
    """
    Base implementation class for tools.

    Provides common functionality that tools can inherit from.
    This is optional - tools can implement BaseTool protocol directly.
    """

    def __init__(self):
        """Initialize base tool."""
        self._schema: Optional[ToolSchema] = None

    @property
    def name(self) -> ToolName:
        """Get tool name from schema."""
        return self.schema.name

    @property
    def description(self) -> str:
        """Get tool description from schema."""
        return self.schema.description

    @property
    def schema(self) -> ToolSchema:
        """
        Get tool schema.

        Subclasses should override this to return their schema.
        """
        if self._schema is None:
            raise NotImplementedError("Subclass must provide schema")
        return self._schema

    async def execute(self, **kwargs: Any) -> ToolResult:
        """
        Execute the tool.

        Subclasses must override this method.
        """
        raise NotImplementedError("Subclass must implement execute()")

    async def validate_input(self, **kwargs: Any) -> bool:
        """
        Default validation: check that all required inputs are present.

        Subclasses can override for custom validation.
        """
        # By default, we can't validate without knowing required fields
        # Subclasses should implement proper validation
        return True

    def _create_success_result(self, data: Dict[str, Any]) -> ToolResult:
        """Helper to create success result."""
        return {
            "success": True,
            "data": data,
            "error": None,
        }

    def _create_error_result(self, error: str) -> ToolResult:
        """Helper to create error result."""
        return {
            "success": False,
            "data": {},
            "error": error,
        }


def is_tool(obj: Any) -> bool:
    """
    Check if an object implements the BaseTool protocol.

    Args:
        obj: Object to check

    Returns:
        True if object is a tool
    """
    return (
        hasattr(obj, "schema")
        and hasattr(obj, "execute")
        and hasattr(obj, "validate_input")
        and callable(getattr(obj, "execute"))
        and callable(getattr(obj, "validate_input"))
    )
