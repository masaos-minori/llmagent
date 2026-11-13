## Goal
Remove the `dlq_requeue_count` and `consumer_id` columns from the `events` table in `scripts/eventbus/schema.sql`, making the old shape refuse the fingerprint gate (REQ-004 / AC-4), covering the schema-gate-test companion.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Line numbers are from the 2026-11-13 plan revalidation; locate each passage by its quoted text and skip and report it if it is already correct.
- Verified 2026-11-13: `schema.sql` lines 11 and 13 define `dlq_requeue_count INTEGER NOT NULL DEFAULT 0` and `consumer_id TEXT`; no index references either column; `consumer_id` has no writer in either `INSERT INTO events` and no reader in `scripts` (zero-reference searches rerun in row 06's Procedure).
- The fingerprint gate builds the canonical shape from `schema.sql` at runtime (`scripts/shared/schema_fingerprint.py` stores no column list — Plan Corrections), so this DDL edit alone moves the fingerprint: an existing older database is refused with the archive-and-recreate error, and no migration step is registered (`compatrm001`; Plan Design item 1, 5, 6).
- The deployed `eventbus.sqlite` already differs from the current schema (UNK-01, recorded in the adrrev005 Plan); deployment timing is a Phase 6 operator decision, not this row.
- `test_eventbus_schema_version.py` qualifies as a companion: it lies under `tests/`, exactly one other target row (`schema.sql`) names it in `Related Tests`, and its change is mechanical (swap the dropped column).

## Design decisions
- Register no migration step by design (Plan Design: "no migration, archive and recreate"); the refusal IS the intended path.

## Alternatives considered
- Keep `consumer_id` "for possible external readers": rejected — the Plan pairs it with the maintainer-decided `dlq_requeue_count` removal; UNK-02 asks the operator before deploy, not before this edit.

## Implementation
### Target file
`scripts/eventbus/schema.sql`

### Procedure
1. Delete the two `events`-table column lines (lines 11 and 13): `dlq_requeue_count      INTEGER NOT NULL DEFAULT 0,` and `consumer_id            TEXT`.
2. Keep every index statement byte-identical (verified 2026-11-13: none names either column).

### Method
- DDL deletion only; the `events` table keeps `seq, event_id, topic, payload, producer, published_at, redelivered_from, dlq_at`.

### Details
- `consumer_delivery.consumer_id` and `consumer_offsets.consumer_id` are different tables and stay (they are not the `events` column).
- Verification pass 2026-11-13 (adversarial re-check): line 13 (`consumer_id TEXT`) is the last `events` column and carries no trailing comma; deleting it requires also dropping the trailing comma on line 12 (`dlq_at                 TEXT,`), otherwise the column list ends with a comma before `);` and the DDL is invalid SQL. After the edit `dlq_at` is the final column.
- After the edit, `rg -n "dlq_requeue_count|_COL_CONSUMER_ID" scripts` returns nothing (AC-4) once rows 04-06 have run; this row is itself the last `scripts/` carrier of the literal `dlq_requeue_count` (`schema.sql:11`), so row 06's AC-4 search gate is evaluated together with this row at the cycle-18 group gate.

### Companion test files
- `tests/eventbus/test_eventbus_schema_version.py`
  - Procedure: in `test_malformed_shape_is_refused_and_left_unchanged`, replace `raw.execute("ALTER TABLE events DROP COLUMN consumer_id")  # nosec B608 — fixed test DDL` (line 103) with `raw.execute("ALTER TABLE events DROP COLUMN published_at")  # nosec B608 — fixed test DDL` (a plain non-indexed column that stays in the new schema), and `assert "consumer_id" not in columns` (line 112) with `assert "published_at" not in columns`; the refusal match string `"columns differ"` and all other tests stay.
  - Validation: `uv run pytest tests/eventbus/test_eventbus_schema_version.py` passes (old-shape refusal still fires).
- `tests/eventbus/test_eventbus_dlq_index.py` (discovered during execution, 2026-11-14 — not in the original Impact Scope): `test_dlq_index_plan_matches_production_sql` asserted `idx_events_dlq_seq` for the count query's EXPLAIN plan. Verified empirically (git HEAD DDL vs post-edit DDL, in-memory `EXPLAIN QUERY PLAN`): removing the two columns legitimately flips the planner's covering-index choice to `idx_events_dlq_at`. The assertion was relaxed to `USING COVERING INDEX idx_events_dlq_` — the test's invariant (covering DLQ index, no table scan, no sort) is preserved.

### Execution notes (2026-11-14)
- The DDL edit alone produced 4 failures + 25 setup errors in `tests/eventbus`. Second root cause: the fingerprint gate correctly rejecting persistent `/tmp` scratch databases created by earlier runs under the old DDL (fixed-path fixtures, e.g. `/tmp/test-no-double-auth/eventbus.sqlite` dated 2026-11-07). Cleared 11 stale test scratch sqlite files under the tests' fixed `/tmp/test-*` paths; no production DB touched. This is the archive-and-recreate behavior the gate documents; after cleanup 524 tests passed, then the relaxed plan assertion closed the last failure.

## Compatibility considerations
- This is the High-blast-radius row (Affected areas table): every pre-change `eventbus.sqlite` fails `open_db()` until the operator recreates it (Plan Risks row 1, UNK-01 — deployment hand-off).

## Security considerations
N/A: DDL deletion only.

## Rollback considerations
N/A: revert the commit; note that databases created after this change carry the new fingerprint and must be recreated on rollback.

## Validation plan
| Target | Testing strategy | Tool / command | Expected outcome |
|---|---|---|---|
| Schema gate | Integration | `uv run pytest tests/eventbus/test_eventbus_schema_version.py` | Pass (new DB created; old shape refused byte-identical) |
| DDL change | Static | `uv run python tools/check_db_separation.py` | Pass |
| AC-4 | Search | `rg -n "dlq_requeue_count|_COL_CONSUMER_ID" scripts` (after rows 04-06) | No match |
| Whole suite | Integration | `uv run pytest tests/eventbus` | Pass |

## Completion criteria
- AC-4: neither column in `schema.sql`; an old-shape file is refused and left byte-identical (companion test proves it).

## Out of Scope
- Migration registry entries (none by design); the deployed database file itself (Phase 6 hand-off, UNK-01).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20261114-001837 |  |
| 2 | Add or update tests per Validation plan | Completed | — | 20261114-001837 | companion swap verified already applied (published_at); dlq_index plan assertion relaxed (documented) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261114-001837 | pytest tests/eventbus 525 passed; schema gate 5 passed; db-separation No violations; bandit gate exit 0; ruff check/format pass; mypy canonical Success |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261114-001851 | Documentation out of scope: docs edits belong to rows 10-13 and 14; only companion tests in scope |

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
- **Requirement ID**: REQ-004 / AC-4
- **Source issue**: issues/20261110-170926_rmcompat005_eventbus-dlq-leftovers.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261112-121134_rmcompat005_eventbus-dlq-leftovers.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261113-173721
- **Related target files**: `scripts/eventbus/schema.sql`, `tests/eventbus/test_eventbus_schema_version.py` (companion)