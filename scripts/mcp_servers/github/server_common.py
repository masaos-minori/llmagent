#!/usr/bin/env python3
"""mcp_servers/github/server_common.py

Shared FastAPI route helpers for github-mcp server endpoints.

This module provides:
  _get_service() — FastAPI dependency returning the singleton GitHubService
  _info(msg, **kwargs) — Structured logging helper
"""

from typing import Any

from mcp_servers.github.service_dispatch import GitHubService


def _get_service() -> GitHubService:
    """Dependency that returns the singleton GitHubService instance."""
    from mcp_servers.github.server import _service  # noqa: PLC0415

    return _service


def _info(msg: str, **kwargs: Any) -> None:
    """Log a structured info message with kv-log formatting."""
    from mcp_servers.github.server import logger  # noqa: PLC0415
    from shared.formatters import fmt_kvlog  # noqa: PLC0415

    logger.info(fmt_kvlog(msg, **kwargs))
