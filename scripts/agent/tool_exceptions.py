"""scripts/agent/tool_exceptions.py

Domain exceptions for the tool execution subsystem.
"""

from __future__ import annotations


class ToolArgumentsDecodeError(ValueError):
    """Raised when tool call arguments cannot be decoded as JSON."""


class ToolExecutorUnavailableError(RuntimeError):
    """Raised when ctx.services.tools is None at execution time."""


class PolicyViolationError(RuntimeError):
    """Raised when a pre-flight policy check denies the tool call."""

    def __init__(self, audit_decision: str, message: str) -> None:
        """Initialize the policy violation exception with audit decision and error message."""
        super().__init__(message)
        self.audit_decision = audit_decision


class ApprovalPreviewError(RuntimeError):
    """Raised when dry-run preview execution fails."""


class ApprovalPreviewBlockingError(ApprovalPreviewError):
    """Raised when dry-run preview returns an explicit error result.

    Distinct from the base ApprovalPreviewError (which also covers
    dry-run being unsupported or unreachable) so callers can deny
    approval outright for HIGH-risk tools on an explicit dry-run
    failure, while still falling back to a text-only preview for the
    unsupported/connection-failure case.
    """


class AuditUnavailableError(RuntimeError):
    """Raised when a mandatory audit record cannot be written for a
    side-effecting tool call (mcpdl001 REQ-007, AC-5).

    Callers treat this as a denial: the side effect must not complete when its
    audit record is unwritable. Read-only calls keep the silent-return
    best-effort policy and never raise this.
    """


class IntentRecordUnavailableError(RuntimeError):
    """Raised when the tool_call_state intent row cannot be written for a
    side-effecting tool call (mcpdl001 REQ-005/REQ-007, AC-6).

    Covers every unwritable path: no logical call id on the prepared call,
    an unwired recorder or task context, and recorder write failures. The
    runner converts this into the call's tool-error row (denial surface);
    the side effect never dispatches without its durable intent record.
    Read-only calls keep the logged best-effort path and never raise this.
    """


class LifecycleConfigurationError(RuntimeError):
    """Raised when a lifecycle operation is attempted with missing configuration."""
