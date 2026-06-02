#!/usr/bin/env python3
"""shell_mcp_models.py
Config loading and Pydantic request/response models for shell-mcp.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field
from shared.config_loader import ConfigLoader
from shared.logger import Logger
from shared.protocols.shell import ShellPolicy

# Logger for config-load warnings; main log path is /opt/llm/logs/shell-mcp.log
_models_logger = Logger(__name__, "/opt/llm/logs/shell-mcp.log")

_cfg: dict[str, Any] | None = None


def _get_cfg() -> dict[str, Any]:
    """Load config on first call; cached for the module lifetime."""
    global _cfg
    if _cfg is None:
        try:
            _cfg = ConfigLoader().load("shell_mcp_server.toml")
        except Exception as e:
            _models_logger.warning(f"Config load failed: {e}")
            _cfg = {}
    return _cfg


def load_shell_policy() -> ShellPolicy:
    """Build ShellPolicy from shell_mcp_server.toml (cached via _get_cfg)."""
    cfg = _get_cfg()
    return ShellPolicy(
        allowed_commands=frozenset(cfg.get("command_allowlist", [])),
        cwd_allowed_dirs=tuple(cfg.get("shell_cwd_allowed_dirs", [])),
        default_cwd=str(cfg.get("default_cwd", "")),
        timeout_sec=int(cfg.get("max_timeout_sec", 300)),
        max_output_kb=int(cfg.get("max_output_kb", 4096)),
        max_memory_mb=int(cfg.get("max_memory_mb", 512)),
        kill_policy=str(cfg.get("kill_policy", "sigterm_then_sigkill")),
        kill_grace_sec=float(cfg.get("kill_grace_sec", 2.0)),
        execution_user=str(cfg.get("execution_user", "")),
        shell_path=str(cfg.get("shell_path", "/usr/bin:/bin")),
        audit_log_path=str(cfg.get("audit_log_path", "")),
        sandbox_backend=str(cfg.get("shell_sandbox_backend", "none")),
        env_allowlist=tuple(cfg.get("env_allowlist", [])),
        env_denylist=tuple(cfg.get("env_denylist", [])),
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
