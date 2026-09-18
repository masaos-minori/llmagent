# Implementation Procedure — New file: RuntimeToolRegistry routing authority validation

## Target File

`tests/shared/test_tool_routing_validation.py` (new file)

## Invariant Addressed

| INV | Description |
|-----|-------------|
| INV-005 | RuntimeToolRegistry is the sole routing authority |

## Context

ADR-003 (`docs/adr/ADR-003-runtime-tool-registry-routing-authority.md`) establishes that `RuntimeToolRegistry` is the single authoritative component for tool routing decisions. The existing test file `tests/shared/test_runtime_tool_registry.py` covers general registry behavior but does not specifically validate the routing authority invariant.

## Steps

### Step 1 — Create the new test file

Create `tests/shared/test_tool_routing_validation.py` with the following structure:

```python
"""tests/shared/test_tool_routing_validation.py
Asserts that RuntimeToolRegistry is the sole routing authority per ADR-003.
"""

from __future__ import annotations

import pytest
from shared.runtime_tool import RuntimeTool, build_runtime_tool
from shared.runtime_tool_registry import RuntimeToolRegistry


def _registry_with(*tools: RuntimeTool) -> RuntimeToolRegistry:
    return RuntimeToolRegistry({tool.name: tool for tool in tools})
```

### Step 2 — Add test: resolve() returns server key for known tool

```python
class TestRoutingAuthority:
    def test_resolve_returns_server_key_for_known_tool(self) -> None:
        """INV-005: resolve() delegates to RuntimeToolRegistry."""
        reg = _registry_with(build_runtime_tool(name="write_file", server_key="fs"))
        assert reg.resolve("write_file") == "fs"
```

### Step 3 — Add test: resolve() returns None for unknown tool

```python
    def test_resolve_returns_none_for_unknown_tool(self) -> None:
        """INV-005: unknown tools must not resolve to any server."""
        reg = _registry_with()
        assert reg.resolve("nope") is None
```

### Step 4 — Add test: get() returns RuntimeTool for known name

```python
    def test_get_returns_runtime_tool_for_known_name(self) -> None:
        """INV-005: get() retrieves the exact registered tool."""
        tool = build_runtime_tool(name="t", server_key="s")
        reg = _registry_with(tool)
        assert reg.get("t") is tool
```

### Step 5 — Add test: get() raises KeyError for unregistered name

```python
    def test_get_raises_for_unregistered_name(self) -> None:
        """INV-005: unregistered names must raise KeyError."""
        reg = _registry_with()
        with pytest.raises(KeyError):
            reg.get("nope")
```

### Step 6 — Add test: all_tools() returns every registered tool

```python
    def test_all_tools_returns_every_registered_tool(self) -> None:
        """INV-005: all_tools() includes all registered tools."""
        reg = _registry_with(
            build_runtime_tool(name="a", server_key="s"),
            build_runtime_tool(name="b", server_key="s"),
        )
        names = {tool.name for tool in reg.all_tools()}
        assert names == {"a", "b"}
```

### Step 7 — Add test: llm_tool_definitions() filters enabled tools and rekeys parameters

```python
    def test_llm_tool_definitions_filters_enabled_and_rekeys_parameters(self) -> None:
        """INV-005: only enabled tools appear in LLM tool definitions."""
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
```

### Step 8 — Add test: tool_spec_map copies write scope fields and falls back to global write scope

```python
    def test_tool_spec_map_copies_write_serial_scope_fields_and_falls_back_to_global_write_scope(
        self,
    ) -> None:
        """INV-005: tool_spec_map preserves write scope semantics."""
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
        assert spec.resource_scopes == ("global:write",)
        assert spec.call_id == ""
```

### Step 9 — Add test: tool_spec_for_call fills call-specific fields

```python
    def test_tool_spec_for_call_fills_call_specific_fields(self) -> None:
        """INV-005: tool_spec_for_call populates call-level metadata."""
        tool = build_runtime_tool(name="write_file", server_key="fs", is_write=True)
        reg = _registry_with(tool)
        spec = reg.tool_spec_for_call(
            call_id="call-1", name="write_file", args={"path": "x"}
        )
        assert spec.call_id == "call-1"
        assert spec.args == {"path": "x"}
        assert spec.is_write is True
```

### Step 10 — Add test: tool_spec_for_call resolves scope from call args

```python
    def test_tool_spec_for_call_resolves_scope_from_call_args(self) -> None:
        """INV-005: tool_spec_for_call resolves resource scopes from call arguments."""
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
```

### Step 11 — Add test: tool_spec_for_call falls back to global write when scope key missing

```python
    def test_tool_spec_for_call_falls_back_to_global_write_when_scope_key_missing(
        self,
    ) -> None:
        """INV-005: missing scope keys fall back to global write scope."""
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
```

### Step 12 — Add test: tool_spec_for_call raises KeyError for unregistered name

```python
    def test_tool_spec_for_call_raises_for_unregistered_name(self) -> None:
        """INV-005: unregistered tool names raise KeyError."""
        reg = _registry_with()
        with pytest.raises(KeyError):
            reg.tool_spec_for_call(call_id="call-1", name="nope", args={})
```

### Step 13 — Add test: apply_policy updates tier and LLM visibility

```python
    def test_apply_policy_updates_tier_and_llm_visibility(self) -> None:
        """INV-005: apply_policy enforces policy on tool tiers and visibility."""
        tool = build_runtime_tool(
            name="shell_run", server_key="s", enabled_for_llm=True
        )
        reg = _registry_with(tool)
        reg.apply_policy(tier_map={"shell_run": "ADMIN"}, allowed_tools=["shell_run"])
        updated = reg.get("shell_run")
        assert updated.agent_safety_tier == "ADMIN"
        assert updated.enabled_for_llm is True
```

### Step 14 — Add test: apply_policy disables tools not in allowed list

```python
    def test_apply_policy_disables_tools_not_in_allowed_list(self) -> None:
        """INV-005: tools excluded from allowed_tools are disabled."""
        tool = build_runtime_tool(
            name="search_web", server_key="s", enabled_for_llm=True
        )
        reg = _registry_with(tool)
        reg.apply_policy(tier_map={}, allowed_tools=["other_tool"])
        assert reg.get("search_web").enabled_for_llm is False
```

### Step 15 — Add test: apply_policy empty allowed_tools keeps all enabled

```python
    def test_apply_policy_empty_allowed_tools_keeps_all_enabled(self) -> None:
        """INV-005: empty allowed_tools list does not disable tools."""
        tool = build_runtime_tool(
            name="search_web", server_key="s", enabled_for_llm=True
        )
        reg = _registry_with(tool)
        reg.apply_policy(tier_map={}, allowed_tools=())
        assert reg.get("search_web").enabled_for_llm is True
```

### Step 16 — Add test: apply_policy updates tier to read-only

```python
    def test_apply_policy_updates_tier_to_read_only(self) -> None:
        """INV-005: READ_ONLY tier assignment works via apply_policy."""
        tool = build_runtime_tool(
            name="read_file", server_key="s", enabled_for_llm=True
        )
        reg = _registry_with(tool)
        reg.apply_policy(tier_map={"read_file": "READ_ONLY"})
        updated = reg.get("read_file")
        assert updated.agent_safety_tier == "READ_ONLY"
```

### Step 17 — Add test: apply_policy keeps current tier when absent from tier_map

```python
    def test_apply_policy_keeps_current_tier_when_absent_from_tier_map(self) -> None:
        """INV-005: existing tier is preserved when not in tier_map."""
        tool = build_runtime_tool(
            name="read_file", server_key="s", agent_safety_tier="READ_ONLY"
        )
        reg = _registry_with(tool)
        reg.apply_policy(tier_map={})
        assert reg.get("read_file").agent_safety_tier == "READ_ONLY"
```

### Step 18 — Add test: diagnostics uses raw_definition disabled_reason when present

```python
    def test_diagnostics_uses_raw_definition_disabled_reason_when_present(self) -> None:
        """INV-005: diagnostics respects raw_definition disabled_reason."""
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
```

### Step 19 — Add test: diagnostics falls back to status when raw_definition lacks disabled_reason

```python
    def test_diagnostics_falls_back_to_status_when_raw_definition_lacks_disabled_reason(
        self,
    ) -> None:
        """INV-005: diagnostics falls back to status field when raw_definition lacks reason."""
        tool = build_runtime_tool(
            name="inactive_tool", server_key="s", status="inactive", raw_definition={}
        )
        reg = _registry_with(tool)
        row = reg.diagnostics()[0]
        assert row["disabled_reason"] == "inactive"
        assert row["enabled"] is False
```

### Step 20 — Add test: diagnostics active status with no raw reason yields empty string

```python
    def test_diagnostics_active_status_with_no_raw_reason_yields_empty_string(
        self,
    ) -> None:
        """INV-005: active tools report empty disabled_reason."""
        tool = build_runtime_tool(
            name="active_tool", server_key="s", status="active", raw_definition={}
        )
        reg = _registry_with(tool)
        row = reg.diagnostics()[0]
        assert row["disabled_reason"] == ""
        assert row["config_dependent"] is False
        assert row["enabled"] is True
        assert row["server_key"] == "s"
```

### Step 21 — Add test: unavailable_servers excludes tools from unavailable server

```python
    def test_unavailable_servers_excludes_tools_from_unavailable_server(self) -> None:
        """INV-005: tools from unavailable servers are excluded from the registry."""
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
```

### Step 22 — Add test: llm_tool_definitions excludes tools from unavailable servers

```python
    def test_llm_tool_definitions_excludes_tools_from_unavailable_servers(self) -> None:
        """INV-005: LLM tool definitions exclude unavailable server tools."""
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
```

### Step 23 — Add test: diagnostics excludes tools from unavailable servers

```python
    def test_diagnostics_excludes_tools_from_unavailable_servers(self) -> None:
        """INV-005: diagnostics excludes unavailable server tools."""
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
```

### Step 24 — Add test: disable then re-enable returns True

```python
    def test_disable_then_re_enable_returns_true(self) -> None:
        """INV-005: a tool can be disabled and re-enabled via apply_policy."""
        tool = build_runtime_tool(name="t", server_key="s", enabled_for_llm=True)
        reg = _registry_with(tool)
        # First call: disable the tool
        reg.apply_policy(tier_map={}, allowed_tools=["other"])
        assert reg.get("t").enabled_for_llm is False
        # Second call: re-enable it
        reg.apply_policy(tier_map={}, allowed_tools=["t"])
        assert reg.get("t").enabled_for_llm is True
```

### Step 25 — Add test: atomic single swap identity change

```python
    def test_atomic_single_swap_identity_change(self) -> None:
        """INV-005: apply_policy creates a new _tools mapping per call."""
        tool = build_runtime_tool(name="t", server_key="s", enabled_for_llm=True)
        reg = _registry_with(tool)
        old_id = id(reg._tools)
        reg.apply_policy(tier_map={}, allowed_tools=("t",))
        new_id = id(reg._tools)
        assert old_id != new_id
```

### Step 26 — Add test class: DisabledServerExclusion

```python
class TestDisabledServerExclusion:
    def test_disabled_server_tools_not_included(self) -> None:
        """Tools from a disabled server should not appear in the registry."""
        from unittest.mock import MagicMock

        disabled_cfg = MagicMock()
        disabled_cfg.is_disabled = True

        tool = build_runtime_tool(name="write_file", server_key="disabled_srv")
        reg = RuntimeToolRegistry(
            {tool.name: tool},
            server_configs={"disabled_srv": disabled_cfg},
        )
        assert "write_file" not in reg.all_tools()

    def test_enabled_server_tools_are_included(self) -> None:
        """Tools from an enabled server should appear in the registry."""
        from unittest.mock import MagicMock

        enabled_cfg = MagicMock()
        enabled_cfg.is_disabled = False

        tool = build_runtime_tool(name="read_file", server_key="enabled_srv")
        reg = RuntimeToolRegistry(
            {tool.name: tool},
            server_configs={"enabled_srv": enabled_cfg},
        )
        tool_names = {t.name for t in reg.all_tools()}
        assert "read_file" in tool_names
```

### Step 27 — Add test class: ApplyPolicyReversibility

```python
class TestApplyPolicyReversibility:
    def test_disable_then_re_enable_sequence(self) -> None:
        """A tool disabled by one apply_policy() call becomes re-enabled by a subsequent call."""
        tool = build_runtime_tool(
            name="shell_run", server_key="s", enabled_for_llm=True
        )
        reg = _registry_with(tool)
        # First call: disable the tool
        reg.apply_policy(tier_map={}, allowed_tools=["other_tool"])
        assert reg.get("shell_run").enabled_for_llm is False
        # Second call: re-enable the tool
        reg.apply_policy(tier_map={}, allowed_tools=["shell_run"])
        assert reg.get("shell_run").enabled_for_llm is True

    def test_atomic_single_swap_per_call(self) -> None:
        """The _tools mapping reference changes identity exactly once per apply_policy() call."""
        tool = build_runtime_tool(
            name="shell_run", server_key="s", enabled_for_llm=True
        )
        reg = _registry_with(tool)
        old_id = id(reg._tools)
        reg.apply_policy(tier_map={}, allowed_tools=[])
        new_id = id(reg._tools)
        assert old_id != new_id
        assert len(reg._tools) == 1
        assert reg.get("shell_run").enabled_for_llm is True
```

## Acceptance Criteria

- New file `tests/shared/test_tool_routing_validation.py` exists at the specified path
- All 27 tests pass when run individually (`pytest -xvs`)
- The file imports use only existing dependencies (no new library requirements)
- No modifications to any other files
