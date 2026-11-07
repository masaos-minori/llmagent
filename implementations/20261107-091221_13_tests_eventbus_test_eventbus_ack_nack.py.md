## Goal

- tests/eventbus/test_eventbus_ack_nack.py — facade migration and required-consumer NACK tests (AC-003, AC-006, REQ-002, REQ-004)

## Scope
**Release unit**: facade-cutover

- The Plan declares one unit covering Phases 1-2: the NACK signature tightening, every import migration, both facade deletions, and the checker patterns land in one commit; any remaining facade import would break suite collection before release (Plan Release unit row, 2026-11-07).

## Assumptions

- All line anchors re-verified 2026-11-07 at HEAD `1a13653e8` (no target-file changes since the Plan freeze at `1b2dded66`).
- Overlap note (compatrm002): 002 edits the auth map/fixture regions; the lines quoted
  here are facade-import and NACK-call regions — re-verify line positions after 002
  lands.

## Design decisions

- Delete the three no-consumer tests instead of rewriting them: the Issue requires the no-consumer path to stop existing.
- New `TypeError`/`ValueError` tests pin the AC-003 matrix at the repository level.

## Alternatives considered

- Keep the no-consumer tests as xfail: rejected — the behavior they lock no longer exists (REQ-004).

## Implementation
### Target file
`tests/eventbus/test_eventbus_ack_nack.py`
### Procedure
1. Import migration:
   - Line 10: `from eventbus.db import NackResult` →
     `from eventbus.delivery_repo import NackResult`.
   - Line 18: `from eventbus.db import open_db` → `from eventbus.db_conn import open_db`.
   - Lines 54-58 block: split into `from eventbus.delivery_repo import ack_event_for_consumer`,
     `from eventbus.event_repo import insert_event`, `from eventbus.db_conn import open_db`
     (keep the deferred placement and the `# noqa: PLC0415` marker).
   - Lines 352, 371, 393, 610, 639, 677, 709: `from eventbus.db import nack_event` →
     `from eventbus.delivery_repo import nack_event`.
   - Lines 402, 432: `from eventbus.db import ack_event_for_consumer, nack_event` →
     `from eventbus.delivery_repo import ack_event_for_consumer, nack_event`.
2. Convert the surviving two-argument calls to pass `consumer_id`:
   - Line 367 (`test_nack_event_increments_failure_count`), lines 386 and 389
     (`test_nack_event_increments_again`), line 395 (`test_nack_event_not_found`): add
     `consumer_id="consumer-A"`. The failure-count assertions stay valid because the
     counts become consumer-scoped.
   - The call at line 485 is inside a deleted test (step 3) and disappears with it.
3. Delete the three no-consumer tests entirely (imports, bodies, and decorators):
   - `test_nack_no_consumer_id_unaffected_by_consumer_acks` (def at line 458, facade
     import at 462, call at 485),
   - `test_nack_same_key_no_increment_no_consumer_id` (def at line 736, import at 740,
     calls at 755 and 758),
   - `test_nack_different_key_no_consumer_id` (def at line 761, import at 763, calls at
     778 and 781).
4. Add the AC-003 regression tests next to the surviving NACK unit tests:
   ```python
   def test_nack_missing_consumer_id_raises_type_error(self, db: sqlite3.Connection) -> None:
       from eventbus.delivery_repo import nack_event

       with pytest.raises(TypeError):
           nack_event(db, "some-event")

   def test_nack_empty_consumer_id_raises_value_error(self, db: sqlite3.Connection) -> None:
       from eventbus.delivery_repo import nack_event

       ev = insert_event(db, "topic.a", "pl", now=now_iso())
       with pytest.raises(ValueError):
           nack_event(db, ev["event_id"], consumer_id="")
       # The guard runs before any query: no consumer_delivery row was written.
       row = db.execute(
           "SELECT * FROM consumer_delivery WHERE event_id = ?", (ev["event_id"],)
       ).fetchone()
       assert row is None
   ```
   (adapt `insert_event`/`now_iso` to the helpers the neighboring tests already import.)
5. Keep unchanged: `test_nack_event_mandatory_consumer_id` (def at line 592, route 422),
   the per-consumer ACK-guard tests (defs at 398, 428), the idempotency-key tests (defs
   at 608-731, which already pass consumer_id), the 403 tests (defs at 791, 831, 847),
   and the unknown-event 404 test (def at 863).
### Method
REQ-002, REQ-004 / AC-003, AC-006. The file has 15 facade import lines (10, 18, the
54-58 block, and per-test `nack_event`/`ack_event_for_consumer` imports at 352, 371,
393, 402, 432, 462, 610, 639, 677, 709, 740, 763) and five two-argument `nack_event`
calls (367, 386, 389, 395, 485) that the tightened signature no longer allows. Three
tests exist only to prove the no-consumer path works; per the Issue they are deleted.
### Details
Test import migration, four call conversions, three test deletions, two new tests.

## Compatibility considerations

- Sibling document ordering (Plan phase sequence):
  - Depends on: doc 03 (the required-`consumer_id` contract must exist before the new
  tests can pass — this document defines the Phase 1 RED matrix).
  - Blocks: sibling documents 02, 26 (this file must stop importing the facade before it is deleted).

## Security considerations

N/A: import-boundary change.

## Rollback considerations

- Reverting the single facade-cutover commit restores this file with every sibling change together; no persisted state is involved.

## Validation plan

- Command: `grep -n "from eventbus.db import\|from eventbus import db\b" tests/eventbus/test_eventbus_ack_nack.py`
  Expected: no matches.
- Command: `uv run pytest tests/eventbus/test_eventbus_ack_nack.py -q`
  Expected: all tests pass, including the two new tests and the unchanged 422/403/404
  route tests (AC-003, AC-004, AC-006).

## Completion criteria

- no call to `nack_event` in the file omits a non-empty `consumer_id`. (AC-003, AC-006, REQ-002, REQ-004)

## Out of Scope

- Every other file in the Plan's Implementation Target Files table is covered by a sibling document of this set; see Compatibility considerations for the ordering this document depends on.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Migrate imports and convert the NACK test matrix in `tests/eventbus/test_eventbus_ack_nack.py` — Plan Phase 1 | Pending | — | — | facade-cutover unit: suite green only with all unit documents landed |
| 2 | Run this document's Validation plan commands | Pending | — | — | |
| 3 | Full validation sequence (`rules/toolchain.md`) in the Plan Phase 4 pass | Pending | — | — | |

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
- **Requirement ID**: REQ-002, REQ-004 / AC-003
- **Source issue**: issues/20261106-125144_compatrm003_remove-db-store-and-eventbus-db-facades-and-optional-nack-consumer-id.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261107-063921_compatrm003_remove-db-store-and-eventbus-db-facades-and-optional-nack-consumer-id.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261107-091221
- **Related target files**: `tests/eventbus/test_eventbus_ack_nack.py`
