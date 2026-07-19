## Goal

Keep the `/session` `CommandDef`'s help text in sync with the new `rag-consistency` subcommand added
to `_cmd_session` (paired doc: `implementations/20260719-102923_cmd_session.py.md`), so `/help`
output does not silently omit the new subcommand.

## Scope

**In scope**
- Update the `/session` `CommandDef` entry's help text in
  `scripts/agent/commands/command_defs_list.py` to append `rag-consistency` to the existing
  `stats|health|checkpoint|vacuum|purge|recover` subcommand list.

**Out of scope**
- Adding a `SubcommandSpec` entry — not used by any existing `CommandDef` in this file (see
  Assumption 1); this plan does not introduce that pattern for `/session`.
- Any change to `tests/test_command_def_sync.py` — investigated and confirmed unnecessary (see
  Assumption 2); this was a conditional step in the plan ("only if needed") that resolved to "not
  needed."
- Any change to any other `CommandDef` entry in this file.

## Assumptions

1. Confirmed by direct grep (`grep -n "SubcommandSpec" scripts/agent/commands/command_defs_list.py`):
   the only match in the whole file is a docstring reference at line 12
   (`CommandDef / SubcommandSpec dataclasses — defined in agent.commands.command_defs.`), not actual
   code usage. All 21 `CommandDef(...)` calls in this file use positional arguments and rely on the
   dataclass default `subcommands: list[SubcommandSpec] = field(default_factory=list)`
   (`scripts/agent/commands/command_defs.py:40`) — none passes a `subcommands=` argument. This
   confirms the plan's Assumption 3 exactly: only the free-text help string needs updating.
2. The plan's Implementation step 3 says "Update `test_command_def_sync.py`-adjacent expectations
   only if that suite's `/help` text assertions hard-code the old `/session` help string (check via
   `grep -n "stats|health|checkpoint" tests/test_command_def_sync.py` before assuming no change is
   needed)." That grep was run during this doc's investigation and returned **no matches** — the
   test file does not hard-code the `/session` help string or its subcommand list anywhere. Its
   assertions (per its module docstring and `test_help_output_mentions_all_command_names`,
   `test_all_commands_have_nonempty_help`, handler-existence checks) only verify that help text is
   non-empty and that command names appear in `/help` output, not the literal subcommand-list
   contents. **Conclusion: no change to `tests/test_command_def_sync.py` is required.** This is
   noted explicitly here per this workflow's stale-plan-detail rule, since the plan left this as a
   conditional to verify rather than a certain action.
3. `_COMMANDS` (`command_defs_list.py:26`) is declared as `_COMMANDS: list[CommandDef] = [...]` — a
   **list**, not a dict. The plan's Implementation Steps text and the paired
   `test_agent_cmd_session.py`/hint-regression-test doc's plan text refer to "`_COMMANDS`" generically
   without specifying list vs. dict; this doc records the verified actual type for anyone writing
   code against it later (relevant to the separate hint-regression-test procedure, which iterates
   `_COMMANDS` to check command names, not dict keys).
4. The `/session` `CommandDef` entry (`command_defs_list.py:77-84`) uses **positional** arguments in
   the order `name, prefix, is_async, handler, help` (per the dataclass field order in
   `scripts/agent/commands/command_defs.py:31-40`), not keyword arguments. There is no `help=` kwarg
   to search for or edit by name — the fifth positional argument (built from two adjacent string
   literals via implicit concatenation, spanning lines 82-83) is the help text to change.

## Implementation

### Target file

`scripts/agent/commands/command_defs_list.py`.

### Procedure

1. Locate the `/session` `CommandDef` entry at lines 77-84:
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
2. Edit the last string literal (line 83) to append `|rag-consistency` after `recover`:
   ```python
       CommandDef(
           "/session",
           True,
           False,
           "_cmd_session",
           "list [n] | load <id> | rename <title> | delete <id>"
           " | export markdown|json [file] | stats|health|checkpoint|vacuum|purge|recover|rag-consistency",
       ),
   ```
   (Verify the resulting line does not exceed the 120-char line-length limit from `rules/coding.md`
   after `ruff format` — if it does, `ruff format` will re-wrap the string concatenation
   automatically since it is already split across two literals; no manual wrapping is required
   ahead of time.)
3. Run `uv run ruff format scripts/agent/commands/command_defs_list.py` and
   `uv run ruff check scripts/agent/commands/command_defs_list.py --fix`.
4. Per Assumption 2, do not modify `tests/test_command_def_sync.py` — re-run its grep check once
   more after the edit as a final confirmation (`grep -n "stats|health|checkpoint"
   tests/test_command_def_sync.py`) to catch any change in that file since this doc was written.

### Method

Single string-literal edit inside an existing `CommandDef(...)` positional-argument call. No new
abstractions, no data-structure changes.

### Details

No new types, no signature changes. The edit is scoped to one field (the help text) of one
`CommandDef` instance in a module-level list literal.

## Validation plan

| Check | Command | Target |
|---|---|---|
| Format/lint | `uv run ruff format scripts/agent/commands/command_defs_list.py && uv run ruff check scripts/agent/commands/command_defs_list.py` | 0 errors |
| Type check | `uv run mypy scripts/agent/commands/command_defs_list.py` | 0 new errors vs. baseline |
| Help text contains new subcommand | `rg -n "rag-consistency" scripts/agent/commands/command_defs_list.py` | 1 match, inside the `/session` `CommandDef` help string |
| Command-def sync suite | `uv run pytest tests/test_command_def_sync.py -v` | all pass (confirmed no assertion depends on the literal subcommand list; re-run to reconfirm after edit) |
| No `SubcommandSpec` regression | `grep -n "SubcommandSpec" scripts/agent/commands/command_defs_list.py` | still only the line-12 docstring reference — no new `subcommands=` usage introduced |
| Full command-registry smoke test | `uv run pytest tests/test_agent_cmd_session.py -v` | all pass (dispatch itself is defined in `cmd_session.py`, unaffected by this help-text-only change) |
