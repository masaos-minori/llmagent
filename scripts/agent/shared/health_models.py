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

    @property
    def has_issues(self) -> bool:
        return bool(self.warnings)

    def warning_messages(self) -> list[str]:
        """Flat list of message strings for write_warning() calls."""
        return [w.message for w in self.warnings]
