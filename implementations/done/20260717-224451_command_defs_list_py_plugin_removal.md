# Implementation: scripts/agent/commands/command_defs_list.py (remove /plugin CommandDef)

Source plan: `plans/done/20260717-123416_plan.md` (Implementation step 1, item 5)

Gap-filling note: see `implementations/20260717-224311_registry_py_plugin_removal.md`
for why this doc exists. This doc and its 4 siblings must all land BEFORE
`cmd_plugins.py` is deleted (step 2).

## Goal

`_COMMANDS` (the single source of truth for all built-in slash commands) no
longer lists `/plugin` — the command is fully unregistered, matching
`registry.py`'s removal of `_dispatch_plugin()` in the sibling doc.

## Scope

**In scope**
- `scripts/agent/commands/command_defs_list.py`: delete the `/plugin` `CommandDef(...)` entry (lines 141-147).

**Out of scope**
- Deleting `cmd_plugins.py` (the `_cmd_plugin` handler implementation) — step 2 (separate doc, must run after this one).
- Any other `CommandDef` entry — unaffected; this is a single-entry deletion from a list.
- `registry.py`'s `_PluginsMixin`/`_dispatch_plugin()` removal — sibling doc (`registry_py_plugin_removal.md`), not this one.

## Assumptions

1. Confirmed by direct read (2026-07-17): the `/plugin` entry is:
   ```python
   CommandDef(
       "/plugin",
       True,
       False,
       "_cmd_plugin",
       "status  Show plugin load results (loaded, failed, conflicts)",
   ),
   ```
   at lines 141-147, positioned between the `/reject` entry and the `/skill` entry in the prefix-commands section of `_COMMANDS`.
2. `CommandRegistry.__init__`'s fail-fast handler validation (`for _cmd in _COMMANDS: if not hasattr(self, _cmd.handler): raise AttributeError(...)`) only iterates `_COMMANDS` — once the `/plugin` entry is gone, it will no longer check for a `_cmd_plugin` handler, so deleting `cmd_plugins.py` in step 2 (which removes `_cmd_plugin`) cannot trigger this fail-fast check as long as this doc's removal lands first (confirms the ordering requirement already stated in the plan's Design section).
3. `agent/repl.py`'s `SLASH_COMMANDS`/`completion_command_names()` (tab-completion) derive from `_COMMANDS` (per `builtin_command_names()`), so removing this entry automatically removes `/plugin` from tab completion too — no separate change needed there (confirmed by direct read of `agent/repl.py`'s `builtin_command_names()` in an earlier, unrelated session task; re-verify this still holds at implementation time since `repl.py` is a file other work has touched recently).

## Implementation

### Target file

`scripts/agent/commands/command_defs_list.py`

### Procedure

1. Delete the entire `/plugin` `CommandDef(...)` entry, lines 141-147:
   ```python
   CommandDef(
       "/plugin",
       True,
       False,
       "_cmd_plugin",
       "status  Show plugin load results (loaded, failed, conflicts)",
   ),
   ```
2. Confirm the surrounding list still parses correctly (the preceding `/reject` entry's trailing comma and the following `/skill` entry are unaffected by removing the entry between them).

### Method

Single-entry deletion from a list literal — no other code change needed in this file.

### Details

- Do not touch any other `CommandDef` entry.
- After this change, `docs/05_agent_01_system-overview.md`'s "Slash Command Categories" table and `docs/05_agent_07_*` slash-command reference docs will need their `/plugin` rows removed too — that is the existing `plugin_documentation_removal` doc's job (already completed per the task list), not this one; if that doc already ran before this one, double-check it didn't leave a `/plugin` doc row referencing a command this doc is only now removing from code (re-verify docs are still consistent after this lands, since doc-then-code ordering matters less here but should still be checked).

## Validation plan

| Check | Command | Expected |
|---|---|---|
| No `/plugin` CommandDef remains | `grep -n '"/plugin"' scripts/agent/commands/command_defs_list.py` | 0 matches |
| Syntax/lint | `uv run ruff check scripts/agent/commands/command_defs_list.py` | 0 errors |
| Type check | `uv run mypy scripts/agent/commands/command_defs_list.py` | no new errors |
| Targeted tests (expect some failures until step-2/step-6 docs also land) | `uv run pytest tests/test_command_registry_dispatch.py tests/docs/test_command_docs_sync.py -v` | pass once plugin-specific test/doc entries are also removed |
