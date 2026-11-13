## Goal
Update all `promote_single`/`sweep_orphans` call sites to the new signatures and replace the `dlq_requeue_count` assertions with lineage assertions (REQ-001, REQ-004 / AC-1, AC-4).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Call-site counts (2026-11-13 verification): 21 `sweep_orphans(db, str(tmp_path / "deadletter"), max_retry=...)` sites (lines 129-1227, some prefixed `dlq.sweep_orphans`) and 4 `promote_single` sites (single-line at 240, 242, 552; multi-line at 732-735, whose first arg is `_CommitFailingConn(db)`); every site passes `str(tmp_path / "deadletter")` as the second positional argument. The `deadletter_dir=str(tmp_path / "deadletter")` kwarg at line 26 is out of scope.
- File-presence tests already call the local `_drain_outbox(db, str(tmp_path / "deadletter"))` helper after a sweep or nack (test-file lines 87-110), so DB-only promotion does not change file assertions; `_drain_outbox`/`process_outbox` keep their `deadletter_dir` argument (out of this plan's scope).
- Run after rows 01-02 (`dlq.py`, `ack_route.py`).

## Design decisions
- Two `dlq_requeue_count` tests are rewritten, not deleted: both encode behaviors the plan keeps (requeue records lineage; a rejected requeue leaves no trace) and the Plan retains this file as the regression carrier for AC-4.

## Alternatives considered
- Deleting the two counter tests outright: rejected — AC-4 requires proof that the requeue model still functions after the column removal; the lineage assertions carry the same coverage.

## Implementation
### Target file
`tests/eventbus/test_eventbus_dlq.py`

### Procedure
1. Mechanical call-site update across the file: every `sweep_orphans(db, str(tmp_path / "deadletter"), max_retry=X)` becomes `sweep_orphans(db, max_retry=X)`; every `dlq.promote_single(db, str(tmp_path / "deadletter"), <id>)` becomes `dlq.promote_single(db, <id>)`. Do not touch `_drain_outbox` calls or the helper itself.
2. `test_requeue_increments_dlq_requeue_count` (line 301): rename to `test_requeue_records_lineage_on_new_event` (new); replace the block at lines 328-333 (`SELECT dlq_requeue_count, dlq_at ... assert orig_row["dlq_requeue_count"] == 1`) with `SELECT dlq_at FROM events WHERE event_id = ?` plus `assert orig_row["dlq_at"] is not None`; keep the existing `new_row["redelivered_from"] == ev["event_id"]` and final descendant-count/file assertions.
3. `test_requeue_non_dlq_event_fails` (line 474): replace the block at lines 488-493 (`SELECT dlq_requeue_count ... assert row["dlq_requeue_count"] == 0`) with `SELECT COUNT(*) FROM events WHERE redelivered_from = ?` on the original id and assert the count is `0` (rejected requeue leaves no descendant).

### Method
- Step 1 is a single uniform textual transform (scriptable: replace `, str(tmp_path / "deadletter"),` inside `sweep_orphans(`/`promote_single(` call openings; for the multi-line `dlq.promote_single(` call at 732-735, delete the standalone `str(tmp_path / "deadletter"),` line). Verify with `rg -n 'str\(tmp_path / "deadletter"\)' tests/eventbus/test_eventbus_dlq.py`: every remaining hit must be an out-of-scope site only (the `deadletter_dir=` kwarg at line 26 and `_drain_outbox(...)` calls); no hit inside a `sweep_orphans`/`promote_single` call.

### Details
- After step 2's rename, no `dlq_requeue_count` string remains anywhere in this file (verified sites are only 301-333 and 488-493).

## Compatibility considerations
- ADR-006's INV-08 row cites the renamed promotion-file test (row 16), not this file's test; this file's rename needs no doc follow-up.

## Security considerations
N/A: test-only change.

## Rollback considerations
N/A: revert the commit.

## Validation plan
| Target | Testing strategy | Tool / command | Expected outcome |
|---|---|---|---|
| Call sites | Test | `uv run pytest tests/eventbus/test_eventbus_dlq.py -q` | All pass |
| Residual old signature | Search | `rg -n 'str\(tmp_path / "deadletter"\)' tests/eventbus/test_eventbus_dlq.py` | No hit inside any `sweep_orphans`/`promote_single` call (only the line 26 kwarg and `_drain_outbox` calls remain) |
| Column removal | Search | `rg -n "dlq_requeue_count" tests/eventbus/test_eventbus_dlq.py` | No match |

## Completion criteria
- AC-1: no call site passes `deadletter_dir`; AC-4: no assertion reads the removed column; file passes against the post-row-01/05 source.

## Out of Scope
- `_drain_outbox`/`process_outbox`/`reconcile_missing_dlq_files` usage (signatures unchanged), the DLQ file-presence assertions themselves.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261113-210040 | 20261113-210826 |  |
| 2 | Add or update tests per Validation plan | Completed | — | 20261113-210826 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261113-210826 | targeted pytest 33 passed; mypy/coverage/full-suite deferred to cycle 18 per group-1 deferral note |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261113-215941 | N/A docs out of scope, handled by row 14 regeneration |

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
- **Requirement ID**: REQ-001, REQ-004 / AC-1, AC-4
- **Source issue**: issues/20261110-170926_rmcompat005_eventbus-dlq-leftovers.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261112-121134_rmcompat005_eventbus-dlq-leftovers.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261113-173721
- **Related target files**: `tests/eventbus/test_eventbus_dlq.py`