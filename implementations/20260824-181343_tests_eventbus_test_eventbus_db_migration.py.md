## Goal

Add regression tests for `scripts/eventbus/db.py::_migrate()` covering column
add/drop, data preservation across migration, and idempotency of repeated calls.
No production code change.

## Scope

- In scope: create `tests/eventbus/test_eventbus_db_migration.py` with
  `test_migrate_adds_new_columns`, `test_migrate_preserves_data`,
  `test_migrate_is_idempotent`.
- Out of scope: any change to `scripts/eventbus/db.py` or `scripts/eventbus/schema.sql`;
  testing the `CREATE INDEX IF NOT EXISTS` branch beyond confirming `_migrate()` does
  not raise when it runs.

## Assumptions

- SQLite 3.46.1 (confirmed via `python3 -c "import sqlite3; print(sqlite3.sqlite_version)"`)
  supports `ALTER TABLE ... DROP COLUMN`, so the drop-column path in `_migrate()` is
  reachable without a version guard in the test.
- No existing test exercises `_migrate()`/`_init_schema()` from `scripts.eventbus.db`
  (verified via `rg "_migrate|_init_schema" tests/` — the only hit is an unrelated
  `_migrate_workflow_schema` in `tests/db/test_create_schema.py`, a different module).
  This is net-new coverage.

## Design decisions

- Use a file-based `tmp_path` SQLite connection (not `:memory:`) to match the
  on-disk I/O path `_init_schema`/`_migrate` run against in production.
- Build the pre-migration `events` table schema inline via `CREATE TABLE` +
  `ALTER TABLE ... ADD COLUMN retry_count`, rather than loading `schema.sql` (which
  already reflects the post-migration schema and would make it impossible to exercise
  the add/drop migration path at all).

## Alternatives considered

- Loading `schema.sql` and reverse-migrating columns out to construct the
  "old schema" fixture — rejected: more fragile than building the pre-migration table
  directly, and couples the test to `schema.sql`'s current content.

## Implementation

### Target file

`tests/eventbus/test_eventbus_db_migration.py` (new file)

### Procedure

1. Add a module docstring noting the `ALTER TABLE ... DROP COLUMN` SQLite-version
   dependency (added in SQLite 3.35.0).
2. Add a local pytest fixture/helper that creates the pre-migration `events` table
   (`retry_count` present; `delivery_failure_count`, `dlq_requeue_count`, and the two
   `idx_events_dlq_*` indexes absent) against a `tmp_path`-provided file-based
   `sqlite3.Connection`.
3. Implement `test_migrate_adds_new_columns`: call `_migrate(conn)` against the
   pre-migration fixture, then assert via `PRAGMA table_info(events)` that
   `delivery_failure_count` and `dlq_requeue_count` exist and `retry_count` is gone.
4. Implement `test_migrate_preserves_data`: same pre-migration fixture, insert one or
   more rows before calling `_migrate(conn)`, assert the same rows (by `event_id`) are
   readable afterward with unchanged `topic`/`payload`/`published_at` and
   `delivery_failure_count`/`dlq_requeue_count` defaulted to `0`.
5. Implement `test_migrate_is_idempotent`: call `_migrate(conn)` twice on the same
   connection; assert the second call does not raise and the resulting schema/data is
   identical to after the first call.

### Method

Import `_migrate` directly: `from scripts.eventbus.db import _migrate` — the same
import pattern used by other `tests/eventbus/test_eventbus_*.py` files that reach into
`scripts.eventbus.db`.

### Details

- `_migrate()` (`scripts/eventbus/db.py:76`) adds `delivery_failure_count` and
  `dlq_requeue_count` via `ALTER TABLE ... ADD COLUMN ... DEFAULT 0`, catching
  `sqlite3.OperationalError` with `"duplicate column name"` for idempotency; drops
  `retry_count` via `ALTER TABLE ... DROP COLUMN`, catching `"no such column"` for
  idempotency; then creates `idx_events_dlq_at`/`idx_events_dlq_seq` via
  `CREATE INDEX IF NOT EXISTS`. All three tests exercise this exact code path.
- No `tests/eventbus/test_eventbus_db_migration.py` file exists yet, and no
  `implementations/` or `implementations/done/` document currently targets this path —
  confirmed via `grep -rl "test_eventbus_db_migration" implementations/ implementations/done/`
  returning no matches. This is not duplicate work.

## Compatibility considerations

Test-only addition; no production code, schema, or public interface changes.

## Security considerations

N/A: test-only change against a temporary, non-production SQLite file; no secrets,
network, or external input involved.

## Rollback considerations

Delete the new test file; no other rollback steps required (no production code touched).

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `tests/eventbus/test_eventbus_db_migration.py` | Unit | `uv run pytest tests/eventbus/test_eventbus_db_migration.py -v` | 3 tests pass |
| `tests/eventbus/` (full suite) | Regression | `uv run pytest tests/eventbus/ -v` | No new failures |
| `scripts/eventbus/db.py` (untouched) | Static | `uv run ruff check scripts/eventbus/` + `uv run mypy scripts/eventbus/` | No new findings |

## Out of scope

Any change to `scripts/eventbus/db.py` or `scripts/eventbus/schema.sql`; version-guard
logic for `ALTER TABLE ... DROP COLUMN` (documented in the test module docstring
instead, matching `_migrate()`'s own lack of a runtime guard).

## Execution Status

### Execution Status

| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: no documentation update in scope |

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
- **Source issue**: N/A: not applicable in this phase (the source plan's own Traceability records `Source issue: N/A` and `Source requirement: requires/20260726-121037_require.md` — this plan predates the issue-to-plan pipeline merge)
- **Source requirement**: `requires/20260726-121037_require.md`
- **Source plan**: `plans/20260823-193128_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260824-181343
- **Related target files**: `tests/eventbus/test_eventbus_db_migration.py`

## Adversarial verification notes (this cycle)

Re-verified the plan against current code:
- `scripts/eventbus/db.py:76` confirms `_migrate()` matches the plan's Design/Details
  description exactly (add-column try/except duplicate-column pattern, drop-column
  try/except no-such-column pattern, `CREATE INDEX IF NOT EXISTS` for both DLQ indexes).
- Confirmed via `rg "_migrate|_init_schema" tests/` that no existing test exercises
  this code path (only an unrelated `_migrate_workflow_schema` in
  `tests/db/test_create_schema.py`).
- Confirmed no `implementations/` or `implementations/done/` document already targets
  `tests/eventbus/test_eventbus_db_migration.py`.
- No blocking unknowns, contradictions, or scope ambiguity found. The plan's own
  "Adversarial verification notes" section (fixing the source requirement's stale
  `_migrate()` quote) remains accurate and required no further change.
