## Goal

Create `scripts/eventbus/schema.py` — Connection layer + schema/migration responsibility per REQ-001. Extracts `_SCHEMA_PATH`, `_apply_eventbus_pragmas()`, `_init_schema()`, `_migrate()` from `db.py`.

## Scope

New file containing SQLite connection lifecycle, pragma application, schema initialization, and additive migration logic.

## Assumptions

- `_SCHEMA_PATH` points to `scripts/eventbus/schema.sql` relative to the project root.
- `_apply_eventbus_pragmas()` applies WAL mode and other pragmas before schema creation.
- `_init_schema()` creates tables from `schema.sql` if they don't exist.
- `_migrate()` adds new columns/indexes to existing tables (additive only).
- `_db_lock` singleton must be shared with `db_conn.py`.

## Design decisions

- Connection layer owns pragma application and schema lifecycle.
- Schema layer owns DDL statements and migration logic.
- Shared constants (`_COL_EVENT_ID`, etc.) imported from `_constants.py`.
- Migration uses `PRAGMA table_info()` to check column existence before ALTER TABLE.

## Alternatives considered

- Keeping pragma application in each caller rejected because it violates DRY and makes it hard to ensure consistency.
- Using SQLAlchemy migrations rejected because it would add a dependency (REQ-010).

## Implementation

### Target file

`scripts/eventbus/schema.py`

### Procedure

Extract connection lifecycle, pragma application, schema initialization, and migration logic from `db.py` into this module.

### Method

1. Define `_SCHEMA_PATH` constant pointing to `scripts/eventbus/schema.sql`.
2. Implement `_apply_eventbus_pragmas(conn)` to apply WAL mode and other pragmas.
3. Implement `_init_schema(conn)` to read and execute `schema.sql`.
4. Implement `_migrate(conn)` to add new columns/indexes to existing tables.
5. Export public symbols: `_SCHEMA_PATH`, `_apply_eventbus_pragmas()`, `_init_schema()`, `_migrate()`.

### Details

```python
"""Schema layer: schema definition, migration logic."""

from pathlib import Path
from sqlite3 import Connection

# _SCHEMA_PATH is relative to the project root
_SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"

def _apply_eventbus_pragmas(conn: Connection) -> None:
    """Apply eventbus-specific pragmas to the connection."""
    conn.execute("PRAGMA journal_mode=WAL")
    # Add other pragmas as needed
    conn.commit()

def _init_schema(conn: Connection) -> None:
    """Initialize the eventbus schema from schema.sql if tables don't exist."""
    schema_sql = _SCHEMA_PATH.read_text(encoding="utf-8")
    conn.executescript(schema_sql)
    conn.commit()

def _migrate(conn: Connection) -> None:
    """Add new columns/indexes to existing tables (additive migration)."""
    # Check if consumer_delivery table exists
    cur = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='consumer_delivery'"
    )
    if cur.fetchone() is None:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS consumer_delivery (
                consumer_id TEXT NOT NULL,
                event_id TEXT NOT NULL,
                acked_at TEXT,
                PRIMARY KEY (consumer_id, event_id)
            )
        """)
        conn.commit()

    # Check if consumer_offsets table exists
    cur = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='consumer_offsets'"
    )
    if cur.fetchone() is None:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS consumer_offsets (
                consumer_id TEXT PRIMARY KEY,
                offset INTEGER NOT NULL DEFAULT 0
            )
        """)
        conn.commit()

    # Add new columns to events table if they don't exist
    # Use PRAGMA table_info to check column existence
    cur = conn.execute("PRAGMA table_info(events)")
    columns = {row[1] for row in cur.fetchall()}
    for col_name in ["delivery_failure_count", "cycle_failure_count", "dlq_requeue_count"]:
        if col_name not in columns:
            conn.execute(f"ALTER TABLE events ADD COLUMN {col_name} INTEGER NOT NULL DEFAULT 0")  # nosec B608
    conn.commit()
```

## Compatibility considerations

- `_SCHEMA_PATH` path resolution uses `Path(__file__).resolve().parent` — works regardless of working directory.
- `_migrate()` uses `PRAGMA table_info()` to check column existence before ALTER TABLE — safe for incremental upgrades.
- All migration operations are idempotent (CREATE IF NOT EXISTS, conditional ALTER TABLE).

## Security considerations

- Column names in ALTER TABLE come from module-level constants (not user input) — safe from SQL injection.
- Parameterized queries used for all values in SELECT/INSERT/UPDATE statements.

## Rollback considerations

- If migration fails, rollback via `conn.rollback()`.
- Keep original `db.py` until full test suite passes.
- Test migration path separately: create DB with old schema, apply `_migrate()`, confirm new columns exist.

## Validation plan

- Run full eventbus test suite: `uv run pytest tests/eventbus/` — 311 collected tests.
- Verify migration path: create DB with old schema, apply `_migrate()`, confirm new columns exist.
- Verify WAL mode remains default after `_apply_eventbus_pragmas()`.

## Completion criteria

- `_SCHEMA_PATH` resolves to `scripts/eventbus/schema.sql`.
- `_apply_eventbus_pragmas()` applies WAL mode.
- `_init_schema()` reads and executes `schema.sql`.
- `_migrate()` adds new columns/indexes to existing tables.
- All 311 eventbus tests pass.

## Out of scope

- Changing HTTP API surface.
- Adding new database indexes beyond `_migrate()`.
- Migrating from SQLite to another engine.
- Adding connection pooling/async drivers.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Create schema.py with _SCHEMA_PATH constant | Pending | — | — | |
| 2 | Implement _apply_eventbus_pragmas() | Pending | — | — | |
| 3 | Implement _init_schema() | Pending | — | — | |
| 4 | Implement _migrate() | Pending | — | — | |
| 5 | Run full eventbus test suite | Pending | — | — | |

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
- **Requirement ID**: REQ-001
- **Source issue**: issues/20260919-160141_refactor_001_eventbus_db_py_refactoring.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260919-170923_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260919-205935
- **Related target files**: scripts/eventbus/schema.py
