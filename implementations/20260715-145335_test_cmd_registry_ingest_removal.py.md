# Implementation Procedure: test_cmd_registry_ingest_removal.py

## Goal

Update `test_export_still_registered` to instead assert that `/export` is **absent**
as a standalone `CommandDef` and that `/session`'s `CommandDef` help text mentions
`export`, reflecting that `/export` has been folded into `/session`.

## Scope

### In scope
- Rewrite `test_export_still_registered` (current lines 25-29).

### Out of scope
- `TestIngestRagCommandsRemoved.test_ingest_not_in_built_in_commands` (lines 13-18) —
  unchanged, `/ingest` remains removed (unrelated to this plan).
- `test_rag_not_in_built_in_commands` (lines 20-23) — unchanged, `/rag` remains
  removed (unrelated to this plan).
- `test_compact_still_registered` (lines 31-34) — unchanged, `/compact` is untouched
  by this plan.
- The module docstring (lines 1-5) — should be updated for accuracy (see Details)
  since it currently says "`/export`, `/compact`, and `/mdq` remain functional",
  which is no longer accurate for `/export` as a standalone command.

## Assumptions

- `_COMMANDS` (imported from `agent.commands.registry`, which re-exports it from
  `command_defs_list.py`) is the correct thing to assert against — verified: this
  test file's only import is `from agent.commands.registry import _COMMANDS`, and
  `registry.py` imports `_COMMANDS` from `command_defs_list.py` (so this indirection
  already exists and is unaffected by this plan).

## Implementation

### Target file

`tests/test_cmd_registry_ingest_removal.py`

### Procedure

1. Replace the class name and body from:
   ```python
   def test_export_still_registered(self) -> None:
       """Verify /export is still in the built-in command registry."""
       export_cmds = [c for c in _COMMANDS if c.name == "/export"]
       assert len(export_cmds) == 1, "/export should still be registered"
       assert export_cmds[0].prefix is True
   ```
   to:
   ```python
   def test_export_not_registered_as_standalone(self) -> None:
       """Verify /export is no longer a standalone command (folded into /session)."""
       export_cmds = [c for c in _COMMANDS if c.name == "/export"]
       assert len(export_cmds) == 0, (
           "/export should not be registered as a standalone command"
       )

   def test_session_help_mentions_export(self) -> None:
       """Verify /session's CommandDef help text documents the export subcommand."""
       session_cmds = [c for c in _COMMANDS if c.name == "/session"]
       assert len(session_cmds) == 1, "/session should be registered"
       assert "export" in session_cmds[0].help
   ```
2. Update the module docstring (lines 1-5) to:
   ```python
   """tests/test_cmd_registry_ingest_removal.py

   Tests that the removed `/ingest`, `/rag`, and standalone `/export` commands are
   no longer dispatched, while `/compact` and `/mdq` remain functional and `/export`
   is documented as a `/session` subcommand.
   """
   ```
3. Consider renaming the class `TestIngestRagCommandsRemoved` to something broader
   (e.g. `TestRemovedAndRelocatedCommands`) since it now covers a relocation, not
   just removals — optional, not required by acceptance criteria; keep the existing
   name if minimizing diff is preferred.

### Method

Targeted rewrite of one test function (split into two, for clarity: "gone as
standalone" and "documented under /session"), plus a docstring correction.

### Details

- This test's pass/fail state directly encodes the acceptance criterion "`/export`
  ... no longer exist[s] as [a] command[]" from the plan's Goal section — keep it
  precise rather than merging both assertions into one test function, so a future
  regression in either direction (re-adding standalone `/export`, or losing the
  `/session` help text) is independently diagnosable.

## Validation plan

- `uv run pytest tests/test_cmd_registry_ingest_removal.py -v` — all 5 tests pass
  (2 unchanged: ingest/rag removed; 1 unchanged: compact still registered; 2 new/
  rewritten: export not standalone + session help mentions export).
- This test file's pass depends on `command_defs_list.py`'s edits landing first (the
  `/export` entry removal and `/session` help-text extension) — sequence accordingly.
- `uv run pytest tests/test_command_def_sync.py -v` — cross-check for consistency
  (no duplicate/missing `CommandDef` names).
