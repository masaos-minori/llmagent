"""scripts/shared/security/policy.py

Security policy definitions."""

from enum import StrEnum


class SecurityMode(StrEnum):
    """Fail-safe behavior mode for high-risk tools."""

    FAIL_CLOSED = "fail_closed"
    FAIL_OPEN = "fail_open"

    @property
    def is_fail_closed(self) -> bool:
        """Whether this mode enforces fail-closed behavior."""
        return self == SecurityMode.FAIL_CLOSED

    @property
    def is_fail_open(self) -> bool:
        """Whether this mode allows fail-open behavior."""
        return self == SecurityMode.FAIL_OPEN


class HighRiskToolPolicy:
    """Policy for high-risk MCP tools."""

    def __init__(
        self,
        allowed_paths: list[str] | None = None,
        allowed_commands: list[str] | None = None,
        mode: SecurityMode = SecurityMode.FAIL_CLOSED,
    ) -> None:
        self.allowed_paths: list[str] = allowed_paths or []
        self.allowed_commands: list[str] = allowed_commands or []
        self.mode = mode

    def validate_path(self, path: str) -> bool:
        """Validate a file path against the policy."""
        if not self.allowed_paths:
            return self.mode == SecurityMode.FAIL_OPEN
        return any(path.startswith(p) for p in self.allowed_paths)

    def validate_command(self, cmd: str) -> bool:
        """Validate a command against the policy."""
        if not self.allowed_commands:
            return self.mode == SecurityMode.FAIL_OPEN
        return cmd in self.allowed_commands
