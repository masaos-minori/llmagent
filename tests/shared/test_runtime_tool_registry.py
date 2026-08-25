"""tests/shared/test_runtime_tool_registry.py
Unit tests for RuntimeToolRegistry: resolve/get, all_tools, llm_tool_definitions,
tool_spec_map/tool_spec_for_call, apply_policy, diagnostics.
"""

from __future__ import annotations

import pytest
from shared.runtime_tool import RuntimeTool, build_runtime_tool
from shared.runtime_tool_registry import RuntimeToolRegistry
from shared.tool_spec import ToolSpec


def _registry_with(*tools: RuntimeTool) -> RuntimeToolRegistry:
    return RuntimeToolRegistry({tool.name: tool for tool in tools})


class TestRuntimeToolRegistry:
    def test_resolve_returns_server_key_for_known_tool(self) -> None:
        reg = _registry_with(build_runtime_tool(name="write_file", server_key="fs"))
        assert reg.resolve("write_file") == "fs"

    def test_resolve_returns_none_for_unknown_tool(self) -> None:
        reg = _registry_with()
        assert reg.resolve("nope") is None

    def test_get_returns_runtime_tool_for_known_name(self) -> None:
        tool = build_runtime_tool(name="t", server_key="s")
        reg = _registry_with(tool)
        assert reg.get("t") is tool

    def test_get_raises_for_unregistered_name(self) -> None:
        reg = _registry_with()
        with pytest.raises(KeyError):
            reg.get("nope")

    def test_all_tools_returns_every_registered_tool(self) -> None:
        reg = _registry_with(
            build_runtime_tool(name="a", server_key="s"),
            build_runtime_tool(name="b", server_key="s"),
        )
        names = {tool.name for tool in reg.all_tools()}
        assert names == {"a", "b"}

    def test_llm_tool_definitions_filters_enabled_and_rekeys_parameters(self) -> None:
        visible = build_runtime_tool(
            name="a",
            server_key="s",
            description="d",
            input_schema={"type": "object"},
            enabled_for_llm=True,
        )
        hidden = build_runtime_tool(name="b", server_key="s", enabled_for_llm=False)
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
        tool = build_runtime_tool(name="write_file", server_key="fs", is_write=True)
        reg = _registry_with(tool)
        spec = reg.tool_spec_for_call(
            call_id="call-1", name="write_file", args={"path": "x"}
        )
        assert spec.call_id == "call-1"
        assert spec.args == {"path": "x"}
        assert spec.is_write is True

    def test_tool_spec_for_call_resolves_scope_from_call_args(self) -> None:
        tool = build_runtime_tool(
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
        tool = build_runtime_tool(
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

    def test_apply_policy_updates_tier_and_llm_visibility(self) -> None:
        tool = build_runtime_tool(
            name="shell_run", server_key="s", enabled_for_llm=True
        )
        reg = _registry_with(tool)
        reg.apply_policy(tier_map={"shell_run": "ADMIN"}, allowed_tools=["shell_run"])
        updated = reg.get("shell_run")
        assert updated.agent_safety_tier == "ADMIN"
        assert updated.enabled_for_llm is True

    def test_apply_policy_disables_tools_not_in_allowed_list(self) -> None:
        tool = build_runtime_tool(
            name="search_web", server_key="s", enabled_for_llm=True
        )
        reg = _registry_with(tool)
        reg.apply_policy(tier_map={}, allowed_tools=["other_tool"])
        assert reg.get("search_web").enabled_for_llm is False

    def test_apply_policy_empty_allowed_tools_keeps_all_enabled(self) -> None:
        tool = build_runtime_tool(
            name="search_web", server_key="s", enabled_for_llm=True
        )
        reg = _registry_with(tool)
        reg.apply_policy(tier_map={}, allowed_tools=())
        assert reg.get("search_web").enabled_for_llm is True

    def test_apply_policy_updates_tier_to_read_only(self) -> None:
        tool = build_runtime_tool(
            name="read_file", server_key="s", enabled_for_llm=True
        )
        reg = _registry_with(tool)
        reg.apply_policy(tier_map={"read_file": "READ_ONLY"})
        updated = reg.get("read_file")
        assert updated.agent_safety_tier == "READ_ONLY"

    def test_apply_policy_keeps_current_tier_when_absent_from_tier_map(self) -> None:
        tool = build_runtime_tool(
            name="read_file", server_key="s", agent_safety_tier="READ_ONLY"
        )
        reg = _registry_with(tool)
        reg.apply_policy(tier_map={})
        assert reg.get("read_file").agent_safety_tier == "READ_ONLY"

    def test_diagnostics_uses_raw_definition_disabled_reason_when_present(self) -> None:
        tool = build_runtime_tool(
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
        tool = build_runtime_tool(
            name="inactive_tool", server_key="s", status="inactive", raw_definition={}
        )
        reg = _registry_with(tool)
        row = reg.diagnostics()[0]
        assert row["disabled_reason"] == "inactive"
        assert row["enabled"] is False

    def test_diagnostics_active_status_with_no_raw_reason_yields_empty_string(
        self,
    ) -> None:
        tool = build_runtime_tool(
            name="active_tool", server_key="s", status="active", raw_definition={}
        )
        reg = _registry_with(tool)
        row = reg.diagnostics()[0]
        assert row["disabled_reason"] == ""
        assert row["config_dependent"] is False
        assert row["enabled"] is True
        assert row["server_key"] == "s"

    def test_unavailable_servers_excludes_tools_from_unavailable_server(self) -> None:
        tool_a = build_runtime_tool(name="tool_a", server_key="unreachable_server")
        tool_b = build_runtime_tool(name="tool_b", server_key="healthy_server")
        reg = RuntimeToolRegistry(
            tools={"tool_a": tool_a, "tool_b": tool_b},
            unavailable_servers=frozenset(["unreachable_server"]),
        )
        assert reg.resolve("tool_a") is None
        assert reg.resolve("tool_b") == "healthy_server"
        assert len(reg.all_tools()) == 1
        assert reg.all_tools()[0].name == "tool_b"

    def test_llm_tool_definitions_excludes_tools_from_unavailable_servers(self) -> None:
        tool_a = build_runtime_tool(
            name="tool_a", server_key="unavailable", enabled_for_llm=True
        )
        tool_b = build_runtime_tool(
            name="tool_b", server_key="healthy", enabled_for_llm=True
        )
        reg = RuntimeToolRegistry(
            tools={"tool_a": tool_a, "tool_b": tool_b},
            unavailable_servers=frozenset(["unavailable"]),
        )
        defs = reg.llm_tool_definitions()
        assert len(defs) == 1
        assert defs[0]["name"] == "tool_b"

    def test_diagnostics_excludes_tools_from_unavailable_servers(self) -> None:
        tool_a = build_runtime_tool(
            name="tool_a", server_key="unavailable", status="inactive"
        )
        tool_b = build_runtime_tool(
            name="tool_b", server_key="healthy", status="active"
        )
        reg = RuntimeToolRegistry(
            tools={"tool_a": tool_a, "tool_b": tool_b},
            unavailable_servers=frozenset(["unavailable"]),
        )
        rows = reg.diagnostics()
        assert len(rows) == 1
        assert rows[0]["name"] == "tool_b"
