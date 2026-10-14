## Goal

Delete the cmd_mdq file-content test from the DB ownership tests (REQ-002: update tests).

## Scope

- Delete one test function. Lines 93-99 only; keep `test_no_unauthorized_mdq_db_access`.

## Assumptions

- Plan `plans/20261014-100930_plan.md` is `Frozen`; this file is one of its `Implementation Target Files` rows.
- Source line numbers were verified in this cycle against the current tree and may shift; locate edits by symbol or test name.

## Design decisions

- `test_cmd_mdq_no_direct_db_access` returns early when the file is absent, so after deletion it would pass vacuously; remove it.

## Alternatives considered

N/A: deletion is the decided direction (Plan Design)

## Implementation

### Target file

`tests/docs/test_db_ownership_boundaries.py`

### Procedure

Delete the `test_cmd_mdq_no_direct_db_access` function.

### Method

Edit by test name; check that `AGENT_DIR` stays used by the remaining tests.

### Details

The directory-wide scan test `test_no_unauthorized_mdq_db_access` still protects the agent code.

## Compatibility considerations

N/A: test-only change

## Security considerations

N/A: test-only change

## Rollback considerations

N/A: revert the commit

## Validation plan

- `uv run pytest tests/docs/test_db_ownership_boundaries.py -q` passes.
- `rg -n 'cmd_mdq' tests/docs/test_db_ownership_boundaries.py` has no match.

## Completion criteria

- The function is gone and the other tests pass.

## Out of scope

- Other ownership tests.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Delete the test | Pending | — | — | |
| 2 | Run the tests that cover this file | Pending | — | — | |
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
- **Requirement ID**: REQ-002
- **Source issue**: issues/20261014-095505_mdq001_remove-the-mdq-slash-command.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261014-100930_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261014-104845
- **Related target files**: tests/docs/test_db_ownership_boundaries.py
