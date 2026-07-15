# Implementation Procedure: command_defs_list.py

## Goal

Remove the `/set`, `/db`, and standalone `/export` `CommandDef` entries from
`_COMMANDS` (the single source of truth for slash-command dispatch/help/tab-completion),
and extend the existing `/session` `CommandDef`'s help text so it documents the
subcommands moved onto it (`export`, `stats`, `health`, `checkpoint`, `vacuum`,
`purge`, `recover`).

## Scope

### In scope
- Delete the `CommandDef("/db", ...)` entry (current lines 112-118).
- Delete the `CommandDef("/set", ...)` entry (current lines 119-125).
- Delete the `CommandDef("/export", ...)` entry (current lines 91-97).
- Extend `CommandDef("/session", ...)`'s help string (current lines 77-83).

### Out of scope
- `CommandDef` dataclass definition itself (`agent.commands.command_defs`) — unchanged.
- Any other entry in `_COMMANDS` (e.g. `/compact`, `/memory`, `/mdq`).
- `AgentREPL.SLASH_COMMANDS` in `repl.py` — it is a `cached_property` derived from
  `_COMMANDS` via `completion_command_names()` (verified: `scripts/agent/repl.py:81-84`
  calls `completion_command_names()` → `builtin_command_names() | reserved_repl_command_names()`,
  and `builtin_command_names()` returns `frozenset(cmd.name for cmd in _COMMANDS)`).
  Removing entries here is therefore sufficient; no separate edit to `repl.py` is needed.

## Assumptions

- Since `SLASH_COMMANDS` is already a derived `cached_property` (not the plain hardcoded
  list the plan's Assumption 1 describes as the "before" state), the plan's contingent
  fallback ("skip the manual list edit... it will already reflect the `_COMMANDS` changes")
  applies: no `repl.py` edit is required as a consequence of this file's changes.
- No other module imports `CommandDef("/db", ...)` / `CommandDef("/set", ...)` /
  `CommandDef("/export", ...)` by reference (they are consumed only via the `_COMMANDS` list
  itself, iterated in `registry.py` and `repl.py`).

## Implementation

### Target file

`scripts/agent/commands/command_defs_list.py`

### Procedure

1. Delete the `/db` `CommandDef` block (currently lines 112-118):
   ```python
   CommandDef(
       "/db",
       True,
       True,
       "_cmd_db",
       "rag stats|urls|clean|rebuild-fts|vec-rebuild|reconcile-url|recover|consistency; session stats|health|checkpoint|vacuum|purge|recover",
   ),
   ```
2. Delete the `/set` `CommandDef` block (currently lines 119-125):
   ```python
   CommandDef(
       "/set",
       True,
       False,
       "_cmd_set",
       "temperature <f> | max_tokens <n>  Set LLM generation parameters",
   ),
   ```
3. Delete the standalone `/export` `CommandDef` block (currently lines 91-97):
   ```python
   CommandDef(
       "/export",
       True,
       False,
       "_cmd_export",
       "[md|json] [file]  Export conversation history (default: md to stdout)",
   ),
   ```
4. Replace the `/session` `CommandDef`'s help string (currently lines 77-83) from:
   ```python
   CommandDef(
       "/session",
       True,
       False,
       "_cmd_session",
       "list [n] | load <id> | rename <title> | delete <id>",
   ),
   ```
   to:
   ```python
   CommandDef(
       "/session",
       True,
       False,
       "_cmd_session",
       "list [n] | load <id> | rename <title> | delete <id>"
       " | export markdown|json [file] | stats|health|checkpoint|vacuum|purge|recover",
   ),
   ```
   (Split across two adjacent string literals — implicit concatenation — to stay
   within the 120-char line limit; `ruff format` will normalize wrapping.)

### Method

Direct text edit of the `_COMMANDS` list literal. No other files are touched by this
step; downstream consumers (`registry.py`'s `_get_handler`/`dispatch`, `repl.py`'s
`SLASH_COMMANDS`, `/help` output in `registry.py::_cmd_help`) all iterate `_COMMANDS`
and require no code change themselves, only the removal of the handler methods they
would otherwise reference (`_cmd_db`, `_cmd_set`, `_cmd_export` — removed in the
`cmd_db.py`, `cmd_config_set.py`, `cmd_rag_export.py` implementation steps).

### Details

- Order of edits does not matter functionally, but do this file first in the overall
  sequence (Phase 1) since `registry.py`'s fail-fast `__init__` check
  (`if not hasattr(self, _cmd.handler): raise AttributeError`) will fail at import/test
  time if a `CommandDef` still references a handler that has been deleted from its
  mixin. Coordinate so this file's edit and the corresponding mixin deletions land
  together (same commit) to avoid a broken intermediate state.
- Do not rename `_cmd_session`'s handler string — it stays `"_cmd_session"`; only the
  help text changes.

## Validation plan

- `uv run pytest tests/test_command_def_sync.py -v` — `test_every_commanddef_has_handler`,
  `test_commanddef_names_are_unique`, `test_commanddef_handlers_are_unique`,
  `test_all_commands_have_nonempty_help`, `test_all_command_names_start_with_slash` all pass.
- `uv run pytest tests/test_cmd_registry_ingest_removal.py -v` — update
  `test_export_still_registered` first (see its own implementation doc) so it now
  asserts `/export` is **absent** as a standalone entry; `test_compact_still_registered`
  must remain green (untouched).
- `grep -n '"/set"\|"/db"' scripts/agent/commands/command_defs_list.py` returns no matches
  after the edit.
- `uv run pytest tests/ -k "command_def or registry" -v` — no new failures.
- Manual: `/help` in a running REPL no longer lists `/set`, `/db`, or a standalone `/export`
  row; `/session`'s help row shows the extended text.
