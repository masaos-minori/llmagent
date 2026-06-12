"""agent/shared/exceptions.py
Cross-cutting exception hierarchy for the agent layer.
"""

from __future__ import annotations


class AgentSharedError(Exception):
    """Base for all agent/shared exceptions."""


class ValidationError(AgentSharedError, ValueError):
    """Raised when input fails domain validation."""


class ConfigurationSchemaError(AgentSharedError, ValueError):
    """Raised when a config dict does not match the expected schema."""


class WorkflowStageError(AgentSharedError, RuntimeError):
    """Raised when a workflow stage fails in an unrecoverable way."""


class UnknownTierError(ValidationError):
    def __init__(self, tier: str) -> None:
        super().__init__(f"Unknown safety tier: {tier!r}")


class UnknownRoleError(ValidationError):
    def __init__(self, role: str, valid: frozenset[str]) -> None:
        super().__init__(f"Unknown role {role!r}. Valid: {', '.join(sorted(valid))}")
