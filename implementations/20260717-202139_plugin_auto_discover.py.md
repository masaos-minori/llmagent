# Implementation: delete `scripts/shared/plugin_auto_discover.py`

Source plan: `plans/20260717-123416_plan.md` ("Remove plugin subsystem completely"), Implementation step 2.

## Goal

Delete `scripts/shared/plugin_auto_discover.py` outright as part of removing the plugin subsystem. This
module (131 lines) implements `load_plugins()`, the plugin directory scanner/importer, plus
`get_last_load_result()` / `_set_last_load_result()` / `_reset_for_testing()` helpers. It has no role
once the plugin subsystem is removed — all tools will instead come from MCP servers indexed by the
forthcoming `RuntimeToolRegistry` (out of scope here, see plan Scope).

## Scope

**In scope**
- Delete the file `scripts/shared/plugin_auto_discover.py` in full.
- Confirm (at delete time) that its sole caller (`scripts/agent/factory.py:442`,
  `_init_plugin_registry()`) has already been removed by Implementation step 1, so this deletion does
  not leave a dangling import anywhere in `scripts/`.

**Out of scope**
- `scripts/agent/factory.py`'s own edit (removing `_init_plugin_registry()` and its call site) — that
  is a separate already-covered item (matches existing `implementations/done/*factory.py*` docs); this
  doc only concerns the deletion of `plugin_auto_discover.py` itself and re-verifying its callers are
  gone before deleting.
- Building any replacement discovery mechanism (`RuntimeToolRegistry` is requirement 02's scope).

## Assumptions

1. `factory.py:442`'s `_init_plugin_registry()` call site (the sole caller of `load_plugins()`) is
   removed by the separate, already-covered `factory.py` implementation item. If, at the time this
   item is executed, that removal has not yet landed, this deletion must be sequenced *after* it
   (per the plan's Design section: "delete consumers first ... then delete the now-unreferenced
   subsystem files").
2. `plugin_auto_discover.py` imports `validate_command_conflicts`/`validate_tool_conflicts` from
   `shared/plugin_conflicts.py` (line 10) and registry internals from `shared/plugin_registries.py`
   (lines 11-17) and result types from `shared/plugin_result.py` (line 18) — all three of those modules
   are themselves being deleted in this same plan (separate implementation items in this batch), so no
   dangling import survives once all four files are removed together.
3. No test file directly imports `plugin_auto_discover` by name outside the plugin-test set already
   enumerated in the plan's "Affected areas" (21/22 test files) — confirmed no `test_plugin_auto_discover.py`
   file exists in `tests/`.

## Implementation

### Target file

`scripts/shared/plugin_auto_discover.py` (131 lines) — delete in full.

### Procedure

1. Verify (via `rg -n "plugin_auto_discover" scripts/`) that the only remaining reference is the
   `factory.py` call site scheduled for removal by the separate `factory.py` item; if that item has
   already landed, the grep should show zero remaining references before this file is deleted.
2. Delete the file: `git rm scripts/shared/plugin_auto_discover.py`.
3. Re-run `rg -n "plugin_auto_discover" scripts/ tests/ docs/` to confirm zero remaining references
   (aside from this plan's own commit message / design docs).
4. Update `deploy/deploy.sh`'s copy-list if it references this file by name (the plan's "Deploy impact"
   note says 6 shared modules + `cmd_plugins.py` must be dropped from the copy-list; that edit is
   covered by the separate `deploy.sh` implementation item already marked done in this batch — no new
   action needed here beyond confirming it happens).

### Method

Pure file deletion — no code transformation, no pseudocode needed. The only "logic" is the
pre-deletion verification grep in step 1 and step 3.

### Details

- Current content (for reference, not to be reproduced verbatim in any commit message): the module's
  public surface consists of `load_plugins(plugin_dir, *, known_tools=frozenset(), override_policy="reject",
  strict_mode=False) -> PluginLoadResult`, `get_last_load_result() -> PluginLoadResult | None`,
  `_set_last_load_result(result) -> None`, and `_reset_for_testing() -> None`.
- No other production module in `scripts/` imports `load_plugins`, `get_last_load_result`, or
  `_reset_for_testing` from this module except `factory.py` (startup) and the plugin-test files
  (already scheduled for deletion/trim in the separate test-removal item).

## Validation plan

| Check | Command | Expected |
|---|---|---|
| No remaining references | `rg -n "plugin_auto_discover" scripts/ tests/ docs/` | 0 matches |
| Import health | `PYTHONPATH=scripts uv run lint-imports` | 0 violations |
| Lint | `uv run ruff check scripts/` | 0 errors |
| Type check | `uv run mypy scripts/` | no new errors |
| Full suite | `uv run pytest -v` | all pass |
