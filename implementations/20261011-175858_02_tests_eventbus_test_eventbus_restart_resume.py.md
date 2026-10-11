## Goal
- Update `tests/eventbus/test_eventbus_restart_resume.py` so every `ack_event_for_consumer()` call unpacks the three returned values (`REQ-002`: unpack arity only).

## Scope
- The two failing tests `TestOutOfOrderAckNoSkipOnReconnect::test_out_of_order_ack_no_skip_on_reconnect` and `::test_ordered_ack_baseline`.
- The currently skipped `test_resume_from_sqlite_offset`, which has two further four-value unpack sites; update it for consistency.
- No change to assertions, skip markers, fixtures, or production code.

## Assumptions
- The 3-value contract is the intended one (Plan Design decision, `UNK-01`).
- Verified against the current file: the four-value sites are two in `test_resume_from_sqlite_offset`, two in `test_out_of_order_ack_no_skip_on_reconnect`, and two in `test_ordered_ack_baseline`. The call in the `_ack` helper does not unpack its result and needs no change.
- The Plan's earlier wording ("their helper") was corrected during this pass: the extra sites belong to the skipped test, not to a helper.

## Design decisions
- Change only the left-hand side: `_, newly_acked_x, _, _ = ...` becomes `_, newly_acked_x, _ = ...`.
- Keep the skip decorator on `test_resume_from_sqlite_offset` untouched; its un-skipping is not part of this Plan.
- Keep this change in the test commit, separate from the implementation commit.

## Alternatives considered
- Leave the skipped test unchanged: rejected, because it would still carry the stale contract and fail the moment it is un-skipped.
- Introduce a local wrapper returning four values: rejected as needless indirection that preserves the obsolete contract.

## Implementation
### Target file
`tests/eventbus/test_eventbus_restart_resume.py`

### Procedure
1. Re-read the file and `implementations/20261011-080000_01_delivery_repo_fix_test_failures.md`; skip sites it has already fixed.
2. Change the six unpack statements to three targets.
3. Run the two failing tests.

### Method
- Use Edit with each full statement as `old_string`; the statements repeat across tests, so include the event id and consumer id arguments in the match to keep each edit unique.

### Details
- `test_resume_from_sqlite_offset`: `newly_acked_a` and `newly_acked_b` statements for `evt-resume-1` and `evt-resume-2`.
- `test_out_of_order_ack_no_skip_on_reconnect`: `newly_acked_c` (`evt-oof-3`) and `newly_acked_b` (`evt-oof-2`).
- `test_ordered_ack_baseline`: `newly_acked_a` (`evt-ok-1`) and `newly_acked_b` (`evt-ok-2`).

## Compatibility considerations
- Test-only; no production interface changes.

## Security considerations
N/A: test-only edit; no secrets, permissions, or runtime behavior.

## Rollback considerations
- Revert the test commit with `git revert`, or `git checkout -- tests/eventbus/test_eventbus_restart_resume.py` before it is committed.

## Validation plan
- `uv run pytest tests/eventbus/test_eventbus_restart_resume.py`: the two failing tests pass; the skipped test remains skipped.
- `uv run ruff check tests/eventbus/test_eventbus_restart_resume.py` and `uv run mypy` report no findings.

## Completion criteria
- No `ack_event_for_consumer(...)` call in this file unpacks four values.
- Both failing tests pass; no assertion or skip marker changed.

## Out of scope
- Production code, other test files, documentation.
- Un-skipping `test_resume_from_sqlite_offset`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Re-read the file and skip sites already fixed by the pending procedure | Pending | — | — | |
| 2 | Change the six four-value unpack sites to three values | Pending | — | — | |
| 3 | Add or update tests per Validation plan | Pending | — | — | N/A: this document edits existing tests only |
| 4 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 5 | Update documentation, if in scope | Pending | — | — | N/A: no documentation change for this file |

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
- **Requirement ID**: `REQ-002` (unpack three values)
- **Source issue**: issues/20261011-075321_eb012ack_resolve-ack_event_for_consumer-return-contract-mismatch-between-code-and-tests.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261011-153619_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261011-175858
- **Related target files**: tests/eventbus/test_eventbus_restart_resume.py
