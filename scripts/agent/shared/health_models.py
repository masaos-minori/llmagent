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
