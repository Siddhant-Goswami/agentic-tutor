"""
Agent module for autonomous learning coach.

Provides:
- AgentController: Main agent loop
- AgentLogger: Execution logging
- ToolRegistry: Tool schemas and execution
"""

from .controller import AgentController, AgentConfig, AgentResult
from .logger import AgentLogger
from .tools import ToolRegistry

__all__ = [
    "AgentController",
    "AgentConfig",
    "AgentResult",
    "AgentLogger",
    "ToolRegistry",
]
