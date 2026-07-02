# Implementation: test_create_schema.py - Add TestEventbusSchemaSQL

## Goal

Add tests for `build_eventbus_schema_sql()` in test_create_schema.py.

## Scope

- tests/test_create_schema.py only: add TestEventbusSchemaSQL class with events table and index verification

## Assumptions

1. Follow existing test pattern (same style as TestCreateWorkflowSchema)
2. Use SQLite in-memory database for DDL validation (no file I/O needed)
3. No vec0 virtual tables for eventbus (no need to patch)

## Implementation

### Target file

- `tests/test_create_schema.py`

### Procedure

1. Add `_EVENTBUS_SCHEMA_NO_VEC0` constant (same as _EVENTBUS_SCHEMA, no vec changes needed)
2. Add `TestEventbusSchemaSQL` test class after TestCreateWorkflowSchema

### Method

- Follow existing TestCreateWorkflowSchema pattern exactly (same style)

### Details

Add after the TestCreateWorkflowSchema class:

```python
_EVENTBUS_SCHEMA_NO_VEC0 = """
PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS events (
    seq                    INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id               TEXT    NOT NULL UNIQUE,
    topic                  TEXT    NOT NULL,
    payload                TEXT    NOT NULL,
    producer               TEXT    NOT NULL,
    published_at           TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    acked_at               TEXT,
    retry_count            INTEGER NOT NULL DEFAULT 0, -- deprecated; use delivery_failure_count
    delivery_failure_count INTEGER NOT NULL DEFAULT 0,
    dlq_requeue_count      INTEGER NOT NULL DEFAULT 0,
    dlq_at                 TEXT
);

CREATE INDEX IF NOT EXISTS idx_events_topic ON events(topic);
CREATE INDEX IF NOT EXISTS idx_events_seq   ON events(seq);
CREATE INDEX IF NOT EXISTS idx_events_dlq_at ON events(dlq_at);
CREATE INDEX IF NOT EXISTS idx_events_dlq_seq ON events(dlq_at, seq);
"""


class TestEventbusSchemaSQL:
    def test_creates_events_table(self) -> None:
        """events table is created by build_eventbus_schema_sql()."""
        conn = sqlite3.connect(":memory:")
        try:
            conn.executescript(cs.build_eventbus_schema_sql())
            assert "events" in _table_names(conn)
        finally:
            conn.close()

    def test_creates_all_indexes(self) -> None:
        """All 4 eventbus indexes are created by build_eventbus_schema_sql()."""
        conn = sqlite3.connect(":memory:")
        try:
            conn.executescript(cs.build_eventbus_schema_sql())
            indexes = _index_names(conn)
            assert {
                "idx_events_topic",
                "idx_events_seq",
                "idx_events_dlq_at",
                "idx_events_dlq_seq",
            } <= indexes
        finally:
            conn.close()

    def test_events_columns(self) -> None:
        """events table has all expected columns including deprecated retry_count."""
        conn = sqlite3.connect(":memory:")
        try:
            conn.executescript(cs.build_eventbus_schema_sql())
            cols = {row[1] for row in conn.execute("PRAGMA table_info(events)").fetchall()}
            assert {
                "seq",
                "event_id",
                "topic",
                "payload",
                "producer",
                "published_at",
                "acked_at",
                "retry_count",
                "delivery_failure_count",
                "dlq_requeue_count",
                "dlq_at",
            } <= cols
        finally:
            conn.close()

    def test_idempotent(self) -> None:
        """Running build_eventbus_schema_sql() twice must not raise."""
        conn = sqlite3.connect(":memory:")
        try:
            conn.executescript(cs.build_eventbus_schema_sql())
            conn.executescript(cs.build_eventbus_schema_sql())  # must not raise
        finally:
            conn.close()


def _index_names(conn: sqlite3.Connection) -> set[str]:
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='index' ORDER BY name"
    ).fetchall()
    return {row[0] for row in rows}
```

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| New tests | `uv run pytest tests/test_create_schema.py::TestEventbusSchemaSQL -v` | all pass |
| Full test suite | `uv run pytest tests/test_create_schema.py -v` | all pass including new eventbus tests |
