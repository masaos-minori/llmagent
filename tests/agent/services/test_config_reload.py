"""tests/test_config_reload.py
Error-path tests for ConfigReloadService.apply_config().
"""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any, cast
from unittest.mock import MagicMock

import pytest
from agent.config_builders import agent_config_payload
from agent.config_dataclasses import AgentConfig
from agent.services.config_outcome_classification import (
    classify_startup_only_fields,
    diff_mcp_definitions,
)
from agent.services.config_reload_transaction import PreparedStep
from shared.mcp_config import StartupMode
from shared.runtime_tool_registry import RuntimeToolRegistry

from tests.agent._config_test_defaults import (
    reload_candidate,
    reload_fixture_ctx,
)


@pytest.fixture(autouse=True)
def prompt_source_env(tmp_path, monkeypatch) -> None:
    """Point the prompt reader at a temporary source for every test (row 15).

    The reload path reads prompt content through ``agent.prompt_source``; tests
    must not depend on the committed ``registry/manifests/prompt_source.toml``,
    so the resolved directory is redirected to a per-test fixture.
    """
    manifest_dir = tmp_path / "manifests"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    (manifest_dir / "prompt_source.toml").write_text(
        'default = "fixture default prompt"\n', encoding="utf-8"
    )
    monkeypatch.setenv("LLMAGENT_REGISTRY_DIR", str(tmp_path))


def _make_ctx(**overrides: Any) -> MagicMock:
    """Build a reload ctx whose live config is what the startup entry point builds."""
    return reload_fixture_ctx(**overrides)


@pytest.fixture()
def svc() -> object:
    """Provide the service for the `apply_config()` entry-point error-path tests.

    `apply_config_dict` is the path that builds and commits a candidate; these tests
    only exercise the typed-request conversion in front of it.
    """
    from agent.services.config_reload import ConfigReloadService

    return ConfigReloadService(_make_ctx())


@pytest.fixture()
def svc_with_ctx() -> tuple[object, MagicMock]:
    from agent.services.config_reload import ConfigReloadService

    ctx = _make_ctx()
    return ConfigReloadService(ctx), ctx


class TestApplyConfig:
    def test_invalid_masked_fields_type_raises(self, svc: object) -> None:
        from agent.services.exceptions import ConfigReloadValidationError
        from agent.services.models import ConfigReloadRequest

        # A request rejects a payload of the wrong shape at construction, so a
        # bare scalar never reaches apply_config (REQ-005).
        with pytest.raises(ConfigReloadValidationError):
            ConfigReloadRequest(masked_fields="not-a-list")  # type: ignore[arg-type]

    def test_valid_masked_fields_does_not_raise(self, svc: object) -> None:
        from unittest.mock import patch

        from agent.services.config_reload import ConfigReloadOutcome
        from agent.services.models import ConfigReloadRequest

        req = ConfigReloadRequest(masked_fields=["api_key", "token"])
        with patch.object(
            type(svc), "apply_config_dict", return_value=ConfigReloadOutcome()
        ):
            result = svc.apply_config(req)  # type: ignore[attr-defined]
        assert result is not None

    def test_empty_request_does_not_raise(self, svc: object) -> None:
        from unittest.mock import patch

        from agent.services.config_reload import ConfigReloadOutcome
        from agent.services.models import ConfigReloadRequest

        req = ConfigReloadRequest()
        with patch.object(
            type(svc), "apply_config_dict", return_value=ConfigReloadOutcome()
        ):
            result = svc.apply_config(req)  # type: ignore[attr-defined]
        assert result is not None

    def test_req_to_dict_skips_none_fields(self) -> None:
        from agent.services.config_reload import ConfigReloadService
        from agent.services.models import ConfigReloadRequest

        req = ConfigReloadRequest(masked_fields=["key"])
        d = ConfigReloadService._req_to_dict(req)
        assert "masked_fields" in d
        assert "mcp_servers" not in d
        assert "approval" not in d

    def test_out_of_range_llm_temperature_rejected(
        self, svc_with_ctx: tuple[object, MagicMock]
    ) -> None:
        svc, ctx = svc_with_ctx
        from agent.services.exceptions import ConfigReloadValidationError

        ctx.cfg.llm.llm_temperature = 0.2
        with pytest.raises(ConfigReloadValidationError):
            svc.apply_config_dict({"llm_temperature": 5.0})
        assert ctx.cfg.llm.llm_temperature == 0.2

    def test_valid_llm_temperature_applied(
        self, svc_with_ctx: tuple[object, MagicMock]
    ) -> None:
        svc, ctx = svc_with_ctx
        ctx.cfg.llm.llm_temperature = 0.2
        svc.apply_config_dict({"llm_temperature": 0.5})
        assert ctx.cfg.llm.llm_temperature == 0.5

    def test_multi_field_reload_applies_all(
        self, svc_with_ctx: tuple[object, MagicMock]
    ) -> None:
        svc, ctx = svc_with_ctx
        ctx.cfg.llm.llm_temperature = 0.2
        ctx.cfg.tool.serial_tool_calls = False
        svc.apply_config_dict(
            {
                "llm_temperature": 0.5,
                "serial_tool_calls": True,
            }
        )
        assert ctx.cfg.llm.llm_temperature == 0.5
        assert ctx.cfg.tool.serial_tool_calls is True


class TestConfigReloadAtomicity:
    """Two-phase apply: an invalid section leaves every live section, direct
    field, and ctx.conv unchanged, and no service step runs (AC-001, AC-002,
    AC-003, AC-004)."""

    def test_invalid_tool_leaves_live_config_unchanged(
        self, svc_with_ctx: tuple[object, MagicMock]
    ) -> None:
        from agent.services.exceptions import ConfigReloadValidationError

        svc, ctx = svc_with_ctx
        before_llm = copy.deepcopy(ctx.cfg.llm)
        before_memory = copy.deepcopy(ctx.cfg.memory)
        payload = {
            "llm_temperature": 0.5,
            "memory_embed_url": "http://localhost:8081/embed",
            "max_tool_turns": 0,
        }
        with pytest.raises(ConfigReloadValidationError):
            svc.apply_config_dict(payload)  # type: ignore[attr-defined]
        assert ctx.cfg.llm == before_llm
        assert ctx.cfg.memory == before_memory
        # The tool policy is applied by the runtime_tools commit step, so a candidate
        # failure that never reaches the commit phase must leave the registry untouched.
        ctx.services_required.runtime_tools.apply_policy.assert_not_called()

    def test_invalid_memory_embed_url_leaves_live_memory_unchanged(
        self, svc_with_ctx: tuple[object, MagicMock]
    ) -> None:
        """The typed Memory candidate is validated before commit: an empty endpoint
        while embedding is enabled raises before any section is applied (REQ-002, AC-002)."""
        from agent.services.exceptions import ConfigReloadValidationError

        svc, ctx = svc_with_ctx
        before_memory = copy.deepcopy(ctx.cfg.memory)
        with pytest.raises(ConfigReloadValidationError):
            svc.apply_config_dict({"memory_embed_url": ""})  # type: ignore[attr-defined]
        assert ctx.cfg.memory == before_memory
        ctx.services_required.runtime_tools.apply_policy.assert_not_called()

    def test_valid_memory_embed_url_is_applied_after_validation(
        self, svc_with_ctx: tuple[object, MagicMock]
    ) -> None:
        """A valid endpoint passes the candidate's validation and is committed (REQ-002)."""
        svc, ctx = svc_with_ctx
        outcome = svc.apply_config_dict(  # type: ignore[attr-defined]
            {"memory_embed_url": "http://localhost:8082/embed"}
        )
        assert ctx.cfg.memory.memory_embed_url == "http://localhost:8082/embed"
        assert "memory" in outcome.applied

    def test_direct_fields_unchanged_on_later_failure(
        self, svc_with_ctx: tuple[object, MagicMock]
    ) -> None:
        from agent.services.exceptions import ConfigReloadValidationError

        svc, ctx = svc_with_ctx
        ctx.conv.system_prompt_content = "original prompt"
        before_allowed = list(ctx.cfg.tool.allowed_tools)
        before_masked = list(ctx.cfg.tool.masked_fields)
        before_system = ctx.conv.system_prompt_content
        # Prompt content now comes from the typed fixture source; the tool field
        # fails validation in the prepare phase, so no prompt update and no
        # other mutation is applied.
        payload = {
            "allowed_tools": ["a", "b"],
            "masked_fields": ["api_key"],
            "max_tool_turns": 0,
        }
        with pytest.raises(ConfigReloadValidationError):
            svc.apply_config_dict(payload)  # type: ignore[attr-defined]
        assert list(ctx.cfg.tool.allowed_tools) == before_allowed
        assert list(ctx.cfg.tool.masked_fields) == before_masked
        assert ctx.conv.system_prompt_content == before_system

    def test_mcp_cleanup_not_run_on_validation_failure(
        self, svc_with_ctx: tuple[object, MagicMock]
    ) -> None:
        from agent.services.exceptions import ConfigReloadValidationError
        from shared.mcp_config import McpServerConfig, TransportType

        svc, ctx = svc_with_ctx
        ctx.services_required.lifecycle.cleanup_server_resources = MagicMock()
        ctx.cfg.mcp.mcp_servers = {
            "removed": McpServerConfig(
                transport=TransportType.HTTP,
                url="http://localhost:9090",
                cmd=[],
            )
        }
        payload = {
            "mcp_servers": {
                "kept": {"transport": "http", "url": "http://localhost:8080"}
            },
            "max_tool_turns": 0,
        }
        with pytest.raises(ConfigReloadValidationError):
            svc.apply_config_dict(payload)  # type: ignore[attr-defined]
        ctx.services_required.lifecycle.cleanup_server_resources.assert_not_called()

    def test_valid_reload_applies_everything(
        self, svc_with_ctx: tuple[object, MagicMock]
    ) -> None:
        svc, ctx = svc_with_ctx
        ctx.conv.system_prompt_content = "original prompt"
        outcome = svc.apply_config_dict(  # type: ignore[attr-defined]
            {
                "llm_temperature": 0.5,
                "memory_embed_url": "http://localhost:8081/embed",
                "max_tool_turns": 7,
                "allowed_tools": ["read_file"],
                "gitops_push_blocked": True,
            }
        )
        assert ctx.cfg.llm.llm_temperature == 0.5
        assert ctx.cfg.memory.memory_embed_url == "http://localhost:8081/embed"
        assert ctx.cfg.tool.max_tool_turns == 7
        assert ctx.cfg.tool.allowed_tools == ["read_file"]
        # gitops_push_blocked is startup-only: the live value keeps the old one and
        # the field is reported instead of applied (REQ-003, AC-2).
        assert ctx.cfg.approval.gitops_push_blocked is False
        assert "gitops_push_blocked" in outcome.startup_only
        # The prompt update comes from the typed fixture source, not from a
        # config key: the fixture default differs from the runtime value, so the
        # commit-phase pending update is applied.
        assert ctx.conv.system_prompt_content == "fixture default prompt"
        assert "llm" in outcome.applied
        assert "memory" in outcome.applied
        assert "tool" in outcome.applied
        assert "approval" not in outcome.applied

    def test_prompt_source_read_error_leaves_ctx_unchanged(
        self, svc_with_ctx: tuple[object, MagicMock], tmp_path: Path, monkeypatch
    ) -> None:
        """A source read error in the candidate phase mutates nothing (AC-4)."""
        from agent.prompt_source import PromptSourceError

        svc, ctx = svc_with_ctx
        ctx.conv.system_prompt_content = "original prompt"
        before_allowed = list(ctx.cfg.tool.allowed_tools)
        # Point the reader at an empty directory: the read boundary raises there.
        empty_dir = tmp_path / "empty-registry"
        empty_dir.mkdir()
        monkeypatch.setenv("LLMAGENT_REGISTRY_DIR", str(empty_dir))
        payload = {"allowed_tools": ["a", "b"], "max_tool_turns": 7}
        with pytest.raises(PromptSourceError, match="not found"):
            svc.apply_config_dict(payload)  # type: ignore[attr-defined]
        assert list(ctx.cfg.tool.allowed_tools) == before_allowed
        assert ctx.conv.system_prompt_content == "original prompt"

    def test_removed_map_reload_keys_are_rejected(
        self, svc_with_ctx: tuple[object, MagicMock]
    ) -> None:
        """agentcfg003 REQ-005/REQ-011: a reload payload naming a removed map is
        rejected by the candidate build, and the live config is untouched."""
        from agent.services.exceptions import ConfigReloadValidationError

        svc, ctx = svc_with_ctx
        paths_before = list(ctx.cfg.approval.approval_protected_paths)
        with pytest.raises(ConfigReloadValidationError) as excinfo:
            svc.apply_config_dict(  # type: ignore[attr-defined]
                {
                    "tool_safety_tiers": {"read_file": "SUPERUSER"},
                    "approval_risk_rules": {"write_file": "extreme"},
                }
            )
        assert "tool_safety_tiers" in str(excinfo.value)
        assert "approval_risk_rules" in str(excinfo.value)
        assert not hasattr(ctx.cfg.approval, "tool_safety_tiers")
        assert not hasattr(ctx.cfg.approval, "approval_risk_rules")
        assert list(ctx.cfg.approval.approval_protected_paths) == paths_before

    def test_empty_allowed_root_rejected(
        self, svc_with_ctx: tuple[object, MagicMock]
    ) -> None:
        from agent.services.exceptions import ConfigReloadValidationError

        svc, ctx = svc_with_ctx
        ctx.cfg.approval.allowed_root = "/opt/llm"

        with pytest.raises(ConfigReloadValidationError):
            svc.apply_config_dict({"allowed_root": ""})  # type: ignore[attr-defined]

        assert ctx.cfg.approval.allowed_root == "/opt/llm"

    def test_non_absolute_allowed_root_rejected(
        self, svc_with_ctx: tuple[object, MagicMock]
    ) -> None:
        from agent.services.exceptions import ConfigReloadValidationError

        svc, ctx = svc_with_ctx
        ctx.cfg.approval.allowed_root = "/opt/llm"

        with pytest.raises(ConfigReloadValidationError):
            svc.apply_config_dict(  # type: ignore[attr-defined]
                {"allowed_root": "relative/path"}
            )

        assert ctx.cfg.approval.allowed_root == "/opt/llm"

    def test_non_string_allowed_tools_entry_rejected(
        self, svc_with_ctx: tuple[object, MagicMock]
    ) -> None:
        from agent.services.exceptions import ConfigReloadValidationError

        svc, ctx = svc_with_ctx
        ctx.cfg.tool.allowed_tools = ["read_file"]

        with pytest.raises(ConfigReloadValidationError):
            svc.apply_config_dict(  # type: ignore[attr-defined]
                {"allowed_tools": ["read_file", 42]}
            )

        assert ctx.cfg.tool.allowed_tools == ["read_file"]

    def test_unchanged_approval_survives_unrelated_invalid_reload(
        self, svc_with_ctx: tuple[object, MagicMock]
    ) -> None:
        """An invalid approval value aborts the whole reload in the candidate
        phase, so a valid change to another section is not applied either."""
        from agent.services.exceptions import ConfigReloadValidationError

        svc, ctx = svc_with_ctx
        paths_before = list(ctx.cfg.approval.approval_protected_paths)
        turns_before = ctx.cfg.tool.max_tool_turns
        ctx.cfg.approval.allowed_root = "/opt/llm"

        with pytest.raises(ConfigReloadValidationError):
            svc.apply_config_dict(  # type: ignore[attr-defined]
                {
                    "max_tool_turns": turns_before + 3,
                    "allowed_root": "",
                }
            )

        assert ctx.cfg.tool.max_tool_turns == turns_before
        assert list(ctx.cfg.approval.approval_protected_paths) == paths_before


class TestDiffMcpDefinitions:
    """diff_mcp_definitions is a pure, deterministic per-field comparison (M-1)."""

    def _make_pair(self) -> tuple[object, object]:
        from shared.mcp_config import McpServerConfig, StartupMode, TransportType

        old = McpServerConfig(
            transport=TransportType.HTTP,
            url="http://localhost:8080",
            cmd=[],
            startup_mode=StartupMode.PERSISTENT,
            auth_token="tok",
        )
        new = McpServerConfig(
            transport=TransportType.HTTP,
            url="http://localhost:8080",
            cmd=[],
            startup_mode=StartupMode.PERSISTENT,
            auth_token="tok",
        )
        return old, new

    def _diff(self, old: object, new: object) -> tuple[str, ...]:
        """Return the field paths one changed server definition reports."""
        from agent.config_dataclasses import MCPConfig

        records = diff_mcp_definitions(
            MCPConfig(mcp_servers={"svc": old}),
            MCPConfig(mcp_servers={"svc": new}),
        )
        assert len(records) == 1
        return records[0].field_paths

    def test_identical_configs_no_diff(self) -> None:
        from agent.config_dataclasses import MCPConfig

        old, new = self._make_pair()
        assert (
            diff_mcp_definitions(
                MCPConfig(mcp_servers={"svc": old}),
                MCPConfig(mcp_servers={"svc": new}),
            )
            == []
        )

    @pytest.mark.parametrize(
        "field_name,new_value",
        [
            ("url", "http://127.0.0.1:9999"),
            ("auth_token", "changed_token"),
            ("role", "changed_role"),
            ("call_timeout_sec", 999.0),
            ("startup_timeout_sec", 999),
            ("cmd", ["changed", "cmd"]),
            ("env", {"CHANGED": "1"}),
        ],
    )
    def test_single_field_change_detected(
        self, field_name: str, new_value: object
    ) -> None:
        old, new = self._make_pair()
        before_old = old.__dict__.copy()
        setattr(new, field_name, new_value)

        assert self._diff(old, new) == (f"mcp_servers/svc.{field_name}",)
        assert old.__dict__ == before_old  # never mutated

    def test_startup_mode_change_detected(self) -> None:
        from shared.mcp_config import StartupMode

        old, new = self._make_pair()
        new.startup_mode = StartupMode.SUBPROCESS
        assert self._diff(old, new) == ("mcp_servers/svc.startup_mode",)


class TestMcpServerChangeClassification:
    """diff_mcp_definitions reports every MCP definition change as a pending
    restart record and never mutates ctx.cfg.mcp.mcp_servers (H-1/H-3/H-4/H-5/H-7)."""

    _SERVER_URL = "http://localhost:8080"
    # `mcp_servers.<key>.cmd` is a non-empty list (shared.config_field_types), so
    # every server these tests declare carries a command.
    _CMD = ["python", "s.py"]

    def _server(
        self,
        url: str = _SERVER_URL,
        auth_token: str = "test-token",
        startup_mode: str = "persistent",
    ) -> dict[str, Any]:
        return {
            "transport": "http",
            "url": url,
            "cmd": self._CMD,
            "auth_token": auth_token,
            "startup_mode": startup_mode,
        }

    def _make_ctx(
        self, old_auth: str = "test-token", old_startup: str = "persistent"
    ) -> tuple[MagicMock, Any]:
        ctx = _make_ctx(
            mcp_servers={
                "svc": self._server(auth_token=old_auth, startup_mode=old_startup)
            }
        )
        return ctx, ctx.cfg.mcp.mcp_servers["svc"]

    def _run(self, ctx: MagicMock, new_mcp_servers: dict[str, Any]) -> list[Any]:
        candidate = _candidate(ctx, mcp_servers=new_mcp_servers)
        return diff_mcp_definitions(ctx.cfg.mcp, candidate.mcp)

    @staticmethod
    def _paths(records: list[Any]) -> list[str]:
        return [path for record in records for path in record.field_paths]

    # --- single-field changes (H-3, H-4, H-5) ---

    def test_url_change_reports_field_qualified_restart_entry(self) -> None:
        ctx, old_srv = self._make_ctx()
        new_srv = self._server(url="http://127.0.0.1:9090")
        records = self._run(ctx, {"svc": new_srv})

        assert "mcp_servers/svc.url" in self._paths(records)
        assert records[0].server_key == "svc"
        assert records[0].change == "changed"
        assert old_srv.url == self._SERVER_URL

    def test_auth_token_change_reports_restart_not_deferred(self) -> None:
        ctx, old_srv = self._make_ctx(old_auth="old_token")
        new_srv = self._server(auth_token="new_token")
        records = self._run(ctx, {"svc": new_srv})

        assert "mcp_servers/svc.auth_token" in self._paths(records)
        assert old_srv.auth_token == "old_token"

    @pytest.mark.parametrize(
        "old_mode,new_mode",
        [
            (StartupMode.PERSISTENT, StartupMode.SUBPROCESS),
            (StartupMode.SUBPROCESS, StartupMode.PERSISTENT),
        ],
    )
    def test_startup_mode_change_reports_restart_not_deferred(
        self, old_mode: StartupMode, new_mode: StartupMode
    ) -> None:
        ctx, old_srv = self._make_ctx(old_startup=old_mode.value)
        new_srv = self._server(startup_mode=new_mode.value)
        records = self._run(ctx, {"svc": new_srv})

        assert "mcp_servers/svc.startup_mode" in self._paths(records)
        assert old_srv.startup_mode == old_mode

    def test_removed_server_reports_restart(self) -> None:
        ctx, _ = self._make_ctx()
        records = self._run(ctx, {"other": self._server(url="http://localhost:8090")})

        assert "mcp_servers/svc" in self._paths(records)
        removed = [r for r in records if r.change == "removed"]
        assert [r.field_paths for r in removed] == [("mcp_servers/svc",)]

    def test_rename_reports_remove_and_add(self) -> None:
        ctx, _ = self._make_ctx()
        records = self._run(ctx, {"renamed_key": self._server()})

        removed = [r for r in records if r.change == "removed"]
        added = [r for r in records if r.change == "added"]
        assert [r.field_paths for r in removed] == [("mcp_servers/svc",)]
        assert [r.field_paths for r in added] == [("mcp_servers/renamed_key",)]

    # --- display strings the CLI prints (rendered by config_reload, not the classifier) ---

    def test_added_and_removed_servers_render_display_suffixes(self) -> None:
        from agent.services.config_reload import ConfigReloadService

        ctx = _make_ctx(mcp_servers={"svc": self._server()})
        outcome = ConfigReloadService(ctx).apply_config_dict(  # type: ignore[attr-defined]
            {"mcp_servers": {"other": self._server(url="http://localhost:8090")}}
        )

        assert "mcp_servers/svc (removed server)" in outcome.needs_restart
        assert "mcp_servers/other (new server)" in outcome.needs_restart
        assert "mcp_servers/svc" not in outcome.needs_restart

    # --- no duplicate skip/restart classification (M-2) ---

    def test_no_item_classified_as_both_skipped_and_needs_restart(self) -> None:
        ctx, old_srv = self._make_ctx()
        live = agent_config_payload(ctx.cfg)["mcp_servers"]
        records = self._run(
            ctx,
            {
                "svc": live["svc"],
                "extra": self._server(url="http://localhost:9000"),
            },
        )

        # A definition change is never also a skipped field: the classifier names
        # the changed server fields, and nothing else reports them.
        paths = self._paths(records)
        assert "mcp_servers/extra" in paths
        assert paths.count("mcp_servers/extra") == 1
        assert not any(path.startswith("mcp_servers/svc.") for path in paths)


def _candidate(ctx: MagicMock, **overrides: Any) -> AgentConfig:
    """Build the candidate the reload path builds for this payload (REQ-002)."""
    return reload_candidate(ctx, **overrides)


class TestStartupOnlyDetection:
    """classify_startup_only_fields reports hot_reloadable=False changes as pending records."""

    def test_no_change_returns_empty(self) -> None:
        ctx = _make_ctx(use_memory_layer=True)
        result = classify_startup_only_fields(
            ctx, _candidate(ctx, use_memory_layer=True)
        )
        assert result == []

    def test_missing_key_returns_empty(self) -> None:
        ctx = _make_ctx(use_memory_layer=False)
        # A payload that names nothing keeps the live value, so nothing is pending.
        result = classify_startup_only_fields(ctx, _candidate(ctx))
        assert result == []

    def test_memory_embed_enabled_change_detected(self) -> None:
        ctx = _make_ctx(use_memory_layer=True, memory_embed_enabled=False)
        result = classify_startup_only_fields(
            ctx, _candidate(ctx, memory_embed_enabled=True)
        )
        assert "memory_embed_enabled" in [record.field_path for record in result]

    def test_memory_embed_enabled_no_change(self) -> None:
        ctx = _make_ctx(use_memory_layer=True, memory_embed_enabled=True)
        result = classify_startup_only_fields(
            ctx, _candidate(ctx, memory_embed_enabled=True)
        )
        assert "memory_embed_enabled" not in [record.field_path for record in result]


class TestRuntimeToolPolicyReapplication:
    """The runtime_tools commit step re-applies RuntimeToolRegistry.apply_policy() (REQ-006)."""

    def _make_ctx(self, with_registry: bool = True) -> MagicMock:
        ctx = MagicMock()
        ctx.cfg.tool.allowed_tools = []
        ctx.cfg.tool.tool_policy_mode = "explicit_allowlist"
        ctx.cfg.tool.disabled_tools = []
        ctx.services_required.llm = None
        ctx.services_required.hist_mgr = None
        ctx.services_required.tools = None
        ctx.services_required.runtime_tools = MagicMock() if with_registry else None
        return ctx

    def _apply_registry_step(self, ctx: MagicMock) -> PreparedStep | None:
        """Run the service step the reload transaction drives for the registry."""
        from agent.services.config_service_sync import ServiceSyncer

        step = ServiceSyncer(ctx).prepare_runtime_tools()
        if step is not None:
            step.apply()
        return step

    def test_apply_policy_called_with_current_allowed_tools_policy(self) -> None:
        """agentcfg003 REQ-005: apply_policy is re-applied without a tier_map —
        the tier each entry carries is the one its producer declared."""
        ctx = self._make_ctx()
        self._apply_registry_step(ctx)
        ctx.services_required.runtime_tools.apply_policy.assert_called_once_with(
            allowed_tools=ctx.cfg.tool.allowed_tools,
            tool_policy_mode=ctx.cfg.tool.tool_policy_mode,
            disabled_tools=ctx.cfg.tool.disabled_tools,
        )

    def test_the_registry_step_is_named_runtime_tools(self) -> None:
        ctx = self._make_ctx()
        step = self._apply_registry_step(ctx)
        assert step is not None
        assert step.service == "runtime_tools"

    def test_no_runtime_tools_registry_produces_no_step(self) -> None:
        from agent.services.config_service_sync import ServiceSyncer

        ctx = self._make_ctx(with_registry=False)
        assert ServiceSyncer(ctx).prepare_runtime_tools() is None

    def test_the_registry_step_does_not_fetch_tools_over_http(self) -> None:
        # Regression guard: the service step must never trigger MCP discovery.
        ctx = self._make_ctx()
        ctx.services_required.http = MagicMock()
        self._apply_registry_step(ctx)
        ctx.services_required.http.get.assert_not_called()

    def test_the_registry_step_applies_policy_to_a_real_registry(self) -> None:
        """E2E: the runtime_tools step → apply_policy on a real RuntimeToolRegistry."""

        from shared.runtime_tool import AgentSafetyTier
        from shared.runtime_tool_registry import RuntimeToolRegistry

        from tests.shared.runtime_tool_factory import build_fixture_runtime_tool

        ctx = self._make_ctx()
        tools = {
            "read_file": build_fixture_runtime_tool(
                name="read_file",
                server_key="fs",
                description="Read a file",
                input_schema={"type": "object"},
                status="active",
                is_write=False,
                agent_safety_tier=cast(AgentSafetyTier, "READ_ONLY"),
                enabled_for_llm=True,
            ),
            "delete_file": build_fixture_runtime_tool(
                name="delete_file",
                server_key="fs",
                description="Delete a file",
                input_schema={"type": "object"},
                status="active",
                is_write=True,
                agent_safety_tier=cast(AgentSafetyTier, "WRITE_DANGEROUS"),
                enabled_for_llm=True,
            ),
        }
        real_registry = RuntimeToolRegistry(
            tools=tools, allowed_servers=frozenset({"fs"})
        )
        ctx.services_required.runtime_tools = real_registry
        ctx.services_required.http = MagicMock()
        ctx.cfg.tool.allowed_tools = ["read_file"]

        self._apply_registry_step(ctx)

        assert real_registry.resolve("read_file") == "fs"
        read_tool = real_registry.get("read_file")
        assert read_tool.agent_safety_tier == "READ_ONLY"
        assert read_tool.enabled_for_llm is True

        # Declared tier survives the policy re-apply (no tier_map); the tool is
        # hidden only because it is outside allowed_tools.
        delete_tool = real_registry.get("delete_file")
        assert delete_tool.agent_safety_tier == "WRITE_DANGEROUS"
        assert delete_tool.enabled_for_llm is False

        ctx.services_required.http.get.assert_not_called()  # type: ignore[attr-defined]

    def test_empty_allowed_tools_denies_every_bound_tool(self) -> None:
        """REQ-002 fail-closed: an empty allowed_tools disables all bound tools."""

        from shared.runtime_tool import AgentSafetyTier
        from shared.runtime_tool_registry import RuntimeToolRegistry

        from tests.shared.runtime_tool_factory import build_fixture_runtime_tool

        ctx = self._make_ctx()
        tools = {
            "read_file": build_fixture_runtime_tool(
                name="read_file",
                server_key="fs",
                description="Read a file",
                input_schema={"type": "object"},
                status="active",
                is_write=False,
                agent_safety_tier=cast(AgentSafetyTier, "READ_ONLY"),
                enabled_for_llm=True,
            ),
            "delete_file": build_fixture_runtime_tool(
                name="delete_file",
                server_key="fs",
                description="Delete a file",
                input_schema={"type": "object"},
                status="active",
                is_write=True,
                agent_safety_tier=cast(AgentSafetyTier, "WRITE_DANGEROUS"),
                enabled_for_llm=True,
            ),
        }
        registry = RuntimeToolRegistry(tools=tools, allowed_servers=frozenset({"fs"}))
        assert registry.get("read_file").enabled_for_llm is True

        ctx.services_required.runtime_tools = registry
        ctx.cfg.tool.allowed_tools = []

        self._apply_registry_step(ctx)

        assert registry.get("read_file").enabled_for_llm is False
        assert registry.get("delete_file").enabled_for_llm is False

    def test_reload_empty_allowed_tools_fails_closed(
        self, svc_with_ctx: tuple[object, MagicMock]
    ) -> None:
        """REQ-002: apply_config_dict with allowed_tools=[] denies the call."""

        from agent.services.exceptions import ConfigReloadValidationError
        from agent.tool_exceptions import PolicyViolationError
        from agent.tool_policy import check_preflight

        svc, ctx = svc_with_ctx
        ctx.cfg.tool.allowed_tools = ["read_file"]

        try:
            svc.apply_config_dict({"allowed_tools": []})  # type: ignore[attr-defined]
        except ConfigReloadValidationError:
            # Rejected by validation: the live config keeps the old allow list.
            assert ctx.cfg.tool.allowed_tools == ["read_file"]
            return

        # Applied as an empty list: pre-flight now denies the previously
        # allowed tool (fail closed).
        assert ctx.cfg.tool.allowed_tools == []
        with pytest.raises(PolicyViolationError):
            check_preflight(ctx.cfg, "read_file", {})

    def test_reload_empty_allowed_root_fails_closed(
        self, svc_with_ctx: tuple[object, MagicMock]
    ) -> None:
        """REQ-003: apply_config_dict with allowed_root='' disables the path jail."""

        from agent.services.exceptions import ConfigReloadValidationError
        from agent.tool_policy import check_allowed_root

        svc, ctx = svc_with_ctx
        ctx.cfg.approval.allowed_root = "/"

        try:
            svc.apply_config_dict({"allowed_root": ""})  # type: ignore[attr-defined]
        except ConfigReloadValidationError:
            # Rejected by validation: the live config keeps the old jail root.
            assert ctx.cfg.approval.allowed_root == "/"
            return

        # Applied as an empty root: a path-carrying call is denied.
        assert ctx.cfg.approval.allowed_root == ""
        assert check_allowed_root(ctx.cfg, "write_file", {"path": "/tmp/x"}) is False

    def _bound_registry(self, svc, ctx) -> RuntimeToolRegistry:
        """Bind a real RuntimeToolRegistry to ctx.services_required.runtime_tools."""
        from shared.runtime_tool import AgentSafetyTier
        from shared.runtime_tool_registry import RuntimeToolRegistry

        from tests.shared.runtime_tool_factory import build_fixture_runtime_tool

        tools = {
            "read_text_file": build_fixture_runtime_tool(
                name="read_text_file",
                server_key="fs",
                agent_safety_tier=cast(AgentSafetyTier, "READ_ONLY"),
                llm_visibility_base=True,
                enabled_for_llm=False,
            ),
            "delete_file": build_fixture_runtime_tool(
                name="delete_file",
                server_key="fs",
                agent_safety_tier=cast(AgentSafetyTier, "WRITE_DANGEROUS"),
                llm_visibility_base=True,
                enabled_for_llm=False,
            ),
        }
        registry = RuntimeToolRegistry(tools=tools, allowed_servers=frozenset({"fs"}))
        ctx.services_required.runtime_tools = registry
        return registry

    def test_reload_discovered_mode_preserves_base_visibility_minus_denylist(
        self, svc_with_ctx: tuple[object, MagicMock]
    ) -> None:
        """REQ-005/REQ-006: /reload with tool_policy_mode='discovered' re-applies
        apply_policy so base visibility survives; disabled_tools is still a hard
        denylist. An empty allowed_tools is valid in discovered mode."""
        svc, ctx = svc_with_ctx
        registry = self._bound_registry(svc, ctx)

        outcome = svc.apply_config_dict(  # type: ignore[attr-defined]
            {
                "tool_policy_mode": "discovered",
                "allowed_tools": [],
                "disabled_tools": ["delete_file"],
            }
        )
        assert "tool" in outcome.applied
        assert "runtime_tools" in outcome.applied

        # Base visibility applies to every registered tool in discovered mode...
        assert registry.get("read_text_file").enabled_for_llm is True
        # ...except the hard denylist entry.
        assert registry.get("delete_file").enabled_for_llm is False

    def test_reload_explicit_allowlist_preserves_allowlist_visibility(
        self, svc_with_ctx: tuple[object, MagicMock]
    ) -> None:
        """REQ-005/REQ-006: /reload with tool_policy_mode='explicit_allowlist' and
        a non-empty allowed_tools re-applies apply_policy so only allowlisted tools
        stay visible."""
        svc, ctx = svc_with_ctx
        registry = self._bound_registry(svc, ctx)

        outcome = svc.apply_config_dict(  # type: ignore[attr-defined]
            {
                "tool_policy_mode": "explicit_allowlist",
                "allowed_tools": ["read_text_file"],
            }
        )
        assert "runtime_tools" in outcome.applied

        assert registry.get("read_text_file").enabled_for_llm is True
        assert registry.get("delete_file").enabled_for_llm is False

    def test_reload_unknown_mode_rejected_and_previous_survives(
        self, svc_with_ctx: tuple[object, MagicMock]
    ) -> None:
        """REQ-006: an unknown tool_policy_mode is rejected by the typed validator;
        the reload aborts atomically and the previous mode survives."""
        from agent.services.exceptions import ConfigReloadValidationError

        svc, ctx = svc_with_ctx
        ctx.cfg.tool.tool_policy_mode = "explicit_allowlist"

        with pytest.raises(ConfigReloadValidationError):
            svc.apply_config_dict({"tool_policy_mode": "bogus_mode"})  # type: ignore[attr-defined]

        assert ctx.cfg.tool.tool_policy_mode == "explicit_allowlist"


class TestApprovalGitopsPushBlocked:
    """gitops_push_blocked is startup-only: /reload reports it and leaves the live value alone."""

    def _make_svc(self, gitops_push_blocked: bool = False) -> object:
        from agent.services.config_reload import ConfigReloadService

        return ConfigReloadService(_make_ctx(gitops_push_blocked=gitops_push_blocked))

    def test_gitops_push_blocked_true_via_reload(self) -> None:
        svc = self._make_svc(gitops_push_blocked=False)
        outcome = svc.apply_config_dict({"gitops_push_blocked": True})
        assert svc._ctx.cfg.approval.gitops_push_blocked is False
        assert "approval" not in outcome.applied
        assert "gitops_push_blocked" in outcome.startup_only

    def test_gitops_push_blocked_false_via_reload(self) -> None:
        svc = self._make_svc(gitops_push_blocked=True)
        outcome = svc.apply_config_dict({"gitops_push_blocked": False})
        assert svc._ctx.cfg.approval.gitops_push_blocked is True
        assert "approval" not in outcome.applied
        assert "gitops_push_blocked" in outcome.startup_only

    def test_unchanged_startup_only_field_is_not_reported(self) -> None:
        svc = self._make_svc(gitops_push_blocked=True)
        outcome = svc.apply_config_dict({"gitops_push_blocked": True})
        assert outcome.startup_only == []

    def test_invalid_llm_temperature_raises(self, svc: object) -> None:
        from agent.services.exceptions import ConfigReloadValidationError
        from agent.services.models import ConfigReloadRequest

        req = ConfigReloadRequest(llm={"llm_temperature": -3.0})
        with pytest.raises(ConfigReloadValidationError):
            svc.apply_config(req)  # type: ignore[attr-defined]

    def test_invalid_llm_max_tokens_raises(self, svc: object) -> None:
        from agent.services.exceptions import ConfigReloadValidationError
        from agent.services.models import ConfigReloadRequest

        req = ConfigReloadRequest(llm={"llm_max_tokens": 0})
        with pytest.raises(ConfigReloadValidationError):
            svc.apply_config(req)  # type: ignore[attr-defined]

    def test_invalid_http_timeout_raises(self, svc: object) -> None:
        from agent.services.exceptions import ConfigReloadValidationError
        from agent.services.models import ConfigReloadRequest

        req = ConfigReloadRequest(llm={"http_timeout": 0})
        with pytest.raises(ConfigReloadValidationError):
            svc.apply_config(req)  # type: ignore[attr-defined]

    def test_empty_llm_url_does_not_raise(self, svc: object) -> None:
        from agent.services.models import ConfigReloadRequest

        req = ConfigReloadRequest(llm={"llm_url": ""})
        result = svc.apply_config(req)  # type: ignore[attr-defined]
        assert result is not None

    def test_empty_memory_embed_url_raises_when_embedding_is_enabled(
        self, svc: object
    ) -> None:
        from agent.services.exceptions import ConfigReloadValidationError
        from agent.services.models import ConfigReloadRequest

        req = ConfigReloadRequest(rag_tool={"memory_embed_url": ""})
        with pytest.raises(ConfigReloadValidationError):
            svc.apply_config(req)  # type: ignore[attr-defined]

    def test_invalid_max_tool_turns_raises(self, svc: object) -> None:
        from agent.services.exceptions import ConfigReloadValidationError
        from agent.services.models import ConfigReloadRequest

        req = ConfigReloadRequest(rag_tool={"max_tool_turns": 0})
        with pytest.raises(ConfigReloadValidationError):
            svc.apply_config(req)  # type: ignore[attr-defined]

    def test_invalid_tool_result_max_llm_chars_raises(self, svc: object) -> None:
        from agent.services.exceptions import ConfigReloadValidationError
        from agent.services.models import ConfigReloadRequest

        req = ConfigReloadRequest(rag_tool={"tool_result_max_llm_chars": 0})
        with pytest.raises(ConfigReloadValidationError):
            svc.apply_config(req)  # type: ignore[attr-defined]

    def test_startup_only_context_token_limit_is_not_applied(self, svc: object) -> None:
        """A startup-only field is validated by the candidate build but never applied:
        reload reports it as pending and leaves the live value alone (REQ-003)."""
        from agent.services.models import ConfigReloadRequest

        req = ConfigReloadRequest(llm={"context_token_limit": 5000})
        result = svc.apply_config(req)  # type: ignore[attr-defined]
        assert "context_token_limit" in result.startup_only
        assert "llm" not in result.applied
        assert svc._ctx.cfg.llm.context_token_limit != 5000  # type: ignore[attr-defined]


class TestRegistryFieldClassification:
    """Tests verifying CONFIG_FIELD_REGISTRY correctly categorizes fields by section."""

    def test_llm_section_fields_are_classified_correctly(self) -> None:
        from agent.services.config_field_registry import CONFIG_FIELD_REGISTRY

        llm_fields = [
            entry.name
            for entry in CONFIG_FIELD_REGISTRY.values()
            if entry.section_path == "llm"
        ]
        expected = {
            "http_timeout",
            "context_token_limit",
            "context_char_limit",
            "context_compress_turns",
            "llm_temperature",
            "llm_max_tokens",
            "llm_url",
            "llm_retry_base_delay",
            "sse_heartbeat_timeout",
            "sse_malformed_retry",
            "sse_reconnect_max",
            "llm_stream_retry_on_heartbeat_timeout",
            "llm_stream_retry_on_malformed_chunk",
        }
        assert set(llm_fields) == expected

    def test_tool_section_fields_are_classified_correctly(self) -> None:
        from agent.services.config_field_registry import CONFIG_FIELD_REGISTRY

        tool_fields = [
            entry.name
            for entry in CONFIG_FIELD_REGISTRY.values()
            if entry.section_path == "tool"
        ]
        expected = {
            "max_tool_turns",
            "tool_result_max_llm_chars",
            "serial_tool_calls",
            "plan_blocked_tools",
            "allowed_tools",
            "tool_policy_mode",
            "disabled_tools",
        }
        assert set(tool_fields) == expected

    def test_approval_section_fields_are_classified_correctly(self) -> None:
        from agent.services.config_field_registry import CONFIG_FIELD_REGISTRY

        approval_fields = [
            entry.name
            for entry in CONFIG_FIELD_REGISTRY.values()
            if entry.section_path == "approval"
        ]
        expected = {
            "approval_protected_paths",
            "approval_high_risk_branches",
            "approval_shell_safe_prefixes",
            "allowed_root",
            "approval_github_allowed_repos",
            "gitops_push_blocked",
            "approval_medium_preview_fallback",
        }
        assert set(approval_fields) == expected

    def test_memory_section_fields_are_classified_correctly(self) -> None:
        from agent.services.config_field_registry import CONFIG_FIELD_REGISTRY

        memory_fields = [
            entry.name
            for entry in CONFIG_FIELD_REGISTRY.values()
            if entry.section_path == "memory"
        ]
        expected = {
            "memory_retention_days",
            "memory_max_pinned",
            "memory_local_only",
            "use_memory_layer",
            "memory_embed_enabled",
            "memory_embed_url",
        }
        assert set(memory_fields) == expected

    def test_mcp_section_fields_are_classified_correctly(self) -> None:
        from agent.services.config_field_registry import CONFIG_FIELD_REGISTRY

        mcp_fields = [
            entry.name
            for entry in CONFIG_FIELD_REGISTRY.values()
            if entry.section_path == "mcp"
        ]
        expected: set[str] = set()
        assert set(mcp_fields) == expected

    def test_all_registry_entries_have_validators_or_none(self) -> None:
        from agent.services.config_field_registry import CONFIG_FIELD_REGISTRY

        for entry in CONFIG_FIELD_REGISTRY.values():
            assert isinstance(entry.name, str)
            assert isinstance(entry.section_path, str)
            assert isinstance(entry.hot_reloadable, bool)
            # validator_fn can be None or a callable
            if entry.validator_fn is not None:
                assert callable(entry.validator_fn)

    def test_no_duplicate_field_names_in_registry(self) -> None:
        from agent.services.config_field_registry import CONFIG_FIELD_REGISTRY

        names = [entry.name for entry in CONFIG_FIELD_REGISTRY.values()]
        assert len(names) == len(set(names)), (
            f"Duplicate field names found: {[n for n in names if names.count(n) > 1]}"
        )

    def test_apply_config_dict_applies_llm_fields_via_registry(
        self, svc: object
    ) -> None:
        svc.apply_config_dict({"llm_temperature": 0.8})  # type: ignore[attr-defined]
        assert svc._ctx.cfg.llm.llm_temperature == 0.8  # type: ignore[attr-defined]

    def test_apply_config_dict_applies_memory_fields_via_registry(
        self, svc: object
    ) -> None:
        svc.apply_config_dict({"memory_embed_url": "http://embed:8081"})  # type: ignore[attr-defined]
        assert svc._ctx.cfg.memory.memory_embed_url == (  # type: ignore[attr-defined]
            "http://embed:8081"
        )

    def test_apply_config_dict_applies_tool_fields_via_registry(
        self, svc: object
    ) -> None:
        svc.apply_config_dict({"max_tool_turns": 10})  # type: ignore[attr-defined]
        assert svc._ctx.cfg.tool.max_tool_turns == 10  # type: ignore[attr-defined]

    def test_apply_config_dict_skips_missing_fields(self, svc: object) -> None:
        svc.apply_config_dict({})  # type: ignore[attr-defined]
        assert svc._ctx.cfg.llm.llm_temperature == 0.7  # type: ignore[attr-defined]

    def test_apply_config_dict_handles_partial_updates(self, svc: object) -> None:
        svc.apply_config_dict(  # type: ignore[attr-defined]
            {"llm_temperature": 0.9, "memory_embed_url": "http://embed:8081"}
        )
        assert svc._ctx.cfg.llm.llm_temperature == 0.9  # type: ignore[attr-defined]
        assert svc._ctx.cfg.memory.memory_embed_url == (  # type: ignore[attr-defined]
            "http://embed:8081"
        )


class TestConfigFieldRegistrySectionCategorization:
    """Row 4: registry_for returns only hot-reloadable entries and startup_only_for is the complement."""

    _SECTIONS = ("llm", "tool", "approval", "memory")

    def test_every_entry_declares_a_type_rule_and_a_validator(self) -> None:
        """REQ-010: no entry reaches the reload path without a declared rule and validator."""
        from agent.services.config_field_registry import CONFIG_FIELD_REGISTRY

        for name, entry in CONFIG_FIELD_REGISTRY.items():
            assert entry.field_type is not None, name
            assert entry.validator_fn is not None, name

    def test_the_two_accessors_partition_every_section(self) -> None:
        """registry_for and startup_only_for are disjoint and cover every entry of a section."""
        from agent.services.config_field_registry import (
            CONFIG_FIELD_REGISTRY,
            registry_for,
            startup_only_for,
        )

        for section in self._SECTIONS:
            live = {entry.name for entry in registry_for(section)}
            pending = {entry.name for entry in startup_only_for(section)}
            all_names = {
                entry.name
                for entry in CONFIG_FIELD_REGISTRY.values()
                if entry.section_path == section
            }
            assert live | pending == all_names
            assert not (live & pending)

    def test_the_startup_only_set_is_the_named_fields(self) -> None:
        """REQ-003: exactly these fields stay pending until restart."""
        from agent.services.config_field_registry import startup_only_for

        pending = {
            entry.name
            for section in self._SECTIONS
            for entry in startup_only_for(section)
        }
        assert pending == {
            "context_token_limit",
            "context_char_limit",
            "context_compress_turns",
            "gitops_push_blocked",
            "approval_medium_preview_fallback",
            "use_memory_layer",
            "memory_embed_enabled",
        }

    def test_mcp_has_no_reloadable_field_entries(self) -> None:
        """REQ-003: MCP server definitions are restart-required, so no field entry exists."""
        from agent.services.config_field_registry import registry_for, startup_only_for

        assert registry_for("mcp") == []
        assert startup_only_for("mcp") == []


class TestSectionCandidateRuleEnforcement:
    """prepare_validated_section applies the registry's declared rule to the candidate."""

    def test_a_wrong_typed_candidate_field_raises_the_reload_error(self) -> None:
        """REQ-001: the declared rule is enforced on the candidate, not only on the payload."""
        from agent.config_dataclasses import ToolConfig
        from agent.services.config_section_reload import prepare_validated_section
        from agent.services.exceptions import ConfigReloadValidationError

        ctx = _make_ctx()
        # The dataclass does not type-check, so a hand-built candidate can carry a
        # value the shared rule rejects.
        candidate = ToolConfig(max_tool_turns="5")  # type: ignore[arg-type]

        with pytest.raises(ConfigReloadValidationError, match="max_tool_turns") as e:
            prepare_validated_section(ctx, "tool", candidate)

        assert "must be int, got str" in str(e.value)
        assert "5" not in str(e.value)
        # The failure happens before any live mutation.
        assert ctx.cfg.tool.max_tool_turns == 5


class TestMaskedFieldsCandidateFold:
    """masked_fields is not a registry entry, so it folds into the tool candidate separately."""

    def _svc(self, ctx: MagicMock) -> object:
        from agent.services.config_reload import ConfigReloadService

        return ConfigReloadService(ctx)

    def test_a_changed_value_is_committed_with_the_tool_section(self) -> None:
        ctx = _make_ctx()
        outcome = self._svc(ctx).apply_config_dict(  # type: ignore[attr-defined]
            {"masked_fields": ["api_key", "token"]}
        )

        assert list(ctx.cfg.tool.masked_fields) == ["api_key", "token"]
        assert "tool" in outcome.applied

    def test_an_unchanged_value_adds_no_tool_candidate(self) -> None:
        """A payload that does not name masked_fields leaves the live value alone (REQ-002)."""
        ctx = _make_ctx()
        before = list(ctx.cfg.tool.masked_fields)
        outcome = self._svc(ctx).apply_config_dict({"llm_temperature": 0.4})  # type: ignore[attr-defined]

        assert list(ctx.cfg.tool.masked_fields) == before
        assert "tool" not in outcome.applied


class TestServiceSyncerLlmStep:
    """The llm commit step the reload transaction drives (REQ-006, REQ-013).

    `apply_config_dict` commits through the transaction, which prepares these steps:
    no separate apply-and-collect path remains.
    """

    def _make_ctx(self, with_llm: bool) -> MagicMock:
        ctx = _make_ctx()
        ctx.services_required.llm = MagicMock() if with_llm else None
        ctx.services_required.hist_mgr = None
        ctx.services_required.runtime_tools = None
        return ctx

    def test_a_live_llm_client_gets_an_apply_step(self) -> None:
        from agent.services.config_service_sync import ServiceSyncer

        ctx = self._make_ctx(with_llm=True)
        step = ServiceSyncer(ctx).prepare_llm()

        assert step is not None
        assert step.service == "llm"
        step.apply()
        ctx.services_required.llm.apply_config.assert_called_once()

    def test_no_llm_client_produces_no_step(self) -> None:
        from agent.services.config_service_sync import ServiceSyncer

        ctx = self._make_ctx(with_llm=False)
        assert ServiceSyncer(ctx).prepare_llm() is None
