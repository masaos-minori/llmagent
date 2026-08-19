#!/usr/bin/env python3
"""scripts/mcp_servers/github/github_server_common.py

Shared FastAPI route helpers for github-mcp server endpoints.

This module provides:
  _get_service() — FastAPI dependency returning the singleton GitHubService
  _info(msg, **kwargs) — Structured logging helper
"""

from typing import Any

from mcp_servers.github.github_service_dispatch import GitHubService


def _get_service() -> GitHubService:
    """Dependency that returns the singleton GitHubService instance."""
    from mcp_servers.github.github_server import _service

    return _service


def _info(msg: str, **kwargs: Any) -> None:
    """Log a structured info message with kv-log formatting."""
    from shared.formatters import fmt_kvlog

    from mcp_servers.github.github_server import logger

    logger.info(fmt_kvlog(msg, **kwargs))
