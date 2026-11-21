"""
tests/test_agent_repl_tool_exec.py
Unit tests for agent_repl_tool_exec security functions:
  - _classify_risk: declared-tier mapping, delete_directory escalation
  - _check_allowed_root: ALLOWED_ROOT enforcement
  - _check_allowed_repo: GitHub repo allowlist (Fail-Closed)

agentcfg003: tier and resource-key decisions read the registered tool's
declared metadata through the RuntimeToolRegistry; the removed per-tool config
maps (approval_risk_rules, tool_safety_tiers, approval_resource_keys) no
longer exist.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
from agent.tool_loop_guard import ToolLoopGuard
from agent.tool_policy import (
    check_allowed_repo as _check_allowed_repo,
)
from agent.tool_policy import (
    check_allowed_root as _check_allowed_root,
)
from agent.tool_policy import (
    classify_risk as _classify_risk,
)
from shared.runtime_tool_registry import RuntimeToolRegistry

from tests.agent.test_tool_policy import _runtime_tool, _stub_registry, _write_registry

# ── Fixtures ──────────────────────────────────────────────────────────────────


def _make_cfg(
    *,
    allowed_root: str = "",
    approval_github_allowed_repos: list | None = None,
    approval_protected_paths: list | None = None,
    approval_high_risk_branches: list | None = None,
    approval_shell_safe_prefixes: list | None = None,
) -> MagicMock:
    cfg = MagicMock()
    cfg.approval.allowed_root = allowed_root
    cfg.approval.approval_github_allowed_repos = (
        approval_github_allowed_repos
        if approval_github_allowed_repos is not None
        else []
    )
    cfg.approval.approval_protected_paths = approval_protected_paths or []
    cfg.approval.approval_high_risk_branches = approval_high_risk_branches or []
    cfg.approval.approval_shell_safe_prefixes = approval_shell_safe_prefixes or []
    return cfg


def _tier_registry(**tier_by_tool: str) -> RuntimeToolRegistry:
    """Registry stub whose tools carry the given declared agent_safety_tier."""
    return RuntimeToolRegistry(
        tools={
            name: _runtime_tool(
                name,
                {},
                tier=tier,
                is_write=tier != "READ_ONLY",
                side_effect_class="read_only" if tier == "READ_ONLY" else "local_write",
            )
            for name, tier in tier_by_tool.items()
        },
        allowed_servers=frozenset({"test_server"}),
    )


# ── _classify_risk: tier fallback ─────────────────────────────────────────────


class TestClassifyRiskTierFallback:
    """REQ-004: the declared agent_safety_tier read from the live registry is the
    only tier source; the removed approval_risk_rules map can no longer override
    it in either direction."""

    def test_read_only_tier_maps_to_none(self) -> None:
        cfg = _make_cfg()
        reg = _tier_registry(read_text_file="READ_ONLY")
        assert _classify_risk(cfg, "read_text_file", {}, reg) == "none"

    def test_write_safe_tier_maps_to_none(self) -> None:
        cfg = _make_cfg()
        reg = _tier_registry(write_file="WRITE_SAFE")
        assert _classify_risk(cfg, "write_file", {}, reg) == "none"

    def test_write_dangerous_tier_maps_to_medium(self) -> None:
        cfg = _make_cfg()
        reg = _tier_registry(delete_file="WRITE_DANGEROUS")
        assert _classify_risk(cfg, "delete_file", {}, reg) == "medium"

    def test_admin_tier_maps_to_high(self) -> None:
        cfg = _make_cfg(approval_shell_safe_prefixes=[])
        reg = _tier_registry(shell_run="ADMIN")
        assert _classify_risk(cfg, "shell_run", {"command": "rm -rf /"}, reg) == "high"

    def test_unregistered_tool_defaults_to_high_risk(self) -> None:
        # The tool is absent from the registry: no declaration to consult →
        # fail-safe HIGH (ADR-003 Decision #6: no fallback source).
        cfg = _make_cfg()
        reg = _tier_registry(write_file="WRITE_SAFE")
        assert _classify_risk(cfg, "some_unknown_tool", {}, reg) == "high"

    def test_declared_tier_is_the_only_risk_source(self) -> None:
        # write_file declares WRITE_SAFE → none: no removed rules map can raise
        # it, so the tier branch alone decides.
        cfg = _make_cfg()
        reg = _tier_registry(write_file="WRITE_SAFE")
        assert _classify_risk(cfg, "write_file", {}, reg) == "none"

    def test_no_override_lowers_dangerous_tier(self) -> None:
        # delete_file declares WRITE_DANGEROUS → medium: no removed rules map
        # exists to force an explicit level below the declaration.
        cfg = _make_cfg()
        reg = _tier_registry(delete_file="WRITE_DANGEROUS")
        assert _classify_risk(cfg, "delete_file", {}, reg) == "medium"


# ── _classify_risk: delete_directory escalation ───────────────────────────────


class TestClassifyRiskDeleteDirectory:
    """delete_directory declares WRITE_DANGEROUS (medium base); the recursive
    argument special-case escalates to HIGH regardless of other args."""

    def test_delete_directory_recursive_escalates_to_high(self) -> None:
        cfg = _make_cfg()
        reg = _write_registry(delete_directory={"path": "path"})
        assert (
            _classify_risk(cfg, "delete_directory", {"recursive": True}, reg) == "high"
        )

    def test_delete_directory_non_recursive_stays_medium(self) -> None:
        cfg = _make_cfg()
        reg = _write_registry(delete_directory={"path": "path"})
        assert (
            _classify_risk(cfg, "delete_directory", {"recursive": False}, reg)
            == "medium"
        )

    def test_delete_directory_no_recursive_key_stays_medium(self) -> None:
        cfg = _make_cfg()
        reg = _write_registry(delete_directory={"path": "path"})
        assert _classify_risk(cfg, "delete_directory", {}, reg) == "medium"

    def test_delete_directory_recursive_from_declared_tier_escalates(self) -> None:
        # Declared tier WRITE_DANGEROUS → medium; then recursive escalates to high
        cfg = _make_cfg()
        reg = _tier_registry(delete_directory="WRITE_DANGEROUS")
        assert (
            _classify_risk(cfg, "delete_directory", {"recursive": True}, reg) == "high"
        )

    def test_delete_directory_without_registry_fails_closed(self) -> None:
        # No registry: no declaration, base HIGH; recursive keeps it HIGH.
        cfg = _make_cfg()
        assert _classify_risk(cfg, "delete_directory", {"recursive": False}) == "high"


# ── _check_allowed_root ────────────────────────────────────────────────────────


class TestCheckAllowedRoot:
    """REQ-008: the jail checks the registered tool's declared path-kind keys; a
    tool whose declared scope cannot be resolved denies (fail closed)."""

    def test_empty_allowed_root_denies_path_arguments(self, tmp_path: Path) -> None:
        # REQ-003: an empty allowed_root fails closed for path-bearing calls
        cfg = _make_cfg(allowed_root="")
        reg = _stub_registry(write_file={"path": "path"})
        assert not _check_allowed_root(
            cfg, "write_file", {"path": str(tmp_path / "a.txt")}, reg
        )

    def test_unregistered_tool_denies(self, tmp_path: Path) -> None:
        # No declaration to resolve the scope against: the jail denies.
        cfg = _make_cfg(allowed_root=str(tmp_path))
        assert not _check_allowed_root(
            cfg, "write_file", {"path": str(tmp_path / "a.txt")}
        )

    def test_path_within_root_is_allowed(self, tmp_path: Path) -> None:
        cfg = _make_cfg(allowed_root=str(tmp_path))
        reg = _stub_registry(write_file={"path": "path"})
        assert _check_allowed_root(
            cfg, "write_file", {"path": str(tmp_path / "sub" / "f.txt")}, reg
        )

    def test_path_outside_root_is_denied(self, tmp_path: Path) -> None:
        root = tmp_path / "allowed"
        root.mkdir()
        cfg = _make_cfg(allowed_root=str(root))
        reg = _stub_registry(write_file={"path": "path"})
        assert not _check_allowed_root(
            cfg, "write_file", {"path": str(tmp_path / "outside.txt")}, reg
        )

    def test_path_at_root_boundary_is_allowed(self, tmp_path: Path) -> None:
        cfg = _make_cfg(allowed_root=str(tmp_path))
        reg = _stub_registry(create_directory={"path": "path"})
        # Exact root itself
        assert _check_allowed_root(
            cfg, "create_directory", {"path": str(tmp_path)}, reg
        )

    def test_relative_path_within_root_is_allowed(self, tmp_path: Path) -> None:
        cfg = _make_cfg(allowed_root=".")
        reg = _stub_registry(write_file={"path": "path"})
        assert _check_allowed_root(cfg, "write_file", {"path": "."}, reg)

    def test_traversal_path_outside_root_is_denied(self, tmp_path: Path) -> None:
        root = tmp_path / "allowed"
        root.mkdir()
        cfg = _make_cfg(allowed_root=str(root))
        reg = _stub_registry(write_file={"path": "path"})
        assert not _check_allowed_root(
            cfg, "write_file", {"path": str(root / ".." / "outside.txt")}, reg
        )

    def test_symlink_inside_root_is_allowed(self, tmp_path: Path) -> None:
        root = tmp_path / "allowed"
        root.mkdir()
        target = root / "target.txt"
        target.write_text("content", encoding="utf-8")
        link = root / "link.txt"
        link.symlink_to(target)
        cfg = _make_cfg(allowed_root=str(root))
        reg = _stub_registry(write_file={"path": "path"})
        assert _check_allowed_root(cfg, "write_file", {"path": str(link)}, reg)

    def test_symlink_outside_root_is_denied(self, tmp_path: Path) -> None:
        root = tmp_path / "allowed"
        root.mkdir()
        outside = tmp_path / "other"
        outside.mkdir()
        target = outside / "target.txt"
        target.write_text("content", encoding="utf-8")
        link = root / "link.txt"
        link.symlink_to(target)
        cfg = _make_cfg(allowed_root=str(root))
        reg = _stub_registry(write_file={"path": "path"})
        assert not _check_allowed_root(cfg, "write_file", {"path": str(link)}, reg)

    def test_tool_without_declared_path_keys_is_allowed(self, tmp_path: Path) -> None:
        # shell_run declares no path-kind keys → nothing to jail-check
        cfg = _make_cfg(allowed_root=str(tmp_path))
        reg = _stub_registry(shell_run={})
        assert _check_allowed_root(cfg, "shell_run", {"command": "ls"}, reg)

    def test_source_and_destination_both_checked(self, tmp_path: Path) -> None:
        root = tmp_path / "allowed"
        root.mkdir()
        outside = tmp_path / "other"
        outside.mkdir()
        cfg = _make_cfg(allowed_root=str(root))
        reg = _stub_registry(move_file={"source": "path", "destination": "path"})
        # source inside, destination outside → denied
        assert not _check_allowed_root(
            cfg,
            "move_file",
            {"source": str(root / "f.txt"), "destination": str(outside / "f.txt")},
            reg,
        )

    def test_undeclared_argument_is_not_jail_checked(self, tmp_path: Path) -> None:
        # move_file declares only source/destination: an "path"-named arg the tool
        # does not declare is outside its declared scope and is not checked.
        root = tmp_path / "allowed"
        root.mkdir()
        cfg = _make_cfg(allowed_root=str(root))
        reg = _stub_registry(move_file={"source": "path"})
        assert _check_allowed_root(
            cfg,
            "move_file",
            {"source": str(root / "f.txt"), "path": "/etc/passwd"},
            reg,
        )

    def test_empty_path_value_is_skipped(self, tmp_path: Path) -> None:
        # Empty string path values are ignored
        cfg = _make_cfg(allowed_root=str(tmp_path))
        reg = _stub_registry(write_file={"path": "path"})
        assert _check_allowed_root(cfg, "write_file", {"path": ""}, reg)

    def test_relative_path_denied_when_root_is_absolute(self, tmp_path: Path) -> None:
        cfg = _make_cfg(allowed_root=str(tmp_path))
        reg = _stub_registry(write_file={"path": "path"})
        assert not _check_allowed_root(
            cfg, "write_file", {"path": "relative/file.txt"}, reg
        )

    def test_relative_path_allowed_when_cwd_is_root(self) -> None:
        cwd = Path.cwd()
        cfg = _make_cfg(allowed_root=str(cwd))
        reg = _stub_registry(write_file={"path": "path"})
        assert _check_allowed_root(cfg, "write_file", {"path": "subdir/file.txt"}, reg)

    def test_absolute_path_denied_when_root_is_relative_and_path_is_outside(
        self,
    ) -> None:
        cfg = _make_cfg(allowed_root=".")
        reg = _stub_registry(write_file={"path": "path"})
        assert not _check_allowed_root(cfg, "write_file", {"path": "/etc/passwd"}, reg)


# ── _check_allowed_repo ────────────────────────────────────────────────────────


class TestCheckAllowedRepo:
    def test_non_github_write_tool_always_allowed(self) -> None:
        cfg = _make_cfg(approval_github_allowed_repos=[])
        assert _check_allowed_repo(cfg, "write_file", {"owner": "x", "repo": "y"})

    def test_github_read_tool_always_allowed(self) -> None:
        cfg = _make_cfg(approval_github_allowed_repos=[])
        assert _check_allowed_repo(
            cfg, "github_get_file_contents", {"owner": "x", "repo": "y"}
        )

    def test_fail_closed_empty_allowlist_denies_all_writes(self) -> None:
        cfg = _make_cfg(approval_github_allowed_repos=[])
        assert not _check_allowed_repo(
            cfg, "github_push_files", {"owner": "myorg", "repo": "myrepo"}
        )

    def test_repo_in_allowlist_is_allowed(self) -> None:
        cfg = _make_cfg(approval_github_allowed_repos=["myorg/myrepo"])
        assert _check_allowed_repo(
            cfg, "github_push_files", {"owner": "myorg", "repo": "myrepo"}
        )

    def test_repo_not_in_allowlist_is_denied(self) -> None:
        cfg = _make_cfg(approval_github_allowed_repos=["myorg/myrepo"])
        assert not _check_allowed_repo(
            cfg, "github_push_files", {"owner": "myorg", "repo": "other"}
        )

    def test_delete_file_denied_when_allowlist_empty(self) -> None:
        cfg = _make_cfg(approval_github_allowed_repos=[])
        assert not _check_allowed_repo(
            cfg, "github_delete_file", {"owner": "a", "repo": "b"}
        )

    def test_merge_pr_allowed_with_matching_repo(self) -> None:
        cfg = _make_cfg(approval_github_allowed_repos=["org/repo"])
        assert _check_allowed_repo(
            cfg, "github_merge_pull_request", {"owner": "org", "repo": "repo"}
        )

    def test_missing_owner_repo_args_treated_as_empty_string(self) -> None:
        # owner/repo = "/" which won't match any allowlist entry
        cfg = _make_cfg(approval_github_allowed_repos=["org/repo"])
        assert not _check_allowed_repo(cfg, "github_push_files", {})

    @pytest.mark.parametrize(
        "tool_name",
        [
            "github_push_files",
            "github_create_or_update_file",
            "github_delete_file",
            "github_merge_pull_request",
            "github_create_pull_request",
            "github_update_pull_request",
            "github_create_branch",
            "github_create_issue",
            "github_add_issue_comment",
        ],
    )
    def test_all_github_write_tools_checked(self, tool_name: str) -> None:
        cfg = _make_cfg(approval_github_allowed_repos=[])
        assert not _check_allowed_repo(cfg, tool_name, {"owner": "a", "repo": "b"})


# ── execute_all_tool_calls DAG evaluation ─────────────────────────────────────


def _make_tool_call(name: str, call_id: str = "id1") -> dict:
    """Helper: build a minimal tool_call dict."""
    return {"id": call_id, "function": {"name": name, "arguments": "{}"}}


def _runtime_tools_for_dag(is_write_by_name: dict[str, bool]) -> MagicMock:
    """Stub RuntimeToolRegistry for agent.tool_preparation.prepare_tool_calls(),

    which now runs unconditionally inside execute_all_tool_calls() before
    these tests' mocked run_approval_checks()/execute_one_tool_call() ever
    see a call. Provides a permissive zero-argument schema (so argument
    validation passes) and the given is_write per tool name (so DAG scheduling
    orders correctly).
    """
    from shared.tool_spec import ToolSpec

    registry = MagicMock()

    def _get(name: str) -> MagicMock:
        tool = MagicMock()
        tool.is_write = is_write_by_name.get(name, False)
        tool.input_schema = {"type": "object", "properties": {}}
        tool.allow_extra_fields = True
        return tool

    def _spec_for_call(call_id: str, name: str, args: dict) -> ToolSpec:
        return ToolSpec(
            call_id=call_id,
            name=name,
            args=args,
            is_write=is_write_by_name.get(name, False),
        )

    registry.get = MagicMock(side_effect=_get)
    registry.tool_spec_for_call = MagicMock(side_effect=_spec_for_call)
    return registry


def _make_ctx_for_dag(
    *,
    serial_tool_calls: bool = False,
    is_write_by_name: dict[str, bool] | None = None,
) -> MagicMock:
    ctx = MagicMock()
    ctx.cfg.tool.serial_tool_calls = serial_tool_calls
    ctx.cfg.tool.tool_result_max_llm_chars = 8000
    ctx.cfg.tools_results_turn_max_chars = 50000
    ctx.cfg.tool.tool_results_turn_max_chars = 50000
    ctx.cfg.tool.tool_empty_result_max_repeats = 0  # mid-round scan disabled
    ctx.conv.history = []
    ctx.conv.extend_messages = AsyncMock()
    ctx.services = MagicMock()
    ctx.services_required.gateway = None
    ctx.services_required.runtime_tools = _runtime_tools_for_dag(is_write_by_name or {})
    ctx.session = MagicMock()
    ctx.session.save_many = MagicMock()
    # Tool-result persist routes through the turn's atomic boundary (SEQ-08);
    # expose an awaitable save_phase_grouped so complete_round()'s round path
    # resolves it without a real session/DB.
    ctx.turn.persistence_boundary = _persistence_boundary_mock()
    return ctx


def _persistence_boundary_mock() -> MagicMock:
    """A stand-in TurnPersistence with awaitable write methods.

    Lets execute_all_tool_calls route its round persist through
    ``ctx.turn.persistence_boundary`` (SEQ-08) without a real session/DB.
    """
    boundary = MagicMock()
    boundary.save = AsyncMock(return_value=None)
    boundary.save_many = AsyncMock(return_value=None)
    boundary.save_phase_grouped = AsyncMock(return_value=None)
    boundary.replace_messages = AsyncMock(return_value=None)
    return boundary


@pytest.mark.asyncio
async def test_dag_write_executed_before_read() -> None:
    """DAG スケジューリング(既定・常時有効)で WRITE_TOOLS が READ/other より先に実行されること。"""
    from unittest.mock import AsyncMock, patch

    from agent.tool_runner import execute_all_tool_calls

    execution_order: list[str] = []

    write_call = _make_tool_call("write_file", "w1")
    read_call = _make_tool_call("read_file", "r1")

    async def fake_execute_one(ctx, pc, guard, *, state_key=None):
        name = pc.name
        execution_order.append(name)
        return MagicMock(
            tool_call_id=pc.call_id,
            content="ok",
            is_error=False,
            tool_name=name,
        )

    ctx = _make_ctx_for_dag(is_write_by_name={"write_file": True, "read_file": False})

    with (
        patch(
            "agent.tool_runner.execute_one_tool_call",
            side_effect=fake_execute_one,
        ),
        patch("agent.tool_runner._collect_tool_result_msgs", return_value=[]),
        patch(
            "agent.tool_approval.run_approval_checks",
            new_callable=AsyncMock,
            side_effect=lambda ctx, prepared: (prepared, []),
        ),
    ):
        await execute_all_tool_calls(
            ctx, [write_call, read_call], turn=1, guard=ToolLoopGuard(ctx)
        )

    assert execution_order.index("write_file") < execution_order.index("read_file")


@pytest.mark.asyncio
async def test_dag_serial_tool_calls_overrides_dag() -> None:
    """serial_tool_calls=True のとき DAG スケジューリングより優先して直列実行になること。"""
    from unittest.mock import AsyncMock, patch

    from agent.tool_runner import execute_all_tool_calls

    execution_order: list[str] = []

    write_call = _make_tool_call("write_file", "w1")
    read_call = _make_tool_call("read_file", "r1")

    async def fake_execute_one(ctx, pc, guard, *, state_key=None):
        name = pc.name
        execution_order.append(name)
        return MagicMock(
            tool_call_id=pc.call_id,
            content="ok",
            is_error=False,
            tool_name=name,
        )

    ctx = _make_ctx_for_dag(
        serial_tool_calls=True,
        is_write_by_name={"write_file": True, "read_file": False},
    )

    with (
        patch(
            "agent.tool_runner.execute_one_tool_call",
            side_effect=fake_execute_one,
        ),
        patch("agent.tool_runner._collect_tool_result_msgs", return_value=[]),
        patch(
            "agent.tool_approval.run_approval_checks",
            new_callable=AsyncMock,
            side_effect=lambda ctx, prepared: (prepared, []),
        ),
    ):
        await execute_all_tool_calls(
            ctx, [write_call, read_call], turn=1, guard=ToolLoopGuard(ctx)
        )

    # serial_tool_calls=True → DAG を使わず直列: LLM 指定順で実行
    assert execution_order == ["write_file", "read_file"]


@pytest.mark.asyncio
async def test_parallel_execution_without_side_effects() -> None:
    """副作用のない read ツールのみのとき、DAG スケジューリングで両方が実行されること。"""
    from unittest.mock import AsyncMock, patch

    from agent.tool_runner import execute_all_tool_calls

    execution_order: list[str] = []

    # 副作用なしツール (READ_TOOLS に含まれる)
    read_call1 = _make_tool_call("read_file", "r1")
    read_call2 = _make_tool_call("read_file", "r2")

    async def fake_execute_one(ctx, pc, guard, *, state_key=None):
        name = pc.name
        execution_order.append(pc.call_id)
        return MagicMock(
            tool_call_id=pc.call_id,
            content="ok",
            is_error=False,
            tool_name=name,
        )

    ctx = _make_ctx_for_dag(is_write_by_name={"read_file": False})

    with (
        patch(
            "agent.tool_runner.execute_one_tool_call",
            side_effect=fake_execute_one,
        ),
        patch("agent.tool_runner._collect_tool_result_msgs", return_value=[]),
        patch(
            "agent.tool_approval.run_approval_checks",
            new_callable=AsyncMock,
            side_effect=lambda ctx, prepared: (prepared, []),
        ),
    ):
        await execute_all_tool_calls(
            ctx, [read_call1, read_call2], turn=1, guard=ToolLoopGuard(ctx)
        )

    # 両方が実行されたこと
    assert set(execution_order) == {"r1", "r2"}
