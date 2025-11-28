"""
Autonomous Learning Coach Agent

A standalone agent module implementing the SENSE → PLAN → ACT → OBSERVE → REFLECT loop
for personalized learning coaching.

This module is completely independent of MCP and can be used by any client (dashboard, CLI, etc.).
"""

from .controller import AgentController, AgentConfig, AgentResult
from .logger import AgentLogger

__all__ = [
    "AgentController",
    "AgentConfig",
    "AgentResult",
    "AgentLogger",
]

__version__ = "0.1.0"
