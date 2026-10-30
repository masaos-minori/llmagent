# Implementation Procedure: test_eventbus_dlq.py outbox transaction + reconcile extensions

## Goal

Extend `tests/eventbus/test_eventbus_dlq.py` with failing-first contract tests for the
outbox promotion transaction and updated reconciliation-report tests (REQ-002, REQ-003,
REQ-007; plan AC-1, AC-2, AC-5).

## Scope

**In scope:**
- New promotion-transaction tests.
- Update of the existing reconcile tests (`test_eventbus_dlq.py:759-913`) whose exact-dict
  assertions gain the new report keys.

**Out of scope:**
- Crash-window fault injection (row 10's new module), shutdown (row 11).

## Assumptions
- Verified at HEAD `124e340b4`: 973-line module; `client` fixture (TestClient with tmp
  dirs, `max_retry=2`) at 13-34; reconcile test block starts at 759 with exact-dict asserts
  `reconciled == {"checked": 1, "rebuilt": 1, "failed": 0}` (783) and
  `== {"checked": 0, "rebuilt": 0, "failed": 0}` (801).
- Written test-first (plan Phase 1): these tests fail before rows 01-06 land — that is the
  contract's purpose.

## Design decisions
- Promotion transaction tests (new): after an inline NACK that triggers promotion, assert
  (a) `events.dlq_at` set and a `dlq_outbox` (new) row with `status='pending'` exist while
  `{event_id}.json` does NOT yet exist (atomic DB pair, no inline file — AC-1/AC-2);
  (b) sweep promotion inserts outbox rows for promotable events; (c) a racing second
  promotion attempt inserts no second outbox row (`rowcount` guard).
- Reconcile test updates: extend the existing exact-dict literals to
  `{"checked": ..., "rebuilt": ..., "failed": 0, "orphans": ..., "interrupted_tmp": ...,
  "mismatch": ...}`. This is an intentional contract change gated by REQ-007 — the existing
  assertions are behavior the plan explicitly changes, not characterization to preserve;
  every other existing test in the file stays byte-identical.
- New reconcile-class tests (new): orphan file (no promoted row, no done outbox row) counted
  and not deleted; `.dlq_tmp_*` leftover counted; content-mismatch (tampered file JSON)
  counted and not silently rewritten; missing-file rebuild class unchanged.

## Alternatives considered
- Replacing the exact-dict asserts with subset checks: rejected — exact-dict assertions are
  this suite's style and catch accidental key changes.

## Implementation
### Target file
`tests/eventbus/test_eventbus_dlq.py`

### Procedure
1. Add the promotion-transaction tests near the existing inline/sweep promotion tests.
2. Update the reconcile dict literals at 783/801 and any sibling literals in 759-913 with
   the new keys.
3. Add orphan / interrupted-tmp / mismatch tests in the reconcile block.

### Method
Additive tests + literal updates; helpers (`client`, `_event`) reused; direct `sqlite3`
assertion queries follow the file's existing patterns.

### Details
- Tests must read `dlq_outbox` (new) via the test DB handle the fixture exposes (tmp_path
  `eventbus.sqlite`), same as existing DLQ-state assertions.

## Compatibility considerations
- None for production code; these are contracts the other rows satisfy.

## Security considerations
- N/A (test file, tmp dirs only).

## Rollback considerations
- Revert with rows 01-06 (tests encode the new contract).

## Validation plan
- `uv run pytest tests/eventbus/test_eventbus_dlq.py` — after rows 01-06 land, all tests pass;
  before, the new tests fail (test-first gate, plan Phase 1).

## Completion criteria
- AC-1/AC-2 promotion contracts and all four reconciliation report classes are asserted.

## Out of Scope
- Fault injection suite (row 10), shutdown join (row 11), config cases (row 07's disclosed
  test edits).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Write failing-first promotion-transaction tests | Completed | 20261031-074833 | 20261031-074833 | Plan Phase 1 Helpers _drain_outbox/_outbox_failure_counter added; 12 old-contract tests converted |
| 2 | Update reconcile dict literals + new class tests | Completed | 20261031-074833 | 20261031-074833 | Plan Phase 4 4 tests renamed/rewritten (promotion-transaction, outbox-failure counter, per-event isolation, sweep repair); 3 promotion + 4 reconcile tests added; 33 passed |
| 3 | Green after rows 01-06 land | Completed | 20261031-074833 | 20261031-074833 | Ride-on updates: test_eventbus_dlq_promotion.py and test_eventbus_requeue_edge_cases.py converted to new contract |

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
- **Requirement ID**: `REQ-002`, `REQ-003`, `REQ-007`
- **Source issue**: `issues/20261029-104501_dlqbox001_dlq-sqlite-outbox.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/done/20261029-221254_dlqbox001_dlq-sqlite-outbox.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-103000
- **Related target files**: `tests/eventbus/test_eventbus_dlq.py`