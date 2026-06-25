#!/usr/bin/env python3
"""mcp/github/server_common.py
Shared FastAPI route helpers for github-mcp server endpoints.

This module provides:
  _get_service() — FastAPI dependency returning the singleton GitHubService
  _info(msg, **kwargs) — Structured logging helper
"""

from typing import Any

from mcp.github.server import _service, logger  # noqa: PLC0415
from mcp.github.service import GitHubService  # noqa: F401


def _get_service() -> GitHubService:
    """Dependency that returns the singleton GitHubService instance."""
    return _service


def _info(msg: str, **kwargs: Any) -> None:
    """Log a structured info message with kv-log formatting."""
    from shared.formatters import fmt_kvlog  # noqa: PLC0415

    logger.info(fmt_kvlog(msg, **kwargs))
