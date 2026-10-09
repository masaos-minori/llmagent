## Goal

Remove the `events.acked_at` column from the runtime DDL source of truth, `_EVENTBUS_SCHEMA`, in `scripts/db/schema_sql.py`, so fresh installs of `eventbus.sqlite` no longer create it. Keep `consumer_delivery.acked_at` and stay column-identical with the reference `schema.sql` (row 3).

## Scope

Modify `scripts/db/schema_sql.py` only:

- Delete `acked_at               TEXT,` from the `events` table inside `_EVENTBUS_SCHEMA` (current line 242).
- Update the header comment at line 233 (`"-- acked_at and dlq_at are nullable ..."`) to reflect that only `dlq_at` is now nullable on `events`.
- Leave `consumer_delivery.acked_at` (line 259) unchanged.

Referenced/updated by other documents (not modified here): the reference copy `scripts/eventbus/schema.sql` (row 3), the migration path that drops the column from existing databases (`scripts/eventbus/schema.py` `_migrate`), and repository reads of `events.acked_at` (`scripts/eventbus/delivery_repo.py` row 1, `scripts/eventbus/ack_route.py` row 2).

## Assumptions

- `_EVENTBUS_SCHEMA` is the runtime DDL SSOT via `create_schema.py` → `build_eventbus_schema_sql()`; `schema.sql` is a reference copy. Both must match.
- Fresh installs use this DDL directly; existing installs are handled by the `_migrate` path.

## Design decisions

- **Edit the SSOT, then mirror**: remove the column here first (the authoritative DDL), then apply the identical removal to `schema.sql` (row 3).
- **Update the stale header comment** so documentation inside the DDL does not claim `acked_at` still exists.
- **Retain `consumer_delivery.acked_at`** — per-consumer ACK state, out of REQ-004 scope.

## Alternatives considered

- Editing only `schema.sql` and not `_EVENTBUS_SCHEMA`: rejected — `schema_sql.py` is the runtime SSOT; editing the reference copy alone would leave fresh installs with the column.

## Implementation

### Target file

`scripts/db/schema_sql.py`

### Procedure

1. Inside `_EVENTBUS_SCHEMA` (line 229), delete the `acked_at               TEXT,` line from the `events` table (current line 242), preserving indentation/comma rules.
2. Update the header comment at line 233 to remove the `acked_at` reference (e.g. `"-- dlq_at is nullable (unset until dead-lettered)"`).
3. Confirm `consumer_delivery.acked_at` (line 259) is untouched.
4. Mirror the identical removal in `scripts/eventbus/schema.sql` (row 3).

### Method

- Remove exactly the `events.acked_at` column line; do not touch `delivery_failure_count`, `cycle_failure_count`, `dlq_at`, or the index block.
- Do not modify `build_eventbus_schema_sql()` (line 271-273) — it simply returns the constant.

### Details

- After this edit, no fresh-install DDL declares `events.acked_at`. Existing databases still hold the column until the `_migrate` DROP runs (see Compatibility / Plan Gap).
- `_EVENTBUS_SCHEMA` is a module-level string literal (lines 229-268); edit within it only.

## Compatibility considerations

- Fresh installs: no `events.acked_at` (runtime DDL).
- Existing installs: the column must be dropped by a `_migrate` statement — see Plan Gap (the DROP lives in `schema.py`, not a listed target).
- Repository code reading `events.acked_at` (delivery_repo.py line 92, 115; ack_route.py lines 190, 193) must be removed (rows 1-2) or existing-DB queries will fail.

## Security considerations

- Schema DDL change; no security impact.

## Rollback considerations

- Re-adding the column line to `_EVENTBUS_SCHEMA` restores the prior fresh-install schema; existing-DB revert needs its own migration.

## Validation plan

- `rg "acked_at" scripts/db/schema_sql.py` — expect only the `consumer_delivery` occurrence and the removed header-comment reference.
- Column-parity diff between `_EVENTBUS_SCHEMA` `events` table and `schema.sql` `events` table.
- `db/create_schema.py` smoke: build a fresh `eventbus.sqlite` and confirm `events` has no `acked_at` while `consumer_delivery` retains it.
- Migration test against a pre-populated DB (statement in `schema.py` — Plan Gap).
- ruff + mypy on `schema_sql.py`.

## Completion criteria

- `_EVENTBUS_SCHEMA` `events` table no longer declares `acked_at`.
- `consumer_delivery.acked_at` retained.
- `schema.sql` and `schema_sql.py` `events` tables column-identical.

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
- **Requirement ID**: `REQ-004` (drop `events.acked_at` from runtime DDL SSOT)
- **Source issue**: `issues/done/20261007-154016_ebnack01_fix-eventbus-ack-and-nack-state-management.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261008-160952_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261009-132618
- **Related target files**: `scripts/db/schema_sql.py`

> **Plan Gap (needs plan amendment)**: (1) The `events.acked_at` DROP COLUMN migration for existing databases runs in `scripts/eventbus/schema.py` `_migrate`, which is not a listed target file — the plan's "existing `_migrate` approach" points at a file outside scope. (2) REQ-001 adds `consumer_delivery_failure_count` / `last_nack_attempt` to `consumer_delivery` and (per design intent) removes `events.consumer_delivery_failure_count`; those DDL edits belong here too but are tagged REQ-004 only.
