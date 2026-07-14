"""agent/shared/health_models.py

DTOs for service health check results.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


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
        parse_failed:             True if an HTTP response was received but the body could not be
                                   parsed as JSON. False for the unreachable case and for any
                                   successful-parse case.
        parse_error:              Short diagnostic string describing the parse failure (exception
                                   message plus a truncated raw-body excerpt); populated only when
                                   `parse_failed` is True, otherwise None.
    """

    reachable: bool
    status_code: int | None
    restart_recommended: bool
    operator_action_required: bool
    body: dict[str, object]
    parse_failed: bool = False
    parse_error: str | None = None


class StartupCheckStatus(StrEnum):
    OK = "ok"
    WARNING = "warning"
    FATAL = "fatal"
    SKIPPED = "skipped"


@dataclass(frozen=True)
class StartupCheckOutcome:
    source: str
    status: StartupCheckStatus
    message: str = ""
    remediation: str = ""


@dataclass
class StartupValidationResult:
    outcomes: list[StartupCheckOutcome] = field(default_factory=list)

    def add_fatal(self, source: str, message: str, remediation: str = "") -> None:
        self.outcomes.append(
            StartupCheckOutcome(source, StartupCheckStatus.FATAL, message, remediation)
        )

    def add_warning(self, source: str, message: str) -> None:
        self.outcomes.append(
            StartupCheckOutcome(source, StartupCheckStatus.WARNING, message)
        )

    def add_ok(self, source: str) -> None:
        self.outcomes.append(StartupCheckOutcome(source, StartupCheckStatus.OK))

    def add_skipped(self, source: str, message: str = "") -> None:
        self.outcomes.append(
            StartupCheckOutcome(source, StartupCheckStatus.SKIPPED, message)
        )

    @property
    def has_fatal(self) -> bool:
        return any(o.status == StartupCheckStatus.FATAL for o in self.outcomes)

    def fatal_messages(self) -> list[str]:
        return [
            o.message for o in self.outcomes if o.status == StartupCheckStatus.FATAL
        ]

    def warning_messages(self) -> list[str]:
        return [
            o.message for o in self.outcomes if o.status == StartupCheckStatus.WARNING
        ]
