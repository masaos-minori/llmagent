"""scripts/agent/http_lifecycle_errors.py

Exceptions and dataclasses for HTTP subprocess MCP server startup failures.

Extracted from http_lifecycle.py to break circular imports between
http_lifecycle.py and http_lifecycle_command_validator.py.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import StrEnum

from agent.secrets_masker import _mask_secrets

logger = logging.getLogger(__name__)


@dataclass
class StartupFailure:
    """Records the full stderr output and reason when an HTTP subprocess fails to start."""

    server_key: str
    reason: str
    stderr_full: str


class HttpStartupError(RuntimeError):
    """Raised when an HTTP subprocess MCP server fails to start."""

    def __init__(self, failure: StartupFailure) -> None:
        """Initialize with the startup failure details."""
        self.failure = failure
        super().__init__(failure.reason)

    def __str__(self) -> str:
        """Return a human-readable representation including all failure details."""
        parts = [f"{self.failure.server_key}: {self.failure.reason}"]
        if self.failure.stderr_full:
            tail = self.failure.stderr_full[-512:]
            masked = _mask_secrets(tail)
            parts.append(f"(stderr_tail: {masked})")
        return " ".join(parts)


class TerminationOutcome(StrEnum):
    """What one MCP server termination attempt proved about the process."""

    EXITED = "exited"
    """Exit observed within the confirmation bound."""
    ALREADY_EXITED = "already_exited"
    """Exit observed before any signal was sent."""
    SIGNAL_NOT_DELIVERED = "signal_not_delivered"
    """No signal call succeeded."""
    EXIT_UNCONFIRMED = "exit_unconfirmed"
    """A signal call succeeded; exit was not observed within the bound."""

    @property
    def confirmed(self) -> bool:
        """Return True when the process is proved gone (EXITED or ALREADY_EXITED)."""
        return self in (TerminationOutcome.EXITED, TerminationOutcome.ALREADY_EXITED)
