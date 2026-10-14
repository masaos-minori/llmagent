## Goal

Remove the `/mdq` entry from the command definition table (REQ-001: remove the command).

## Scope

- Delete one `CommandDef` block and the comment above it. Lines 164-171 only; the `/reject` entry before it stays.

## Assumptions

- Plan `plans/20261014-100930_plan.md` is `Frozen`; this file is one of its `Implementation Target Files` rows.
- Source line numbers were verified in this cycle against the current tree and may shift; locate edits by symbol or test name.

## Design decisions

- `_COMMANDS` is the single source for dispatch, completion, and `/help`; removing the block removes the command everywhere.
- The `# ── Prefix async` comment at line 164 heads only this entry, so remove it too; the list then ends after the `/reject` entry.

## Alternatives considered

N/A: deletion is the decided direction (Plan Design)

## Implementation

### Target file

`scripts/agent/commands/command_defs_list.py`

### Procedure

Delete the `# ── Prefix async` comment and the `CommandDef(...)` block whose `name="/mdq"` (handler `_cmd_mdq`).

### Method

Locate with `rg -n '/mdq|Prefix async' scripts/agent/commands/command_defs_list.py`; remove from the comment through the block's closing `),`, then run `uv run ruff format` on the file.

### Details

`tests/agent/commands/test_command_def_sync.py` requires every `handler` to exist on the registry, so this edit and procedure 03 must land together.

## Compatibility considerations

Removes `/mdq` from tab completion and `/help` output.

## Security considerations

N/A: removal only; no new input path

## Rollback considerations

N/A: removal only, applied as one commit unit with procedures 01-15 (revert the commit)

## Validation plan

- `uv run pytest tests/agent/commands/test_command_def_sync.py tests/agent/commands/test_command_defs.py -q` passes.
- `rg -n '_cmd_mdq|"/mdq"' scripts` has no match.

## Completion criteria

- `_COMMANDS` contains no `/mdq` entry.
- The sync tests pass.

## Out of scope

- Other `CommandDef` entries and help wording.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Delete the comment and CommandDef block | Completed | 20261014-110318 | 20261014-110318 |  |
| 2 | Run the tests that cover this file | Completed | 20261014-110318 | 20261014-110318 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261014-110318 | 20261014-110318 |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001
- **Source issue**: issues/20261014-095505_mdq001_remove-the-mdq-slash-command.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261014-100930_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261014-104845
- **Related target files**: scripts/agent/commands/command_defs_list.py