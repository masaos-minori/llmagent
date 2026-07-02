# Implementation: create_schema.py - Add create_eventbus_schema() and import

## Goal

Add `create_eventbus_schema()` function to create_schema.py and update `create_schema()` to call it.

## Scope

- scripts/db/create_schema.py: add import, add create_eventbus_schema(), update create_schema(), update docstring

## Assumptions

1. build_eventbus_schema_sql() is implemented in 52 (or same PR)
2. SQLiteHelper("eventbus") is implemented in 51
3. No migration logic for eventbus schema (DDL-only, no ADD COLUMN history)

## Implementation

### Target file

- `scripts/db/create_schema.py`

### Procedure

1. Add import: `from db.schema_sql import build_eventbus_schema_sql`
2. Add `create_eventbus_schema()` function after `create_workflow_schema()`
3. Update `create_schema()` to call `create_eventbus_schema()`
4. Update module docstring to include eventbus.sqlite (4 DBs)

### Method

- Follow existing pattern exactly (same style as create_workflow_schema)

### Details

Change 1: Add import (after line 25):
```python
from db.schema_sql import (
    build_rag_schema_sql,
    build_session_schema_sql,
    build_workflow_schema_sql,
    build_eventbus_schema_sql,  # NEW - one line addition
)
```

Change 2: Add create_eventbus_schema() function after create_workflow_schema():
```python
def create_eventbus_schema() -> None:
    """Create eventbus.sqlite tables (events)."""
    with SQLiteHelper("eventbus").open(write_mode=True) as db:
        try:
            db.executescript(build_eventbus_schema_sql())
        except (sqlite3.OperationalError, sqlite3.DatabaseError) as e:
            logger.error("Failed to execute Event Bus schema DDL: %s", e)
            raise
    logger.info("Event Bus schema created successfully.")
```

Change 3: Update create_schema() function:
```python
def create_schema() -> None:
    """Create schemas for rag.sqlite, session.sqlite, workflow.sqlite, and eventbus.sqlite."""
    create_rag_schema()
    create_session_schema()
    create_workflow_schema()
    create_eventbus_schema()  # NEW - one line addition
    logger.info("All schemas created successfully.")
```

Change 4: Update module docstring (lines 2-14):
```python
"""create_schema.py
Initialize SQLite schemas for rag.sqlite (RAG pipeline), session.sqlite (sessions/memory),
workflow.sqlite (metadata), and eventbus.sqlite (event queue).

Creates the latest schema only. No migration logic.
Existing tables are protected by IF NOT EXISTS for idempotent re-runs.

SQL templates are in db/schema_sql.py.

Functions:
  create_rag_schema()        — rag.sqlite: documents, chunks, chunks_vec, chunks_fts, triggers
  create_session_schema()    — session.sqlite: sessions, messages, tool_results, memory
  create_workflow_schema()   — workflow.sqlite: tasks, attempts, processed_events, artifacts, approvals
  create_eventbus_schema()   — eventbus.sqlite: events
  create_schema()            — convenience wrapper calling all four
"""
```

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| Type check | `uv run mypy scripts/db/create_schema.py` | No type errors |
| Lint | `uv run ruff check scripts/db/create_schema.py` | No lint errors |
| Manual verify | `python -c "from db.create_schema import create_eventbus_schema; print('OK')"` | No ImportError |
