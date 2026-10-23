"""tests/mcp_servers/conftest.py — Fixtures shared by the MCP server tests."""

from __future__ import annotations

import logging
from collections.abc import Iterator

import pytest

# shared.logger.Logger sets propagate = False, which hides these servers' records from
# caplog; production behavior is unaffected because a server process has no root handler.
_SERVER_LOGGER_NAMES = (
    "mcp_servers.shell.shell_server",
    "mcp_servers.git.git_server",
    "mcp_servers.github.github_server",
    "mcp_servers.cicd.cicd_server",
    "mcp_servers.rag_pipeline.rag_pipeline_server",
    "mcp_servers.web_search.web_search_server",
)


@pytest.fixture(autouse=True)
def _propagate_server_loggers(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Let caplog capture the server module loggers by restoring propagation."""
    for name in _SERVER_LOGGER_NAMES:
        monkeypatch.setattr(logging.getLogger(name), "propagate", True)
    yield
