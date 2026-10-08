## Goal

Update the EventBus source-of-truth DDL in `scripts/eventbus/schema.sql`: drop the
`events.acked_at` column (`REQ-004`) and add the per-consumer NACK-attempt column
`consumer_delivery.last_nack_attempt` (`REQ-001`), keeping this file consistent with
`scripts/db/schema_sql.py`.

## Scope

Modifies `scripts/eventbus/schema.sql` only. References
`scripts/db/schema_sql.py` (runtime `_EVENTBUS_SCHEMA` mirror) and
`scripts/eventbus/schema.py` (`_migrate`, additional target file — see Out of scope).
See Design decisions for the `acked_at` migration and column-placement questions.

## Assumptions

- `schema.sql` is the canonical DDL; `_init_schema()` builds fresh databases from it
  (`scripts/eventbus/schema.py:_init_schema`).
- Existing databases are migrated via `schema.py::_migrate`; dropping a column there
  requires an explicit `ALTER TABLE ... DROP COLUMN` (SQLite has no `ADD COLUMN IF
  NOT EXISTS`/`DROP COLUMN IF EXISTS`).
- `consumer_delivery.last_nack_attempt` is `TEXT` and nullable so existing rows are
  unaffected by a fresh install.

## Design decisions

- Remove the `acked_at` column definition from the `events` table DDL (`REQ-004`);
  per-consumer ACK state now lives solely in `consumer_delivery.acked_at`.
- Add `last_nack_attempt TEXT` to the `consumer_delivery` table (`REQ-001`) to key
  NACK idempotency on the delivery attempt.
- Keep the `idx_consumer_delivery_consumer_ack` index on
  `(consumer_id, acked_at)` — it still supports the per-consumer ACK lookups used by
  `ack_event_for_consumer()` and the NACK guard.
- Column placement: `consumer_delivery_failure_count` currently lives on the `events`
  table (line 17). The source issue intends per-consumer failure counting in
  `consumer_delivery`. Resolve this with the `REQ-002` / ADR-006 decision before
  relocating it; this row does not move it.

## Alternatives considered

- Leaving `acked_at` in the fresh-install DDL and dropping it only via migration —
  rejected: fresh databases would then define a column nothing writes, which is
  misleading and inconsistent with migrated databases.

## Implementation

### Target file

`scripts/eventbus/schema.sql`

### Procedure

1. `REQ-004` — Delete the `acked_at TEXT` line from the `events` table definition
   (line 10).
2. `REQ-001` — Add `last_nack_attempt TEXT` to the `consumer_delivery` table
   definition (after `acked_at`, line 29).
3. Mirror both changes in `scripts/db/schema_sql.py` (`_EVENTBUS_SCHEMA`) via its own
   row — do not edit that file here.

### Method

- Open `scripts/eventbus/schema.sql`; locate the `events` table (lines 3-18) and
  `consumer_delivery` table (lines 26-31).
- Apply the two edits above; run no SQL here — validate by loading the file into a
  fresh SQLite database (`python -c "import sqlite3; ..."`) and confirming the
  columns exist/absent as intended.
- Diff against `scripts/db/schema_sql.py`'s equivalent `_EVENTBUS_SCHEMA` blocks to
  keep them in sync.

### Details

- Do not touch `consumer_delivery_failure_count` (line 17) in this row — its
  placement is decided by the `REQ-002` / ADR-006 decision.
- The `last_nack_attempt` column name must match `_COL_LAST_NACK_ATTEMPT` added in the
  `_constants.py` row.

## Compatibility considerations

- Fresh databases built from this file lose `events.acked_at`. Existing databases
  keep the column until migrated (see Out of scope for the migration file).
- No other DDL changes.

## Security considerations

- Schema change is out-of-band from request handling; no injection surface.

## Rollback considerations

- Restore the `acked_at` line and remove `last_nack_attempt` to revert the DDL.

## Validation plan

- Load `schema.sql` into a fresh SQLite DB; assert `events` has no `acked_at` and
  `consumer_delivery` has `last_nack_attempt`.
- Confirm `scripts/db/schema_sql.py._EVENTBUS_SCHEMA` matches.
- `ruff`/`lint-imports` are not applicable to raw DDL; verify by loading.

## Completion criteria

- `events.acked_at` absent from `schema.sql`.
- `consumer_delivery.last_nack_attempt` present in `schema.sql`.
- `schema_sql.py` mirror updated (via its row).

## Out of scope

- Migration of existing databases: `schema.py::_migrate` needs an
  `ALTER TABLE events DROP COLUMN acked_at` (and the `last_nack_attempt` add is
  covered by fresh DDL). `schema.py` is an additional target file not listed in the
  Plan's `Implementation Target Files` — flag as a Plan Gap / re-freeze before
  executing the migration step.
- `schema_sql.py` edits (its own row).

## Execution Status

| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement REQ-001/REQ-004 DDL changes in schema.sql | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation | N/A | — | — | Docs handled by REQ-006 rows |

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
- **Requirement ID**: `REQ-004`, `REQ-001`
- **Source issue**: `issues/done/20261007-154016_ebnack01_fix-eventbus-ack-and-nack-state-management.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261008-160952_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261009-071937
- **Related target files**: `scripts/eventbus/schema.sql`
