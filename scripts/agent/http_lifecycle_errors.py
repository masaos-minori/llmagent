"""scripts/agent/http_lifecycle_errors.py

Exceptions and dataclasses for HTTP subprocess MCP server startup failures.
"""

from __future__ import annotations

import logging
import re
from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum

from agent.secrets_masker import _mask_secrets, redact_path
from agent.shutdown_budget import ShutdownOutcome

logger = logging.getLogger(__name__)


class StartupCode(StrEnum):
    """Stable public error codes for lifecycle startup failures."""

    GENERAL = "general"
    """Default code for a failure category that has no dedicated code yet."""


@dataclass
class StartupFailure:
    """Records the full stderr output and reason when an HTTP subprocess fails to start."""

    server_key: str
    reason: str
    stderr_full: str
    code: StartupCode = StartupCode.GENERAL


# Absolute-path substrings inside a free-text reason are replaced with the logical
# identifier from redact_path before rendering (REQ-002 AC-1).
_ABSOLUTE_PATH = re.compile(r"/[^\s\"']+")


def _redact_reason(reason: str) -> str:
    """Replace each absolute-path substring in *reason* with its logical identifier."""
    return _ABSOLUTE_PATH.sub(lambda match: redact_path(match.group(0)), reason)


class HttpStartupError(RuntimeError):
    """Raised when an HTTP subprocess MCP server fails to start."""

    def __init__(self, failure: StartupFailure) -> None:
        """Initialize with the startup failure details."""
        self.failure = failure
        super().__init__(failure.reason)

    def __str__(self) -> str:
        """Return a human-readable representation including all failure details."""
        parts = [
            f"{self.failure.server_key}: {self.failure.code}: {_redact_reason(self.failure.reason)}"
        ]
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


class ShutdownSuppressedError(RuntimeError):
    """Base for non-retryable lifecycle refusals issued while shutting down."""


class EnsureSuppressedError(ShutdownSuppressedError):
    """Non-retryable: ensure_ready() refused because the lifecycle is shutting down."""


class RestartSuppressedError(ShutdownSuppressedError):
    """Non-retryable: restart() refused because the lifecycle is shutting down."""


class RestartBlockedError(RuntimeError):
    """Non-retryable: restart() refused over an unconfirmed old exit; the record is retained."""


def termination_step_outcome(
    outcomes: Sequence[TerminationOutcome], *, other_failures: int
) -> ShutdownOutcome:
    """Map MCP termination results onto the shutdown step outcome vocabulary.

    This module owns the termination outcomes, so the mapping into the step vocabulary
    lives here rather than in the step machine. A server that was signalled but whose
    exit was never observed is a wait that ran out, so the step is timed_out. A signal
    that never reached a process, any other failure collected in the same step, or an
    empty result set when the caller has something to report is a failure.
    """
    if other_failures or not outcomes:
        return ShutdownOutcome.FAILED
    if all(outcome == TerminationOutcome.EXIT_UNCONFIRMED for outcome in outcomes):
        return ShutdownOutcome.TIMED_OUT
    return ShutdownOutcome.FAILED
