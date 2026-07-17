# Implementation procedure: `tests/shared/test_runtime_tool_registry.py`

Source plan: `plans/done/20260717-124020_plan.md` (requirement `requires/20260717_02_require.md`), Implementation step 6.

## Goal

Create `tests/shared/test_runtime_tool_registry.py` covering `scripts/shared/runtime_tool_registry.py`'s
`RuntimeToolRegistry`'s 9 methods (`resolve`, `get`, `all_tools`, `llm_tool_definitions`,
`tool_spec_map`, `tool_spec_for_call`, `is_side_effect`, `classify_operation_type`, `apply_policy`),
using hand-built `RuntimeTool` fixtures only (no live MCP server, per the plan's Assumption 2). Confirmed
via `ls tests/shared/ | grep runtime_tool` (no output) that this file does not yet exist.

## Scope

**In scope**: new file `tests/shared/test_runtime_tool_registry.py` only.

**Out of scope**: `tests/shared/test_runtime_tool.py` (separate doc, covers the dataclass itself), any
test against `scripts/shared/tool_registry.py`'s existing `ToolRegistry` (unrelated, unmodified class).

## Assumptions

1. Same directory conventions as the paired `test_runtime_tool.py` doc (per `tests/shared/test_tool_result_cache.py`):
   class-based tests, plain `assert`, local helper functions, plain absolute imports, no `conftest.py`
   fixtures needed.
2. Fixtures are built via `scripts/shared/runtime_tool.py`'s `build_runtime_tool()` factory (from the
   paired `runtime_tool.py` doc) — a local helper `_registry_with(*tools: RuntimeTool) -> RuntimeToolRegistry`
   builds a populated registry for each test without needing MCP discovery.
3. Per the paired `runtime_tool_registry.py` doc's Assumption 1, `classify_operation_type()` returns a
   plain `"read"`/`"write"` string (not an `agent.tool_enums.OperationType` member) — tests assert
   against these string literals, not an enum.
4. Per the paired `runtime_tool_registry.py` doc's Assumption 2, `apply_policy()` takes
   `tier_map: Mapping[str, AgentSafetyTier]` and `allowed_tools: Sequence[str] = ()` — tests call it with
   plain dicts/lists, not a `ToolConfig`/`ApprovalConfig` instance.
5. `tool_spec.py`'s `ToolSpec` (`call_id`, `name`, `args`, `resource_scope`, `requires_serial`,
   `is_write` — confirmed unmodified) is imported directly from `shared.tool_spec` for assertions on
   `tool_spec_map()`/`tool_spec_for_call()`'s return shape.

## Implementation

### Target file

`tests/shared/test_runtime_tool_registry.py` (new).

### Procedure

1. Import `from shared.runtime_tool import build_runtime_tool`, `from shared.runtime_tool_registry import
   RuntimeToolRegistry`, `from shared.tool_spec import ToolSpec`.
2. Add local helper `_registry_with(*tools) -> RuntimeToolRegistry` building `{t.name: t for t in tools}`
   and constructing the registry from it.
3. Write `class TestRuntimeToolRegistry:` with one test method per method under test (see Details),
   plus edge-case tests for unknown-name handling on `resolve()`/`get()`.

### Method

Pytest class-based tests, plain `assert`, matching `tests/shared/test_tool_result_cache.py`'s style.

### Details

Test methods (pseudocode — no production code):

```
class TestRuntimeToolRegistry:
    def test_resolve_returns_server_key_for_known_tool(self) -> None:
        # reg = _registry_with(build_runtime_tool(name="write_file", server_key="fs"))
        # assert reg.resolve("write_file") == "fs"

    def test_resolve_returns_none_for_unknown_tool(self) -> None:
        # reg = _registry_with()
        # assert reg.resolve("nope") is None

    def test_get_returns_runtime_tool_for_known_name(self) -> None:
        # tool = build_runtime_tool(name="t", server_key="s")
        # reg = _registry_with(tool)
        # assert reg.get("t") is tool  # or equality, depending on final storage semantics

    def test_get_raises_for_unregistered_name(self) -> None:
        # reg = _registry_with()
        # with pytest.raises(KeyError):
        #     reg.get("nope")

    def test_all_tools_returns_every_registered_tool(self) -> None:
        # reg = _registry_with(build_runtime_tool(name="a", server_key="s"),
        #                       build_runtime_tool(name="b", server_key="s"))
        # names = {t.name for t in reg.all_tools()}
        # assert names == {"a", "b"}

    def test_llm_tool_definitions_filters_enabled_and_rekeys_parameters(self) -> None:
        # visible = build_runtime_tool(name="a", server_key="s", description="d",
        #                               input_schema={"type": "object"}, enabled_for_llm=True)
        # hidden = build_runtime_tool(name="b", server_key="s", enabled_for_llm=False)
        # reg = _registry_with(visible, hidden)
        # defs = reg.llm_tool_definitions()
        # assert len(defs) == 1
        # assert defs[0]["name"] == "a"
        # assert defs[0]["parameters"] == {"type": "object"}  # re-keyed from input_schema

    def test_tool_spec_map_copies_write_serial_scope_fields(self) -> None:
        # tool = build_runtime_tool(name="delete_file", server_key="fs", is_write=True,
        #                            requires_serial=True, resource_scope="delete_file")
        # reg = _registry_with(tool)
        # spec = reg.tool_spec_map()["delete_file"]
        # assert isinstance(spec, ToolSpec)
        # assert spec.is_write is True and spec.requires_serial is True
        # assert spec.resource_scope == "delete_file"

    def test_tool_spec_for_call_fills_call_specific_fields(self) -> None:
        # tool = build_runtime_tool(name="write_file", server_key="fs", is_write=True)
        # reg = _registry_with(tool)
        # spec = reg.tool_spec_for_call(call_id="call-1", name="write_file", args={"path": "x"})
        # assert spec.call_id == "call-1"
        # assert spec.args == {"path": "x"}
        # assert spec.is_write is True

    def test_is_side_effect_reflects_is_write(self) -> None:
        # reg = _registry_with(build_runtime_tool(name="w", server_key="s", is_write=True),
        #                       build_runtime_tool(name="r", server_key="s", is_write=False))
        # assert reg.is_side_effect("w") is True
        # assert reg.is_side_effect("r") is False

    def test_classify_operation_type_read_vs_write(self) -> None:
        # reg = _registry_with(build_runtime_tool(name="w", server_key="s", is_write=True),
        #                       build_runtime_tool(name="r", server_key="s", is_write=False))
        # assert reg.classify_operation_type("w") == "write"
        # assert reg.classify_operation_type("r") == "read"

    def test_apply_policy_updates_tier_and_approval_and_llm_visibility(self) -> None:
        # tool = build_runtime_tool(name="shell_run", server_key="s", enabled_for_llm=True)
        # reg = _registry_with(tool)
        # reg.apply_policy(tier_map={"shell_run": "ADMIN"}, allowed_tools=["shell_run"])
        # updated = reg.get("shell_run")
        # assert updated.agent_safety_tier == "ADMIN"
        # assert updated.requires_approval is True

    def test_apply_policy_disables_tools_not_in_allowed_list(self) -> None:
        # tool = build_runtime_tool(name="search_web", server_key="s", enabled_for_llm=True)
        # reg = _registry_with(tool)
        # reg.apply_policy(tier_map={}, allowed_tools=["other_tool"])
        # assert reg.get("search_web").enabled_for_llm is False
```

## Validation plan

| Check | Command | Target |
|---|---|---|
| Run tests | `uv run pytest tests/shared/test_runtime_tool_registry.py -v` | all pass |
| Lint | `uv run ruff check tests/shared/test_runtime_tool_registry.py` | 0 errors |
| Type check | `uv run mypy tests/shared/test_runtime_tool_registry.py` | 0 errors |
| Full suite | `uv run pytest -v` | no new failures |
| Diff coverage | `uv run coverage run -m pytest tests/ && uv run coverage xml && uv run diff-cover coverage.xml --compare-branch=main --fail-under=90` | ≥90% on changed lines |
