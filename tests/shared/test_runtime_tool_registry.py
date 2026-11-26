"""tests/shared/test_runtime_tool_registry.py
Unit tests for RuntimeToolRegistry: resolve/get, all_tools, llm_tool_definitions,
tool_spec_map/tool_spec_for_call, apply_policy, diagnostics.
"""

from __future__ import annotations

import dataclasses
import logging
import threading
from typing import Any
from unittest.mock import patch

import pytest
from shared.runtime_tool import RuntimeTool, build_runtime_tool
from shared.runtime_tool_registry import RuntimeToolRegistry
from shared.tool_spec import ToolSpec

from tests.shared.runtime_tool_factory import build_fixture_runtime_tool


def _registry_with(*tools: RuntimeTool) -> RuntimeToolRegistry:
    return RuntimeToolRegistry(
        {tool.name: tool for tool in tools},
        allowed_servers=frozenset({tool.server_key for tool in tools}),
    )


class TestRuntimeToolRegistry:
    def test_resolve_returns_server_key_for_known_tool(self) -> None:
        reg = _registry_with(
            build_fixture_runtime_tool(name="write_file", server_key="fs")
        )
        assert reg.resolve("write_file") == "fs"

    def test_resolve_returns_none_for_unknown_tool(self) -> None:
        reg = _registry_with()
        assert reg.resolve("nope") is None

    def test_get_returns_runtime_tool_for_known_name(self) -> None:
        tool = build_fixture_runtime_tool(name="t", server_key="s")
        reg = _registry_with(tool)
        assert reg.get("t") is tool

    def test_get_raises_for_unregistered_name(self) -> None:
        reg = _registry_with()
        with pytest.raises(KeyError):
            reg.get("nope")

    def test_all_tools_returns_every_registered_tool(self) -> None:
        reg = _registry_with(
            build_fixture_runtime_tool(name="a", server_key="s"),
            build_fixture_runtime_tool(name="b", server_key="s"),
        )
        names = {tool.name for tool in reg.all_tools()}
        assert names == {"a", "b"}

    def test_llm_tool_definitions_filters_enabled_and_rekeys_parameters(self) -> None:
        visible = build_fixture_runtime_tool(
            name="a",
            server_key="s",
            description="d",
            input_schema={"type": "object"},
            enabled_for_llm=True,
        )
        hidden = build_fixture_runtime_tool(
            name="b", server_key="s", enabled_for_llm=False
        )
        reg = _registry_with(visible, hidden)
        defs = reg.llm_tool_definitions()
        assert len(defs) == 1
        assert defs[0]["name"] == "a"
        assert defs[0]["description"] == "d"
        assert defs[0]["parameters"] == {"type": "object"}

    def test_tool_spec_map_copies_write_serial_scope_fields_and_falls_back_to_global_write_scope(
        self,
    ) -> None:
        tool = build_runtime_tool(
            name="delete_file",
            server_key="fs",
            is_write=True,
            requires_serial=True,
            resource_scope_kind="filesystem",
            resource_scope_keys=("path",),
            policy_version="2.1",
            preview_capability="none",
            idempotency_required=True,
            reconciliation_policy="local_state",
            retry_policy="never",
            side_effect_class="local_write",
            agent_safety_tier="WRITE_SAFE",
        )
        reg = _registry_with(tool)
        spec = reg.tool_spec_map()["delete_file"]
        assert isinstance(spec, ToolSpec)
        assert spec.is_write is True
        assert spec.requires_serial is True
        # tool_spec_map() calls _build_tool_spec() with no real args, so a write tool
        # with unresolvable resource_scope_keys hits the fail-closed fallback rather
        # than resolving a literal "filesystem:..." scope.
        assert spec.resource_scopes == ("global:write",)
        assert spec.call_id == ""

    def test_tool_spec_for_call_fills_call_specific_fields(self) -> None:
        tool = build_fixture_runtime_tool(
            name="write_file", server_key="fs", is_write=True
        )
        reg = _registry_with(tool)
        spec = reg.tool_spec_for_call(
            call_id="call-1", name="write_file", args={"path": "x"}
        )
        assert spec.call_id == "call-1"
        assert spec.args == {"path": "x"}
        assert spec.is_write is True

    def test_tool_spec_for_call_resolves_scope_from_call_args(self) -> None:
        tool = build_fixture_runtime_tool(
            name="write_file",
            server_key="fs",
            is_write=True,
            resource_scope_kind="filesystem",
            resource_scope_keys=("path",),
        )
        reg = _registry_with(tool)
        spec = reg.tool_spec_for_call(
            call_id="call-1", name="write_file", args={"path": "/data/a.txt"}
        )
        assert spec.resource_scopes == ("filesystem:/data/a.txt",)

    def test_tool_spec_for_call_falls_back_to_global_write_when_scope_key_missing(
        self,
    ) -> None:
        tool = build_fixture_runtime_tool(
            name="write_file",
            server_key="fs",
            is_write=True,
            resource_scope_kind="filesystem",
            resource_scope_keys=("path",),
        )
        reg = _registry_with(tool)
        spec = reg.tool_spec_for_call(call_id="call-2", name="write_file", args={})
        assert spec.resource_scopes == ("global:write",)

    def test_tool_spec_for_call_raises_for_unregistered_name(self) -> None:
        reg = _registry_with()
        with pytest.raises(KeyError):
            reg.tool_spec_for_call(call_id="call-1", name="nope", args={})

    def test_apply_policy_preserves_declared_tier_and_updates_llm_visibility(
        self,
    ) -> None:
        """agentcfg003 REQ-002/REQ-004: the entry keeps the tier its producer
        declared; the removed tier_map would have produced ADMIN here."""
        tool = build_fixture_runtime_tool(
            name="shell_run",
            server_key="s",
            agent_safety_tier="WRITE_SAFE",
            enabled_for_llm=True,
        )
        reg = _registry_with(tool)
        reg.apply_policy(allowed_tools=["shell_run"])
        updated = reg.get("shell_run")
        assert updated.agent_safety_tier == "WRITE_SAFE"
        assert updated.enabled_for_llm is True

    def test_apply_policy_disables_tools_not_in_allowed_list(self) -> None:
        tool = build_fixture_runtime_tool(
            name="search_web", server_key="s", enabled_for_llm=True
        )
        reg = _registry_with(tool)
        reg.apply_policy(allowed_tools=["other_tool"])
        assert reg.get("search_web").enabled_for_llm is False

    def test_apply_policy_empty_allowed_tools_disables_all(self) -> None:
        tool = build_fixture_runtime_tool(
            name="search_web", server_key="s", enabled_for_llm=True
        )
        reg = _registry_with(tool)
        reg.apply_policy(allowed_tools=())
        assert reg.get("search_web").enabled_for_llm is False

    def test_apply_policy_keeps_hidden_tool_disabled_when_allowed(self) -> None:
        tool = build_fixture_runtime_tool(
            name="hidden_tool",
            server_key="s",
            enabled_for_llm=True,
            llm_visibility_base=False,
        )
        reg = _registry_with(tool)
        reg.apply_policy(allowed_tools=["hidden_tool"])
        assert reg.get("hidden_tool").enabled_for_llm is False

    def test_apply_policy_logs_warning_when_hidden_tool_would_otherwise_be_enabled(
        self, caplog: Any
    ) -> None:
        tool = build_fixture_runtime_tool(
            name="hidden_tool",
            server_key="s",
            enabled_for_llm=True,
            llm_visibility_base=False,
        )
        reg = _registry_with(tool)
        with caplog.at_level(logging.WARNING, logger="shared.runtime_tool_registry"):
            reg.apply_policy(allowed_tools=["hidden_tool"])
        assert "hidden_tool" in caplog.text

    def test_apply_policy_does_not_log_warning_for_visible_tool(
        self, caplog: Any
    ) -> None:
        tool = build_fixture_runtime_tool(
            name="visible_tool", server_key="s", enabled_for_llm=True
        )
        reg = _registry_with(tool)
        with caplog.at_level(logging.WARNING, logger="shared.runtime_tool_registry"):
            reg.apply_policy(allowed_tools=["visible_tool"])
        assert "visible_tool" not in caplog.text

    def test_apply_policy_keeps_declared_tier(self) -> None:
        tool = build_fixture_runtime_tool(
            name="read_file",
            server_key="s",
            agent_safety_tier="READ_ONLY",
            enabled_for_llm=True,
        )
        reg = _registry_with(tool)
        reg.apply_policy(allowed_tools=["read_file"])
        updated = reg.get("read_file")
        assert updated.agent_safety_tier == "READ_ONLY"

    def test_apply_policy_keeps_declared_tier_across_repeated_calls(self) -> None:
        tool = build_fixture_runtime_tool(
            name="read_file", server_key="s", agent_safety_tier="READ_ONLY"
        )
        reg = _registry_with(tool)
        reg.apply_policy(allowed_tools=["read_file"])
        assert reg.get("read_file").agent_safety_tier == "READ_ONLY"

    def test_apply_policy_discovered_mode_allows_registered_tool_with_empty_allowlist(
        self,
    ) -> None:
        """REQ-005: in discovered mode an empty allowed_tools does not disable
        a registered tool (base visibility applies)."""
        tool = build_fixture_runtime_tool(
            name="read_file", server_key="s", enabled_for_llm=True
        )
        reg = _registry_with(tool)
        reg.apply_policy(
            allowed_tools=(),
            tool_policy_mode="discovered",
        )
        assert reg.get("read_file").enabled_for_llm is True

    def test_apply_policy_discovered_mode_denies_disabled_tool(self) -> None:
        """REQ-005: disabled_tools is a hard denylist applied in discovered mode."""
        tool = build_fixture_runtime_tool(
            name="read_file", server_key="s", enabled_for_llm=True
        )
        reg = _registry_with(tool)
        reg.apply_policy(
            allowed_tools=(),
            tool_policy_mode="discovered",
            disabled_tools=["read_file"],
        )
        assert reg.get("read_file").enabled_for_llm is False

    def test_apply_policy_discovered_mode_respects_base_visibility_false(self) -> None:
        """REQ-005: discovered mode still honors llm_visibility_base=False."""
        tool = build_fixture_runtime_tool(
            name="hidden_tool",
            server_key="s",
            enabled_for_llm=True,
            llm_visibility_base=False,
        )
        reg = _registry_with(tool)
        reg.apply_policy(
            allowed_tools=(),
            tool_policy_mode="discovered",
        )
        assert reg.get("hidden_tool").enabled_for_llm is False

    def test_diagnostics_uses_raw_definition_disabled_reason_when_present(self) -> None:
        tool = build_fixture_runtime_tool(
            name="quota_tool",
            server_key="s",
            status="inactive",
            raw_definition={"disabled_reason": "quota exceeded"},
        )
        reg = _registry_with(tool)
        row = reg.diagnostics()[0]
        assert row["disabled_reason"] == "quota exceeded"
        assert row["enabled"] is False

    def test_diagnostics_falls_back_to_status_when_raw_definition_lacks_disabled_reason(
        self,
    ) -> None:
        tool = build_fixture_runtime_tool(
            name="inactive_tool", server_key="s", status="inactive", raw_definition={}
        )
        reg = _registry_with(tool)
        row = reg.diagnostics()[0]
        assert row["disabled_reason"] == "inactive"
        assert row["enabled"] is False

    def test_diagnostics_active_status_with_no_raw_reason_yields_empty_string(
        self,
    ) -> None:
        tool = build_fixture_runtime_tool(
            name="active_tool", server_key="s", status="active", raw_definition={}
        )
        reg = _registry_with(tool)
        row = reg.diagnostics()[0]
        assert row["disabled_reason"] == ""
        # REQ-007: the row is the declared field, not a value derived from `status`.
        assert row["config_dependent"] is False
        assert row["enabled"] is True
        assert row["server_key"] == "s"

    def test_diagnostics_reads_the_explicit_config_dependent_field(self) -> None:
        """T-07 (REQ-007): a declared value and a non-active status no longer agree by construction."""
        declared = build_fixture_runtime_tool(
            name="declared_tool",
            server_key="s",
            status="active",
            raw_definition={},
            config_dependent=True,
        )
        unflagged = build_fixture_runtime_tool(
            name="inactive_tool",
            server_key="s",
            status="inactive",
            raw_definition={},
            config_dependent=False,
        )
        reg = _registry_with(declared, unflagged)
        rows = {row["name"]: row for row in reg.diagnostics()}
        assert rows["declared_tool"]["config_dependent"] is True
        assert rows["inactive_tool"]["config_dependent"] is False
        assert rows["inactive_tool"]["disabled_reason"] == "inactive"

    def test_capability_excluded_tool_has_no_diagnostics_row(self) -> None:
        """T-06/T-07: the capability dependency is reported as the excluded state, not as a row."""
        dependent = build_fixture_runtime_tool(
            name="dependent", server_key="github", capabilities=("github.api",)
        )
        kept = build_fixture_runtime_tool(
            name="kept", server_key="github", capabilities=("github.operations",)
        )
        reg = RuntimeToolRegistry(
            {"dependent": dependent, "kept": kept},
            allowed_servers=frozenset(["github"]),
            degraded_capabilities={"github": ("github.api",)},
        )
        rows = reg.diagnostics()
        assert [row["name"] for row in rows] == ["kept"]
        assert reg.exclusion_reason("dependent") == "capability"

    def test_unavailable_servers_excludes_tools_from_unavailable_server(self) -> None:
        tool_a = build_fixture_runtime_tool(
            name="tool_a", server_key="unreachable_server"
        )
        tool_b = build_fixture_runtime_tool(name="tool_b", server_key="healthy_server")
        reg = RuntimeToolRegistry(
            tools={"tool_a": tool_a, "tool_b": tool_b},
            unavailable_servers=frozenset(["unreachable_server"]),
            allowed_servers=frozenset(["unreachable_server", "healthy_server"]),
        )
        assert reg.resolve("tool_a") is None
        assert reg.resolve("tool_b") == "healthy_server"
        assert len(reg.all_tools()) == 1
        assert reg.all_tools()[0].name == "tool_b"

    def test_llm_tool_definitions_excludes_tools_from_unavailable_servers(self) -> None:
        tool_a = build_fixture_runtime_tool(
            name="tool_a", server_key="unavailable", enabled_for_llm=True
        )
        tool_b = build_fixture_runtime_tool(
            name="tool_b", server_key="healthy", enabled_for_llm=True
        )
        reg = RuntimeToolRegistry(
            tools={"tool_a": tool_a, "tool_b": tool_b},
            unavailable_servers=frozenset(["unavailable"]),
            allowed_servers=frozenset(["unavailable", "healthy"]),
        )
        defs = reg.llm_tool_definitions()
        assert len(defs) == 1
        assert defs[0]["name"] == "tool_b"

    def test_diagnostics_excludes_tools_from_unavailable_servers(self) -> None:
        tool_a = build_fixture_runtime_tool(
            name="tool_a", server_key="unavailable", status="inactive"
        )
        tool_b = build_fixture_runtime_tool(
            name="tool_b", server_key="healthy", status="active"
        )
        reg = RuntimeToolRegistry(
            tools={"tool_a": tool_a, "tool_b": tool_b},
            unavailable_servers=frozenset(["unavailable"]),
            allowed_servers=frozenset(["unavailable", "healthy"]),
        )
        rows = reg.diagnostics()
        assert len(rows) == 1
        assert rows[0]["name"] == "tool_b"

    def test_exclusion_reason_reports_the_drop_reason_and_none_for_known_or_unknown(
        self,
    ) -> None:
        unavailable_tool = build_fixture_runtime_tool(
            name="unavailable_tool", server_key="unreachable"
        )
        posture_tool = build_fixture_runtime_tool(
            name="posture_tool", server_key="postured"
        )
        healthy_tool = build_fixture_runtime_tool(
            name="healthy_tool", server_key="healthy"
        )
        reg = RuntimeToolRegistry(
            tools={
                "unavailable_tool": unavailable_tool,
                "posture_tool": posture_tool,
                "healthy_tool": healthy_tool,
            },
            unavailable_servers=frozenset(["unreachable"]),
            allowed_servers=frozenset(["healthy"]),
        )
        assert reg.exclusion_reason("unavailable_tool") == "unavailable"
        assert reg.exclusion_reason("posture_tool") == "posture"
        assert reg.exclusion_reason("healthy_tool") is None
        assert reg.exclusion_reason("never_seen") is None

    def test_exclusion_reason_unavailable_server(self) -> None:
        tool = build_fixture_runtime_tool(name="down_tool", server_key="down_srv")
        reg = RuntimeToolRegistry(
            {"down_tool": tool},
            unavailable_servers=frozenset(["down_srv"]),
            allowed_servers=frozenset(["down_srv"]),
        )
        assert reg.exclusion_reason("down_tool") == "unavailable"

    def test_exclusion_reason_disabled_server(self) -> None:
        from unittest.mock import MagicMock

        cfg = MagicMock()
        cfg.is_disabled = True
        tool = build_fixture_runtime_tool(
            name="disabled_tool", server_key="disabled_srv"
        )
        reg = RuntimeToolRegistry(
            {"disabled_tool": tool},
            server_configs={"disabled_srv": cfg},
            allowed_servers=frozenset(["disabled_srv"]),
        )
        assert reg.exclusion_reason("disabled_tool") == "disabled"

    def test_exclusion_reason_posture_in_posture_gate(self) -> None:
        tool = build_fixture_runtime_tool(name="gated_tool", server_key="git")
        reg = RuntimeToolRegistry(
            {"gated_tool": tool},
            allowed_servers=frozenset(["mdq"]),
        )
        assert reg.exclusion_reason("gated_tool") == "posture"

    def test_capability_exclusion_drops_only_the_dependent_tool(self) -> None:
        """T-06 (REQ-006/AC-06): only the tool whose declared capability is degraded is dropped."""
        dependent = build_fixture_runtime_tool(
            name="github_create_issue",
            server_key="github",
            capabilities=("github.api",),
        )
        independent = build_fixture_runtime_tool(
            name="github_list_issues",
            server_key="github",
            capabilities=("github.operations",),
        )
        other_server = build_fixture_runtime_tool(
            name="mdq_query", server_key="mdq", capabilities=("mdq.corpus",)
        )
        reg = RuntimeToolRegistry(
            {
                "github_create_issue": dependent,
                "github_list_issues": independent,
                "mdq_query": other_server,
            },
            allowed_servers=frozenset(["github", "mdq"]),
            degraded_capabilities={"github": ("github.api",)},
        )
        assert reg.exclusion_reason("github_create_issue") == "capability"
        assert reg.resolve("github_create_issue") is None
        assert reg.exclusion_reason("github_list_issues") is None
        assert reg.resolve("github_list_issues") == "github"
        assert reg.exclusion_reason("mdq_query") is None

    def test_capability_exclusion_covers_a_tool_with_no_declared_capability(
        self,
    ) -> None:
        """T-06: an entry that declares no capability depends on the owning server's catalog
        capabilities, which reach this module as the degraded subset of the map."""
        tool = build_fixture_runtime_tool(name="github_get_issue", server_key="github")
        reg = RuntimeToolRegistry(
            {"github_get_issue": tool},
            allowed_servers=frozenset(["github"]),
            degraded_capabilities={"github": ("github.api",)},
        )
        assert reg.exclusion_reason("github_get_issue") == "capability"

    def test_capability_exclusion_keeps_the_server_level_reason(self) -> None:
        """A tool from a server already excluded for availability keeps that reason."""
        tool = build_fixture_runtime_tool(
            name="down_tool", server_key="down_srv", capabilities=("github.api",)
        )
        reg = RuntimeToolRegistry(
            {"down_tool": tool},
            unavailable_servers=frozenset(["down_srv"]),
            allowed_servers=frozenset(["down_srv"]),
            degraded_capabilities={"down_srv": ("github.api",)},
        )
        assert reg.exclusion_reason("down_tool") == "unavailable"

    def test_capability_exclusion_survives_policy_application(self) -> None:
        """REQ-008: the single rebinding does not re-register a capability-excluded tool."""
        dependent = build_fixture_runtime_tool(
            name="dependent", server_key="github", capabilities=("github.api",)
        )
        kept = build_fixture_runtime_tool(
            name="kept", server_key="github", capabilities=("github.operations",)
        )
        reg = RuntimeToolRegistry(
            {"dependent": dependent, "kept": kept},
            allowed_servers=frozenset(["github"]),
            degraded_capabilities={"github": ("github.api",)},
        )
        reg.apply_policy(allowed_tools=("dependent", "kept"))
        assert reg.exclusion_reason("dependent") == "capability"
        assert reg.resolve("dependent") is None
        assert reg.resolve("kept") == "github"

    def test_excluded_tools_lists_the_dropped_names_and_reasons(self) -> None:
        """The display path lists the dropped tools; `diagnostics()` has no row for them."""
        dependent = build_fixture_runtime_tool(
            name="dependent", server_key="github", capabilities=("github.api",)
        )
        kept = build_fixture_runtime_tool(
            name="kept", server_key="github", capabilities=("github.operations",)
        )
        reg = RuntimeToolRegistry(
            {"dependent": dependent, "kept": kept},
            allowed_servers=frozenset(["github"]),
            degraded_capabilities={"github": ("github.api",)},
        )
        assert dict(reg.excluded_tools()) == {"dependent": "capability"}
        # Read-only view (REQ-008): the caller cannot add an entry the registry did not decide.
        with pytest.raises(TypeError):
            reg.excluded_tools()["added"] = "capability"

    def test_disable_then_re_enable_returns_true(self) -> None:
        tool = build_fixture_runtime_tool(
            name="t", server_key="s", enabled_for_llm=True
        )
        reg = _registry_with(tool)
        # First call: disable the tool
        reg.apply_policy(allowed_tools=["other"])
        assert reg.get("t").enabled_for_llm is False
        # Second call: re-enable it
        reg.apply_policy(allowed_tools=["t"])
        assert reg.get("t").enabled_for_llm is True

    def test_atomic_single_swap_identity_change(self) -> None:
        tool = build_fixture_runtime_tool(
            name="t", server_key="s", enabled_for_llm=True
        )
        reg = _registry_with(tool)
        old_id = id(reg._tools)
        reg.apply_policy(allowed_tools=("t",))
        new_id = id(reg._tools)
        assert old_id != new_id

    def test_apply_policy_leaves_tools_unchanged_when_build_raises(self) -> None:
        tool_a = build_fixture_runtime_tool(
            name="tool_a", server_key="s", enabled_for_llm=True
        )
        tool_b = build_fixture_runtime_tool(
            name="tool_b", server_key="s", enabled_for_llm=True
        )
        reg = _registry_with(tool_a, tool_b)
        original_a = reg.get("tool_a")
        original_b = reg.get("tool_b")

        real_replace = dataclasses.replace

        def _raising_replace(obj: object, **changes: object) -> object:
            if getattr(obj, "name", None) == "tool_b":
                raise ValueError("simulated mid-build failure")
            return real_replace(obj, **changes)  # type: ignore[type-var]  # — obj is a RuntimeTool at runtime; typed as object only to match dataclasses.replace's patched signature

        with patch(
            "shared.runtime_tool_registry.dataclasses.replace",
            side_effect=_raising_replace,
        ):
            with pytest.raises(ValueError):
                reg.apply_policy(allowed_tools=())

        assert reg.get("tool_a") is original_a
        assert reg.get("tool_b") is original_b

    def test_apply_policy_swap_never_exposes_mixed_state_to_concurrent_reader(
        self,
    ) -> None:
        """CPython-GIL-dependent regression test: a single self._tools reference swap
        is atomic with respect to concurrent readers under CPython's GIL."""
        tool = build_fixture_runtime_tool(
            name="t",
            server_key="s",
            agent_safety_tier="READ_ONLY",
            enabled_for_llm=True,
        )
        reg = _registry_with(tool)
        snapshots: list[tuple[str, bool]] = []
        stop = threading.Event()

        def _reader() -> None:
            while not stop.is_set():
                observed = reg.get("t")
                snapshots.append((observed.agent_safety_tier, observed.enabled_for_llm))

        reader = threading.Thread(target=_reader)
        reader.start()
        for i in range(5000):
            if i % 2 == 0:
                reg.apply_policy(allowed_tools=("t",))
            else:
                reg.apply_policy(allowed_tools=("t",))
        stop.set()
        reader.join()

        valid_states = {("ADMIN", True), ("READ_ONLY", True)}
        assert set(snapshots) <= valid_states


class TestDisabledServerExclusion:
    def test_disabled_server_tools_not_included(self) -> None:
        """Tools from a disabled server should not appear in the registry."""
        from unittest.mock import MagicMock

        disabled_cfg = MagicMock()
        disabled_cfg.is_disabled = True

        tool = build_fixture_runtime_tool(name="write_file", server_key="disabled_srv")
        reg = RuntimeToolRegistry(
            {tool.name: tool},
            server_configs={"disabled_srv": disabled_cfg},
            allowed_servers=frozenset(["disabled_srv"]),
        )
        assert "write_file" not in reg.all_tools()

    def test_enabled_server_tools_are_included(self) -> None:
        """Tools from an enabled server should appear in the registry."""
        from unittest.mock import MagicMock

        enabled_cfg = MagicMock()
        enabled_cfg.is_disabled = False

        tool = build_fixture_runtime_tool(name="read_file", server_key="enabled_srv")
        reg = RuntimeToolRegistry(
            {tool.name: tool},
            server_configs={"enabled_srv": enabled_cfg},
            allowed_servers=frozenset(["enabled_srv"]),
        )
        tool_names = {t.name for t in reg.all_tools()}
        assert "read_file" in tool_names


class TestApplyPolicyReversibility:
    def test_disable_then_re_enable_sequence(self) -> None:
        """A tool disabled by one apply_policy() call becomes re-enabled by a subsequent call with the tool back in allowed_tools."""
        tool = build_fixture_runtime_tool(
            name="shell_run", server_key="s", enabled_for_llm=True
        )
        reg = _registry_with(tool)
        # First call: disable the tool
        reg.apply_policy(allowed_tools=["other_tool"])
        assert reg.get("shell_run").enabled_for_llm is False
        # Second call: re-enable the tool
        reg.apply_policy(allowed_tools=["shell_run"])
        assert reg.get("shell_run").enabled_for_llm is True

    def test_atomic_single_swap_per_call(self) -> None:
        """The _tools mapping reference changes identity exactly once per apply_policy() call."""
        tool = build_fixture_runtime_tool(
            name="shell_run", server_key="s", enabled_for_llm=True
        )
        reg = _registry_with(tool)
        old_id = id(reg._tools)
        reg.apply_policy(allowed_tools=[])
        new_id = id(reg._tools)
        assert old_id != new_id
        assert len(reg._tools) == 1
        # ADR-004: an empty allowed_tools denies every tool (fail closed).
        assert reg.get("shell_run").enabled_for_llm is False


class TestPostureGate:
    """`allowed_servers` is the Security Posture gate: a key absent from it is excluded."""

    def test_a_server_absent_from_the_gate_is_excluded(self) -> None:
        gated = build_fixture_runtime_tool(name="git_push", server_key="git")
        green = build_fixture_runtime_tool(name="mdq_query", server_key="mdq")
        reg = RuntimeToolRegistry(
            {"git_push": gated, "mdq_query": green},
            allowed_servers=frozenset(["mdq"]),
        )
        assert reg.resolve("git_push") is None
        assert reg.resolve("mdq_query") == "mdq"
        assert reg.posture_excluded_servers == frozenset(["git"])

    def test_an_empty_gate_registers_nothing(self) -> None:
        """The fail-closed reading: no validated posture means no MCP tool at all."""
        tools = {
            "a": build_fixture_runtime_tool(name="a", server_key="git"),
            "b": build_fixture_runtime_tool(name="b", server_key="mdq"),
        }
        reg = RuntimeToolRegistry(tools, allowed_servers=frozenset())
        assert reg.all_tools() == []
        assert reg.llm_tool_definitions() == []
        assert reg.resolve("a") is None
        with pytest.raises(KeyError):
            reg.get("a")
        assert reg.posture_excluded_servers == frozenset(["git", "mdq"])

    def test_allowed_servers_none_raises_type_error(self) -> None:
        """REQ-001: the Security Posture gate is mandatory; None is rejected."""
        tools = {
            "a": build_fixture_runtime_tool(name="a", server_key="git"),
            "b": build_fixture_runtime_tool(name="b", server_key="mdq"),
        }
        with pytest.raises(TypeError):
            RuntimeToolRegistry(tools, allowed_servers=None)

    def test_a_green_gate_excludes_nothing(self) -> None:
        tool = build_fixture_runtime_tool(name="mdq_query", server_key="mdq")
        reg = RuntimeToolRegistry(
            {"mdq_query": tool}, allowed_servers=frozenset(["mdq"])
        )
        assert reg.resolve("mdq_query") == "mdq"
        assert reg.posture_excluded_servers == frozenset()

    def test_a_gated_tool_is_not_offered_to_the_llm(self) -> None:
        gated = build_fixture_runtime_tool(
            name="git_push", server_key="git", enabled_for_llm=True
        )
        green = build_fixture_runtime_tool(
            name="mdq_query", server_key="mdq", enabled_for_llm=True
        )
        reg = RuntimeToolRegistry(
            {"git_push": gated, "mdq_query": green},
            allowed_servers=frozenset(["mdq"]),
        )
        assert [entry["name"] for entry in reg.llm_tool_definitions()] == ["mdq_query"]

    def test_posture_exclusion_stays_separate_from_unavailability(self) -> None:
        """REQ-013 classifies the two causes differently, so the reports must not merge."""
        down = build_fixture_runtime_tool(name="git_push", server_key="git")
        unsafe = build_fixture_runtime_tool(name="mdq_query", server_key="mdq")
        reg = RuntimeToolRegistry(
            {"git_push": down, "mdq_query": unsafe},
            unavailable_servers=frozenset(["git"]),
            allowed_servers=frozenset(),
        )
        assert reg.unavailable_servers == frozenset(["git"])
        assert reg.posture_excluded_servers == frozenset(["mdq"])

    def test_a_disabled_server_is_excluded_before_the_gate_is_consulted(self) -> None:
        from unittest.mock import MagicMock

        cfg = MagicMock()
        cfg.is_disabled = True
        tool = build_fixture_runtime_tool(name="write_file", server_key="disabled_srv")
        reg = RuntimeToolRegistry(
            {"write_file": tool},
            server_configs={"disabled_srv": cfg},
            allowed_servers=frozenset(["disabled_srv"]),
        )
        assert reg.all_tools() == []
        assert reg.posture_excluded_servers == frozenset()

    def test_construction_logs_one_line_naming_the_excluded_keys(
        self, caplog: Any
    ) -> None:
        gated = build_fixture_runtime_tool(name="git_push", server_key="git")
        green = build_fixture_runtime_tool(name="mdq_query", server_key="mdq")
        with caplog.at_level(logging.WARNING, logger="shared.runtime_tool_registry"):
            RuntimeToolRegistry(
                {"git_push": gated, "mdq_query": green},
                allowed_servers=frozenset(["mdq"]),
            )
        assert "posture-excluded servers: git" in caplog.text

    def test_a_green_registry_logs_no_warning(self, caplog: Any) -> None:
        tool = build_fixture_runtime_tool(name="mdq_query", server_key="mdq")
        with caplog.at_level(logging.WARNING, logger="shared.runtime_tool_registry"):
            RuntimeToolRegistry({"mdq_query": tool}, allowed_servers=frozenset(["mdq"]))
        assert "posture-excluded" not in caplog.text


# ── policy snapshot / restore pair (REQ-006) ──────────────────────────────────


class TestPolicySnapshotAndRestore:
    """apply_policy is reversible through snapshot_policy and restore_policy."""

    def _registry(self) -> RuntimeToolRegistry:
        return _registry_with(
            build_fixture_runtime_tool(
                name="read_file",
                server_key="fs",
                is_write=False,
                agent_safety_tier="READ_ONLY",
                enabled_for_llm=True,
            ),
            build_fixture_runtime_tool(
                name="delete_file",
                server_key="fs",
                is_write=True,
                agent_safety_tier="WRITE_DANGEROUS",
                enabled_for_llm=True,
            ),
        )

    def test_snapshot_captures_the_tool_objects_apply_policy_replaces(self) -> None:
        registry = self._registry()

        snapshot = registry.snapshot_policy()

        assert snapshot.service == "runtime_tools"
        assert snapshot.values["tools"]["read_file"] is registry.get("read_file")

    def test_restore_reattaches_the_original_tool_objects(self) -> None:
        """apply_policy replaces every entry with a dataclasses.replace copy."""
        registry = self._registry()
        snapshot = registry.snapshot_policy()
        original = registry.get("read_file")

        registry.apply_policy(allowed_tools=[], tool_policy_mode="explicit_allowlist")
        assert registry.get("read_file") is not original
        assert registry.get("read_file").enabled_for_llm is False

        registry.restore_policy(snapshot)

        assert registry.get("read_file") is original
        assert registry.get("read_file").enabled_for_llm is True

    def test_restore_changes_nothing_beyond_the_tool_mapping(self) -> None:
        """The policy inputs are call arguments, not stored registry state."""
        registry = self._registry()
        snapshot = registry.snapshot_policy()
        before = registry.diagnostics()

        registry.apply_policy(
            allowed_tools=["read_file"],
            tool_policy_mode="explicit_allowlist",
            disabled_tools=["delete_file"],
        )
        registry.restore_policy(snapshot)

        assert registry.diagnostics() == before

    def test_resolve_and_llm_definitions_see_the_restored_policy(self) -> None:
        registry = self._registry()
        snapshot = registry.snapshot_policy()
        before_names = [row["name"] for row in registry.llm_tool_definitions()]

        registry.apply_policy(allowed_tools=[], tool_policy_mode="explicit_allowlist")
        registry.restore_policy(snapshot)

        assert [row["name"] for row in registry.llm_tool_definitions()] == before_names
        assert registry.resolve("delete_file") == "fs"
