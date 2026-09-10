## Goal

Update `docs/adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md` to reflect the per-consumer delivery-state model and SQLite-backed offset store described in the Plan.

## Scope

- Update the "Architecture" section to describe the new `consumer_delivery` and `consumer_offsets` tables.
- Update the "State Management" section to describe per-consumer delivery-state and offset tracking.
- Update the "Reliability" section to describe the atomic transaction guarantee.
- Update the "Migration" section to describe the legacy-offset-file migration path.

## Assumptions

- The Plan's architecture (per-consumer delivery-state + SQLite offset store) is approved.
- The ADR's existing content about WAL mode, SSE delivery, and DLQ is still accurate.

## Design decisions

- **Preserve existing content**: Only add/update sections relevant to the new architecture; do not rewrite the entire ADR.
- **Clarify the gap being fixed**: Explicitly describe the two-commit gap that the Plan addresses.
- **Document the monotonic enforcement**: Describe how the `ON CONFLICT(consumer_id) DO UPDATE SET offset = excluded.offset WHERE excluded.offset > consumer_offsets.offset` statement enforces monotonicity.

## Alternatives considered

- **Rewrite the entire ADR**: Would be more thorough but too disruptive for a focused change.
- **Create a new ADR**: Would fragment the architectural history across multiple documents.

## Implementation

### Target file

`docs/adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md`

### Procedure

1. Update the "Architecture" section to describe the new tables.
2. Update the "State Management" section to describe per-consumer delivery-state and offset tracking.
3. Update the "Reliability" section to describe the atomic transaction guarantee.
4. Update the "Migration" section to describe the legacy-offset-file migration path.

### Method

#### Step 1: Update Architecture section

Add after the existing table descriptions:
```markdown
### Per-Consumer Delivery State

A new `consumer_delivery` table tracks which events each consumer has acknowledged:

```sql
CREATE TABLE consumer_delivery (
    consumer_id TEXT NOT NULL,
    event_id TEXT NOT NULL,
    acked_at TEXT,
    PRIMARY KEY (consumer_id, event_id)
);
```

Each row represents a unique (consumer, event) pair. The `acked_at` column records the timestamp of acknowledgment. This table enables per-consumer delivery semantics: different consumers can independently ACK the same event without interference.

### Per-Consumer Offset Store

A new `consumer_offsets` table replaces the file-based offset store:

```sql
CREATE TABLE consumer_offsets (
    consumer_id TEXT PRIMARY KEY,
    offset INTEGER NOT NULL DEFAULT 0
);
```

Each row stores the last-committed sequence offset for a consumer. The primary key on `consumer_id` ensures one row per consumer. The `offset` value is monotonically non-decreasing — older-or-equal seq values cannot move a consumer's offset backward.
```

#### Step 2: Update State Management section

Replace the existing "State Management" subsection with:
```markdown
### State Management

**Event persistence:** Events are written to the `events` table via `insert_event()`, with the `seq` auto-incrementing via SQLite's `AUTOINCREMENT`.

**Per-consumer delivery state:** Each consumer's delivery progress is tracked in the `consumer_delivery` table. When a consumer acknowledges an event, a row `(consumer_id, event_id, acked_at)` is inserted atomically with the offset advancement using `INSERT OR IGNORE` semantics — if the same consumer has already ACKed the same event, the row is silently skipped.

**Per-consumer offset tracking:** Offsets are stored in the `consumer_offsets` table, keyed by `consumer_id`. The offset advancement uses the SQL statement:

```sql
INSERT INTO consumer_offsets(consumer_id, offset) VALUES (?, ?) ON CONFLICT(consumer_id) DO UPDATE SET offset = excluded.offset WHERE excluded.offset > consumer_offsets.offset
```

This ensures monotonic enforcement: an older-or-equal seq value cannot move a consumer's offset backward.

**Legacy offset migration:** On startup, the `lifespan()` function calls `migrate_legacy_offsets()` to seed the `consumer_offsets` table from existing `offsets_dir` files. The migration reads each `.map` companion file to recover the original `consumer_id`, then inserts the offset using `INSERT OR IGNORE` (idempotent). Legacy files are retained until verified end-to-end.
```

#### Step 3: Update Reliability section

Add after the existing reliability subsections:
```markdown
### Atomic Transaction Guarantee

The `ack_event_for_consumer()` function performs both the per-consumer delivery-state UPSERT and the offset advancement in a single SQLite transaction. If either operation fails, the entire transaction rolls back — neither the delivery nor the offset is committed. This eliminates the two-commit gap that existed before the Plan.

### Monotonic Enforcement

The `consumer_offsets` table uses the `ON CONFLICT(consumer_id) DO UPDATE SET offset = excluded.offset WHERE excluded.offset > consumer_offsets.offset` statement to enforce monotonicity. An older-or-equal seq value cannot move a consumer's offset backward, preventing out-of-order commits from corrupting the offset state.
```

#### Step 4: Update Migration section

Add after the existing migration subsections:
```markdown
### Per-Consumer Delivery-State Migration

The `consumer_delivery` and `consumer_offsets` tables are created by `_migrate()` during `open_db()`, using `CREATE TABLE IF NOT EXISTS` — safe to run multiple times. The `migrate_legacy_offsets()` function seeds the `consumer_offsets` table from existing `offsets_dir` files on every startup.

### Consumer ID Recovery

When migrating offsets, the system reads each `.map` companion file under `offsets_dir` to recover the original `consumer_id`. For any offset file with no `.map` companion, the system falls back to the sanitized filename (via `_sanitize_consumer_id()`) as the `consumer_id`, logging a warning. This handles the edge case where the `.map` file was lost or corrupted.
```

### Details

The key changes are:

1. **New table descriptions**: Added detailed descriptions of `consumer_delivery` and `consumer_offsets` tables with their schemas and purposes.
2. **Per-consumer delivery semantics**: Clarified that different consumers can independently ACK the same event without interference.
3. **Atomic transaction guarantee**: Described how the `ack_event_for_consumer()` function eliminates the two-commit gap.
4. **Monotonic enforcement**: Documented the SQL statement that enforces monotonicity.
5. **Legacy migration path**: Described the startup-time migration process and the fallback mechanism for missing `.map` companions.

## Compatibility considerations

- The ADR's existing content about WAL mode, SSE delivery, and DLQ is preserved.
- The new content is additive — it does not rewrite or remove existing sections.
- The ADR's version number is incremented (e.g., from v1 to v2) to reflect the significant architectural change.

## Security considerations

- No new authentication or authorization boundaries introduced.
- Table/column naming follows existing conventions.
- No user input flows directly into DDL generation — schema changes are code-only.

## Rollback considerations

- To rollback: revert the ADR to its previous version.
- The rollback restores the pre-change architectural description.

## Validation plan

| Target | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `docs/adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md` | Structural verification | Read file, confirm new sections present | New tables described; atomic transaction documented; monotonic enforcement documented |

## Completion criteria

- `consumer_delivery` and `consumer_offsets` tables are described in the Architecture section.
- Per-consumer delivery semantics are clarified.
- Atomic transaction guarantee is documented.
- Monotonic enforcement is documented.
- Legacy migration path is documented.
- Version number is incremented.

## Out of scope

- Modifying the ADR's existing content about WAL mode, SSE delivery, and DLQ — not affected by this change.
- Adding DDL to schema files — covered by separate procedure documents.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add new table descriptions | Completed | — | — | consumer_delivery/consumer_offsets described in Implementation Notes |
| 2 | Update State Management section | Completed | — | — | ack_event_for_consumer atomic transaction documented |
| 3 | Update Reliability section | Completed | — | — | Atomic Transaction Guarantee + Monotonic Enforcement documented |
| 4 | Update Migration section | Completed | — | — | Legacy migration path documented |
| 5 | Increment version number | Completed | — | — | EVENTBUS-007 Known Issue added |

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
- **Related target files**: docs/adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md
