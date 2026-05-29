#!/usr/bin/env python3
"""
shell_mcp_models.py
Config loading and Pydantic request/response models for shell-mcp.
"""

from __future__ import annotations

from pydantic import BaseModel, Field
from shared.config_loader import ConfigLoader
from shared.logger import Logger

# Logger for config-load warnings; main log path is /opt/llm/logs/shell-mcp.log
_models_logger = Logger(__name__, "/opt/llm/logs/shell-mcp.log")

_cfg: dict | None = None


def _get_cfg() -> dict:
    """Load config on first call; cached for the module lifetime."""
    global _cfg
    if _cfg is None:
        try:
            _cfg = ConfigLoader().load("shell_mcp_server.toml")
        except Exception as e:
            _models_logger.warning(f"Config load failed: {e}")
            _cfg = {}
    return _cfg


# ──────────────────────────────────────────────────────────────────────────────
# Pydantic schema definitions (shell execution)
# ──────────────────────────────────────────────────────────────────────────────


class ShellRunRequest(BaseModel):
    command: str = Field(
        ..., description="Command string (argv[0] must be in allowlist)"
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


class ShellRunResponse(BaseModel):
    stdout: str
    stderr: str
    exit_code: int
    timed_out: bool
    truncated: bool
    elapsed_sec: float
