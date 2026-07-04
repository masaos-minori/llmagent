"""agent/shared/health_models.py
DTOs for service health check results.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ServiceWarning:
    label: str
    url: str
    message: str


@dataclass(frozen=True)
class HealthCheckResult:
    warnings: list[ServiceWarning] = field(default_factory=list)
    errors: list[ServiceWarning] = field(default_factory=list)

    @property
    def has_issues(self) -> bool:
        return bool(self.warnings or self.errors)

    def warning_messages(self) -> list[str]:
        """Flat list of warning message strings for write_warning() calls."""
        return [w.message for w in self.warnings]

    def error_messages(self) -> list[str]:
        """Flat list of error message strings for critical failure reporting."""
        return [e.message for e in self.errors]


@dataclass(frozen=True)
class McpHealthProbeResult:
    """Structured result of a single /health GET probe to an MCP server.

    Fields:
        reachable:                True if an HTTP response was received (any status code).
        status_code:              HTTP status code, or None if connection failed.
        restart_recommended:      Body field `restart_recommended`; False if absent or parse fails.
        operator_action_required: Body field `operator_action_required`; False if absent or parse fails.
        body:                     Parsed JSON body dict; empty dict if parse failed or unreachable.
    """

    reachable: bool
    status_code: int | None
    restart_recommended: bool
    operator_action_required: bool
    body: dict[str, object]
