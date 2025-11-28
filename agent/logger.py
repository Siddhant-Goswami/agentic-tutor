"""
Agent Logger

Logs agent execution for visibility and debugging.
"""

import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from uuid import UUID
import json

logger = logging.getLogger(__name__)


class AgentLogger:
    """
    Logs agent execution phases for visibility and debugging.

    Stores logs in-memory (MVP). Can be extended to persist in database.
    """

    def __init__(self):
        """Initialize logger with in-memory storage."""
        self.sessions: Dict[UUID, Dict[str, Any]] = {}

    def start_session(self, session_id: UUID, goal: str, user_id: str) -> None:
        """
        Initialize a new agent session.

        Args:
            session_id: Unique session identifier
            goal: User's natural language goal
            user_id: UUID of the user
        """
        self.sessions[session_id] = {
            "id": str(session_id),
            "user_id": user_id,
            "goal": goal,
            "started_at": datetime.now().isoformat(),
            "completed_at": None,
            "logs": [],
            "status": "running",
        }
        logger.info(f"Started agent session {session_id} for user {user_id}")

    def log(
        self,
        session_id: UUID,
        phase: str,
        content: Dict[str, Any],
        iteration: Optional[int] = None,
    ) -> None:
        """
        Log a phase execution.

        Args:
            session_id: UUID of the session
            phase: SENSE, PLAN, ACT, OBSERVE, REFLECT, COMPLETE
            content: Phase-specific data
            iteration: Loop iteration number (optional)
        """
        if session_id not in self.sessions:
            logger.error(f"Session {session_id} not found")
            return

        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "phase": phase,
            "iteration": iteration,
            "content": content,
        }

        self.sessions[session_id]["logs"].append(log_entry)
        logger.debug(f"[{session_id}] {phase}: {content}")

    def complete_session(
        self, session_id: UUID, status: str, output: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Mark session as complete.

        Args:
            session_id: UUID of the session
            status: "completed", "failed", "timeout"
            output: Final output from agent (optional)
        """
        if session_id not in self.sessions:
            logger.error(f"Session {session_id} not found")
            return

        self.sessions[session_id]["completed_at"] = datetime.now().isoformat()
        self.sessions[session_id]["status"] = status
        if output:
            self.sessions[session_id]["output"] = output

        logger.info(f"Completed agent session {session_id} with status: {status}")

    def get_logs(self, session_id: UUID) -> List[Dict[str, Any]]:
        """
        Retrieve all logs for a session.

        Args:
            session_id: UUID of the session

        Returns:
            List of log entries
        """
        if session_id not in self.sessions:
            logger.warning(f"Session {session_id} not found")
            return []

        return self.sessions[session_id]["logs"]

    def get_session(self, session_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Retrieve complete session data.

        Args:
            session_id: UUID of the session

        Returns:
            Session data including logs, or None if not found
        """
        return self.sessions.get(session_id)

    def export_as_text(self, session_id: UUID, include_timestamps: bool = True) -> str:
        """
        Export logs as formatted text for UI display.

        Args:
            session_id: UUID of the session
            include_timestamps: Whether to include timestamps (default: True)

        Returns:
            Formatted text string
        """
        session = self.get_session(session_id)
        if not session:
            return f"Session {session_id} not found"

        lines = []
        lines.append("=" * 60)
        lines.append(f"Agent Session: {session_id}")
        lines.append(f"Goal: {session['goal']}")
        lines.append(f"Status: {session['status']}")
        lines.append(f"Started: {session['started_at']}")
        if session['completed_at']:
            lines.append(f"Completed: {session['completed_at']}")
        lines.append("=" * 60)
        lines.append("")

        # Phase emojis for visual clarity
        phase_emojis = {
            "SENSE": "🔵",
            "PLAN": "🟡",
            "ACT": "🟢",
            "OBSERVE": "🟣",
            "REFLECT": "🟠",
            "COMPLETE": "✅",
            "ERROR": "❌",
        }

        for log in session["logs"]:
            phase = log["phase"]
            emoji = phase_emojis.get(phase, "⚪")

            if log.get("iteration"):
                header = f"{emoji} [{phase}] Iteration {log['iteration']}"
            else:
                header = f"{emoji} [{phase}]"

            if include_timestamps:
                timestamp = datetime.fromisoformat(log["timestamp"]).strftime(
                    "%H:%M:%S"
                )
                header = f"[{timestamp}] {header}"

            lines.append(header)
            lines.append("-" * 60)

            # Format content
            content = log["content"]
            for key, value in content.items():
                if isinstance(value, (dict, list)):
                    lines.append(f"  {key}:")
                    lines.append(f"    {json.dumps(value, indent=4)}")
                else:
                    lines.append(f"  {key}: {value}")

            lines.append("")

        return "\n".join(lines)

    def export_as_json(self, session_id: UUID) -> str:
        """
        Export session as JSON.

        Args:
            session_id: UUID of the session

        Returns:
            JSON string
        """
        session = self.get_session(session_id)
        if not session:
            return json.dumps({"error": f"Session {session_id} not found"})

        return json.dumps(session, indent=2)

    def clear_session(self, session_id: UUID) -> None:
        """
        Clear a session from memory.

        Args:
            session_id: UUID of the session
        """
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"Cleared session {session_id}")

    def clear_all(self) -> None:
        """Clear all sessions from memory."""
        count = len(self.sessions)
        self.sessions.clear()
        logger.info(f"Cleared {count} sessions")
