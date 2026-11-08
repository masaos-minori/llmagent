"""tests/mcp_servers/conftest.py — Fixtures shared by the MCP server tests."""

from __future__ import annotations

import logging
import pathlib
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


@pytest.fixture
def isolated_dedup(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> Iterator[pathlib.Path]:
    """Point dispatch_tool's durable-dedup store at a throwaway tmp DB.

    Server endpoint tests route through ``dispatch_tool``; without isolation they
    fall back to the production ``mcp_dedup.sqlite``, which the autouse
    ``_forbid_production_paths`` guard rejects (raising inside ``open_dedup_store``
    and degrading dedup to unavailable). A fresh isolated store keeps dedup
    initializing cleanly so side-effecting calls dispatch normally and never
    touch a production path. Opt in by adding ``isolated_dedup`` to a test's
    parameters.
    """
    import mcp_servers.dispatch as dispatch_mod
    from shared.mcp_dedup import DedupConfig, DedupStore

    db_path = tmp_path / "mcp_dedup.sqlite"
    db_str = str(db_path)
    store = DedupStore(db_str)
    config = DedupConfig(
        db_path=db_str,
        retention_days=14,
        pending_timeout_minutes=10,
        retry_class={},
    )
    monkeypatch.setattr(dispatch_mod, "_dedup_store", store)
    monkeypatch.setattr(dispatch_mod, "_dedup_config", config)
    monkeypatch.setattr(dispatch_mod, "_dedup_disabled", False)
    yield db_path
    store.close()
    dispatch_mod._duplicate_cache.clear()
