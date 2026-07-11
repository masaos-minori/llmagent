# Implementation: `workflow_schema_version` table and version recording

## Goal

Add a `workflow_schema_version` table to `workflow.sqlite` and a `WORKFLOW_SCHEMA_VERSION` constant, and idempotently record the current version whenever `create_workflow_schema()` runs.

## Scope

**In:**
- `scripts/db/schema_sql.py`: add the `workflow_schema_version` table DDL to `_WORKFLOW_SCHEMA`, add `WORKFLOW_SCHEMA_VERSION = "1.0.0"` constant
- `scripts/db/create_schema.py`: add version-recording logic, called at the end of `create_workflow_schema()`

**Out:**
- No change to existing table/column structure of `tasks`, `attempts`, `processed_events`, `artifacts`, `approvals`
- No versioned-migration framework — this adds version *tracking* only; `_WORKFLOW_MIGRATIONS` stays a plain list

## Assumptions

1. `workflow_schema_version` is an append-only log table (one row per version ever applied, `applied_at` timestamp) — "current version" is the row with the maximum `applied_at`.
2. A new row is inserted only when the latest existing row's version differs from `WORKFLOW_SCHEMA_VERSION` (or no row exists), so repeated `create_workflow_schema()` calls stay idempotent (no duplicate rows for an already-recorded version).
3. `WORKFLOW_SCHEMA_VERSION = "1.0.0"` is a fresh starting point (no prior version was ever tracked), covering the current full schema shape including all 5 pre-existing `_WORKFLOW_MIGRATIONS` entries.

## Implementation

### Target files

`scripts/db/schema_sql.py`, `scripts/db/create_schema.py`

### Procedure

1. In `scripts/db/schema_sql.py`, add near the top (module-level constant):
   ```python
   # Bump this constant whenever a new entry is added to _WORKFLOW_MIGRATIONS.
   WORKFLOW_SCHEMA_VERSION = "1.0.0"
   ```
2. In the same file, append to `_WORKFLOW_SCHEMA` (after the existing `approvals` table DDL):
   ```sql
   CREATE TABLE IF NOT EXISTS workflow_schema_version (
       version    TEXT NOT NULL,
       applied_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
   );
   ```
3. In `scripts/db/create_schema.py`, add:
   ```python
   def _record_workflow_schema_version(db) -> None:
       row = db.execute(
           "SELECT version FROM workflow_schema_version ORDER BY applied_at DESC LIMIT 1"
       ).fetchone()
       current = row[0] if row else None
       if current != WORKFLOW_SCHEMA_VERSION:
           db.execute(
               "INSERT INTO workflow_schema_version (version) VALUES (?)",
               (WORKFLOW_SCHEMA_VERSION,),
           )
   ```
   Import `WORKFLOW_SCHEMA_VERSION` from `db.schema_sql` at the top of the file.
4. Call `_record_workflow_schema_version(db)` at the end of `create_workflow_schema()`, after the existing `_WORKFLOW_MIGRATIONS` loop and before `db.commit()`.

### Method

Additive-only DDL (`CREATE TABLE IF NOT EXISTS`) plus a small idempotent recording function — no change to any existing table or migration.

### Details

- The comment above `WORKFLOW_SCHEMA_VERSION` is the sole safeguard against future drift between the constant and `_WORKFLOW_MIGRATIONS`'s actual length; no automated check enforces this (documented as an accepted, low-likelihood risk in the plan).
- `_record_workflow_schema_version()` reads the *actual* current row (not an in-memory assumption) before deciding whether to insert, so it is correct even if called against a DB whose version row was set by a different process/run.

## Validation plan

```bash
uv run ruff check scripts/db/schema_sql.py scripts/db/create_schema.py
uv run mypy scripts/db/schema_sql.py scripts/db/create_schema.py

# New-DB test
rm -f /tmp/wf_test.sqlite
uv run python -c "
import sqlite3
from db.create_schema import create_workflow_schema
db = sqlite3.connect('/tmp/wf_test.sqlite')
create_workflow_schema(db)
print(db.execute('SELECT version FROM workflow_schema_version').fetchall())
"
# expect: exactly one row, ('1.0.0',)

# Idempotency test: run again against the same file, confirm still exactly one row
uv run python -c "
import sqlite3
from db.create_schema import create_workflow_schema
db = sqlite3.connect('/tmp/wf_test.sqlite')
create_workflow_schema(db)
print(db.execute('SELECT version FROM workflow_schema_version').fetchall())
"
```

Expected outcome: a fresh DB ends up with exactly one `workflow_schema_version` row (`1.0.0`); re-running `create_workflow_schema()` against the same DB does not insert a duplicate row.
