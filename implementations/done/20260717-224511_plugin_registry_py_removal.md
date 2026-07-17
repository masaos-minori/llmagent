# Implementation: scripts/shared/plugin_registry.py (delete)

Source plan: `plans/done/20260717-123416_plan.md` (Implementation step 2)

Gap-filling note: matches the granularity of the 4 existing sibling docs for
this same plan step (`plugin_auto_discover.py`, `plugin_registries.py`,
`plugin_result.py`, `plugin_conflicts.py`, all in `implementations/done/`).
**Must run AFTER all 5 step-1 docs land** (`registry_py_plugin_removal.md`,
`tool_executor_py_plugin_removal.md`, `factory_py_plugin_removal.md`,
`rag_pipeline_py_plugin_removal.md`, `command_defs_list_py_plugin_removal.md`)
— those remove every external consumer of this module first. Should also run
alongside (same commit-sized unit as) the other two step-2 gap-filling docs
(`plugin_tool_invoker_py_removal.md`, `cmd_plugins_py_removal.md`), since all
seven step-2 files become unreferenced together once step 1 lands.

## Goal

`scripts/shared/plugin_registry.py` no longer exists; nothing in the
production tree imports or calls it.

## Scope

**In scope**: delete `scripts/shared/plugin_registry.py` (274 lines) in full.

**Out of scope**: any other plugin-subsystem file (covered by sibling docs);
`scripts/shared/tool_constants.py`'s stale docstring comment mentioning
"plugin_registry" (see Details — trivial prose fix, not a code dependency).

## Assumptions

1. Confirmed by direct read (2026-07-17): this module exports `register_command`,
   `register_tool`, `register_pipeline_stage`, `get_pipeline_post_stages`,
   `get_command`, `iter_commands`, `get_tool`, `iter_tools`,
   `register_builtin_commands`, `get_last_load_result`, `load_plugins`,
   `_reset_for_testing`, plus a `PipelineHook` Protocol — all consumed
   exclusively by the 5 files removed in step 1 (`registry.py`,
   `tool_executor.py` transitively via `plugin_tool_invoker.py`,
   `factory.py`, `rag/pipeline.py`, `cmd_plugins.py`) and by its own
   sibling subsystem files (`plugin_auto_discover.py`, `plugin_registries.py`
   — its internal state backing, per the plan's Affected areas).
2. Confirmed via `grep -rln "plugin_registry" scripts/ --include="*.py"` (excluding this file itself): the only hits are `factory.py`, `commands/registry.py`, `commands/cmd_plugins.py`, `rag/pipeline.py` (all step 1, already removed by the time this doc runs), `plugin_tool_invoker.py` (step 2, deleted alongside this file), and `shared/tool_constants.py` (a docstring **comment**, not an import — see Details).
3. `plugin_registries.py` and `plugin_result.py` (this module's own internal dependencies, per the plan's Affected areas: "internal state backing `plugin_registry.py`" / "dataclasses consumed by ... `cmd_plugins.py`") are deleted in the same step-2 batch (already done per `implementations/done/`), so no import-order concern exists among the step-2 files themselves.

## Implementation

### Target file

`scripts/shared/plugin_registry.py` (delete)

### Procedure

1. Confirm (re-verify at implementation time) that all 5 step-1 docs have already landed — `grep -rn "plugin_registry" scripts/agent/commands/registry.py scripts/shared/tool_executor.py scripts/agent/factory.py scripts/rag/pipeline.py scripts/agent/commands/command_defs_list.py` must return 0 matches before proceeding.
2. Delete `scripts/shared/plugin_registry.py`.
3. Fix the stale docstring comment in `scripts/shared/tool_constants.py` (lines 161-162, currently "This is the source of truth used by plugin_registry to detect plugin tools that shadow MCP tools.") — reword or remove the `plugin_registry` mention since the module it refers to no longer exists; do not remove the surrounding docstring content describing what `tool_constants.py` itself is the source of truth for.

### Method

Whole-file deletion plus a one-line prose fix in an unrelated file's docstring — no other code change.

### Details

- `shared/tool_constants.py`'s reference is prose only (a comment describing a consumer), not an import — confirmed via `grep -n "plugin_registry\|plugin" scripts/shared/tool_constants.py` returning only that docstring line; this is NOT a 4th consumer requiring its own removal doc, just a trivial doc-comment fix bundled into this one.
- Do not delete `plugins/` (the directory) here — that's the existing `plugins_directory_removal` doc, already done.
- Test file changes (`test_plugin_registry.py` deletion) are the existing `plugin_test_files_removal` doc's job.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| File deleted | `ls scripts/shared/plugin_registry.py` | No such file |
| No remaining imports anywhere | `grep -rn "plugin_registry" scripts/ config/` | 0 matches |
| Full suite (run only once all step-1/step-2/step-6 docs have landed) | `uv run pytest -q` | all pass, no `ModuleNotFoundError` |
