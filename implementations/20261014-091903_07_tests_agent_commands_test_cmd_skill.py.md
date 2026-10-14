## Goal

Delete the `/skill` command tests (REQ-003: update tests).

## Scope

- Delete the file. Only this test file.

## Assumptions

- Plan `plans/20261014-091322_plan.md` is `Frozen`; this file is one of its `Implementation Target Files` rows.
- Source line numbers were verified in this cycle against the current tree and may shift; locate edits by symbol or test name.

## Design decisions

- The whole file tests the removed command (25 matches, imports `agent.commands.cmd_skill`).

## Alternatives considered

N/A: deletion is the decided direction (Plan Design)

## Implementation

### Target file

`tests/agent/commands/test_cmd_skill.py`

### Procedure

Delete `tests/agent/commands/test_cmd_skill.py` with `git rm`.

### Method

No edit.

### Details

The replacement guard is the new test in procedure 11.

## Compatibility considerations

N/A: test-only change

## Security considerations

N/A: test-only change

## Rollback considerations

N/A: revert the commit

## Validation plan

- `uv run pytest tests/agent/commands/ -q` passes with no collection error.

## Completion criteria

- The file does not exist.
- No test imports `cmd_skill`.

## Out of scope

- Other test files.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Delete the file | Pending | — | — | |
| 2 | Run the affected tests | Pending | — | — | |
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
- **Requirement ID**: REQ-003
- **Source issue**: issues/20261014-090429_skill001_remove-the-skill-slash-command-and-its-ephemeral-plumbing.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261014-091322_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261014-091903
- **Related target files**: tests/agent/commands/test_cmd_skill.py
