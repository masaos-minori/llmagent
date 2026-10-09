## Goal

Drop the `events.acked_at` column from the reference schema DDL in `scripts/eventbus/schema.sql`, keeping the per-consumer `consumer_delivery.acked_at` intact. This mirrors the runtime DDL change in `scripts/db/schema_sql.py` (row 4); the two files must remain in sync.

## Scope

Modify `scripts/eventbus/schema.sql` only:

- Remove the `acked_at TEXT` column from the `events` table DDL (current line 10).
- Leave `consumer_delivery.acked_at` (line 29) unchanged — that column is per-consumer and is NOT removed by REQ-004.
- Keep the `events` index definitions unchanged.

Referenced/updated by other documents (not modified here): the runtime DDL SSOT (`scripts/db/schema_sql.py`, row 4), the migration path that drops the column from existing databases (`scripts/eventbus/schema.py` `_migrate`), and the repository code that must stop reading `events.acked_at` (`scripts/eventbus/delivery_repo.py` row 1, `scripts/eventbus/ack_route.py` row 2).

## Assumptions

- `schema.sql` is a human-readable reference copy of the runtime DDL defined in `schema_sql.py` `_EVENTBUS_SCHEMA`; both must define identical tables/columns.
- Existing databases drop the column via the `_migrate` path (see Rollback/Compatibility), not by re-creating the table.

## Design decisions

- **Remove only the `events` column**: the per-consumer `consumer_delivery.acked_at` is retained; deleting it would break ACK state and is out of REQ-004 scope.
- **Keep DDL parity**: the edit is applied identically to `schema.sql` and `schema_sql.py` so fresh installs (runtime DDL) and the reference file never diverge.

## Alternatives considered

- Comment out vs delete: delete the column line outright (do not comment) so a future reader/migration cannot assume it exists.

## Implementation

### Target file

`scripts/eventbus/schema.sql`

### Procedure

1. Delete the `acked_at               TEXT,` line from the `events` table definition (current line 10), preserving surrounding column indentation and trailing-comma rules.
2. Confirm `consumer_delivery.acked_at` (line 29) is untouched.
3. Apply the identical removal to `scripts/db/schema_sql.py` `_EVENTBUS_SCHEMA` (`events.acked_at`, line 242) so the two files stay in sync.

### Method

- Remove exactly the `acked_at` column line under the `events` CREATE TABLE; do not alter `delivery_failure_count`, `dlq_at`, or the index block.
- In `schema_sql.py`, also update the header comment at line 233 (`"-- acked_at and dlq_at are nullable ..."`) to reflect that only `dlq_at` is now nullable on `events` (e.g. `"-- dlq_at is nullable (unset until dead-lettered)"`).

### Details

- `events.acked_at` is currently referenced in `delivery_repo.py` `nack_event()` base WHERE (line 92) and `ack_route.py` `-2` branch (lines 190, 193); those reads are removed under REQ-004 by rows 1 and 2. This document only changes the DDL.
- Do not touch `consumer_delivery.acked_at` anywhere in this file.

## Compatibility considerations

- Fresh installs build the schema from the runtime DDL (`schema_sql.py`) without `events.acked_at`.
- Existing installs drop the column via the `_migrate` path — see the Plan Gap note: the DROP COLUMN statement must be added to `scripts/eventbus/schema.py` `_migrate`, which is not a listed target file.

## Security considerations

- Schema DDL change; no security impact.

## Rollback considerations

- Re-adding the `acked_at` column line to both files restores the prior schema shape (existing DBs still need their own migration revert).

## Validation plan

- `rg "acked_at" scripts/eventbus/schema.sql` — expect only the `consumer_delivery` occurrence remains.
- Diff `schema.sql` against `schema_sql.py` `_EVENTBUS_SCHEMA` `events` table — columns must match.
- Migration test: an existing `eventbus.sqlite` with `events.acked_at` migrates to no such column without data loss in other columns (REQ-004). Note the migration statement lives in `schema.py` (Plan Gap).
- ruff + mypy (no source change here); documentation review.

## Completion criteria

- `events` table in `schema.sql` no longer declares `acked_at`.
- `consumer_delivery.acked_at` still present.
- `schema.sql` and `schema_sql.py` `events` tables are column-identical.

## Out of scope

- The `_migrate` DROP COLUMN for existing databases (`schema.py`, not a listed target — Plan Gap).
- Removing `consumer_delivery.acked_at` (out of REQ-004 scope).
- Repository reads of `acked_at` (rows 1-2).
- REQ-001's `consumer_delivery` column additions (see Plan Gap note).

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
- **Requirement ID**: `REQ-004` (drop `events.acked_at` from reference DDL)
- **Source issue**: `issues/done/20261007-154016_ebnack01_fix-eventbus-ack-and-nack-state-management.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261008-160952_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261009-132618
- **Related target files**: `scripts/eventbus/schema.sql`

> **Plan Gap (needs plan amendment)**: (1) The `events.acked_at` DROP COLUMN migration for existing databases executes in `scripts/eventbus/schema.py` `_migrate`, which is not a listed target file — the plan's "existing `_migrate` approach" points at a file outside scope. (2) REQ-001 adds `consumer_delivery_failure_count` / `last_nack_attempt` to the `consumer_delivery` table and (per design intent) removes `events.consumer_delivery_failure_count`; those DDL edits belong here too but are tagged REQ-004 only. (3) The plan's Target Files evidence line "acked_at column line 242" is wrong for this file — `acked_at` is at `schema.sql` line 10 (line 242 is in `schema_sql.py`).
