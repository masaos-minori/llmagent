## Goal

Make the ACK/NACK route handlers consistent with per-consumer delivery state: gate DLQ promotion on the per-consumer failure count (REQ-002), determine the NACK `-2` invalid-transition state atomically with the NACK increment inside a single lock acquisition (REQ-003), and drop every read of the removed `events.acked_at` column from the route (REQ-004). Verify the `_do_ack` debug log is already `logger.debug(...)` and make no level change (implementation hygiene).

## Scope

Modify `scripts/eventbus/ack_route.py` only:

- `_nack_and_promote()` (lines 151-169): use the per-consumer failure count returned by `nack_event()` for the `cfg.max_retry` threshold check at line 165 and in the response field at line 204; refresh the comment at lines 154-158 that describes the counter as a per-event lifetime value.
- `nack()` `-2` handling (lines 174-198): fold the state determination into the same transaction/lock as the NACK increment (REQ-003); remove the `events.acked_at` read and its 409 branch (lines 190, 193-194) while keeping the `consumer_delivery.acked_at` check (lines 178-186) and the `events.dlq_at` check (lines 195-196) (REQ-004).
- `_do_ack()` debug log (line 39): verify it is already `logger.debug(...)`; no change.

Referenced/updated by other documents (not modified here): `nack_event()` / `ack_event_for_consumer()` return shape and logic (`scripts/eventbus/delivery_repo.py`, row 1), `consumer_delivery` DDL and column additions (`scripts/eventbus/schema.sql`, row 3; `scripts/db/schema_sql.py`, row 4), and the per-consumer DLQ sweep (`scripts/eventbus/dlq.py`, row 6).

## Assumptions

- `nack_event()` returns the per-consumer `consumer_delivery_failure_count` after REQ-001/REQ-005 (see `delivery_repo.py` row 1); `ack_route.py` consumes that value.
- The `-2` state must still distinguish "event deleted between NACK and check" (→ 404) from "already ACKed / already in DLQ / otherwise invalid" (→ 409).
- At-least-once semantics are preserved; merging the checks does not change which events are promoted.

## Design decisions

- **Atomic `-2` determination**: move the state probe from the post-lock `run_with_db_lock` calls (lines 178-198) into `_nack_and_promote()` so the NACK increment and the state read commit in one transaction. This closes the EVENTBUS-011 race (event deleted in the gap) without a second lock acquisition.
- **Enriched `-2` return**: encode which sub-state caused `-2` (already-acked vs dlq'd vs deleted) in the return tuple so the outer `nack()` maps it to 409 vs 404 without re-querying. Prefer a small tagged sentinel (e.g. `-2` plus a short status string) over new HTTP codes inside the helper.
- **Per-consumer threshold reuse**: line 165 already compares the returned count to `cfg.max_retry`; once `nack_event()` returns the per-consumer count the gate is per-consumer with no comparator change — only the field/comment semantics change.
- **Keep per-consumer ACK check**: the `consumer_delivery.acked_at` probe (lines 178-186) is per-consumer and survives REQ-004; only the event-level `acked_at` read goes.

## Alternatives considered

- **Return an enum instead of a sentinel int**: cleaner than a bare `-2` plus string, but adds a type; a tagged string alongside `-2` is minimal and readable.
- **Determine state in `delivery_repo` and return the HTTP status**: couples the repo to HTTP codes; keep status mapping in the route layer.

## Implementation

### Target file

`scripts/eventbus/ack_route.py`

### Procedure

1. In `_nack_and_promote()`, use the per-consumer failure count for the line 165 threshold and the line 204 response field; rewrite the lines 154-158 comment to describe the per-consumer count.
2. Move the `-2` state determination from `nack()` lines 178-198 into `_nack_and_promote()` so it runs inside the same lock/transaction as the NACK increment; return an enriched result encoding the sub-state.
3. In `nack()`, replace the separate `run_with_db_lock` probes (lines 178-198) with a branch on the enriched return: map "deleted" → 404, "already-acked"/"dlq'd"/"other invalid" → 409.
4. Remove the `events.acked_at` read (line 190 SELECT list) and its 409 branch (lines 193-194); retain the `consumer_delivery.acked_at` check (lines 178-186) and the `events.dlq_at` check (lines 195-196).
5. Verify the `_do_ack` debug log at line 39 is already `logger.debug(...)`; leave it unchanged.

### Method

- Rewrite `_nack_and_promote()` to perform the state probe (per-consumer ACK, then `events.dlq_at`, then existence) before returning, and return `(status_code_signal, promoted)` where the signal distinguishes `-1` (not found → 404), `-2a` (already-acked → 409), `-2b` (dlq'd → 409), `-2c` (other → 409).
- Simplify `nack()`'s post-lock block: a single `if/elif` on the signal maps to the four outcomes; delete the two inline `run_with_db_lock` lambdas (lines 178-196).
- Edit only the SELECT list and the acked_at branch for REQ-004; do not touch the `events.dlq_at` branch.

### Details

- Line 165 `if failure_count >= cfg.max_retry:` — keep the comparator; `failure_count` now carries the per-consumer count from `nack_event()`. Update the lines 154-158 docstring/comment referencing "lifetime failure counter" / `cycle_failure_count` reset semantics to per-consumer.
- Lines 178-186 (`consumer_delivery.acked_at`): preserve verbatim inside the merged transaction; this is the REQ-001/REQ-003 per-consumer ACK probe.
- Lines 188-194 (`events.acked_at`): under REQ-004 the `acked_at` column no longer exists. Inside the merged transaction, drop `acked_at` from the SELECT (line 190) and delete the `if row and row["acked_at"] is not None: raise 409` branch (lines 193-194).
- Lines 195-196 (`events.dlq_at`) and 197-198 (else → 409 "invalid NACK transition"): preserve; `dlq_at` is not removed by REQ-004.
- Line 39: `logger.debug("DEBUG _do_ack: ...")` is already `logger.debug`; no level change (verified against current source).

## Compatibility considerations

- The `nack()` HTTP contract is unchanged: 404 for missing event, 409 for already-acked/DLQ/invalid. Only the internal path to reach those codes changes.
- The response field `delivery_failure_count` (line 204) now reports the per-consumer count; consumers that key on this field see per-consumer semantics (intended, REQ-002).

## Security considerations

- No authz change; the consumer_id ownership check (lines 133-146) is untouched. Merging the transaction does not widen the authorization surface.

## Rollback considerations

- Change is confined to route handler logic; reverting `ack_route.py` restores prior behavior. No schema impact (schema changes live in rows 3-4).

## Validation plan

- Integration test: a NACK on an already-ACKed event (per consumer) returns 409 and an event deleted between NACK and check returns 404, proving atomicity (REQ-003).
- Integration test: per-consumer NACKs do not advance another consumer's DLQ threshold via this route (REQ-002).
- Repository `rg` sweep for `acked_at` reads in `ack_route.py` after the edit — expect none.
- ruff + mypy on `ack_route.py`; targeted + full pytest.

## Completion criteria

- `ack_route.py` has no read of `events.acked_at` (SELECT list or branch).
- The `-2` state is determined inside the same lock/transaction as the NACK increment; no separate `run_with_db_lock` probe remains in `nack()`.
- DLQ promotion at line 165 uses the per-consumer count; response field reflects per-consumer semantics.
- `_do_ack` debug log verified already `logger.debug(...)`.

## Out of scope

- `nack_event()` / `ack_event_for_consumer()` logic and return shape (REQ-001/REQ-005; `delivery_repo.py`, row 1).
- `consumer_delivery` DDL and the new `consumer_delivery_failure_count` / `last_nack_attempt` column additions (REQ-001; rows 3-4). See Plan Gap note below.
- DLQ promotion implementation (`dlq.py`, row 6).
- The `_do_ack` log level (already satisfied).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: `REQ-002` (per-consumer DLQ promotion), `REQ-003` (atomic NACK state), `REQ-004` (drop `events.acked_at` reads)
- **Source issue**: `issues/done/20261007-154016_ebnack01_fix-eventbus-ack-and-nack-state-management.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261008-160952_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261009-132618
- **Related target files**: `scripts/eventbus/ack_route.py`

> **Plan Gap (needs plan amendment)**: REQ-001 adds `consumer_delivery_failure_count` and `last_nack_attempt` to the `consumer_delivery` table. Those column additions must also be reflected in this file's DDL siblings (`scripts/eventbus/schema.sql` row 3, `scripts/db/schema_sql.py` row 4) and in the migration path (`scripts/eventbus/schema.py` `_migrate`, which currently adds the count to `events`, not `consumer_delivery`). `schema.py` is not a listed target file. Scope decision for a Plan revision; this document covers only the REQ-002/003/004 edits tagged for `ack_route.py`.
