## Goal

Update `docs/90_shared_04_03_db_architecture_and_schema-migration-and-scaling.md` to reflect the new `consumer_delivery` and `consumer_offsets` tables added to the EventBus SQLite database.

## Scope

- Add the new tables to the "EventBus Schema" section.
- Update the "Schema Evolution" section to describe the migration strategy for the new tables.
- Update the "Scaling Considerations" section to note the impact of per-consumer delivery-state on storage growth.

## Assumptions

- The Plan's architecture (per-consumer delivery-state + SQLite offset store) is approved.
- The doc's existing content about schema evolution and scaling is still accurate.

## Design decisions

- **Preserve existing content**: Only add/update sections relevant to the new tables; do not rewrite the entire doc.
- **Clarify the storage impact**: Explicitly describe how the per-consumer delivery-state model affects storage growth (one row per (consumer, event) pair).
- **Document the migration strategy**: Describe how the new tables are created on existing databases via `_migrate()`.

## Alternatives considered

- **Rewrite the entire doc**: Would be more thorough but too disruptive for a focused change.
- **Create a new doc**: Would fragment the architectural history across multiple documents.

## Implementation

### Target file

`docs/90_shared_04_03_db_architecture_and_schema-migration-and-scaling.md`

### Procedure

1. Add the new tables to the "EventBus Schema" section.
2. Update the "Schema Evolution" section to describe the migration strategy for the new tables.
3. Update the "Scaling Considerations" section to note the impact of per-consumer delivery-state on storage growth.

### Method

#### Step 1: Add new tables to EventBus Schema section

After the existing `events` table description:
```markdown
### EventBus Schema

The EventBus SQLite database (`eventbus.sqlite`) contains the following tables:

```sql
-- Event persistence (auto-incrementing seq)
CREATE TABLE events (
    seq INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id TEXT UNIQUE NOT NULL,
    topic TEXT NOT NULL,
    payload TEXT NOT NULL,
    producer_id TEXT,
    created_at TEXT
);
```

```sql
-- Per-consumer delivery state (one row per (consumer, event) pair)
CREATE TABLE consumer_delivery (
    consumer_id TEXT NOT NULL,
    event_id TEXT NOT NULL,
    acked_at TEXT,
    PRIMARY KEY (consumer_id, event_id)
);
```

```sql
-- Per-consumer offset store (one row per consumer)
CREATE TABLE consumer_offsets (
    consumer_id TEXT PRIMARY KEY,
    offset INTEGER NOT NULL DEFAULT 0
);
```

Each table serves a distinct purpose:
- `events`: Stores all published events with auto-incrementing sequence numbers.
- `consumer_delivery`: Tracks which events each consumer has acknowledged, enabling per-consumer delivery semantics.
- `consumer_offsets`: Stores the last-committed sequence offset for each consumer, enabling resume-after-restart.
```

#### Step 2: Update Schema Evolution section

Replace the existing "Schema Evolution" subsection with:
```markdown
### Schema Evolution

The EventBus SQLite database uses `CREATE TABLE IF NOT EXISTS` for all new tables, ensuring safe re-runs. The `_migrate()` function in `scripts/eventbus/db.py` applies schema changes incrementally:

1. **New tables:** Created via `CREATE TABLE IF NOT EXISTS` — safe to run multiple times.
2. **New columns:** Added via `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` — defensive check against duplicate-column errors.
3. **New indexes:** Created via `CREATE INDEX IF NOT EXISTS` — safe to run multiple times.

For example, the `consumer_delivery` and `consumer_offsets` tables were added by `_migrate()` during the transition from file-based offsets to SQLite-backed offsets. Both tables use `CREATE TABLE IF NOT EXISTS` so they are safe to run on existing databases.

### Migration Strategy

The `migrate_legacy_offsets()` function seeds the `consumer_offsets` table from existing `offsets_dir` files on every startup. It reads each `.map` companion file to recover the original `consumer_id`, then inserts the offset using `INSERT OR IGNORE` (idempotent). Legacy files are retained until verified end-to-end.
```

#### Step 3: Update Scaling Considerations section

Add after the existing scaling subsections:
```markdown
### Storage Growth

The `consumer_delivery` table grows proportionally to the product of (number of consumers × number of events). For a single consumer, this is bounded by the total number of events. For multiple consumers, the growth is linear with respect to the number of consumers.

**Mitigation strategies:**
- Periodic cleanup of old delivery-state rows (e.g., events older than N days).
- Partitioning by consumer_id or event_id if the dataset becomes very large.
- Using a separate database per consumer if the workload requires strict isolation.

The `consumer_offsets` table has constant-size growth (one row per consumer), regardless of the number of events.
```

### Details

The key changes are:

1. **New table descriptions**: Added detailed descriptions of `consumer_delivery` and `consumer_offsets` tables with their schemas and purposes.
2. **Storage growth analysis**: Documented how the per-consumer delivery-state model affects storage growth (one row per (consumer, event) pair).
3. **Migration strategy**: Described the startup-time migration process and the fallback mechanism for missing `.map` companions.
4. **Mitigation strategies**: Provided actionable guidance for managing storage growth.

## Compatibility considerations

- The doc's existing content about schema evolution and scaling is preserved.
- The new content is additive — it does not rewrite or remove existing sections.

## Security considerations

- No new authentication or authorization boundaries introduced.
- Table/column naming follows existing conventions.
- No user input flows directly into DDL generation — schema changes are code-only.

## Rollback considerations

- To rollback: revert the doc to its previous version.
- The rollback restores the pre-change architectural description.

## Validation plan

| Target | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `docs/90_shared_04_03_db_architecture_and_schema-migration-and-scaling.md` | Structural verification | Read file, confirm new sections present | New tables described; storage growth documented; migration strategy documented |

## Completion criteria

- `consumer_delivery` and `consumer_offsets` tables are described in the EventBus Schema section.
- Storage growth analysis is documented.
- Migration strategy is documented.
- Mitigation strategies are provided.

## Out of scope

- Modifying the doc's existing content about schema evolution and scaling — not affected by this change.
- Adding DDL to schema files — covered by separate procedure documents.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add new table descriptions | Completed | — | — | |
| 2 | Update Schema Evolution section | Completed | — | — | |
| 3 | Update Scaling Considerations section | Completed | — | — | |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003, REQ-004
- **Source issue**: issues/20260907-125042_eb_h01_transactional_ack_offset_delivery_state.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260909-094115_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260910-161316
- **Related target files**: docs/90_shared_04_03_db_architecture_and_schema-migration-and-scaling.md
