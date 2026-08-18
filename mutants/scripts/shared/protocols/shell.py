#!/usr/bin/env python3
"""scripts/shared/protocols/shell.py

Execution policy dataclass for shell-mcp.

Pure dataclass — no fastapi, mcp, or agent dependencies allowed.
Dependency direction: shared -> external only.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar


from mutmut.mutation.trampoline import wrap_in_trampoline as _mutmut_mutated, MutantDict
mutants_x__check_min__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x__check_min__mutmut)
def _check_min(name: str, value: float, minimum: float) -> None:
    """Raise ValueError if value is below minimum, using the shared message shape."""
    if value < minimum:
        raise ValueError(f"{name} must be >= {minimum}, got {value}")


def x__check_min__mutmut_orig(name: str, value: float, minimum: float) -> None:
    """Raise ValueError if value is below minimum, using the shared message shape."""
    if value < minimum:
        raise ValueError(f"{name} must be >= {minimum}, got {value}")


def x__check_min__mutmut_1(name: str, value: float, minimum: float) -> None:
    """Raise ValueError if value is below minimum, using the shared message shape."""
    if value <= minimum:
        raise ValueError(f"{name} must be >= {minimum}, got {value}")


def x__check_min__mutmut_2(name: str, value: float, minimum: float) -> None:
    """Raise ValueError if value is below minimum, using the shared message shape."""
    if value < minimum:
        raise ValueError(None)

mutants_x__check_min__mutmut['_mutmut_orig'] = x__check_min__mutmut_orig # type: ignore # mutmut generated
mutants_x__check_min__mutmut['x__check_min__mutmut_1'] = x__check_min__mutmut_1 # type: ignore # mutmut generated
mutants_x__check_min__mutmut['x__check_min__mutmut_2'] = x__check_min__mutmut_2 # type: ignore # mutmut generated


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

    _VALID_KILL_POLICIES: ClassVar[frozenset[str]] = frozenset(
        {"sigterm_then_sigkill", "sigkill_only"}
    )
    _VALID_SANDBOX_BACKENDS: ClassVar[frozenset[str]] = frozenset({"firejail", "none"})

    def __post_init__(self) -> None:
        """Validate all fields after initialization."""
        if self.kill_policy not in self._VALID_KILL_POLICIES:
            raise ValueError(
                f"kill_policy must be one of {sorted(self._VALID_KILL_POLICIES)!r}, got {self.kill_policy!r}"
            )
        if self.sandbox_backend not in self._VALID_SANDBOX_BACKENDS:
            raise ValueError(
                f"sandbox_backend must be one of {sorted(self._VALID_SANDBOX_BACKENDS)!r}, got {self.sandbox_backend!r}"
            )
        _check_min("timeout_sec", self.timeout_sec, 1)
        _check_min("max_output_kb", self.max_output_kb, 1)
        _check_min("max_memory_mb", self.max_memory_mb, 1)
        _check_min("kill_grace_sec", self.kill_grace_sec, 0)
