## Goal

Update the EventBus runtime DDL mirror `scripts/db/schema_sql.py` (`_EVENTBUS_SCHEMA`)
to drop the `events.acked_at` column (`REQ-004`), add the per-consumer NACK-attempt
column `consumer_delivery.last_nack_attempt` (`REQ-001`), and relocate the per-consumer
failure counter `consumer_delivery_failure_count` from `events` to
`consumer_delivery` (`REQ-002`), keeping it consistent with `scripts/eventbus/schema.sql`.

## Scope

Modifies `scripts/db/schema_sql.py` only. References
`scripts/eventbus/schema.sql` (canonical DDL source) and
`scripts/eventbus/schema.py` (`_migrate`, additional target file — see Out of scope).
See Design decisions for the `acked_at` migration and column-placement questions.

## Assumptions

- `_EVENTBUS_SCHEMA` is consumed by `build_eventbus_schema_sql()` and fed into the
  same `_init_schema()` path as `schema.sql`; both must describe identical tables.
- Existing databases are migrated via `schema.py::_migrate`; dropping a column there
  requires an explicit `ALTER TABLE ... DROP COLUMN` (SQLite has no `DROP COLUMN IF
  EXISTS`).
- `consumer_delivery.last_nack_attempt` is `TEXT` and nullable so existing rows are
  unaffected.

## Design decisions

- Remove the `acked_at` column definition from the `events` table block of
  `_EVENTBUS_SCHEMA` (`REQ-004`); per-consumer ACK state now lives solely in
  `consumer_delivery.acked_at`.
- Add `last_nack_attempt TEXT` to the `consumer_delivery` table block (`REQ-001`) to
  key NACK idempotency on the delivery attempt.
- Keep the `idx_consumer_delivery_consumer_ack` index on
  `(consumer_id, acked_at)` if present in this block — it supports the per-consumer
  ACK lookups used by `ack_event_for_consumer()` and the NACK guard.
- Relocate `consumer_delivery_failure_count` from `events` to `consumer_delivery`
  (`REQ-002`): add it to the `consumer_delivery` table block. The `_EVENTBUS_SCHEMA`
  `events` block never carried this column (pre-existing divergence from
  `schema.sql`); leave the `events` block untouched except for the `acked_at` removal.

## Alternatives considered

- Editing only `schema.sql` and leaving `_EVENTBUS_SCHEMA` stale — rejected: the
  runtime schema would diverge from the canonical DDL and fresh databases built via
  `build_eventbus_schema_sql()` would differ from migrated ones.

## Implementation

### Target file

`scripts/db/schema_sql.py`

### Procedure

1. `REQ-004` — Delete the `acked_at TEXT` line from the `events` table block inside
   `_EVENTBUS_SCHEMA` (line 242).
2. `REQ-001` — Add `last_nack_attempt TEXT` to the `consumer_delivery` table block
   (after `acked_at`).
3. `REQ-002` — Add `consumer_delivery_failure_count INTEGER NOT NULL DEFAULT 0` to the
   `consumer_delivery` table block (after `last_nack_attempt`). The `events` block never
   carried this column; do not add it there.
4. Mirror all changes in `scripts/eventbus/schema.sql` via its own row — do not edit
   that file here.

### Method

- Open `scripts/db/schema_sql.py`; locate the `events` table block (lines 235-248) and
  `consumer_delivery` table block (lines 256-261) inside `_EVENTBUS_SCHEMA`.
- Apply the two edits above.
- Diff against `scripts/eventbus/schema.sql`'s equivalent blocks to confirm they match
  (column names, order, nullability).

### Details

- Do not touch any other table block or the surrounding `_WORKFLOW_MIGRATIONS` list.
- Leave the `events` block's pre-existing divergence from `schema.sql`
  (`published_at` default, missing `consumer_id`) untouched — out of scope.
- The `last_nack_attempt` and `consumer_delivery_failure_count` column names must match
  `_COL_LAST_NACK_ATTEMPT` / `_COL_CONSUMER_DELIVERY_FAILURE_COUNT` in `_constants.py`.

## Compatibility considerations

- Fresh databases built from this mirror lose `events.acked_at`. Existing databases
  keep the column until migrated (see Out of scope for the migration file).
- No other DDL changes.

## Security considerations

- Schema change is out-of-band from request handling; no injection surface.

## Rollback considerations

- Restore the `acked_at` line and remove `last_nack_attempt` to revert the mirror.

## Validation plan

- Call `build_eventbus_schema_sql()` and load the result into a fresh SQLite DB;
  assert `events` has no `acked_at` and `consumer_delivery` has `last_nack_attempt`.
- Confirm `schema.sql` matches.
- `ruff`/`lint-imports` are not applicable to raw DDL strings; verify by loading.

## Completion criteria

- `events.acked_at` absent from `_EVENTBUS_SCHEMA`.
- `consumer_delivery.last_nack_attempt` present in `_EVENTBUS_SCHEMA`.
- `consumer_delivery_failure_count` present in the `_EVENTBUS_SCHEMA` `consumer_delivery`
  block (and absent from its `events` block, where it was never defined).
- `schema.sql` mirror updated (via its row).

## Out of scope

- Migration of existing databases: `schema.py::_migrate` needs an
  `ALTER TABLE events DROP COLUMN acked_at` and an `ALTER TABLE consumer_delivery ADD
  COLUMN` for both `last_nack_attempt` and `consumer_delivery_failure_count` (the latter
  two are covered by fresh DDL). `schema.py` is an additional target file not listed in
  the Plan's `Implementation Target Files` — flag as a Plan Gap / re-freeze before
  executing the migration step.
- `schema.sql` edits (its own row).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement REQ-001/REQ-002/REQ-004 DDL changes in schema_sql.py | Completed | 20261009-191624 | 20261009-191624 | acked_at removed from events; last_nack_attempt + consumer_delivery_failure_count added to consumer_delivery; pre-existing schema.sql vs schema_sql.py divergence (published_at default, events.consumer_id) left untouched (out of scope) |
| 2 | Add or update tests per Validation plan | Completed | 20261009-191624 | 20261009-191624 | DDL validated by loading build_eventbus_schema_sql() into a fresh SQLite DB |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261009-191624 | 20261009-191624 | ruff format/check, mypy, bandit all clean |
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
- **Requirement ID**: `REQ-004`, `REQ-001`, `REQ-002`
- **Source issue**: `issues/done/20261007-154016_ebnack01_fix-eventbus-ack-and-nack-state-management.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261008-160952_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261009-071937
- **Related target files**: `scripts/db/schema_sql.py`