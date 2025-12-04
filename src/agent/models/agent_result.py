"""
Agent Result Model

Represents the result of agent execution with metadata.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any
from src.core.types import SessionId, AgentStatus


@dataclass
class AgentResult:
    """
    Result from agent execution.

    Contains the final output, execution logs, and metadata about the
    agent's execution.
    """

    output: Dict[str, Any]
    logs: List[Dict[str, Any]]
    iteration_count: int
    status: str  # "completed", "timeout", "failed", "needs_approval", "needs_clarification"
    session_id: SessionId
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_successful(self) -> bool:
        """
        Check if execution was successful.

        Returns:
            True if status is 'completed'
        """
        return self.status == "completed"

    def needs_user_action(self) -> bool:
        """
        Check if user action is needed.

        Returns:
            True if status requires user input
        """
        return self.status in ("needs_approval", "needs_clarification")

    def has_error(self) -> bool:
        """
        Check if execution failed.

        Returns:
            True if status is 'failed'
        """
        return self.status == "failed"

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "output": self.output,
            "logs": self.logs,
            "iteration_count": self.iteration_count,
            "status": self.status,
            "session_id": self.session_id,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentResult":
        """
        Create from dictionary.

        Args:
            data: Dictionary with result data

        Returns:
            AgentResult instance
        """
        return cls(
            output=data["output"],
            logs=data["logs"],
            iteration_count=data["iteration_count"],
            status=data["status"],
            session_id=data["session_id"],
            metadata=data.get("metadata", {}),
        )
