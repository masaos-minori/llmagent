# Implementation procedure: `tests/shared/test_runtime_tool_registry.py` (disabled-tool diagnostics variant)

Source plan: `plans/20260717-175327_plan.md` ("RuntimeToolRegistry — represent disabled MCP tools
without exposing them to the LLM", requirement 17), Implementation step 3.

## Goal

Create `tests/shared/test_runtime_tool_registry.py` covering the 6-field `RuntimeTool` /
`RuntimeToolRegistry` pair designed in `implementations/20260718-094020_runtime_tool.py.md` and
`implementations/20260718-094055_runtime_tool_registry.py.md`: registration/overwrite semantics,
`get_llm_visible_definitions()` excluding disabled tools, `check_executable()` raising
`DisabledToolError` for disabled tools and succeeding for enabled ones, `is_executable()`, and
`diagnostics()` returning all 6 required fields with correct values (including empty
`disabled_reason` for enabled tools).

**Filename note**: `implementations/20260717-203310_test_runtime_tool_registry.py.md` also targets
`tests/shared/test_runtime_tool_registry.py`, but tests the *other*, incompatible 9-method registry
from requirement 02 (`plans/done/20260717-124020_plan.md`). Same physical test-file collision as
the paired source-file docs — flagged, not silently treated as covering this plan.

## Scope

**In scope**
- New file `tests/shared/test_runtime_tool_registry.py` (the `tests/shared/` directory already
  exists — confirmed via `ls tests/shared/`, currently holding `test_plugin_tool_invoker.py`,
  `test_plugin_tool_registration.py`, `test_tool_executor_stampede.py`, `test_tool_result_cache.py`,
  `test_tool_transport_invoker.py`; no `__init__.py` needed beyond what already makes this a
  discoverable pytest package).
- Direct unit tests against `RuntimeTool`/`RuntimeToolRegistry` only (no MCP discovery, no
  `llm_turn_runner.py`/`cmd_mcp.py` integration — those are separate test docs).

**Out of scope**
- `tests/test_mcp_tool_discovery.py` (separate doc).
- Any assertions about `llm_turn_runner.py` or `cmd_mcp.py` behavior.

## Assumptions

- Test fixtures build `RuntimeTool` instances directly via the dataclass constructor (no factory
  function exists for this 6-field shape — confirmed in the paired `runtime_tool.py` doc, which
  notes the 6-field design has no nontrivial "safe default" logic beyond
  `compute_enabled_for_llm()`), so tests also exercise `compute_enabled_for_llm()` directly as a
  standalone function in addition to via full `RuntimeTool` construction.
- Per the registry doc's Assumptions (recommendation option (b)), `get_llm_visible_definitions()`
  is tested as returning `list[str]` (tool names), not tool-definition dicts — if the implementer
  instead follows the source plan's literal wording and returns dicts, this test's assertions on
  that method must be updated accordingly; this doc tests the documented, corrected shape.

## Implementation

### Target file

`tests/shared/test_runtime_tool_registry.py` (new).

### Procedure

1. Import `RuntimeTool`, `compute_enabled_for_llm` from `shared.runtime_tool`; `RuntimeToolRegistry`,
   `DisabledToolError` from `shared.runtime_tool_registry`.
2. `TestComputeEnabledForLlm` (or plain module-level test functions): (a) `enabled=False` always
   yields `enabled_for_llm=False` regardless of `policy_check`; (b) `enabled=True`,
   `policy_check=None` yields `enabled_for_llm=True`; (c) `enabled=True`, `policy_check` returning
   `False` yields `enabled_for_llm=False`; (d) `enabled=True`, `policy_check` returning `True` yields
   `enabled_for_llm=True`.
3. `TestRuntimeToolRegistryRegister`: (a) registering a new tool makes it retrievable via
   `diagnostics()`; (b) re-registering the same `name` with different field values overwrites the
   prior entry (no `ValueError`, unlike `ToolRegistry.register()`).
4. `TestGetLlmVisibleDefinitions`: register one enabled (`enabled_for_llm=True`) and one disabled
   (`enabled=False`, `enabled_for_llm=False`) tool; assert `get_llm_visible_definitions()` returns
   only the enabled tool's name.
5. `TestIsExecutable`: `is_executable()` returns `True` for a registered enabled tool, `False` for a
   registered disabled tool, `False` for an unregistered name (no raise).
6. `TestCheckExecutable`: (a) succeeds silently (returns `None`) for a registered enabled tool; (b)
   raises `DisabledToolError` with `.name` and `.reason` matching the tool's `disabled_reason` for a
   registered disabled tool; (c) raises `KeyError` for an unregistered name — assert this is a
   different exception type than case (b), proving the registry distinguishes "unknown" from
   "known-but-disabled" per the requirement's acceptance criterion.
7. `TestDiagnostics`: register two tools (one enabled, one disabled with a non-empty
   `disabled_reason`); assert `diagnostics()` returns one dict per tool with all 6 keys (`name`,
   `server_key`, `config_dependent`, `enabled`, `disabled_reason`, `enabled_for_llm`) and correct
   values; explicitly assert the enabled tool's `disabled_reason == ""`.

### Method

Plain `pytest` functions/classes, no fixtures needed beyond direct construction (both types are
simple enough that a `conftest.py` fixture would add indirection without benefit).

### Details

Pseudocode sketch (no production code):

```
def test_disabled_tool_never_llm_visible() -> None:
    # assert compute_enabled_for_llm(enabled=False, policy_check=lambda n: True, name="x") is False

def test_check_executable_distinguishes_unknown_from_disabled() -> None:
    # registry = RuntimeToolRegistry()
    # registry.register(RuntimeTool(name="a", server_key="s", config_dependent=False,
    #                                enabled=False, disabled_reason="server unreachable",
    #                                enabled_for_llm=False))
    # with pytest.raises(DisabledToolError) as exc_info:
    #     registry.check_executable("a")
    # assert exc_info.value.reason == "server unreachable"
    # with pytest.raises(KeyError):
    #     registry.check_executable("unknown_tool")
```

## Validation plan

| Check | Command | Target |
|---|---|---|
| Format/lint | `uv run ruff format tests/shared/test_runtime_tool_registry.py && uv run ruff check tests/shared/test_runtime_tool_registry.py` | 0 errors |
| Type check | `uv run mypy tests/shared/test_runtime_tool_registry.py` | 0 errors |
| Unit tests | `uv run pytest tests/shared/test_runtime_tool_registry.py -v` | all pass |
| Security | `uv run bandit -r tests/shared/test_runtime_tool_registry.py -c pyproject.toml` | 0 high/medium |
| Coverage | `diff-cover` on `scripts/shared/runtime_tool.py` and `scripts/shared/runtime_tool_registry.py` | ≥90% on changed lines |
