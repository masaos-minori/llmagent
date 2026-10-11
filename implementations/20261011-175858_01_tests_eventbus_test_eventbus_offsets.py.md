## Goal
- Update the tests in `tests/eventbus/test_eventbus_offsets.py` that unpack four values from `ack_event_for_consumer()` so they unpack the three values the function returns (`REQ-002`: unpack arity only, no weaker assertions).

## Scope
- Change the unpack statements in the four failing tests: `test_ack_writes_offset`, `TestSqliteOffsetMonotonicity::test_older_seq_cannot_move_offset_backward`, `TestConsumerOffsetsTable::test_ack_event_for_consumer_advances_offset`, and `TestConsumerOffsetsTable::test_offset_does_not_regress_on_older_seq`.
- No change to assertions, fixtures, or production code.

## Assumptions
- The 3-value contract `(found, newly_acked, seq)` is the intended one (Plan Design decision, `UNK-01`).
- Verified against the current file: the unpack sites with a trailing `_` fourth target are the call in `test_ack_writes_offset`, two calls in `test_older_seq_cannot_move_offset_backward`, one in `test_ack_event_for_consumer_advances_offset`, and three in `test_offset_does_not_regress_on_older_seq`.
- `test_offset_does_not_regress_on_older_seq` asserts `seq3 is not None` after a duplicate ACK; that assertion passes only once `scripts/eventbus/delivery_repo.py` returns `seq` for an already-acked event (`REQ-005`, procedure 03).

## Design decisions
- Change only the left-hand side of each assignment: drop the fourth `_` target. Do not touch the assertions that follow.
- Keep this change in its own commit, separate from the implementation commit, as the source issue requires.

## Alternatives considered
- Restore the 4-value return instead: rejected by the Plan (more call sites, the endpoint documentation and reference API already state three values).
- Loosen the `seq3` assertion so the test passes without the code fix: rejected, because the issue forbids loosening assertions and the assertion encodes the documented contract.

## Implementation
### Target file
`tests/eventbus/test_eventbus_offsets.py`

### Procedure
1. Re-read the file and the pending procedure `implementations/20261011-080000_01_delivery_repo_fix_test_failures.md`; skip any site that procedure has already fixed.
2. In each failing test, change every `a, b, c, _ = ack_event_for_consumer(...)` to `a, b, c = ack_event_for_consumer(...)`, and every `_, newly, _, _ = ...` to `_, newly, _ = ...`.
3. Run the four tests.

### Method
- Use Edit with the exact existing statement as `old_string`; there are seven call sites, so edit them one by one.
- Do not change imports, comments, or assertions.

### Details
- `test_ack_writes_offset`: `found, newly_acked, result_seq, _ = ...` becomes `found, newly_acked, result_seq = ...`.
- `test_older_seq_cannot_move_offset_backward`: two statements `_, newly_acked, _, _ = ...` become `_, newly_acked, _ = ...`.
- `test_ack_event_for_consumer_advances_offset`: `found, newly_acked, seq, _ = ...` becomes `found, newly_acked, seq = ...`.
- `test_offset_does_not_regress_on_older_seq`: `found1, _, seq1, _`, `found2, newly_acked2, seq2, _`, and `found3, newly_acked3, seq3, _` each lose the trailing `_`.
- After this change, `test_offset_does_not_regress_on_older_seq` still fails on `assert seq3 is not None` until procedure 03 is applied; say so in the commit message.

## Compatibility considerations
- Test-only; no production interface changes. Tests in other modules already use three values (`tests/eventbus/test_eventbus_ack_nack.py`).

## Security considerations
N/A: test-only edit; no secrets, permissions, or runtime behavior.

## Rollback considerations
- Revert the test commit with `git revert`, or `git checkout -- tests/eventbus/test_eventbus_offsets.py` before it is committed. No data or deployment state is touched.

## Validation plan
- `uv run pytest tests/eventbus/test_eventbus_offsets.py`: three of the four tests pass after this step; `test_offset_does_not_regress_on_older_seq` passes after procedure 03.
- `uv run ruff check tests/eventbus/test_eventbus_offsets.py` and `uv run mypy` report no findings.

## Completion criteria
- No `ack_event_for_consumer(...)` call in this file unpacks four values.
- No assertion was changed, removed, or marked `xfail`.
- All four listed tests pass once procedure 03 is also applied.

## Out of scope
- Production code, other test files, and documentation.
- The other eventbus failures owned by `implementations/20261011-080000_01_delivery_repo_fix_test_failures.md`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Re-read the file and skip sites already fixed by the pending procedure | Completed | 20261011-195047 | 20261011-195047 | Already applied upstream in commit 93179f0f7; verified unpack sites use three values |
| 2 | Change the seven four-value unpack sites to three values | Completed | 20261011-195047 | 20261011-195047 | Already applied upstream in 93179f0f7; no edit needed here |
| 3 | Add or update tests per Validation plan | Completed | 20261011-195047 | 20261011-195047 | N/A: this document edits existing tests only N/A: existing tests only |
| 4 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261011-195047 | 20261011-195047 | pytest tests/eventbus tests/db: 568 passed; full suite 8200 passed; ruff check clean |
| 5 | Update documentation, if in scope | Completed | 20261011-195047 | 20261011-195047 | N/A: no documentation change for this file N/A: no documentation change for this file |

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
- **Related target files**: tests/eventbus/test_eventbus_offsets.py