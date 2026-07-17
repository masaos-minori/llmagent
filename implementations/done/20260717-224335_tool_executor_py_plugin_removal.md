# Implementation: scripts/shared/tool_executor.py (remove plugin tool short-circuit)

Source plan: `plans/done/20260717-123416_plan.md` (Implementation step 1, item 2)

Gap-filling note: see `implementations/20260717-224311_registry_py_plugin_removal.md`
for the full explanation of why this doc exists (step 1 of the plugin-removal
plan had no implementation docs). This doc and its 4 siblings for
`registry.py`, `factory.py`, `rag/pipeline.py`, `command_defs_list.py` must all
land BEFORE `plugin_tool_invoker.py` is deleted (step 2).

## Goal

`ToolExecutor` becomes MCP-only: it no longer imports or instantiates
`PluginToolInvoker`, and `execute()` no longer short-circuits to a plugin
result before checking `is_side_effect()`/cache.

## Scope

**In scope**
- `scripts/shared/tool_executor.py`: remove the `from shared.plugin_tool_invoker import PluginToolInvoker` import (line 27), the `self._plugin_invoker = PluginToolInvoker()` instantiation in `__init__` (line 67), and the plugin short-circuit in `execute()` (lines 208-210).

**Out of scope**
- Deleting `plugin_tool_invoker.py` itself — that is step 2 (separate doc, must run after this one).
- Any other method in `ToolExecutor` (`_raw_execute`, `_execute_with_cache`, `clear_cache`, `get_error_counters`, etc.) — unaffected.
- Test file changes — covered by the existing `implementations/done/` plugin-test-removal doc (which lists `test_tool_executor.py`, `test_tool_executor_routing.py`, `test_tool_executor_order.py` as needing plugin-specific test removal, not this doc's job).

## Assumptions

1. Confirmed by direct read (2026-07-17): the only three plugin touch-points in this file are the import (line 27), the `__init__` field (line 67), and the `execute()` short-circuit (lines 206-210, including the docstring's "Plugin tools bypass cache and MCP routing" clause).
2. `execute()`'s current body:
   ```python
   async def execute(
       self,
       tool_name: str,
       args: dict[str, Any],
   ) -> ToolCallResult:
       """Execute a tool. Plugin tools bypass cache and MCP routing; side-effecting
       tools bypass the cache and always re-execute; other tools use the cache."""
       plugin_result = await self._plugin_invoker.try_execute(tool_name, args)
       if plugin_result is not None:
           return plugin_result
       if is_side_effect(tool_name):
           return await self._raw_execute(tool_name, args)
       return await self._execute_with_cache(tool_name, args)
   ```
   Removing the first two lines of the body (the plugin short-circuit) leaves a fully correct, self-contained `is_side_effect()`/cache dispatch — no other logic depends on the plugin branch ever having run first (confirmed: `is_side_effect()` and `_execute_with_cache()` take only `tool_name`/`args`, not any plugin-derived state).
3. No production caller depends on `ToolExecutor` having a `_plugin_invoker` attribute — grep confirms `_plugin_invoker` appears only in this file (`__init__` and `execute()`); no external code introspects it.

## Implementation

### Target file

`scripts/shared/tool_executor.py`

### Procedure

1. Delete `from shared.plugin_tool_invoker import PluginToolInvoker` (line 27).
2. Delete `self._plugin_invoker = PluginToolInvoker()` (line 67, inside `__init__`).
3. In `execute()`, delete:
   ```python
   plugin_result = await self._plugin_invoker.try_execute(tool_name, args)
   if plugin_result is not None:
       return plugin_result
   ```
   leaving:
   ```python
   async def execute(
       self,
       tool_name: str,
       args: dict[str, Any],
   ) -> ToolCallResult:
       """Execute a tool. Side-effecting tools bypass the cache and always
       re-execute; other tools use the cache."""
       if is_side_effect(tool_name):
           return await self._raw_execute(tool_name, args)
       return await self._execute_with_cache(tool_name, args)
   ```
   (docstring's plugin clause removed too, per Assumption 1).

### Method

Direct deletions only — no control-flow redesign. The remaining two-line dispatch (`is_side_effect` → raw execute vs. cached execute) is unchanged from what already ran on every non-plugin call.

### Details

- Do not touch `_raw_execute()`, `_execute_with_cache()`, or any transport/caching logic — plugin removal is confined to the three touch-points above.
- This file has high churn (32 commits/30d per the plan's Affected areas) — rebase immediately before landing this change and re-verify line numbers against the current file state before editing, since they may have shifted.
- Test file changes (`test_tool_executor.py`, `test_tool_executor_routing.py`, `test_tool_executor_order.py`) are the existing `plugin_test_files_removal` doc's job — do not edit them here.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| No plugin references remain in this file | `grep -n "plugin\|Plugin" scripts/shared/tool_executor.py` | 0 matches |
| Syntax/lint | `uv run ruff check scripts/shared/tool_executor.py` | 0 errors |
| Type check | `uv run mypy scripts/shared/tool_executor.py` | no new errors |
| Targeted tests (expect some failures until step-2/step-6 docs also land) | `uv run pytest tests/test_tool_executor.py -v` | pass once plugin-specific test cases are also removed per the test-removal doc |
