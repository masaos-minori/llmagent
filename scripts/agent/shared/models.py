"""agent/shared/models.py
Cross-cutting frozen dataclass DTOs for the agent layer.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class CommandResult:
    """Structured result returned by a command handler."""

    success: bool
    message: str
    needs_restart: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ValidationErrorDetail:
    """Structured detail for a validation failure."""

    field: str
    message: str
    value: object = None
