# Implementation Procedure: eventbus schema.sql dlq_outbox baseline

## Goal

Add the `dlq_outbox` (new) table DDL to `scripts/eventbus/schema.sql` and raise the baseline
stamp to the post-outbox version, so a fresh `eventbus.sqlite` carries the outbox contract
(REQ-002, REQ-010; plan AC-1, AC-7).

## Scope

**In scope:**
- `scripts/eventbus/schema.sql`: append the `dlq_outbox` (new) DDL and index, change the stamp line.

**Out of scope:**
- Migration step registration (row 02), outbox runtime code (rows 03-06).

## Assumptions
- Verified at HEAD `124e340b4`: `schema.sql:3-45` holds the five tables +
  `PRAGMA user_version = 3;` (line 45).
- Hard sequencing gate: dbmig001 rows 01/02/04 (`shared/db_migrations.py`,
  `eventbus/migrations.py`, schema.sql ledger bump 3→4) must be implemented first.
  This row applies on top of the ledger baseline: stamp becomes `5` (registry head 4 + 1),
  per plan Assumption "baseline numbering follows dbmig001". If dbmig001 lands a different
  head version, use head + 1 and record the number here before implementing.
- Re-verified at HEAD `452a7335b` (2026-10-31): dbmig001 has landed on `origin/master`;
  `schema.sql` carried `PRAGMA user_version = 4;` and `eventbus/migrations.py` registry head
  is 4. Baseline stamp implemented as `5` (head 4 + 1), as predicted.

## Design decisions
- Column contract fixed by plan Design:
  `dlq_outbox(event_id TEXT PRIMARY KEY REFERENCES events(event_id), requested_at TEXT NOT
  NULL, status TEXT NOT NULL CHECK(status IN ('pending','done','failed')), attempts INTEGER
  NOT NULL DEFAULT 0, last_error TEXT, next_attempt_at TEXT, completed_at TEXT)`.
- Add `CREATE INDEX IF NOT EXISTS idx_dlq_outbox_status ON dlq_outbox(status,
  next_attempt_at);` (new) so the worker's pending scan is index-bounded; the same index
  text appears in row 02's migration SQL so baseline-created and migrated databases are
  shape-identical (fingerprint equivalence, `tests/db/test_eventbus_schema_equivalence.py`).
- `done` rows are retained as the durable generation record; reconciliation classifies
  orphans/mismatches against them (row 03). No deletes in this Plan.

## Alternatives considered
- Dropping the index (plan Design omits it): rejected — pending fetch is ordered by
  `next_attempt_at` (new) every 60s cycle; without an index the scan is a full table read of a
  growing durable record.

## Implementation
### Target file
`scripts/eventbus/schema.sql`

### Procedure
1. Append the `dlq_outbox` (new) DDL + index after the existing table definitions (before the
   stamp line).
2. Change `PRAGMA user_version = 3;` to the post-outbox baseline stamp (expected `5`, see
   Assumptions).

### Method
DDL-only edit; SQL text must be byte-identical to row 02's `mutation_sql` (new) body.

### Details
- `event_id` FK to `events(event_id)` mirrors the existing `events` DDL style; FKs are
  enforced at runtime (existing `PRAGMA foreign_keys` handling in `eventbus/db_conn.py`).
- No changes to the other five tables or their indexes.
- Implemented note (2026-10-31): the `dlq_outbox` block uses the DDL text byte-identical to
  row 02's `_DLQ_OUTBOX_SQL` (spaced `CHECK (status IN ('pending', 'done', 'failed'))` plus
  the trailing `FOREIGN KEY (event_id) REFERENCES events(event_id)` clause), so databases
  created from schema.sql and databases migrated through the registry step are
  fingerprint-equal. The Design decision column above lists the contract, not the exact SQL
  text; the SQL text above is the canonical form for both files.

## Compatibility considerations
- Existing databases at version 3/4 are untouched by this file; they upgrade only through
  row 02's registered step (REQ-010, AC-7). `eventbus/schema.py` fail-closed validation
  keeps refusing unregistered targets.
- `tests/db/test_eventbus_schema_equivalence.py` (dbmig001-owned) must stay green: baseline
  stamp == registry head after both plans land.

## Security considerations
- Static in-repo DDL only; no user input paths.

## Rollback considerations
- Revert the commit; deployed databases are unaffected (no ad-hoc DDL ever runs).

## Validation plan
- `uv run pytest tests/eventbus/test_eventbus_migrations.py
  tests/db/test_eventbus_schema_equivalence.py` — fresh DB created from baseline equals a
  migrated DB (fingerprint + stamp match), rows 10/row-02 harness tests pass.

## Completion criteria
- Fresh EventBus databases carry `dlq_outbox` (new) with the exact contract and stamp the new
  baseline; fingerprint equivalence tests pass.

## Out of Scope
- Migration registration (row 02), promotion/worker/reconcile code (rows 03-06), docs (rows 12-14).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `dlq_outbox` (new) DDL + index, bump stamp | Completed | 20261031-063000 | 20261031-063946 | Requires dbmig001 rows 01/02/04 implemented Implemented at 452a7335b; stamp 5 = registry head 4 + 1; DDL text byte-identical to row 02 _DLQ_OUTBOX_SQL |
| 2 | Run equivalence + migration tests | Completed | 20261031-063000 | 20261031-063946 | test_eventbus_migrations + test_eventbus_schema_version + test_eventbus_schema_equivalence all passed |
| 3 | Run `uv run python tools/check_db_separation.py` | Completed | 20261031-063000 | 20261031-063946 | dlq_outbox added to TABLE_OWNERSHIP[eventbus]; no violations |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | dbmig001 ledger baseline (3→4) not yet implemented; baseline stamp value is head + 1 | Yes | 20261031 (dbmig001 landed on origin/master at `452a7335b`; head=4, stamp=5) |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-002`, `REQ-010`
- **Source issue**: `issues/20261029-104501_dlqbox001_dlq-sqlite-outbox.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/done/20261029-221254_dlqbox001_dlq-sqlite-outbox.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-103000
- **Related target files**: `scripts/eventbus/schema.sql`