#!/usr/bin/env python3
"""shell_mcp_models.py
Config loading, Pydantic models, and domain exceptions for shell-mcp.
"""

from __future__ import annotations

import dataclasses
import logging
from typing import Any

from pydantic import BaseModel, Field
from shared.config_loader import ConfigLoader
from shared.protocols.shell import ShellPolicy

logger = logging.getLogger(__name__)


class ShellAuthorizationError(RuntimeError):
    """Raised when a command/cwd/permission policy check fails (HTTP 403)."""


class ShellValidationError(ValueError):
    """Raised on invalid input (HTTP 400/422)."""


# ──────────────────────────────────────────────────────────────────────────────
# Typed config object
# ──────────────────────────────────────────────────────────────────────────────


@dataclasses.dataclass
class ShellConfig:
    """Typed configuration for the Shell MCP server."""

    command_allowlist: list[str] = dataclasses.field(default_factory=list)
    shell_cwd_allowed_dirs: list[str] = dataclasses.field(default_factory=list)
    default_cwd: str = ""
    max_timeout_sec: int = 300
    max_output_kb: int = 4096
    max_memory_mb: int = 512
    kill_policy: str = "sigterm_then_sigkill"
    kill_grace_sec: float = 2.0
    execution_user: str = ""
    shell_path: str = "/usr/bin:/bin"
    audit_log_path: str = ""
    shell_sandbox_backend: str = "none"
    env_allowlist: list[str] = dataclasses.field(default_factory=list)
    env_denylist: list[str] = dataclasses.field(default_factory=list)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> ShellConfig:
        """Construct from a raw config dict (e.g. loaded from TOML)."""
        return cls(
            command_allowlist=list(d.get("command_allowlist", [])),
            shell_cwd_allowed_dirs=list(d.get("shell_cwd_allowed_dirs", [])),
            default_cwd=str(d.get("default_cwd", "")),
            max_timeout_sec=int(d.get("max_timeout_sec", 300)),
            max_output_kb=int(d.get("max_output_kb", 4096)),
            max_memory_mb=int(d.get("max_memory_mb", 512)),
            kill_policy=str(d.get("kill_policy", "sigterm_then_sigkill")),
            kill_grace_sec=float(d.get("kill_grace_sec", 2.0)),
            execution_user=str(d.get("execution_user", "")),
            shell_path=str(d.get("shell_path", "/usr/bin:/bin")),
            audit_log_path=str(d.get("audit_log_path", "")),
            shell_sandbox_backend=str(d.get("shell_sandbox_backend", "none")),
            env_allowlist=list(d.get("env_allowlist", [])),
            env_denylist=list(d.get("env_denylist", [])),
        )

    @classmethod
    def load(cls) -> ShellConfig:
        """Load from shell_mcp_server.toml; raises on failure (fail-fast)."""
        return cls.from_dict(ConfigLoader().load("shell_mcp_server.toml"))


# ──────────────────────────────────────────────────────────────────────────────
# Policy builder
# ──────────────────────────────────────────────────────────────────────────────


def load_shell_policy() -> ShellPolicy:
    """Build ShellPolicy from shell_mcp_server.toml via ShellConfig."""
    cfg = ShellConfig.load()
    return ShellPolicy(
        allowed_commands=frozenset(cfg.command_allowlist),
        cwd_allowed_dirs=tuple(cfg.shell_cwd_allowed_dirs),
        default_cwd=str(cfg.default_cwd),
        timeout_sec=int(cfg.max_timeout_sec),
        max_output_kb=int(cfg.max_output_kb),
        max_memory_mb=int(cfg.max_memory_mb),
        kill_policy=str(cfg.kill_policy),
        kill_grace_sec=float(cfg.kill_grace_sec),
        execution_user=str(cfg.execution_user),
        shell_path=str(cfg.shell_path),
        audit_log_path=str(cfg.audit_log_path),
        sandbox_backend=str(cfg.shell_sandbox_backend),
        env_allowlist=tuple(cfg.env_allowlist),
        env_denylist=tuple(cfg.env_denylist),
    )


# ──────────────────────────────────────────────────────────────────────────────
# Pydantic schema definitions (shell execution)
# ──────────────────────────────────────────────────────────────────────────────


class ShellRunRequest(BaseModel):
    command: str = Field(
        ...,
        description="Command string (argv[0] must be in allowlist)",
    )
    argv: list[str] | None = Field(
        default=None,
        description=(
            "Explicit argv list; when provided, used instead of shlex.split(command)"
            " to prevent shell injection"
        ),
    )
    timeout_sec: int = Field(default=30, ge=1, le=3600)
    cwd: str | None = Field(default=None)
    env: dict[str, str] = Field(default_factory=dict)
    max_output_kb: int = Field(default=512, ge=1, le=65536)
    dry_run: bool = Field(
        default=False,
        description="Preview only; command is not executed",
    )


class ShellRunResponse(BaseModel):
    stdout: str
    stderr: str
    exit_code: int
    timed_out: bool
    truncated: bool
    elapsed_sec: float
