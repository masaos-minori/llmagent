# Implementation: Remove the `events.retry_count` schema artifact column (Phase 4)

## Goal

Remove the `retry_count` column from the Event Bus `events` table — a schema artifact that is never read or written by any code path (superseded by `delivery_failure_count`) — via an idempotent `ALTER TABLE ... DROP COLUMN` migration, without requiring any production data backfill.

## Scope

**In:**
- `scripts/eventbus/schema.sql`: remove `retry_count INTEGER NOT NULL DEFAULT 0, -- deprecated; use delivery_failure_count` from the `CREATE TABLE events` statement (affects fresh DB creation only)
- `scripts/eventbus/db.py`: add a `DROP COLUMN` step to `_migrate()` for existing databases, following the same idempotent try/except pattern already used for the additive `delivery_failure_count`/`dlq_requeue_count` migrations
- `tests/test_eventbus_dlq_promotion.py`, `tests/test_create_schema.py`: remove or update assertions referencing `retry_count`
- `docs/06_eventbus_03_persistence_schema_and_replay.md`, `docs/06_eventbus_06_reference_api.md`, `docs/06_eventbus_90_inconsistencies_and_known_issues.md`: remove the `retry_count` row from schema tables

**Out:**
- `delivery_failure_count` and `dlq_requeue_count` columns — unchanged, these are the actively used replacements
- No application-level data migration/backfill — `retry_count` has never been written to, so there is no data to preserve

## Assumptions

1. `retry_count` is never written or read by any Event Bus code path — confirmed via `grep -rn "retry_count" scripts/eventbus --include="*.py"` returning no matches, and corroborated by `docs/06_eventbus_90_inconsistencies_and_known_issues.md`, which already documents it as "a schema artifact only."
2. The runtime SQLite version supports `ALTER TABLE ... DROP COLUMN` (available since SQLite 3.35.0, released 2021-03-12). Confirmed in the current development environment: `python3 -c "import sqlite3; print(sqlite3.sqlite_version)"` → `3.46.1`. The production environment (`/opt/llm/venv/`, Python 3.13) must be checked with the same command before deploying this change — if it reports a version below 3.35.0, this migration cannot run as designed and must be redesigned (e.g., rebuild-table approach) before Phase 4 proceeds in production.
3. No user-approved requirement exists for preserving historical `retry_count` values (the user explicitly approved "no production data migration needed, but implement the schema change" in the plan's clarifying questions).

## Implementation

### Target file

1. `scripts/eventbus/schema.sql`
2. `scripts/eventbus/db.py`
3. `tests/test_eventbus_dlq_promotion.py`
4. `tests/test_create_schema.py`
5. The 3 doc files listed in Scope

### Procedure

1. Before writing any code, run `python3 -c "import sqlite3; print(sqlite3.sqlite_version)"` in the target deployment environment and confirm the version is >= 3.35.0.
2. In `scripts/eventbus/schema.sql`, delete the `retry_count` column line from the `CREATE TABLE events (...)` statement.
3. In `scripts/eventbus/db.py`'s `_migrate()` function, add a new block that attempts `ALTER TABLE events DROP COLUMN retry_count`, catching `sqlite3.OperationalError` and treating "no such column" (already dropped, or fresh DB created from the updated `schema.sql`) as success — mirroring the existing pattern used for the `ADD COLUMN` loop.
4. Update `tests/test_eventbus_dlq_promotion.py` and `tests/test_create_schema.py` to stop asserting on `retry_count`'s presence/default value.
5. Update the 3 doc files to remove the `retry_count` row from their schema tables.
6. Run the standard validation sequence (see Validation plan).
7. Manually verify migration idempotency: start the Event Bus twice in a row against the same on-disk `.sqlite` file and confirm the second startup does not raise on the `DROP COLUMN` step.

### Method

Idempotent destructive schema migration, following the existing additive-migration pattern in `_migrate()` but inverted (drop instead of add), guarded by catching the SQLite "column does not exist" error on repeat runs.

### Details

```python
# In _migrate(), alongside the existing ADD COLUMN loop:
try:
    conn.execute("ALTER TABLE events DROP COLUMN retry_count")
    logger.info("migrated: dropped column retry_count from events")
except sqlite3.OperationalError as exc:
    if exc.args and "no such column" in exc.args[0].lower():
        pass  # already dropped, or table created fresh without it
    else:
        raise
```

- This must run inside the existing `_migrate(conn)` code path (invoked only when the `events` table already exists), so fresh databases created from the updated `schema.sql` never attempt the `DROP COLUMN` (the column will not exist to drop) — the try/except guard handles that case safely regardless.
- No index or foreign key references `retry_count`, so no secondary schema object needs updating.
- The column removal is irreversible without a backup; standard operational practice (a pre-migration snapshot of the `.sqlite` file) should be followed at deploy time even though no data is lost by design.

## Validation plan

```bash
uv run ruff check scripts/eventbus/
uv run mypy scripts/eventbus/
uv run bandit -r scripts/eventbus/ -c pyproject.toml
uv run pytest tests/test_eventbus_dlq_promotion.py tests/test_create_schema.py -v
uv run pytest tests/ -k eventbus -v

# Idempotency check: start twice against the same DB file, expect no errors on the second run
python3 -c "from eventbus.db import open_db; open_db('/tmp/eventbus_migration_check.sqlite')"
python3 -c "from eventbus.db import open_db; open_db('/tmp/eventbus_migration_check.sqlite')"

grep -rn "retry_count" scripts/eventbus tests --include="*.py"   # expect no output
```

Expected outcome: schema and migration tests pass, the migration is idempotent across repeated startups, and no code references `retry_count` afterward.
