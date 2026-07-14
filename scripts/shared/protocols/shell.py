#!/usr/bin/env python3
"""shared/protocols/shell.py

Execution policy dataclass for shell-mcp.

Pure dataclass — no fastapi, mcp, or agent dependencies allowed.
Dependency direction: shared -> external only.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ShellPolicy:
    """Immutable execution policy consumed by ShellService.

    All fields are validated by ShellService.__init__; this class holds
    values only, with no business logic.
    """

    allowed_commands: frozenset[str]
    cwd_allowed_dirs: tuple[str, ...]
    default_cwd: str
    timeout_sec: int
    max_output_kb: int
    max_memory_mb: int
    kill_policy: str  # "sigterm_then_sigkill" | "sigkill_only"
    kill_grace_sec: float  # grace period before SIGKILL (sigterm_then_sigkill only)
    execution_user: str  # "" = no switch; non-empty requires root (CAP_SETUID)
    shell_path: str
    audit_log_path: str
    sandbox_backend: str  # "firejail" | "none"
    env_allowlist: tuple[str, ...]
    env_denylist: tuple[str, ...]

    _VALID_KILL_POLICIES: frozenset[str] = field(
        default=frozenset({"sigterm_then_sigkill", "sigkill_only"}),
        init=False,
        repr=False,
        compare=False,
    )
    _VALID_SANDBOX_BACKENDS: frozenset[str] = field(
        default=frozenset({"firejail", "none"}),
        init=False,
        repr=False,
        compare=False,
    )

    def __post_init__(self) -> None:
        if self.kill_policy not in self._VALID_KILL_POLICIES:
            raise ValueError(
                f"kill_policy must be one of {sorted(self._VALID_KILL_POLICIES)!r},"
                f" got {self.kill_policy!r}"
            )
        if self.sandbox_backend not in self._VALID_SANDBOX_BACKENDS:
            raise ValueError(
                f"sandbox_backend must be one of"
                f" {sorted(self._VALID_SANDBOX_BACKENDS)!r},"
                f" got {self.sandbox_backend!r}"
            )
        if self.timeout_sec < 1:
            raise ValueError(f"timeout_sec must be >= 1, got {self.timeout_sec}")
        if self.max_output_kb < 1:
            raise ValueError(f"max_output_kb must be >= 1, got {self.max_output_kb}")
        if self.max_memory_mb < 1:
            raise ValueError(f"max_memory_mb must be >= 1, got {self.max_memory_mb}")
        if self.kill_grace_sec < 0:
            raise ValueError(f"kill_grace_sec must be >= 0, got {self.kill_grace_sec}")
