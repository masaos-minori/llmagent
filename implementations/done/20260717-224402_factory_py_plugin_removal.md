# Implementation: scripts/agent/factory.py (remove plugin loading at startup)

Source plan: `plans/done/20260717-123416_plan.md` (Implementation step 1, item 3)

Gap-filling note: see `implementations/20260717-224311_registry_py_plugin_removal.md`
for why this doc exists. This doc and its 4 siblings must all land BEFORE
`plugin_registry.py` is deleted (step 2).

## Goal

`build_agent_context()` no longer loads or registers plugins at startup;
`_init_plugin_registry()` and its call site are removed entirely.

## Scope

**In scope**
- `scripts/agent/factory.py`: delete the `_init_plugin_registry()` function (lines 404-465) and its sole call site `_init_plugin_registry(ctx, audit_logger)` at the end of `build_agent_context()` (line 502). Also delete the now-unused `from shared import plugin_registry` import (line 18) — confirmed no other function in this file references `plugin_registry`.

**Out of scope**
- Deleting `plugin_registry.py` itself — step 2 (separate doc, must run after this one).
- `build_agent_context()`'s other service-construction calls (`_build_audit_logger`, `_build_llm_client`, `_build_tool_executor`, `_build_history_manager`, `_build_memory_services`, `RepositoryGateway`, `AppServices` construction) — unaffected; only the trailing `_init_plugin_registry(ctx, audit_logger)` line at the very end of the function is removed.
- `ctx.cfg.tool.plugin_tool_override`/`plugin_strict` field removal — that's step 3 (`config_dataclasses.py`, separate doc); this doc only removes the *reads* of those fields inside `_init_plugin_registry()`, which happens automatically since the whole function is deleted.

## Assumptions

1. Confirmed by direct read (2026-07-17): `_init_plugin_registry()` spans lines 404-465 exactly (from `def _init_plugin_registry(ctx: AgentContext, audit_logger: Logger) -> None:` through its closing `)` after the final `audit_logger.info(...)` call); its sole call site is `_init_plugin_registry(ctx, audit_logger)` at line 502, the last statement in `build_agent_context()`.
2. `from shared import plugin_registry` (line 18) has no other use in this file — `_init_plugin_registry()`'s body is the only place `plugin_registry.register_builtin_commands()`/`plugin_registry.load_plugins()` are called; confirmed via `grep -n "plugin_registry" scripts/agent/factory.py`.
3. `build_agent_context()`'s return type is `None` and `_init_plugin_registry()`'s return type is also `None` with no side-effect on `ctx.services` (it works entirely through its own local `plugin_registry` module-level state) — deleting the call site does not require adjusting `build_agent_context()`'s signature, return value, or any other line in that function.
4. `Path`, `logging`, `sys` imports (used inside `_init_plugin_registry()` for `plugin_dir`, stdout-handler wiring, and the plugin logger) may become unused after this function is deleted — verify with `ruff check` after the edit (Details below) rather than assuming which specific imports are now dead, since `Path`/`logging`/`sys` are commonly used elsewhere in a file this size too.

## Implementation

### Target file

`scripts/agent/factory.py`

### Procedure

1. Delete `from shared import plugin_registry` (line 18).
2. Delete the entire `_init_plugin_registry()` function, lines 404-465 (from `def _init_plugin_registry(ctx: AgentContext, audit_logger: Logger) -> None:` through the closing of its trailing `audit_logger.info(...)` call).
3. Delete `_init_plugin_registry(ctx, audit_logger)` (line 502), the last line inside `build_agent_context()`'s body, leaving `AppServices(...)` construction as the function's final statement.
4. Run `uv run ruff check scripts/agent/factory.py --select F401` (or the full lint pass) to catch any now-unused import (e.g. if `Path`, `logging`, or `sys` were only used by the deleted function) and remove only what ruff flags as unused — do not remove any import still used elsewhere in the file.

### Method

Direct deletions. `build_agent_context()` needs no other change — it simply stops calling the now-deleted function.

### Details

- This file has high churn (27 commits/30d per the plan's Affected areas) — rebase immediately before landing and re-verify line numbers against the current file state before editing.
- Do not remove `from agent.commands.command_defs_list import _COMMANDS` if it appears elsewhere in this file for a non-plugin reason — the deleted function's local `from agent.commands.command_defs_list import _COMMANDS` (line 436, inside `_init_plugin_registry()`) is a function-local import and disappears along with the function; check whether the file also has a module-level import of the same name used elsewhere before assuming it's fully gone.
- Test file changes (`test_agent_factory.py`) are the existing `plugin_test_files_removal` doc's job — do not edit it here.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| No plugin references remain in this file | `grep -n "plugin\|Plugin" scripts/agent/factory.py` | 0 matches |
| No unused imports | `uv run ruff check scripts/agent/factory.py` | 0 errors (including F401) |
| Type check | `uv run mypy scripts/agent/factory.py` | no new errors |
| Targeted tests (expect some failures until step-2/step-6 docs also land) | `uv run pytest tests/test_agent_factory.py -v` | pass once plugin-specific test cases are also removed per the test-removal doc |
