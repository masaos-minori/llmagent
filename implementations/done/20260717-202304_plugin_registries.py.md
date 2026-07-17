# Implementation: delete `scripts/shared/plugin_registries.py`

Source plan: `plans/20260717-123416_plan.md` ("Remove plugin subsystem completely"), Implementation step 2.

## Goal

Delete `scripts/shared/plugin_registries.py` (29 lines) — the module-level mutable state (dicts/lists)
backing the plugin command/tool/pipeline-hook registries — since it has no consumer once the plugin
subsystem is removed.

## Scope

**In scope**
- Delete the file `scripts/shared/plugin_registries.py` in full.
- Confirm all four internal registry symbols it defines (`_commands`, `_tools`, `_pipeline_post`,
  `_current_loading_module`, `_builtin_command_names`, and the `ToolHandler` type alias) have no
  surviving importer once the rest of the subsystem is deleted.

**Out of scope**
- Any replacement registry design (`RuntimeToolRegistry` is requirement 02's scope, not this plan's).

## Assumptions

1. `plugin_registries.py` is pure internal state with no public API beyond module-level names — it is
   imported by `plugin_registry.py` (already covered/skipped — matches existing
   `implementations/done/*plugin_registry.py*` docs), `plugin_auto_discover.py` (deleted by a sibling
   item in this batch), and `plugin_conflicts.py` (deleted by a sibling item in this batch, via
   `TYPE_CHECKING`-only import at lines 10-14, plus two runtime imports at lines 28 and 71 to break a
   circular-import).
2. No file outside the plugin subsystem itself imports from `plugin_registries` — confirmed via
   `rg -n "plugin_registries" scripts/` returning only the four subsystem files
   (`plugin_registry.py`, `plugin_auto_discover.py`, `plugin_conflicts.py`, and itself via
   self-reference in type hints — none from `agent/`, `rag/`, `db/`, or `mcp_servers/`).
3. Deletion order: this file must be deleted only after (or together with, in the same commit) its
   three consumers `plugin_registry.py`, `plugin_auto_discover.py`, and `plugin_conflicts.py`, per the
   plan's Design section ("delete consumers first ... then delete the now-unreferenced subsystem files
   themselves").

## Implementation

### Target file

`scripts/shared/plugin_registries.py` (29 lines) — delete in full.

### Procedure

1. Verify via `rg -n "plugin_registries" scripts/` that the only importers are the other plugin
   subsystem files being deleted in the same batch (`plugin_registry.py`, `plugin_auto_discover.py`,
   `plugin_conflicts.py`).
2. Delete the file: `git rm scripts/shared/plugin_registries.py`.
3. Re-run `rg -n "plugin_registries" scripts/ tests/ docs/` to confirm zero remaining references
   outside this plan's own commit history.

### Method

Pure file deletion — no code transformation needed.

### Details

- Current content: two internal dict registries (`_commands: dict[str, tuple[Callable, bool, str]]`,
  `_tools: dict[str, tuple[Callable, str]]`), one list (`_pipeline_post: list[Callable]`), and two
  mutable single-element sequences used as cross-module shared state
  (`_current_loading_module: MutableSequence[str]`, `_builtin_command_names: MutableSequence[frozenset[str]]`),
  plus the `ToolHandler` type alias (`Callable[[dict], Awaitable[tuple[str, bool]]]`).
- This module has no `__all__`/public contract — every name is consumed only by the other three
  plugin-subsystem modules being deleted in the same batch, so no separate "consumer removal" step is
  needed beyond deleting those three modules themselves.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| No remaining references | `rg -n "plugin_registries" scripts/ tests/ docs/` | 0 matches |
| Import health | `PYTHONPATH=scripts uv run lint-imports` | 0 violations |
| Lint | `uv run ruff check scripts/` | 0 errors |
| Type check | `uv run mypy scripts/` | no new errors |
| Full suite | `uv run pytest -v` | all pass |
