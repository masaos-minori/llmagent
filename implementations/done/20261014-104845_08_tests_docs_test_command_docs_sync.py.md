## Goal

Remove the `/mdq` registration test from the docs-sync tests (REQ-002: update tests).

## Scope

- Delete one test method. Lines 119-122 only; keep `mdq` in the scan regex at line 41.

## Assumptions

- Plan `plans/20261014-100930_plan.md` is `Frozen`; this file is one of its `Implementation Target Files` rows.
- Source line numbers were verified in this cycle against the current tree and may shift; locate edits by symbol or test name.

## Design decisions

- Keeping `mdq` in the regex means a `/mdq` mention in a scanned doc (agent_01, agent_07_01 to agent_07_10) fails `test_active_docs_match_registered_commands`, which is a useful guard.
- Delete `test_mdq_commands_in_registry`; do not invert it (the unregistered check lives in `test_removed_commands.py`, procedure 11).

## Alternatives considered

N/A: deletion is the decided direction (Plan Design)

## Implementation

### Target file

`tests/docs/test_command_docs_sync.py`

### Procedure

Delete the `test_mdq_commands_in_registry` method.

### Method

Edit by test name.

### Details

No other test in the file refers to `/mdq`.

## Compatibility considerations

N/A: test-only change

## Security considerations

N/A: test-only change

## Rollback considerations

N/A: revert the commit

## Validation plan

- `uv run pytest tests/docs/test_command_docs_sync.py -q` passes after procedure 19.
- `rg -n '/mdq' tests/docs/test_command_docs_sync.py` has no match.

## Completion criteria

- The test is gone and the regex line is unchanged.

## Out of scope

- The scan regex and the other command tests.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Delete the test | Completed | 20261014-110318 | 20261014-110318 |  |
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
- **Requirement ID**: REQ-002
- **Source issue**: issues/20261014-095505_mdq001_remove-the-mdq-slash-command.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261014-100930_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261014-104845
- **Related target files**: tests/docs/test_command_docs_sync.py