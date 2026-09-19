## Goal

Create `scripts/eventbus/event_repo.py` — Event CRUD repository per REQ-001. Extracts `insert_event()`, `get_seq()`, `fetch_events_since()`, `fetch_dlq()`, `count_dlq()` from `db.py`.

## Scope

New file containing all event read/write operations. Uses parameterized queries exclusively for values.

## Assumptions

- Shared column constants (`_COL_EVENT_ID`, `_COL_SEQ`, `_COL_ACKED_AT`, `_COL_DLQ_AT`) imported from `_constants.py`.
- `orjson` available for payload serialization/deserialization.
- `sqlite3.Connection` passed as first argument to all functions.

## Design decisions

- Event repository owns all event CRUD operations.
- Payload serialized using `orjson.dumps()` / deserialized using `orjson.loads()`.
- Column names remain as module-level constants within each layer.
- Parameterized queries used for all values.

## Alternatives considered

- Using SQLAlchemy ORM rejected because it would add a dependency (REQ-010).
- Keeping everything in `db.py` rejected because events have their own CRUD surface area.

## Implementation

### Target file

`scripts/eventbus/event_repo.py`

### Procedure

Extract event CRUD operations from `db.py` into this module.

### Method

1. Import shared column constants from `_constants.py`.
2. Import `orjson` for payload serialization.
3. Implement `insert_event(conn, event_id, topic, payload, producer, published_at)` — insert a new event.
4. Implement `get_seq(conn, event_id)` — get sequence number for an event.
5. Implement `fetch_events_since(conn, since_seq)` — fetch events since a given sequence.
6. Implement `fetch_dlq(conn, limit, offset)` — fetch DLQ events.
7. Implement `count_dlq(conn)` — count DLQ events.
8. Export public symbols.

### Details

```python
"""Event repository: all event read/write operations."""

from sqlite3 import Connection

import orjson

from eventbus._constants import (
    _COL_ACKED_AT,
    _COL_DLQ_AT,
    _COL_EVENT_ID,
    _COL_SEQ,
)

def insert_event(
    conn: Connection,
    event_id: str,
    topic: str,
    payload: bytes,
    producer: str,
    published_at: str,
) -> None:
    """Insert a new event into the events table."""
    conn.execute(
        "INSERT INTO events(event_id, topic, payload, producer, published_at) VALUES (?, ?, ?, ?, ?)",
        (event_id, topic, orjson.dumps(payload).decode("utf-8"), producer, published_at),
    )
    conn.commit()

def get_seq(conn: Connection, event_id: str) -> int:
    """Get sequence number for an event."""
    cur = conn.execute(
        f"SELECT {_COL_SEQ} FROM events WHERE {_COL_EVENT_ID} = ?",  # nosec B608
        (event_id,),
    )
    row = cur.fetchone()
    if row is None:
        raise ValueError(f"Event {event_id} not found")
    return int(row[0])

def fetch_events_since(conn: Connection, since_seq: int) -> list[tuple[str, str]]:
    """Fetch events since a given sequence number."""
    cur = conn.execute(
        f"SELECT {_COL_EVENT_ID}, {_COL_SEQ} FROM events WHERE {_COL_SEQ} > ? ORDER BY {_COL_SEQ}",  # nosec B608
        (since_seq,),
    )
    return [(row[0], row[1]) for row in cur.fetchall()]

def fetch_dlq(conn: Connection, limit: int = 100, offset: int = 0) -> list[tuple[str, str]]:
    """Fetch DLQ events."""
    cur = conn.execute(
        f"SELECT {_COL_EVENT_ID}, {_COL_DLQ_AT} FROM events WHERE {_COL_DLQ_AT} IS NOT NULL ORDER BY {_COL_DLQ_AT} DESC LIMIT ? OFFSET ?",  # nosec B608
        (limit, offset),
    )
    return [(row[0], row[1]) for row in cur.fetchall()]

def count_dlq(conn: Connection) -> int:
    """Count DLQ events."""
    cur = conn.execute(
        f"SELECT COUNT(*) FROM events WHERE {_COL_DLQ_AT} IS NOT NULL"  # nosec B608
    )
    return int(cur.fetchone()[0])
```

## Compatibility considerations

- All function signatures match existing `db.py` exports.
- `orjson` already in project dependencies (used elsewhere).
- Return types unchanged: `int`, `list[tuple[str, str]]`.

## Security considerations

- All SQL statements use parameterized queries for values.
- Column names come from module-level constants (not user input) — safe from SQL injection.
- Payload serialized using `orjson.dumps()` — safe binary encoding.

## Rollback considerations

- If any function fails validation, revert to original `db.py` implementation.
- Keep original `db.py` until full test suite passes.

## Validation plan

- Run full eventbus test suite: `uv run pytest tests/eventbus/` — 311 collected tests.
- Verify `insert_event()` inserts correctly.
- Verify `get_seq()` returns correct sequence number.
- Verify `fetch_events_since()` returns events after given sequence.
- Verify `fetch_dlq()` returns DLQ events.
- Verify `count_dlq()` returns correct count.

## Completion criteria

- All 5 functions exist under `scripts/eventbus/event_repo.py`.
- All 311 eventbus tests pass.
- No behavioral regression in event CRUD operations.

## Out of scope

- Changing HTTP API surface.
- Adding new database indexes beyond `_migrate()`.
- Migrating from SQLite to another engine.
- Adding connection pooling/async drivers.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Create event_repo.py with shared constant imports | Pending | — | — | |
| 2 | Implement insert_event() | Pending | — | — | |
| 3 | Implement get_seq() | Pending | — | — | |
| 4 | Implement fetch_events_since() | Pending | — | — | |
| 5 | Implement fetch_dlq() | Pending | — | — | |
| 6 | Implement count_dlq() | Pending | — | — | |
| 7 | Run full eventbus test suite | Pending | — | — | |

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
- **Related target files**: scripts/eventbus/event_repo.py
