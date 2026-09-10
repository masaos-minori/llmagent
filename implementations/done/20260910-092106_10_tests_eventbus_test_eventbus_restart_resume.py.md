## Goal
Update/add a test confirming resume-from-offset still works when the offset comes
from the new SQLite-backed table instead of a file (REQ-002, REQ-005; AC-4, AC-6).

## Scope
In scope: `test_same_consumer_id_resumes_from_last_acked_offset` and
`test_different_consumer_id_starts_from_zero` — confirm they still pass against the
new backing store (update assertions/setup only if they inspect the offset file
directly rather than going through the HTTP/route layer). Out of scope:
`test_same_consumer_id_last_write_wins` — confirm during implementation whether this
test's name/assertion describes `write_offset()`'s existing monotonicity-skip
behavior (which is preserved by row 03's atomic advancement) or something else; do not
change its assertion unless it directly inspects the legacy file path in a way the new
route (row 05) no longer produces.

## Assumptions
- `test_same_consumer_id_resumes_from_last_acked_offset` and
  `test_different_consumer_id_starts_from_zero` currently assert via the HTTP
  `/subscribe` endpoint's observable behavior (received events), not by reading
  `offsets_dir` files directly — if so, no change is needed beyond confirming they
  still pass once `subscribe_route.py` (row 05) reads from `consumer_offsets`.
- If either test does inspect `cfg.offsets_dir` directly (e.g. via
  `read_offset(cfg.offsets_dir, consumer_id)`), it must be updated to query
  `consumer_offsets` instead (via `get_consumer_offset()`, row 03), since the file
  path is no longer the live-service source of truth per REQ-005.

## Design decisions
Confirm both existing tests pass unmodified against the new backing store first (they
likely already only assert on HTTP-observable behavior — reconnect and check which
events are received — which is backing-store-agnostic). If they do inspect the file
directly, switch the inspection to `get_consumer_offset(db, consumer_id)` instead of
`read_offset(cfg.offsets_dir, consumer_id)`.

## Alternatives considered
Adding an entirely new, separate test class for the SQLite-backed path (rather than
confirming the existing two tests already exercise it end-to-end via the HTTP layer)
was considered; reusing the existing tests is preferred since they already express the
correct behavioral contract (resume from last offset; new consumer starts from zero) —
adding a parallel test class would duplicate coverage rather than adapt it.

## Implementation
### Target file
`tests/eventbus/test_eventbus_restart_resume.py`

### Procedure
1. Run both existing tests against the changed `subscribe_route.py` (row 05) and
   confirm they pass unmodified — if so, no code change is needed in this file beyond
   confirming coverage (this row still "completes" by verifying, not necessarily by
   editing).
2. If either test reads `offsets_dir` directly, update it to use
   `get_consumer_offset()` against the same `db` connection the test fixture already
   provides.
3. Confirm `test_same_consumer_id_last_write_wins`'s continued relevance: if its name
   describes the pre-existing (and per Plan Risks, contradictory)
   `write_offset()`/`test_eventbus_ack_endpoint.py::TestAckMonotonicOffset` behavior
   rather than this Plan's new atomic-advancement semantics, leave it unmodified per
   Plan Out-of-Scope (pre-existing, unrelated test behavior is not corrected by this
   Plan).

### Method
Read-and-confirm first; edit only if direct file-path inspection is found.

### Details
No code snippet is prescribed here since the exact change (if any) depends on what
Step 3a's investigation of this specific file's current assertions finds — investigate
whether either test calls `read_offset()`/reads `cfg.offsets_dir` directly before
writing any diff.

## Compatibility considerations
If no direct file-path inspection exists, this row requires no code change — only
confirmation that the existing tests keep passing (a form of regression coverage for
row 05's change, not a new assertion).

## Security considerations
Test-only file; no production security surface.

## Rollback considerations
If a change was made (direct offset-read path swapped), revert this file's diff to
restore the original assertion; the test would then need row 05 to also be reverted
together for consistency.

## Validation plan
`uv run pytest tests/eventbus/test_eventbus_restart_resume.py -v` — all three tests
pass against the SQLite-backed offset store (row 05).

## Completion criteria
`test_same_consumer_id_resumes_from_last_acked_offset` and
`test_different_consumer_id_starts_from_zero` pass against the new backing store
(AC-6); `test_same_consumer_id_last_write_wins` is confirmed either unaffected or
explicitly left unmodified per Plan Out-of-Scope.

## Out of scope
Correcting `test_same_consumer_id_last_write_wins`'s own assertion if it reflects the
pre-existing, unrelated monotonicity-contradiction test already flagged in the Plan's
Risks (`test_eventbus_ack_endpoint.py::TestAckMonotonicOffset::test_older_seq_ack_moves_offset_backward`) —
not corrected by this Plan.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Confirm existing two tests pass unmodified against the new offset store | Pending | — | — | |
| 2 | Update direct file-path inspection to `get_consumer_offset()`, if found | Pending | — | — | |
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
- **Requirement ID**: REQ-002, REQ-005
- **Source issue**: issues/20260907-125042_eb_h01_transactional_ack_offset_delivery_state.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260909-094115_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260910-092106
- **Related target files**: tests/eventbus/test_eventbus_restart_resume.py
