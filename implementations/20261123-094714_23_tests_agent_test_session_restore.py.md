## Goal

Update the restore tests for the non-mutating builder, the four separate counts, and failure leaving the old session intact (REQ-002 transactional restore, REQ-009 separate counts; AC-1, AC-5).

## Scope
**Release unit**: N/A: not part of a release unit

Test-only row with its own document: this test file is named by two code rows (seq 04 and seq 05), so it fails the companion single-owner condition and is not covered as a companion.

## Assumptions
- Existing file verified present; current tests exercise the mutating `restore_session` and a single `n_messages` count.
- Tests are written before the code change (plan Phase 3 order), so they define the builder contract for seq 04/05.

## Design decisions
- Add tests that assert the builder returns state without touching `ctx.conv.history`, session id, undo floor, correlation, or stats, and that a mid-pipeline failure leaves them exactly as before (driven through the seq 02 service once wired).
- Assert the four counts on `SessionRestoreResult` for a fixture containing orphaned tool_call rows (synthesized), unusable rows (dropped), and normal rows (fetched/restored).

## Alternatives considered
N/A: the row is fixed test follow-up.

## Implementation
### Target file
`tests/agent/test_session_restore.py`
### Procedure
1. Rework existing restore tests to the builder result (no context mutation assertions on the builder path).
2. Add the four-count tests and the failure-unchanged tests.
### Method
Extend existing fixtures; keep the current error-contract tests (`SessionNotFoundError`, `SessionNoMessagesError`) unchanged.
### Details
- Coordination: seq 04 and seq 05 documents reference this file as their validation owner; land this row's tests first per the plan's tests-first phase order.

## Compatibility considerations
- Existing boundary-test behavior (undo floor computation before mutation) must keep passing.

## Security considerations
N/A: tests only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/test_session_restore.py -q`.

## Completion criteria
The suite proves the builder never mutates the context, failure leaves the old session unchanged, and the four counts are reported (AC-1, AC-5).

## Out of Scope
Builder implementation (seq 04), result fields (seq 05), service integration tests (seq 02 companion).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Tests-first row |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | Test-only row: implement step is the test change |

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
- **Requirement ID**: `REQ-002` (non-mutating restore), `REQ-009` (four load counts)
- **Source issue**: `issues/20261119-145300_cliplc002_session-transition-generation.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261122-232757_cliplc002_session-transition-generation.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261123-094714
- **Related target files**: `tests/agent/test_session_restore.py`
