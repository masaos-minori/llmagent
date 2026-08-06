"""agent/shared/health_models.py

DTOs for service health check results.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import cast


@dataclass(frozen=True)
class ServiceWarning:
    """A warning about a service during startup validation."""

    label: str
    url: str
    message: str


@dataclass(frozen=True)
class HealthCheckResult:
    """Aggregated health check results with warnings and errors."""

    warnings: list[ServiceWarning] = field(default_factory=list)
    errors: list[ServiceWarning] = field(default_factory=list)

    @property
    def has_issues(self) -> bool:
        """True if there are warnings or errors."""
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
    """Status of a startup validation check."""

    OK = "ok"
    WARNING = "warning"
    FATAL = "fatal"
    SKIPPED = "skipped"


@dataclass(frozen=True)
class StartupCheckOutcome:
    """Result of a single startup validation check."""

    source: str
    status: StartupCheckStatus
    message: str = ""
    remediation: str = ""


@dataclass
class StartupValidationResult:
    """Aggregated startup validation results across all checks."""

    outcomes: list[StartupCheckOutcome] = field(default_factory=list)

    def add_fatal(self, source: str, message: str, remediation: str = "") -> None:
        """Add a fatal outcome to the validation result."""
        self.outcomes.append(
            StartupCheckOutcome(source, StartupCheckStatus.FATAL, message, remediation)
        )

    def add_warning(self, source: str, message: str) -> None:
        """Add a warning outcome to the validation result."""
        self.outcomes.append(
            StartupCheckOutcome(source, StartupCheckStatus.WARNING, message)
        )

    def add_ok(self, source: str) -> None:
        """Add an OK outcome to the validation result."""
        self.outcomes.append(StartupCheckOutcome(source, StartupCheckStatus.OK))

    def add_skipped(self, source: str, message: str = "") -> None:
        """Add a skipped outcome to the validation result."""
        self.outcomes.append(
            StartupCheckOutcome(source, StartupCheckStatus.SKIPPED, message)
        )

    @property
    def has_fatal(self) -> bool:
        """True if any fatal outcome exists."""
        return any(o.status == StartupCheckStatus.FATAL for o in self.outcomes)

    def fatal_messages(self) -> list[str]:
        """Return all fatal message strings."""
        return [
            o.message for o in self.outcomes if o.status == StartupCheckStatus.FATAL
        ]

    def warning_messages(self) -> list[str]:
        """Return all warning message strings."""
        return [
            o.message for o in self.outcomes if o.status == StartupCheckStatus.WARNING
        ]


# ── Health body interpretation helpers ───────────────────────────────────────

_MAX_DETAIL_SUMMARY_LEN = 200
_MAX_DEP_REASON_LEN = 120


def _truncate(text: str, max_len: int) -> str:
    """Truncate *text* to *max_len* characters, appending '…' when truncated."""
    if len(text) <= max_len:
        return text
    return text[: max_len - 1] + "\u2026"


@dataclass(frozen=True)
class HealthInterpretation:
    """Structured interpretation of a raw /health response body dict."""

    self_reported_status: str
    ready: bool
    dependency_summary: list[str]
    details_summary: list[str]
    restart_recommended: bool
    operator_action_required: bool
    parse_failure_reason: str | None = None


def interpret_health_body(body: dict[str, object]) -> HealthInterpretation:
    """Interpret a raw /health JSON body into structured fields."""
    if not body:
        return HealthInterpretation(
            self_reported_status="unknown",
            ready=False,
            dependency_summary=[],
            details_summary=[],
            restart_recommended=False,
            operator_action_required=False,
        )

    try:
        status_val = body.get("status")
        status = str(status_val) if status_val else "unknown"
        ready = bool(body.get("ready"))
        deps_raw = cast(list[dict[str, object] | str], body.get("dependencies") or [])
        details_raw = cast(list[dict[str, object]], body.get("details") or [])
        restart_rec = bool(body.get("restart_recommended"))
        op_action = bool(body.get("operator_action_required"))
    except Exception as exc:  # noqa: BLE001 — health body may have unexpected shape from any MCP server; parse failures fall back to unknown status
        return HealthInterpretation(
            self_reported_status="unknown",
            ready=False,
            dependency_summary=[],
            details_summary=[],
            restart_recommended=False,
            operator_action_required=False,
            parse_failure_reason=str(exc),
        )

    dep_summaries = summarize_dependencies(deps_raw)
    detail_summaries = summarize_details(details_raw)

    return HealthInterpretation(
        self_reported_status=status,
        ready=ready,
        dependency_summary=dep_summaries,
        details_summary=detail_summaries,
        restart_recommended=restart_rec,
        operator_action_required=op_action,
    )


def extract_health_reason(body: dict[str, object]) -> str | None:
    """Extract a human-readable reason string from a /health body.

    Priority order:
      1. ``reason`` field
      2. ``message`` field
      3. dependencies summary (first failed required dependency)
      4. details summary (first non-ok component)
      5. ``operator_action_required`` flag
      6. ``restart_recommended`` flag
    """
    if not body:
        return None

    # Priority 1: reason
    reason = body.get("reason")
    if reason:
        return str(reason)

    # Priority 2: message
    msg = body.get("message")
    if msg:
        return str(msg)

    # Priority 3: dependencies
    deps_raw = cast(list[dict[str, object] | str], body.get("dependencies") or [])
    dep_summaries = summarize_dependencies(deps_raw)
    if dep_summaries:
        return "Dependency failure: " + "; ".join(dep_summaries)

    # Priority 4: details
    details_raw = cast(list[dict[str, object]], body.get("details") or [])
    detail_summaries = summarize_details(details_raw)
    if detail_summaries:
        return "Issue: " + "; ".join(detail_summaries)

    # Priority 5: operator_action_required
    if body.get("operator_action_required"):
        return "Operator action required"

    # Priority 6: restart_recommended
    if body.get("restart_recommended"):
        return "Restart recommended"

    return None


def summarize_dependencies(deps: list[dict[str, object] | str]) -> list[str]:
    """Summarise dependency statuses, returning only failed required ones."""
    summaries: list[str] = []
    for dep in deps:
        if isinstance(dep, str):
            summaries.append(_truncate(dep, _MAX_DEP_REASON_LEN))
            continue
        name = dep.get("name") or dep.get("status", "unknown")
        status = dep.get("status", "unknown")
        if status != "ok":
            reason = dep.get("reason") or ""
            if reason:
                summaries.append(_truncate(f"{name}: {reason}", _MAX_DEP_REASON_LEN))
            else:
                summaries.append(f"{name}: {status}")
    return summaries


def summarize_details(details: list[dict[str, object]]) -> list[str]:
    """Summarise detail entries, truncating large payloads."""
    summaries: list[str] = []
    for d in details:
        component = d.get("component") or "unknown"
        status = d.get("status") or "unknown"
        extra = d.get("data") or d.get("details") or ""
        if extra:
            if isinstance(extra, str):
                extra_str = _truncate(extra, _MAX_DETAIL_SUMMARY_LEN)
            else:
                extra_str = _truncate(
                    str(extra)[:_MAX_DETAIL_SUMMARY_LEN], _MAX_DETAIL_SUMMARY_LEN
                )
            summaries.append(f"{component} ({status}): {extra_str}")
        else:
            summaries.append(f"{component}: {status}")
    return summaries
