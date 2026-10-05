## Goal

Add an index on `consumer_delivery(consumer_id, acked_at)` to enable efficient low-water-mark queries during reconnect. Without this index, the query degrades to a full table scan per reconnect.

## Scope

- Modify `scripts/eventbus/schema.sql`: add `CREATE INDEX IF NOT EXISTS` statement after the `consumer_delivery` table definition.

## Assumptions

- The `consumer_delivery` table has columns `consumer_id`, `event_id`, and `acked_at`.
- The low-water-mark query filters on `(consumer_id, acked_at IS NULL)` — confirmed by the query in `delivery_repo.py::get_resume_position()`.
- SQLite supports `CREATE INDEX IF NOT EXISTS` syntax.

## Design decisions

- Use `IF NOT EXISTS` to make the migration idempotent — safe to run multiple times without error.
- Index name `idx_consumer_delivery_consumer_ack` avoids implying it indexes only unacked rows (it indexes ALL rows, enabling both indexed lookups and covering scans).
- Composite index `(consumer_id, acked_at)` rather than separate single-column indexes — enables efficient filtering on both columns simultaneously.

## Alternatives considered

- Separate indexes on `consumer_id` and `acked_at`: rejected because a composite index provides better selectivity for the specific query pattern (filter by consumer, then check acked_at).
- Partial index on `(consumer_id, acked_at) WHERE acked_at IS NULL`: rejected because SQLite does not support partial indexes; would require application-level filtering.

## Implementation

### Target file

`scripts/eventbus/schema.sql`

### Procedure

Add `CREATE INDEX IF NOT EXISTS idx_consumer_delivery_consumer_ack ON consumer_delivery(consumer_id, acked_at);` after the `consumer_delivery` table definition.

### Method

1. In `schema.sql`: locate the `consumer_delivery` table definition.
2. After the closing `);` of the table definition, add the index creation statement.

### Details

**Change — Add index after `consumer_delivery` table definition:**

```sql
-- consumer_delivery table definition (existing)
CREATE TABLE IF NOT EXISTS consumer_delivery (
    ...
);

-- NEW: Index for efficient low-water-mark query in get_resume_position()
CREATE INDEX IF NOT EXISTS idx_consumer_delivery_consumer_ack
    ON consumer_delivery(consumer_id, acked_at);
```

**Rationale**: The low-water-mark query filters on `(consumer_id, acked_at IS NULL)`. An index on `(consumer_id, acked_at)` enables efficient lookup of unacked rows per consumer. Note: Index name changed from `idx_consumer_delivery_unacked` to avoid implying it indexes only unacked rows (it indexes ALL rows).

## Compatibility considerations

- Adding an index is a backward-compatible operation — existing consumers see no behavioral change.
- The index adds storage overhead proportional to the number of rows in `consumer_delivery`.
- For large datasets, the index may improve reconnect performance significantly.

## Security considerations

- No security impact. The index is a read-only optimization.
- No new data exposure — the index covers existing columns.

## Rollback considerations

- Drop the index with `DROP INDEX IF EXISTS idx_consumer_delivery_consumer_ack;`.
- If the index causes write performance degradation, dropping it restores the original behavior.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/eventbus/schema.sql | Static: format, lint | `uv run ruff format` / `ruff check` on the file | Clean; no new errors |
| Full suite | Regression | `uv run pytest tests/` | No new failures |
| Changed lines | Coverage | `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` | ≥ 90% on changed lines |

## Completion criteria

- [ ] Index `idx_consumer_delivery_consumer_ack` exists on `consumer_delivery(consumer_id, acked_at)`.
- [ ] `ruff format` and `ruff check` pass cleanly on the modified file.
- [ ] All affected integration tests pass.

## Out of scope

- Changes to `delivery_repo.py` (separate procedure document).
- Changes to `subscribe_route.py` (separate procedure document).
- Documentation updates beyond function docstrings.

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
- **Requirement ID**: REQ-003
- **Source issue**: issues/20261004-095313_eventbus001_eventbus-out-of-order-ack-skips-lower-seq-events-on-resume.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261004-100000_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261005-073241
- **Related target files**: scripts/eventbus/schema.sql
