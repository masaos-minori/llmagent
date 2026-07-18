# Implementation procedure: `scripts/shared/runtime_tool_registry.py` (disabled-tool diagnostics variant)

Source plan: `plans/20260717-175327_plan.md` ("RuntimeToolRegistry — represent disabled MCP tools
without exposing them to the LLM", requirement 17), Implementation step 2.

## Goal

Create `scripts/shared/runtime_tool_registry.py`, a new `RuntimeToolRegistry` class that stores
`RuntimeTool` entries (this plan's 6-field shape, `implementations/20260718-094020_runtime_tool.py.md`)
keyed by tool name, exposes only the LLM-visible subset for the LLM's tool-definitions payload,
rejects execution attempts against disabled tools with a distinguishing exception, and provides a
diagnostics dump for `/mcp status` display. Instance-scoped (constructed per session/discovery
pass), not a global singleton, since discovery output changes across MCP config reloads.

**IMPORTANT — filename collision with an unrelated design (flag, do not merge)**: a prior doc,
`implementations/20260717-203200_runtime_tool_registry.py.md`, also targets
`scripts/shared/runtime_tool_registry.py` but is sourced from a different plan/requirement
(`plans/done/20260717-124020_plan.md`, requirement 02) and defines a **different, incompatible**
9-method `RuntimeToolRegistry` (`resolve`, `get`, `all_tools`, `llm_tool_definitions`,
`tool_spec_map`, `tool_spec_for_call`, `is_side_effect`, `classify_operation_type`,
`apply_policy`) built on top of the *other* 13-field `RuntimeTool`. That is a general
routing/policy/scheduling registry — a different responsibility than this requirement's
disabled-tool-visibility registry. As with the paired `runtime_tool.py` doc, this is a genuine
cross-plan naming collision to flag for a future integrator, not a stale match to reuse.

## Scope

**In scope**
- New file `scripts/shared/runtime_tool_registry.py` only.
- `RuntimeToolRegistry` class + `DisabledToolError` exception + the 4 methods in Design step 2 of
  the source plan: `register`, `get_llm_visible_definitions`, `is_executable`/`check_executable`,
  `diagnostics`.

**Out of scope**
- Populating the registry from live MCP discovery (separate doc,
  `scripts/agent/services/mcp_tool_discovery.py`).
- Wiring any existing call site (`llm_turn_runner.py`, `cmd_mcp.py`, `tool_runner.py`) to actually
  use this registry (separate docs for those integration points).
- Any change to `scripts/shared/tool_registry.py`'s `ToolRegistry` (confirmed unmodified; this
  plan's own Assumptions state it stays the compile-time ownership/routing source of truth).
- Reconciling the file-path/name collision noted above with requirement 02's `RuntimeToolRegistry`
  design.

## Assumptions

- Unlike `scripts/shared/tool_registry.py:64-72`'s `ToolRegistry.register()` (which raises
  `ValueError` on duplicate name — confirmed at those exact lines), `RuntimeToolRegistry.register()`
  must allow re-registration/update on the same name, since MCP server state (enabled/disabled) can
  change across config reloads and rediscovery must be able to overwrite a stale entry. Internal
  storage is therefore a plain mutable `dict[str, RuntimeTool]` with `dict[name] = tool` semantics
  (overwrite), not an insert-only structure.
- `check_executable(name)` must distinguish "tool unknown to this registry" from "tool known but
  disabled" per the source plan's Design step 2 and the requirement's "reject execution attempts"
  acceptance criterion. Resolution: raise `KeyError` (mirroring the "raise on truly unregistered
  name" convention already used for lookups elsewhere in this codebase, e.g.
  `scripts/shared/tool_registry.py`'s docstring-documented routing-authority pattern) for unknown
  names, and raise a new `DisabledToolError(name: str, reason: str)` (a distinct exception class
  defined in this same module) specifically for "known but `enabled=False`."
- `get_llm_visible_definitions()`'s output shape must match what `llm.stream()`'s `tool_definitions`
  parameter already expects, confirmed via `scripts/agent/llm_turn_runner.py:213`
  (`ctx.services_required.llm.stream(llm_url, ctx.conv.history, ctx.cfg.tool.tool_definitions)`) and
  `config/agent.toml`'s existing `[[tool_definitions.function.parameters]]` TOML shape — i.e. each
  entry is `{"type": "function", "function": {"name": ..., "description": ..., "parameters": ...}}`.
  Since this plan's 6-field `RuntimeTool` (per `implementations/20260718-094020_runtime_tool.py.md`)
  carries no `description`/`input_schema`/`parameters` fields of its own (that data lives on the
  MCP-server side `TOOL_LIST`, not duplicated into this diagnostics-focused `RuntimeTool`), this
  method's exact return shape is a documented gap: either (a) `RuntimeTool` needs those fields added
  before this method can return real LLM tool-definition dicts, or (b) this method returns only the
  list of LLM-visible tool *names*, and the caller (`llm_turn_runner.py`) merges those names against
  the existing `ctx.cfg.tool.tool_definitions` list to filter it. Recommendation for the implementer:
  option (b) is simpler and avoids widening `RuntimeTool`'s scope — `get_llm_visible_definitions()`
  should be renamed/implemented as returning `list[str]` (tool names) in practice, with the actual
  filtering against `ctx.cfg.tool.tool_definitions` happening in `llm_turn_runner.py` (see that
  integration doc). This is flagged here as a design correction rather than silently implemented
  either way, since the source plan's own Design step 2 states the method "returns ... shaped for
  `llm.stream()`'s `tool_definitions` parameter" without reconciling the missing description/schema
  fields.

## Implementation

### Target file

`scripts/shared/runtime_tool_registry.py` (new).

### Procedure

1. Module docstring: state the registry's purpose (disabled-tool visibility, not routing —
   `ToolRegistry` remains sole routing authority per its own docstring at
   `scripts/shared/tool_registry.py:18-19`); state it is unpopulated until
   `mcp_tool_discovery.py`'s discovery service constructs and fills one; flag the Assumptions-section
   gap around `get_llm_visible_definitions()`'s exact return shape; flag the physical-file-path
   collision with `implementations/20260717-203200_runtime_tool_registry.py.md`'s registry so future
   contributors do not conflate the two.
2. Define `DisabledToolError(Exception)` with `__init__(self, name: str, reason: str) -> None`
   storing both as attributes and formatting a message like
   `f"tool {name!r} is disabled: {reason}"`.
3. Define `RuntimeToolRegistry.__init__(self) -> None` with an internal `dict[str, RuntimeTool]`
   (empty by default — population is discovery's job).
4. Implement the 4 methods per Details below.

### Method

Plain mutable class wrapping a `dict[str, RuntimeTool]`, mirroring `ToolRegistry`'s structural style
but with update-on-register semantics instead of insert-only. No `Protocol`/`ABC` — single concrete
implementation.

### Details

Method signatures (pseudocode — no production code):

```
class DisabledToolError(Exception):
    def __init__(self, name: str, reason: str) -> None: ...
        # self.name = name
        # self.reason = reason
        # super().__init__(f"tool {name!r} is disabled: {reason}")


class RuntimeToolRegistry:
    def __init__(self) -> None: ...
        # self._tools: dict[str, RuntimeTool] = {}

    def register(self, tool: RuntimeTool) -> None:
        # self._tools[tool.name] = tool   # overwrite allowed, unlike ToolRegistry.register

    def get_llm_visible_definitions(self) -> list[str]:
        # NOTE: returns tool *names* only, per Assumptions gap above — caller filters
        # ctx.cfg.tool.tool_definitions against this name list.
        # return sorted(t.name for t in self._tools.values() if t.enabled_for_llm)

    def is_executable(self, name: str) -> bool:
        # tool = self._tools.get(name)
        # return tool is not None and tool.enabled

    def check_executable(self, name: str) -> None:
        # tool = self._tools.get(name)
        # if tool is None:
        #     raise KeyError(f"unregistered tool: {name}")
        # if not tool.enabled:
        #     raise DisabledToolError(name, tool.disabled_reason)

    def diagnostics(self) -> list[dict[str, object]]:
        # return [
        #     {
        #         "name": t.name,
        #         "server_key": t.server_key,
        #         "config_dependent": t.config_dependent,
        #         "enabled": t.enabled,
        #         "disabled_reason": t.disabled_reason,
        #         "enabled_for_llm": t.enabled_for_llm,
        #     }
        #     for t in sorted(self._tools.values(), key=lambda t: t.name)
        # ]
```

## Validation plan

| Check | Command | Target |
|---|---|---|
| Format/lint | `uv run ruff format scripts/shared/runtime_tool_registry.py && uv run ruff check scripts/shared/runtime_tool_registry.py` | 0 errors |
| Type check | `uv run mypy scripts/shared/runtime_tool_registry.py` | 0 errors |
| Architecture | `PYTHONPATH=scripts uv run lint-imports` | 0 violations — confirms no `agent`/`db`/`rag`/`mcp_servers` import |
| Security | `uv run bandit -r scripts/shared/runtime_tool_registry.py -c pyproject.toml` | 0 high/medium |
| Unit tests | `uv run pytest tests/shared/test_runtime_tool_registry.py -v` | all pass (see paired test doc) |
| Constraint | `ast-grep --pattern 'except: $$$' --lang python scripts/shared/runtime_tool_registry.py` | no bare except |
