"""tests/mcp_servers/conftest.py — Fixtures shared by the MCP server tests."""

from __future__ import annotations

import logging
import pathlib
from collections.abc import Callable, Iterator
from types import ModuleType
from typing import Any

import pytest
from fastapi.testclient import TestClient

from tests.mcp_servers._auth_headers import MCP_TEST_AUTH_HEADERS

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

# Every module that declares a TOOL_LIST with the required retry_policy field.
_TOOL_LIST_MODULES = (
    "mcp_servers.cicd.cicd_tools",
    "mcp_servers.file.delete_tools",
    "mcp_servers.file.read_tools",
    "mcp_servers.file.write_tools",
    "mcp_servers.git.git_tools",
    "mcp_servers.github.github_tools",
    "mcp_servers.mdq.mdq_tools",
    "mcp_servers.rag_pipeline.rag_pipeline_tools",
    "mcp_servers.shell.shell_tools",
    "mcp_servers.web_search.web_search_tools",
)


def _declared_tool_entries() -> list[dict]:
    """Every TOOL_LIST entry across the declared modules, in module order."""
    from importlib import import_module

    entries: list[dict] = []
    for name in _TOOL_LIST_MODULES:
        entries.extend(getattr(import_module(name), "TOOL_LIST", ()))
    return entries


def _declared_retry_policies() -> dict[str, str]:
    """Union of the declared retry_policy metadata across all TOOL_LISTs."""
    policies: dict[str, str] = {}
    for entry in _declared_tool_entries():
        policies[str(entry["name"])] = str(entry["retry_policy"])
    return policies


@pytest.fixture(autouse=True)
def _emulate_dedup_bootstrap() -> Iterator[None]:
    """Emulate the server bootstrap seams for TestClient-based endpoint tests.

    A live MCP server calls ``configure_dedup()``,
    ``configure_tool_retry_policies()`` and
    ``configure_tool_preview_capabilities()`` inside ``run_http()`` (mcpdl003
    REQ-001/REQ-005; the preview seam is plan mcpai005 REQ-010); these tests
    construct server apps directly and skip that
    bootstrap. Without it, side-effecting tools fail closed on the
    ``not_configured`` degradation path and a declared ``dry_run`` argument
    resolves to ``applied`` instead of ``preview``. The store config comes from the
    session's isolated config copy (its ``[dedup]`` db_path is rewritten into
    the isolation root), matching what each server file would inject in
    production.
    """
    import os
    import tomllib
    from pathlib import Path

    import mcp_servers.dispatch as dispatch_mod
    from mcp_servers.execution_context import configure_tool_preview_capabilities
    from shared.mcp_dedup import load_dedup_section

    cfg_dir = Path(
        os.environ.get("LLMAGENT_CONFIG_DIR")
        or Path(__file__).resolve().parents[2] / "config"
    )
    own_file = "shell_mcp_server.toml"
    data = tomllib.loads((cfg_dir / own_file).read_text(encoding="utf-8"))
    store_config = load_dedup_section(data.get("dedup"), own_file)
    dispatch_mod.configure_dedup(store_config)
    entries = _declared_tool_entries()
    dispatch_mod._tool_retry_policies = _declared_retry_policies()
    configure_tool_preview_capabilities(entries)
    yield
    opened = dispatch_mod._dedup_store
    if opened is not None:
        opened.close()
    dispatch_mod._dedup_store = None
    dispatch_mod._dedup_config = None
    dispatch_mod._dedup_disabled = False
    dispatch_mod._dedup_start_state = None
    dispatch_mod._purge_done = False
    dispatch_mod._tool_retry_policies = {}
    configure_tool_preview_capabilities(())


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
    """Give dispatch_tool's durable-dedup store a throwaway tmp DB.

    Server endpoint tests route through ``dispatch_tool``; the injection-only
    contract (mcpdl003 REQ-001) leaves an unconfigured dispatcher fail-closed
    (`not_configured`), so this fixture builds a `DedupStoreConfig` and injects
    the opened store through the dispatch module's configure seam rather than
    relying on any config discovery. Opt in by adding ``isolated_dedup`` to a
    test's parameters.
    """
    import mcp_servers.dispatch as dispatch_mod
    from shared.mcp_dedup import DedupStore, DedupStoreConfig

    db_path = tmp_path / "mcp_dedup.sqlite"
    db_str = str(db_path)
    store = DedupStore(db_str)
    config = DedupStoreConfig(
        db_path=db_str,
        retention_days=14,
        pending_timeout_minutes=10,
    )
    monkeypatch.setattr(dispatch_mod, "_dedup_store", store)
    monkeypatch.setattr(dispatch_mod, "_dedup_config", config)
    monkeypatch.setattr(dispatch_mod, "_dedup_disabled", False)
    monkeypatch.setattr(dispatch_mod, "_dedup_start_state", None)
    yield db_path
    store.close()
    dispatch_mod._duplicate_cache.clear()


class HttpBoundary:
    """One MCP server app at the real HTTP boundary, plus its schema helper.

    `client` is the live FastAPI application with the shared test token headers;
    `dedup_path` is the tmp store `isolated_dedup` injected through the dispatch
    seam. `tool_schema` reads the published schema from the same boundary the
    runtime contract is asserted at, so a contract test does not mix an
    in-process view with the wire view.
    """

    def __init__(self, client: TestClient, dedup_path: pathlib.Path) -> None:
        self.client = client
        self.dedup_path = dedup_path

    def tool_schema(self, tool_name: str) -> dict[str, Any]:
        """Return the published `inputSchema` for one tool name at this boundary."""
        resp = self.client.get("/v1/tools?include_disabled=true")
        resp.raise_for_status()
        for tool in resp.json()["tools"]:
            if tool["name"] == tool_name:
                return dict(tool["inputSchema"])
        raise KeyError(f"tool {tool_name!r} is not published at the HTTP boundary")


@pytest.fixture
def http_boundary(
    isolated_dedup: pathlib.Path,
) -> Iterator[Callable[[ModuleType], HttpBoundary]]:
    """Give a security-contract test the real HTTP boundary of one MCP server app.

    The app, the service, the validation, and the dedup gate stay real; only the
    upstream API client is mocked, and that mock is supplied by the consuming test
    file, so a refused request is observable as a refusal rather than a stubbed
    response. Opt in by adding `http_boundary` to a test's parameters and calling
    the factory with the server module.
    """
    opened: list[HttpBoundary] = []

    def boundary(module: ModuleType) -> HttpBoundary:
        client = TestClient(module.app, headers=MCP_TEST_AUTH_HEADERS)
        item = HttpBoundary(client, isolated_dedup)
        opened.append(item)
        return item

    yield boundary
    for item in opened:
        item.client.close()
