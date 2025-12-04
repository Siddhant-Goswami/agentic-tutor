"""
Exception Hierarchy for Agentic Learning Coach

This module defines a comprehensive exception hierarchy for the application,
providing specific exception types for different error scenarios.

All application exceptions inherit from AgenticTutorError, making it easy to
catch all application-specific errors.

Usage:
    >>> from src.core.exceptions import ToolNotFoundError
    >>> raise ToolNotFoundError("search-tool")

Exception Hierarchy:
    AgenticTutorError
    ├── ConfigurationError
    ├── DatabaseError
    │   ├── ConnectionError
    │   ├── QueryError
    │   └── RepositoryError
    ├── AgentError
    │   ├── AgentExecutionError
    │   ├── AgentTimeoutError
    │   ├── PlanningError
    │   └── ReflectionError
    ├── ToolError
    │   ├── ToolNotFoundError
    │   ├── ToolExecutionError
    │   └── ToolValidationError
    ├── RAGError
    │   ├── RetrievalError
    │   ├── SynthesisError
    │   ├── EvaluationError
    │   └── EmbeddingError
    ├── IngestionError
    │   ├── ExtractionError
    │   ├── ChunkingError
    │   └── IndexingError
    ├── UIError
    │   ├── RenderingError
    │   └── TemplateError
    └── IntegrationError
        ├── APIError
        └── AuthenticationError
"""


class AgenticTutorError(Exception):
    """
    Base exception for all application errors.

    All custom exceptions in the application should inherit from this class.
    This makes it easy to catch all application-specific errors.
    """

    def __init__(self, message: str, details: dict = None):
        """
        Initialize exception.

        Args:
            message: Human-readable error message
            details: Optional dictionary with additional error context
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __str__(self) -> str:
        if self.details:
            return f"{self.message} | Details: {self.details}"
        return self.message


# =============================================================================
# Configuration Errors
# =============================================================================


class ConfigurationError(AgenticTutorError):
    """Configuration-related errors (missing env vars, invalid config, etc.)."""

    pass


# =============================================================================
# Database Errors
# =============================================================================


class DatabaseError(AgenticTutorError):
    """Base class for database-related errors."""

    pass


class ConnectionError(DatabaseError):
    """Database connection errors."""

    pass


class QueryError(DatabaseError):
    """Database query execution errors."""

    pass


class RepositoryError(DatabaseError):
    """Repository operation errors."""

    pass


# =============================================================================
# Agent Errors
# =============================================================================


class AgentError(AgenticTutorError):
    """Base class for agent-related errors."""

    pass


class AgentExecutionError(AgentError):
    """Agent execution failed unexpectedly."""

    pass


class AgentTimeoutError(AgentError):
    """Agent exceeded maximum iterations."""

    def __init__(self, max_iterations: int, message: str = None):
        if message is None:
            message = f"Agent exceeded maximum iterations ({max_iterations})"
        super().__init__(message, {"max_iterations": max_iterations})
        self.max_iterations = max_iterations


class PlanningError(AgentError):
    """Error during agent planning phase."""

    pass


class ReflectionError(AgentError):
    """Error during agent reflection phase."""

    pass


# =============================================================================
# Tool Errors
# =============================================================================


class ToolError(AgentError):
    """Base class for tool-related errors."""

    pass


class ToolNotFoundError(ToolError):
    """Requested tool not found in registry."""

    def __init__(self, tool_name: str):
        super().__init__(
            f"Tool not found: {tool_name}", {"tool_name": tool_name}
        )
        self.tool_name = tool_name


class ToolExecutionError(ToolError):
    """Tool execution failed."""

    def __init__(self, tool_name: str, reason: str):
        super().__init__(
            f"Tool execution failed: {tool_name} - {reason}",
            {"tool_name": tool_name, "reason": reason},
        )
        self.tool_name = tool_name
        self.reason = reason


class ToolValidationError(ToolError):
    """Tool input validation failed."""

    def __init__(self, tool_name: str, validation_errors: dict):
        super().__init__(
            f"Tool validation failed: {tool_name}",
            {"tool_name": tool_name, "validation_errors": validation_errors},
        )
        self.tool_name = tool_name
        self.validation_errors = validation_errors


# =============================================================================
# RAG Errors
# =============================================================================


class RAGError(AgenticTutorError):
    """Base class for RAG pipeline errors."""

    pass


class RetrievalError(RAGError):
    """Content retrieval failed."""

    pass


class SynthesisError(RAGError):
    """Insight synthesis failed."""

    def __init__(self, reason: str, llm_error: Exception = None):
        super().__init__(
            f"Synthesis failed: {reason}",
            {"reason": reason, "llm_error": str(llm_error) if llm_error else None},
        )
        self.reason = reason
        self.llm_error = llm_error


class EvaluationError(RAGError):
    """Quality evaluation failed."""

    pass


class EmbeddingError(RAGError):
    """Embedding generation failed."""

    pass


# =============================================================================
# Ingestion Errors
# =============================================================================


class IngestionError(AgenticTutorError):
    """Base class for content ingestion errors."""

    pass


class ExtractionError(IngestionError):
    """Content extraction failed."""

    def __init__(self, source_url: str, reason: str):
        super().__init__(
            f"Extraction failed for {source_url}: {reason}",
            {"source_url": source_url, "reason": reason},
        )
        self.source_url = source_url
        self.reason = reason


class ChunkingError(IngestionError):
    """Content chunking failed."""

    pass


class IndexingError(IngestionError):
    """Vector indexing failed."""

    pass


# =============================================================================
# UI Errors
# =============================================================================


class UIError(AgenticTutorError):
    """Base class for UI-related errors."""

    pass


class RenderingError(UIError):
    """UI rendering failed."""

    def __init__(self, template_name: str, reason: str):
        super().__init__(
            f"Rendering failed for {template_name}: {reason}",
            {"template_name": template_name, "reason": reason},
        )
        self.template_name = template_name
        self.reason = reason


class TemplateError(UIError):
    """Template not found or invalid."""

    def __init__(self, template_name: str):
        super().__init__(
            f"Template error: {template_name}", {"template_name": template_name}
        )
        self.template_name = template_name


# =============================================================================
# Integration Errors
# =============================================================================


class IntegrationError(AgenticTutorError):
    """Base class for external integration errors."""

    pass


class APIError(IntegrationError):
    """External API call failed."""

    def __init__(self, service: str, status_code: int = None, reason: str = None):
        super().__init__(
            f"API error from {service}: {reason}",
            {"service": service, "status_code": status_code, "reason": reason},
        )
        self.service = service
        self.status_code = status_code
        self.reason = reason


class AuthenticationError(IntegrationError):
    """Authentication with external service failed."""

    def __init__(self, service: str):
        super().__init__(
            f"Authentication failed for {service}", {"service": service}
        )
        self.service = service


# =============================================================================
# Utility Functions
# =============================================================================


def get_exception_hierarchy() -> dict:
    """
    Get the exception hierarchy as a dictionary.

    Returns:
        Dictionary representing the exception tree
    """
    return {
        "AgenticTutorError": {
            "ConfigurationError": {},
            "DatabaseError": {
                "ConnectionError": {},
                "QueryError": {},
                "RepositoryError": {},
            },
            "AgentError": {
                "AgentExecutionError": {},
                "AgentTimeoutError": {},
                "PlanningError": {},
                "ReflectionError": {},
                "ToolError": {
                    "ToolNotFoundError": {},
                    "ToolExecutionError": {},
                    "ToolValidationError": {},
                },
            },
            "RAGError": {
                "RetrievalError": {},
                "SynthesisError": {},
                "EvaluationError": {},
                "EmbeddingError": {},
            },
            "IngestionError": {
                "ExtractionError": {},
                "ChunkingError": {},
                "IndexingError": {},
            },
            "UIError": {
                "RenderingError": {},
                "TemplateError": {},
            },
            "IntegrationError": {
                "APIError": {},
                "AuthenticationError": {},
            },
        }
    }


def is_application_error(exception: Exception) -> bool:
    """
    Check if an exception is an application error.

    Args:
        exception: Exception to check

    Returns:
        True if exception is an application error (AgenticTutorError)
    """
    return isinstance(exception, AgenticTutorError)
