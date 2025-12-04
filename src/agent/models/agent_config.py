"""
Agent Configuration Model

Defines configuration for agent execution.
"""

from dataclasses import dataclass


@dataclass
class AgentConfig:
    """
    Configuration for agent execution.

    Controls agent behavior, limits, and features.
    """

    max_iterations: int = 10
    llm_model: str = "gpt-4o-mini"
    temperature: float = 0.3
    log_level: str = "INFO"
    enable_safety: bool = True
    enable_reflection: bool = True

    def __post_init__(self):
        """Validate configuration."""
        if self.max_iterations < 1:
            raise ValueError("max_iterations must be at least 1")
        if not 0 <= self.temperature <= 2:
            raise ValueError("temperature must be between 0 and 2")
        if self.log_level not in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"):
            raise ValueError(f"Invalid log_level: {self.log_level}")

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "max_iterations": self.max_iterations,
            "llm_model": self.llm_model,
            "temperature": self.temperature,
            "log_level": self.log_level,
            "enable_safety": self.enable_safety,
            "enable_reflection": self.enable_reflection,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AgentConfig":
        """Create from dictionary."""
        return cls(**data)

    @classmethod
    def for_testing(cls) -> "AgentConfig":
        """Create test configuration."""
        return cls(
            max_iterations=5,
            llm_model="gpt-4o-mini",
            temperature=0.0,  # Deterministic
            log_level="DEBUG",
            enable_safety=False,  # Faster tests
            enable_reflection=True,
        )
