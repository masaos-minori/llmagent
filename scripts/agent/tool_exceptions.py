"""agent/tool_exceptions.py

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
    """Defined for completeness; not raised — silent return is the policy

    when audit logger is not configured.
    """


class LifecycleConfigurationError(RuntimeError):
    """Raised when a lifecycle operation is attempted with missing configuration."""
