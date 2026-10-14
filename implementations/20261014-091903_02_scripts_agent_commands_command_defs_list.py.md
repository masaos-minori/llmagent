## Goal

Remove the `/skill` entry from the command definition table (REQ-001: remove the command).

## Scope

- Delete one `CommandDef` block. Only the `/skill` block (lines 164-170); other commands are untouched.

## Assumptions

- Plan `plans/20261014-091322_plan.md` is `Frozen`; this file is one of its `Implementation Target Files` rows.
- Source line numbers were verified in this cycle against the current tree and may shift; locate edits by symbol or test name.

## Design decisions

- `_COMMANDS` is the single source for dispatch, completion, and `/help`; removing the block removes the command everywhere.
- Keep the `# ── Prefix async` comment that follows the block.

## Alternatives considered

N/A: deletion is the decided direction (Plan Design)

## Implementation

### Target file

`scripts/agent/commands/command_defs_list.py`

### Procedure

Delete the `CommandDef(...)` block whose `name="/skill"` (handler `_cmd_skill`, help text mentioning `skills/<name>/SKILL.md`).

### Method

Locate with `rg -n '/skill' scripts/agent/commands/command_defs_list.py`; remove from `CommandDef(` through its closing `),`.

### Details

`tests/agent/commands/test_command_def_sync.py` requires every `handler` to exist on the registry, so this edit and procedure 03 must land together.

## Compatibility considerations

Removes `/skill` from tab completion and `/help` output.

## Security considerations

N/A: removal only; no new input path

## Rollback considerations

N/A: revert the commit; apply procedures 01-06 and 07-11 as one commit unit

## Validation plan

- `uv run pytest tests/agent/commands/test_command_def_sync.py tests/agent/commands/test_command_defs.py -q` passes.
- `rg -n '_cmd_skill|"/skill"' scripts` has no match.

## Completion criteria

- `_COMMANDS` contains no `/skill` entry.
- The sync tests pass.

## Out of scope

- Other `CommandDef` entries and help wording.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Delete the CommandDef block | Pending | — | — | |
| 2 | Run the tests that cover this file (updated by procedures 07-11) | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Source issue**: issues/20261014-090429_skill001_remove-the-skill-slash-command-and-its-ephemeral-plumbing.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261014-091322_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261014-091903
- **Related target files**: scripts/agent/commands/command_defs_list.py
