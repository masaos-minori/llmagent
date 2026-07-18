# Implementation: scripts/agent/commands/registry.py (remove plugin command dispatch)

Source plan: `plans/done/20260717-123416_plan.md` (Implementation step 1, item 1)

Gap-filling note: this doc fills a gap in the original implementation-doc set for
this plan — Implementation step 1 ("Remove consumer call sites first") had no
corresponding `implementations/` doc despite steps 2/3/5/6/7/9 being covered.
This doc, plus its 4 siblings for `tool_executor.py`, `factory.py`,
`rag/pipeline.py`, and `command_defs_list.py`, must all land BEFORE any of the
existing `implementations/done/`-bound docs that delete
`plugin_registry.py`/`plugin_auto_discover.py`/`plugin_registries.py`/
`plugin_result.py`/`plugin_conflicts.py`/`plugin_tool_invoker.py`/`cmd_plugins.py`
(step 2) run — otherwise those deletions leave dangling imports here.

## Goal

`CommandRegistry` no longer mixes in `_PluginsMixin`, no longer has a
`_dispatch_plugin()` fallback, and `dispatch()` returns `False` for any line
that doesn't match a built-in `_COMMANDS` entry (per the plan's Assumption 7 —
no new logic needed, only deletion).

## Scope

**In scope**
- `scripts/agent/commands/registry.py`: remove the `from shared import plugin_registry` import, the `from agent.commands.cmd_plugins import _PluginsMixin` import, `_PluginsMixin` from `CommandRegistry`'s base-class list, the `_dispatch_plugin()` method, and change `dispatch()`'s tail from `return await self._dispatch_plugin(line)` to `return False`. Also update the module docstring's mixin table (remove the `cmd_plugins.py — _PluginsMixin: /plugin` row) and the docstring's "This module owns" note (currently says it owns `_dispatch_plugin()` too).

**Out of scope**
- Deleting `cmd_plugins.py` itself, or `plugin_registry.py` — those are step 2's job (separate implementation docs, must run after this one).
- Any change to `command_defs_list.py`'s `/plugin` `CommandDef` entry — that is a sibling doc (`command_defs_list_py_plugin_removal.md`, same batch), not this one.
- Any test file changes — covered by the existing `implementations/done/` plugin-test-removal doc.

## Assumptions

1. Confirmed by direct read (2026-07-17) that `registry.py`'s only plugin-related pieces are: line 37 import, line 46 import, line 71 base class, lines 152-153 (the fallback call, inline comment "Plugin commands: exact-match and prefix-match (checked after built-ins)"), and lines 155-170 (`_dispatch_plugin()` method body, ending in `return False`).
2. `dispatch()`'s existing `for cmd in _COMMANDS` loop (lines 134-150) already returns `True` on any match and falls through otherwise — replacing the plugin fallback with a literal `return False` requires no other control-flow change (matches plan Assumption 7 exactly).
3. No other method in `registry.py` references `plugin_registry` or `_PluginsMixin` — confirmed via `grep -n "plugin" scripts/agent/commands/registry.py` returning only the 5 line groups above plus the module docstring's mixin table (line 21) and ownership note (line 29).

## Implementation

### Target file

`scripts/agent/commands/registry.py`

### Procedure

1. Delete `from shared import plugin_registry` (line 37).
2. Delete `from agent.commands.cmd_plugins import _PluginsMixin` (line 46).
3. Delete `_PluginsMixin,` from `CommandRegistry`'s base-class list (line 71).
4. In `dispatch()`, replace:
   ```python
   # Plugin commands: exact-match and prefix-match (checked after built-ins)
   return await self._dispatch_plugin(line)
   ```
   with:
   ```python
   return False
   ```
5. Delete the entire `_dispatch_plugin()` method (the `async def _dispatch_plugin(self, line: str) -> bool:` block through its final `return False`).
6. Update the module docstring:
   - Remove the `cmd_plugins.py    — _PluginsMixin:    /plugin` line from the "Mixins" table.
   - Remove `_dispatch_plugin()` from the "This module owns: dispatch behavior (dispatch(), _get_handler(), _dispatch_plugin())" sentence, e.g. reword to "dispatch behavior (dispatch(), _get_handler())".

### Method

Direct deletions only — no new logic, per plan Assumption 7. This is a pure subtraction from a single file.

### Details

- Do not touch `command_defs_list.py`'s `/plugin` entry here — separate doc, separate commit-sized unit, but must land in the same overall change before step 2's file deletions for the tree to keep importing cleanly at every commit boundary (per the plan's own "Design" section on deletion ordering).
- `CommandRegistry.__init__`'s fail-fast handler validation (loops over `_COMMANDS`) is unaffected — it doesn't reference `_PluginsMixin` directly, only `_COMMANDS` entries' `.handler` strings, which is `command_defs_list.py`'s concern.
- Existing tests (`tests/test_command_registry_dispatch.py`, `tests/test_dispatch_plugin_boundary.py`) are handled by the already-completed `plugin_test_files_removal` doc — do not edit test files from this doc.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| No plugin references remain in this file | `grep -n "plugin\|Plugin" scripts/agent/commands/registry.py` | 0 matches |
| Syntax/lint | `uv run ruff check scripts/agent/commands/registry.py` | 0 errors |
| Type check | `uv run mypy scripts/agent/commands/registry.py` | no new errors |
| Targeted tests (expect failures here until step-2/step-6 docs also land — see Details) | `uv run pytest tests/test_command_registry_dispatch.py -v` | pass once `cmd_plugins.py`/plugin tests are also removed per the test-removal doc |
