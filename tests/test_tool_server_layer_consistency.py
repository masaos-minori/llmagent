"""tests/test_tool_server_layer_consistency.py

Guardrail tests preventing tool-definition drift across the independent layers
for all 8 MCP servers (mdq, github, shell, git, cicd, rag_pipeline,
file[read/write/delete], web_search): schema (`tools.py`), runtime dispatch
(`server.py`/service `get_dispatch_table()`), registry population
(`tool_constants.py`), and write/serial flags.

Generalizes `tests/test_mdq_tool_layer_consistency.py` (MDQ-only) to every
server. Dispatch tables are built without any real DB/network dependency:
service constructors here take only plain config values (allowlists, policy
objects), matching the same test-safe construction pattern already used by
tests/test_mcp_git.py, tests/test_shell_mcp_service.py,
tests/test_cicd_mcp_service.py, tests/test_github_mcp_service.py,
tests/test_read_service.py, tests/test_file_write_mcp_service.py, and
tests/test_file_delete_mcp_service.py.

Dispatch shapes observed (confirmed by reading each server's actual dispatch
module — do not assume from the general pattern):
  - Module-level dict: mdq (`mcp_servers.mdq.server._DISPATCH_TABLE`) and
    web_search (`mcp_servers.web_search.formatters._WEB_DISPATCH`). Both are
    plain module-level `dict[str, Callable]` built at import time.
  - Instance `get_dispatch_table()`: the other 6 registry keys (github, shell,
    git, cicd, rag_pipeline, file_read, file_write, file_delete) build the
    table from a service instance's bound methods.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock

import pytest
from shared.tool_constants import (
    CICD_TOOLS,
    CICD_WRITE_TOOLS,
    DELETE_TOOLS,
    GIT_TOOLS,
    GIT_WRITE_TOOLS,
    GITHUB_DANGEROUS_TOOLS,
    GITHUB_TOOLS,
    GITHUB_WRITE_TOOLS,
    MDQ_TOOLS,
    MDQ_WRITE_TOOLS,
    RAG_TOOLS,
    RAG_WRITE_TOOLS,
    READ_TOOLS,
    SHELL_TOOLS,
    WEB_SEARCH_TOOLS,
    WRITE_TOOLS,
)
from shared.tool_executor_helpers import is_side_effect
from shared.tool_registry import get_registry
from shared.tool_routing_validation import validate_routing_against_live


def _dispatch_keys(table: Mapping[str, Callable[..., Any]]) -> set[str]:
    return set(table)


# ── Per-server dispatch table builders ───────────────────────────────────────
# Each builder returns the live dispatch key set for one server, using only
# lightweight, test-safe construction (no real DB/network I/O).


def _mdq_dispatch() -> set[str]:
    from mcp_servers.mdq.mdq_server import _DISPATCH_TABLE

    return _dispatch_keys(_DISPATCH_TABLE)


def _web_search_dispatch() -> set[str]:
    # web_search also builds a module-level dispatch dict (_WEB_DISPATCH),
    # contrary to the "no table" assumption in the source plan — confirmed by
    # reading mcp_servers/web_search/formatters.py directly.
    from mcp_servers.web_search.formatters import _WEB_DISPATCH

    return _dispatch_keys(_WEB_DISPATCH)


def _git_dispatch() -> set[str]:
    from mcp_servers.git.git_service import GitService

    svc = GitService(allowed_repo_paths=[], read_only=True, max_log_entries=50)
    return _dispatch_keys(svc.get_dispatch_table())


def _shell_dispatch(tmp_path: Path) -> set[str]:
    from mcp_servers.shell.shell_service import ShellService
    from shared.protocols.shell import ShellPolicy

    policy = ShellPolicy(
        allowed_commands=frozenset(["ls"]),
        cwd_allowed_dirs=(str(tmp_path),),
        default_cwd=str(tmp_path),
        timeout_sec=30,
        max_output_kb=64,
        max_memory_mb=256,
        kill_policy="sigterm_then_sigkill",
        kill_grace_sec=2.0,
        execution_user="",
        shell_path="/usr/bin:/bin",
        audit_log_path=str(tmp_path / "audit.log"),
        sandbox_backend="none",
        env_allowlist=(),
        env_denylist=(),
    )
    svc = ShellService(policy)
    return _dispatch_keys(svc.get_dispatch_table())


def _cicd_dispatch() -> set[str]:
    from mcp_servers.cicd.cicd_models import CicdConfig
    from mcp_servers.cicd.cicd_service import CiCdService

    cfg = CicdConfig(repo_allowlist=[], workflow_allowlist=[], max_log_size_kb=256)
    svc = CiCdService(cfg=cfg, backend=AsyncMock())
    return _dispatch_keys(svc.get_dispatch_table())


def _github_dispatch() -> set[str]:
    from mcp_servers.github.github_models import GitHubConfig
    from mcp_servers.github.service_dispatch import GitHubService

    svc = GitHubService(
        gh=MagicMock(), cfg=GitHubConfig.from_dict({"allowed_repos": ["org/repo"]})
    )
    return _dispatch_keys(svc.get_dispatch_table())


def _rag_pipeline_dispatch() -> set[str]:
    from mcp_servers.rag_pipeline.rag_pipeline_service import RagPipelineMCPService

    svc = RagPipelineMCPService()
    return _dispatch_keys(svc.get_dispatch_table())


def _file_read_dispatch(tmp_path: Path) -> set[str]:
    from mcp_servers.file.read_service import ReadFileService

    svc = ReadFileService(
        allowed_dirs=[tmp_path],
        max_read_bytes=1024,
        max_tree_depth=3,
        max_search_results=50,
    )
    return _dispatch_keys(svc.get_dispatch_table())


def _file_write_dispatch(tmp_path: Path) -> set[str]:
    from mcp_servers.file.write_service import WriteFileService

    svc = WriteFileService(allowed_dirs=[tmp_path], max_write_bytes=1024)
    return _dispatch_keys(svc.get_dispatch_table())


def _file_delete_dispatch(tmp_path: Path) -> set[str]:
    from mcp_servers.file.delete_service import DeleteFileService

    svc = DeleteFileService(
        allowed_dirs=[tmp_path], audit_log_path=str(tmp_path / "audit.log")
    )
    return _dispatch_keys(svc.get_dispatch_table())


# ── Per-server schema (TOOL_LIST) accessors ──────────────────────────────────


def _mdq_schema() -> list[dict[str, Any]]:
    from mcp_servers.mdq.mdq_tools import TOOL_LIST

    # TOOL_LIST is typed as list[MCPToolSchema] (a TypedDict); cast to the
    # common dict[str, Any] shape used by every other server's TOOL_LIST.
    return cast(list[dict[str, Any]], list(TOOL_LIST))


def _web_search_schema() -> list[dict[str, Any]]:
    from mcp_servers.web_search.web_search_tools import TOOL_LIST

    return list(TOOL_LIST)


def _git_schema() -> list[dict[str, Any]]:
    from mcp_servers.git.git_tools import TOOL_LIST

    return list(TOOL_LIST)


def _shell_schema() -> list[dict[str, Any]]:
    from mcp_servers.shell.shell_tools import TOOL_LIST

    return list(TOOL_LIST)


def _cicd_schema() -> list[dict[str, Any]]:
    from mcp_servers.cicd.cicd_tools import TOOL_LIST

    return list(TOOL_LIST)


def _github_schema() -> list[dict[str, Any]]:
    from mcp_servers.github.github_tools import TOOL_LIST

    return list(TOOL_LIST)


def _rag_pipeline_schema() -> list[dict[str, Any]]:
    from mcp_servers.rag_pipeline.rag_pipeline_tools import TOOL_LIST

    return list(TOOL_LIST)


def _file_read_schema() -> list[dict[str, Any]]:
    from mcp_servers.file.read_tools import TOOL_LIST

    return list(TOOL_LIST)


def _file_write_schema() -> list[dict[str, Any]]:
    from mcp_servers.file.write_tools import TOOL_LIST

    return list(TOOL_LIST)


def _file_delete_schema() -> list[dict[str, Any]]:
    from mcp_servers.file.delete_tools import TOOL_LIST

    return list(TOOL_LIST)


class _ServerLayers:
    """Describes one server's cross-layer identity for the six consistency checks."""

    def __init__(
        self,
        *,
        registry_key: str,
        schema_fn: Callable[..., list[dict[str, Any]]],
        dispatch_fn: Callable[..., set[str]],
        tools_set: frozenset[str],
        write_tools: frozenset[str],
        needs_tmp_path: bool = False,
        schema_declares_flags: bool = False,
    ) -> None:
        self.registry_key = registry_key
        self.schema_fn = schema_fn
        self.dispatch_fn = dispatch_fn
        self.tools_set = tools_set
        self.write_tools = write_tools
        self.needs_tmp_path = needs_tmp_path
        self.schema_declares_flags = schema_declares_flags

    def dispatch(self, tmp_path: Path) -> set[str]:
        return self.dispatch_fn(tmp_path) if self.needs_tmp_path else self.dispatch_fn()


_SERVERS: dict[str, _ServerLayers] = {
    "mdq": _ServerLayers(
        registry_key="mdq",
        schema_fn=_mdq_schema,
        dispatch_fn=_mdq_dispatch,
        tools_set=MDQ_TOOLS,
        write_tools=MDQ_WRITE_TOOLS,
        schema_declares_flags=True,
    ),
    "web_search": _ServerLayers(
        registry_key="web_search",
        schema_fn=_web_search_schema,
        dispatch_fn=_web_search_dispatch,
        tools_set=WEB_SEARCH_TOOLS,
        write_tools=frozenset(),
    ),
    "git": _ServerLayers(
        registry_key="git",
        schema_fn=_git_schema,
        dispatch_fn=_git_dispatch,
        tools_set=GIT_TOOLS,
        write_tools=GIT_WRITE_TOOLS,
    ),
    "shell": _ServerLayers(
        registry_key="shell",
        schema_fn=_shell_schema,
        dispatch_fn=_shell_dispatch,
        tools_set=SHELL_TOOLS,
        write_tools=SHELL_TOOLS,
        needs_tmp_path=True,
    ),
    "cicd": _ServerLayers(
        registry_key="cicd",
        schema_fn=_cicd_schema,
        dispatch_fn=_cicd_dispatch,
        tools_set=CICD_TOOLS,
        write_tools=CICD_WRITE_TOOLS,
    ),
    "github": _ServerLayers(
        registry_key="github",
        schema_fn=_github_schema,
        dispatch_fn=_github_dispatch,
        tools_set=GITHUB_TOOLS,
        write_tools=GITHUB_WRITE_TOOLS | GITHUB_DANGEROUS_TOOLS,
    ),
    "rag_pipeline": _ServerLayers(
        registry_key="rag_pipeline",
        schema_fn=_rag_pipeline_schema,
        dispatch_fn=_rag_pipeline_dispatch,
        tools_set=RAG_TOOLS,
        write_tools=RAG_WRITE_TOOLS,
    ),
    "file_read": _ServerLayers(
        registry_key="file_read",
        schema_fn=_file_read_schema,
        dispatch_fn=_file_read_dispatch,
        tools_set=READ_TOOLS,
        write_tools=frozenset(),
        needs_tmp_path=True,
    ),
    "file_write": _ServerLayers(
        registry_key="file_write",
        schema_fn=_file_write_schema,
        dispatch_fn=_file_write_dispatch,
        tools_set=WRITE_TOOLS,
        write_tools=WRITE_TOOLS,
        needs_tmp_path=True,
    ),
    "file_delete": _ServerLayers(
        registry_key="file_delete",
        schema_fn=_file_delete_schema,
        dispatch_fn=_file_delete_dispatch,
        tools_set=DELETE_TOOLS,
        write_tools=DELETE_TOOLS,
        needs_tmp_path=True,
    ),
}


@pytest.mark.parametrize("server_key", sorted(_SERVERS))
def test_schema_subset_of_dispatch_table(server_key: str, tmp_path: Path) -> None:
    layers = _SERVERS[server_key]
    schema_names = {t["name"] for t in layers.schema_fn()}
    assert schema_names <= layers.dispatch(tmp_path)


@pytest.mark.parametrize("server_key", sorted(_SERVERS))
def test_dispatch_table_subset_of_schema(server_key: str, tmp_path: Path) -> None:
    layers = _SERVERS[server_key]
    schema_names = {t["name"] for t in layers.schema_fn()}
    assert layers.dispatch(tmp_path) <= schema_names


@pytest.mark.parametrize("server_key", sorted(_SERVERS))
def test_tool_constants_set_matches_schema(server_key: str) -> None:
    layers = _SERVERS[server_key]
    schema_names = {t["name"] for t in layers.schema_fn()}
    assert layers.tools_set == schema_names


@pytest.mark.parametrize("server_key", sorted(_SERVERS))
def test_tools_registered_in_registry(server_key: str) -> None:
    layers = _SERVERS[server_key]
    registry = get_registry()
    assert set(registry.get_tool_names(layers.registry_key)) == layers.tools_set


@pytest.mark.parametrize("server_key", sorted(_SERVERS))
def test_write_tools_flagged_is_write(server_key: str) -> None:
    """Write tools are recognized as side-effecting by whichever mechanism this
    server's schema uses.

    MDQ's schema declares "is_write" explicitly per tool (mirrors the original
    MDQ-only guardrail). Every other server's schema does not declare the key
    at all; for those, the schema-independent runtime fallback is
    shared.tool_executor_helpers.is_side_effect(), so the equivalent guardrail
    is verifying the write-tool set is recognized there instead — this is the
    same class of bug this whole test module (and the classify_operation_type
    fix) guards against, applied to the other serialization mechanism.
    """
    layers = _SERVERS[server_key]
    if layers.schema_declares_flags:
        for t in layers.schema_fn():
            if t["name"] in layers.write_tools:
                assert t.get("is_write") is True
    else:
        for name in layers.write_tools:
            assert is_side_effect(name)


@pytest.mark.parametrize("server_key", sorted(_SERVERS))
def test_serial_tools_flagged_requires_serial(server_key: str) -> None:
    """MDQ's schema explicitly requires_serial=True for its write tools (a
    per-tool design choice — see ToolSpec.requires_serial in
    agent/tool_scheduler.py). No other server's schema declares this key
    today; guard that invariant so a future addition is a deliberate,
    reviewed change rather than silent drift.
    """
    layers = _SERVERS[server_key]
    if layers.schema_declares_flags:
        for t in layers.schema_fn():
            if t["name"] in layers.write_tools:
                assert t.get("requires_serial") is True
    else:
        for t in layers.schema_fn():
            assert t.get("requires_serial") in (None, False)


# NOTE: validate_routing_against_live() is exercised directly here, scoped to
# search_web only (not generalized across the _SERVERS matrix above, which
# already covers a different axis: schema/dispatch/registry triple-consistency
# for all 8 servers). It is not currently wired into agent startup — see
# plans/20260719-202346_plan.md Scope, which explicitly keeps wiring
# validate_all_routing()/validate_routing_against_live() into agent/startup.py
# out of scope. This uses the real, default get_registry() rather than a
# synthetic registry, complementing tests/test_tool_registry.py's existing
# synthetic-registry unit tests for the same function.


def test_search_web_live_drift_detected_when_missing() -> None:
    """search_web is reported as missing from live discovery when the stubbed
    live_tool_lists omits it for the web_search server key."""
    drift = validate_routing_against_live(
        live_tool_lists={"web_search": ["other_tool"]}
    )
    assert "web_search" in drift
    assert any("search_web" in msg for msg in drift["web_search"])


def test_search_web_no_live_drift_when_matching() -> None:
    """No drift is reported when the stubbed live_tool_lists matches the real
    registry's search_web + browser_fetch registration for the web_search
    server key (browser_fetch merged into web_search from the retired
    standalone browser-mcp server)."""
    drift = validate_routing_against_live(
        live_tool_lists={"web_search": ["search_web", "browser_fetch"]}
    )
    assert drift == {}
