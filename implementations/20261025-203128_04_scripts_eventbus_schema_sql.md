## Goal

Record the UNK-03 owner decision on NACK idempotency-key storage for `scripts/eventbus/schema.sql`: the recommended **latest-key-only** model requires **no change** — the single `consumer_last_nack_attempt` column already suffices. This document verifies the current schema and records the conditional branch that would apply only if the owner later adopts the bounded-set model.

## Scope

- **In-Scope** (`scripts/eventbus/schema.sql` only):
  - Verify and record the current per-consumer delivery-state schema (single `consumer_last_nack_attempt` column).
  - Record the UNK-03 decision (latest-key-only → no schema change, no `user_version` bump).
  - Document the conditional bounded-set branch (would apply only if UNK-03 selects that model).
- **Out-of-Scope** (handled by sibling documents this Plan generates):
  - Route key source + keyless handling (`scripts/eventbus/ack_route.py`, seq 01).
  - Repository guard live-ification (`scripts/eventbus/delivery_repo.py`, seq 02).
  - SSE delivery-attempt identity (`scripts/eventbus/subscribe_route.py`, seq 03).
  - Tests (seq 05/06), contract doc (seq 07), ADR close (seq 08).

## Assumptions

- UNK-03 recommended = latest-key-only: the single column `consumer_last_nack_attempt` is compared against the incoming key; no new store and no `user_version` bump are needed.
- The eventbus database is recreated, never migrated: any storage change must bump `PRAGMA user_version`, and `open_db()` refuses a database stamped otherwise.
- A well-formed client sends the same key for a retry of attempt N and a new key for attempt N+1, so latest-key dedup covers real retries; the out-of-order `NACK(A)`, `NACK(B)`, `NACK(A retry)` sequence only arises from arbitrary client keys and is defined as "a non-latest key counts as a new attempt."

## Design decisions

- **Latest-key-only (no schema change).** The recommended UNK-03 model uses the existing single column `consumer_last_nack_attempt` in `consumer_delivery`. No new table, no `user_version` bump. `schema.sql` is left unchanged.
- **Bounded set of recent keys (conditional, not adopted).** Only if the owner explicitly wants out-of-order retry deduplication would `schema.sql` gain a bounded store (for example a table `consumer_nack_keys` (new) with a `nack_attempt` (new) column, or a bounded JSON column) and bump `PRAGMA user_version` from 1 to 2. This recreates the eventbus DB (data loss); adopt only with explicit owner sign-off (`REQ-008`).

## Alternatives considered

- **Bounded set of recent keys (UNK-03 option 2):** remember the last K keys per `(consumer_id, event_id)` so an out-of-order retry of a recent attempt is still deduped. Requires a new store and a `user_version` bump (DB recreation). Rejected as the default; kept as a documented conditional branch.
- **Leave the row unrecorded:** rejected — the one-doc-per-row invariant requires this conditional row to carry a recorded decision with verified current-source evidence.

## Implementation

### Target file

`scripts/eventbus/schema.sql`

### Procedure

1. Verify the current per-consumer delivery-state schema (no change required): `consumer_delivery` (schema.sql:22-29) carries a single `consumer_last_nack_attempt TEXT` column (schema.sql:27) keyed by `(consumer_id, event_id)`; `PRAGMA user_version = 1` (schema.sql:43).
2. Confirm the recommended latest-key-only model needs no new store — the single column is compared against the incoming key in `delivery_repo.py::nack_event()`.
3. Record the UNK-03 decision (latest-key-only → no modification) and the conditional bounded-set branch above.
4. Run the documentation checkers.

### Method

`schema.sql` defines `consumer_delivery` (schema.sql:22-29) with `consumer_id`, `event_id`, `acked`, `consumer_delivery_failure_count`, and the single `consumer_last_nack_attempt` column (schema.sql:27), primary key `(consumer_id, event_id)`. The schema version pragma sits at schema.sql:43 (`PRAGMA user_version = 1`). Under the recommended latest-key-only model this is complete as-is; the repository's `nack_event()` compares the incoming key against this one remembered key.

```python
-- schema.sql — per-consumer delivery state, single latest-NACK-key column (UNCHANGED under recommended UNK-03)
CREATE TABLE IF NOT EXISTS consumer_delivery (
    consumer_id                    TEXT    NOT NULL,
    event_id                       TEXT    NOT NULL,
    acked                          INTEGER NOT NULL DEFAULT 0,
    consumer_delivery_failure_count INTEGER NOT NULL DEFAULT 0,
    consumer_last_nack_attempt     TEXT,   -- schema.sql:27 — latest key only
    PRIMARY KEY (consumer_id, event_id)
);
-- schema.sql:43 — PRAGMA user_version = 1; unchanged under latest-key-only
```

```sql
-- schema.sql — conditional bounded-set branch (NOT adopted; UNK-03 = latest key only)
-- Only if UNK-03 selects the bounded-set model, add a recent-key store and bump the version:
CREATE TABLE IF NOT EXISTS consumer_nack_keys (new) (
    consumer_id   TEXT NOT NULL,
    event_id      TEXT NOT NULL,
    nack_attempt  TEXT (new),
    PRIMARY KEY (consumer_id, event_id, nack_attempt)
);
PRAGMA user_version = 2;   -- recreates the eventbus DB (REQ-008)
```

### Details

- **UNK-03 (recommended, latest-key-only):** no change. The single `consumer_last_nack_attempt` column (schema.sql:27) is compared against the incoming key; no new store, no `user_version` bump.
- **UNK-03 (conditional, bounded set):** would require adding a recent-key store (for example `consumer_nack_keys` (new) with a `nack_attempt` (new) column) and bumping `PRAGMA user_version` from 1 to 2 (schema.sql:43). The DB is recreated, never migrated (`REQ-008`). Not implemented — recorded only.
- **No route/repo impact:** this row changes nothing under the recommended model; seq 02 (`delivery_repo.py`) and seq 03 (`subscribe_route.py`) also stay unmodified.

## Compatibility considerations

- No schema change under the recommended model — existing databases and the eventbus DB are unaffected.
- The conditional bounded-set branch would bump `user_version`, recreating the eventbus DB and losing data; this is intentional and gated on explicit owner sign-off (`REQ-008`).

## Security considerations

- No change under the recommended model; no new secrets or injection surface.
- The conditional bounded-set branch stores caller-supplied keys in a new table — keys are opaque client identifiers, not secrets; no special handling beyond the existing tables.

## Rollback considerations

- No code change under the recommended model; there is nothing to revert. This document is a decision record.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `schema.sql` unchanged | Current-source verification against this procedure | `uv run python tools/stale_detector.py {this doc}` | All referenced constructs found; schema at :22-29/:43 matches |
| Decision record integrity | Structure check | `uv run python tools/check_workitem_structure.py {this doc}` | No findings |

## Completion criteria

- The current per-consumer schema (`consumer_delivery`, single `consumer_last_nack_attempt` at schema.sql:27; `PRAGMA user_version = 1` at schema.sql:43) is verified against source.
- The UNK-03 decision (latest-key-only → no modification) is recorded, with the conditional bounded-set branch documented.
- `stale_detector.py` and `check_workitem_structure.py` pass.

## Out of Scope

- Route key source + keyless handling (`scripts/eventbus/ack_route.py`, seq 01).
- Repository guard live-ification (`scripts/eventbus/delivery_repo.py`, seq 02).
- SSE delivery-attempt identity (`scripts/eventbus/subscribe_route.py`, seq 03).
- Tests (seq 05/06), contract doc (seq 07), ADR close (seq 08).
- UNK-03 bounded-set branch — recorded as a conditional branch, not implemented.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Verify current per-consumer schema; record UNK-03 latest-key decision (no modification) + conditional bounded-set branch | Pending | — | — | Recommended model = no change; decision recorded |
| 2 | Run the documentation checkers (`stale_detector.py`, `check_workitem_structure.py`) | Pending | — | — | No code change → no test run needed |

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
- **Requirement ID**: `REQ-004`, `REQ-008`
- **Source issue**: `issues/20261023-154326_eventbus005_nack-idempotency-retries.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261025-120857_eventbus005_nack-idempotency-retries.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261025-203128
- **Related target files**: `scripts/eventbus/schema.sql`
