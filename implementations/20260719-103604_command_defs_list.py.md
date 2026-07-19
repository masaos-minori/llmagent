## Goal

Keep the `/session` `CommandDef`'s help text in sync with the new `rag-rebuild-fts` subcommand added
to `_cmd_session` (paired doc: `implementations/20260719-103526_cmd_session.py.md`), so `/help`
output does not silently omit it.

**Builds on prior doc**: `implementations/20260719-103003_command_defs_list.py.md` already specifies
appending `|rag-consistency` to the `/session` `CommandDef`'s help string. This document assumes that
change is already applied and appends `|rag-rebuild-fts` after it — it does not repeat the
`rag-consistency` change.

## Scope

**In scope**
- Update the `/session` `CommandDef` entry's help text in
  `scripts/agent/commands/command_defs_list.py` to append `rag-rebuild-fts` to the subcommand list
  (after `rag-consistency`, once that is present per the prior doc).

**Out of scope**
- The `rag-consistency` addition itself — already covered by
  `implementations/20260719-103003_command_defs_list.py.md`; not repeated here. If, at implementation
  time, that prior doc has not yet been applied, the implementer must apply it first.
- Adding a `SubcommandSpec` entry — not used by any `CommandDef` in this file today (verified:
  `grep -n "SubcommandSpec" scripts/agent/commands/command_defs_list.py` returns only a docstring
  reference at line 12; all 21 `CommandDef(...)` calls use positional arguments and the dataclass
  default empty `subcommands` list). This plan does not introduce that pattern.
- Any change to `tests/test_command_def_sync.py` — re-verified below (Assumption 2); the sibling
  plan's cycle already confirmed this suite has no hard-coded `/session` help-string assertions, and
  re-checking now shows no new assertions were added since.
- Any other `CommandDef` entry in this file.

## Assumptions

1. Current actual file state, verified by direct grep/read of
   `scripts/agent/commands/command_defs_list.py`: the `/session` `CommandDef` entry is at lines 77-84
   (pre-091140-landing baseline):
   ```
   77:    CommandDef(
   78:        "/session",
   79:        True,
   80:        False,
   81:        "_cmd_session",
   82:        "list [n] | load <id> | rename <title> | delete <id>"
   83:        " | export markdown|json [file] | stats|health|checkpoint|vacuum|purge|recover",
   84:    ),
   ```
   Positional argument order per `CommandDef`'s dataclass field order (`command_defs.py:31-40`):
   `name, prefix, is_async, handler, help`. There is no `help=` keyword — the fifth positional string
   (built from two adjacent literals, lines 82-83) is the field to edit.
   Once `implementations/20260719-103003_command_defs_list.py.md` lands, line 83's literal will read
   `" | export markdown|json [file] | stats|health|checkpoint|vacuum|purge|recover|rag-consistency"`.
   This doc's edit is written against that post-landing string, not the pre-landing one quoted above.
2. Re-confirmed via `grep -n "stats|health|checkpoint" tests/test_command_def_sync.py`: no match
   (current file state, verified independently in this cycle). This file's assertions verify only
   that help text is non-empty and command names appear in `/help` output (per its own docstring and
   test names), not literal subcommand-list contents. No change to this test file is required for
   this doc either, matching the prior doc's Assumption 2 for the `rag-consistency` addition.
3. `_COMMANDS` (`command_defs_list.py:26`) is a `list[CommandDef]`, not a dict — consistent with the
   prior doc's Assumption 3; irrelevant to this doc's single string-literal edit but recorded for
   consistency with the paired cycle's documentation.

## Implementation

### Target file

`scripts/agent/commands/command_defs_list.py`.

### Procedure

Performed *after* `implementations/20260719-103003_command_defs_list.py.md`'s `|rag-consistency`
change is applied:

1. Locate the `/session` `CommandDef` entry's help string (last positional argument).
2. Append `|rag-rebuild-fts` after `rag-consistency`:
   ```python
   CommandDef(
       "/session",
       True,
       False,
       "_cmd_session",
       "list [n] | load <id> | rename <title> | delete <id>"
       " | export markdown|json [file] | stats|health|checkpoint|vacuum|purge|recover"
       "|rag-consistency|rag-rebuild-fts",
   ),
   ```
   (Exact line-wrapping of the concatenated string literals is left to `ruff format`, matching the
   prior doc's note — no manual pre-wrapping required.)
3. Run `uv run ruff format scripts/agent/commands/command_defs_list.py` and
   `uv run ruff check scripts/agent/commands/command_defs_list.py --fix`.
4. Re-run `grep -n "stats|health|checkpoint" tests/test_command_def_sync.py` once more after the edit
   as a final confirmation that no hard-coded assertion was introduced since Assumption 2 was checked.

### Method

Single string-literal edit inside an existing `CommandDef(...)` positional-argument call, appended
after the sibling plan's own edit to the same field. No new abstractions, no data-structure changes.

### Details

No new types, no signature changes. The edit is scoped to one field (the help text) of one
`CommandDef` instance in a module-level list literal.

## Validation plan

| Check | Command | Target |
|---|---|---|
| Format/lint | `uv run ruff format scripts/agent/commands/command_defs_list.py && uv run ruff check scripts/agent/commands/command_defs_list.py` | 0 errors |
| Type check | `uv run mypy scripts/agent/commands/command_defs_list.py` | 0 new errors vs. baseline |
| Help text contains new subcommand | `rg -n "rag-rebuild-fts" scripts/agent/commands/command_defs_list.py` | 1 match, inside the `/session` `CommandDef` help string |
| Both RAG subcommands present | `rg -n "rag-consistency\|rag-rebuild-fts" scripts/agent/commands/command_defs_list.py` | 2 matches, same help string, no duplication |
| Command-def sync suite | `uv run pytest tests/test_command_def_sync.py -v` | all pass (no assertion depends on the literal subcommand list) |
| No `SubcommandSpec` regression | `grep -n "SubcommandSpec" scripts/agent/commands/command_defs_list.py` | still only the line-12 docstring reference |
| Full command-registry smoke test | `uv run pytest tests/test_agent_cmd_session.py -v` | all pass (dispatch defined in `cmd_session.py`, unaffected by this help-text-only change) |
