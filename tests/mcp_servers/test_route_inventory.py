"""tests/mcp_servers/test_route_inventory.py — One route-inventory case per MCP app.

Each case imports its app and asserts (via the shared helper in
``_route_inventory.py``) that the only operation-specific execution route is
``POST /v1/call_tool``. Reintroducing a direct execution route fails CI here
(REQ-007, AC-5). The helper stays import-light; this module is the only place that
knows which production app modules exist and which non-execution GET paths each
app legitimately retains.
"""

from __future__ import annotations

import importlib
from collections.abc import Sequence

import pytest

from tests.mcp_servers._route_inventory import (
    DEFAULT_APPROVED_NON_EXECUTION_GET,
    assert_single_call_tool_post,
)

# (module, approved non-execution GET set) for every MCP app. Every app approves the
# two standard diagnostics; the read app additionally retains /list_allowed_directories
# (AC-4 disposition). Keep this list in step with the apps in scripts/mcp_servers.
_APPS: Sequence[tuple[str, set[str]]] = [
    ("mcp_servers.shell.shell_server", set(DEFAULT_APPROVED_NON_EXECUTION_GET)),
    ("mcp_servers.git.git_server", set(DEFAULT_APPROVED_NON_EXECUTION_GET)),
    (
        "mcp_servers.web_search.web_search_server",
        set(DEFAULT_APPROVED_NON_EXECUTION_GET),
    ),
    ("mcp_servers.file.delete_server", set(DEFAULT_APPROVED_NON_EXECUTION_GET)),
    ("mcp_servers.file.write_server", set(DEFAULT_APPROVED_NON_EXECUTION_GET)),
    (
        "mcp_servers.file.read_server",
        {"/health", "/v1/tools", "/list_allowed_directories"},
    ),
    ("mcp_servers.github.github_server", set(DEFAULT_APPROVED_NON_EXECUTION_GET)),
    ("mcp_servers.cicd.cicd_server", set(DEFAULT_APPROVED_NON_EXECUTION_GET)),
    (
        "mcp_servers.rag_pipeline.rag_pipeline_server",
        set(DEFAULT_APPROVED_NON_EXECUTION_GET),
    ),
    ("mcp_servers.mdq.mdq_server", set(DEFAULT_APPROVED_NON_EXECUTION_GET)),
]


@pytest.mark.parametrize(("module", "approved_get"), _APPS)
def test_route_inventory(module: str, approved_get: set[str]) -> None:
    server = importlib.import_module(module)
    assert_single_call_tool_post(
        server.app, label=module, approved_non_execution_get=approved_get
    )
