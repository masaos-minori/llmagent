# Implementation: scripts/shared/plugin_tool_invoker.py (delete)

Source plan: `plans/done/20260717-123416_plan.md` (Implementation step 2)

Gap-filling note: matches the granularity of the 4 existing sibling docs for
this plan step. **Must run AFTER** `tool_executor_py_plugin_removal.md`
(step 1) lands — that doc removes this module's sole consumer.

## Goal

`scripts/shared/plugin_tool_invoker.py` no longer exists; `ToolExecutor` is
MCP-only (already true once the step-1 doc lands, this doc just removes the
now-dead file itself).

## Scope

**In scope**: delete `scripts/shared/plugin_tool_invoker.py` (81 lines) in full.

**Out of scope**: `ToolExecutor`'s own code (already edited by the step-1 doc);
`plugin_registry.py` (sibling step-2 doc).

## Assumptions

1. Confirmed by direct read (2026-07-17): this file defines only `PluginToolInvoker`
   with one public method, `try_execute()`; its sole consumer is
   `scripts/shared/tool_executor.py` (`self._plugin_invoker = PluginToolInvoker()`
   in `__init__`, and the `execute()` short-circuit) — both removed by
   `tool_executor_py_plugin_removal.md`.
2. Confirmed via `grep -rln "plugin_tool_invoker\|PluginToolInvoker" scripts/ --include="*.py"` (excluding this file itself): the only hit is `scripts/shared/tool_executor.py`.
3. This file itself imports `from shared import plugin_registry` (line 7) and `from shared.transport_dto import ToolCallResult` (line 8) — the `plugin_registry` import disappears along with this file (no need to separately "remove an import" since the whole file is deleted); `transport_dto`'s `ToolCallResult` is untouched elsewhere (that dataclass survives, only its field-comment documentation changes per step 4's separate doc).

## Implementation

### Target file

`scripts/shared/plugin_tool_invoker.py` (delete)

### Procedure

1. Confirm (re-verify at implementation time) `tool_executor_py_plugin_removal.md` has already landed — `grep -n "plugin_tool_invoker\|PluginToolInvoker" scripts/shared/tool_executor.py` must return 0 matches before proceeding.
2. Delete `scripts/shared/plugin_tool_invoker.py`.

### Method

Whole-file deletion — no other code change.

### Details

- Test file changes (`shared/test_plugin_tool_invoker.py` deletion) are the existing `plugin_test_files_removal` doc's job — do not delete it from this doc.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| File deleted | `ls scripts/shared/plugin_tool_invoker.py` | No such file |
| No remaining imports anywhere | `grep -rn "plugin_tool_invoker\|PluginToolInvoker" scripts/` | 0 matches |
| Full suite (run only once all step-1/step-2/step-6 docs have landed) | `uv run pytest -q` | all pass, no `ModuleNotFoundError` |
