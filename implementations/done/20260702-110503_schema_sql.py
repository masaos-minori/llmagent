# Implementation: schema_sql.py - Add _EVENTBUS_SCHEMA

## Goal

Add `_EVENTBUS_SCHEMA` string constant to schema_sql.py with DDL from scripts/eventbus/schema.sql.

## Scope

- scripts/db/schema_sql.py only: add EVENTBUS_SCHEMA constant

## Assumptions

1. PRAGMA journal_mode=WAL is included like _WORKFLOW_SCHEMA (idempotent, harmless)
2. published_at DEFAULT uses ISO-8601 UTC Z suffix: strftime('%Y-%m-%dT%H:%M:%SZ', 'now')
3. retry_count kept with deprecated comment for backward compatibility

## Implementation

### Target file

- `scripts/db/schema_sql.py`

### Procedure

1. Add `_EVENTBUS_SCHEMA` string constant after _WORKFLOW_SCHEMA
2. Port events table DDL from schema.sql (with retry_count deprecated comment)
3. Set published_at DEFAULT to strftime('%Y-%m-%dT%H:%M:%SZ', 'now')
4. Port 4 indexes: idx_events_topic, idx_events_seq, idx_events_dlq_at, idx_events_dlq_seq
5. Add timestamp policy as comment

### Method

- Follow _WORKFLOW_SCHEMA pattern exactly (same style)

### Details

```python
_EVENTBUS_SCHEMA: str = """
PRAGMA journal_mode=WAL;

-- Timestamps use ISO-8601 UTC Z suffix format: 2026-07-02T10:00:00Z
-- acked_at and dlq_at are nullable (unset until acknowledged/dead-lettered)

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
```

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| Type check | `uv run mypy scripts/db/schema_sql.py` | No type errors |
| Lint | `uv run ruff check scripts/db/schema_sql.py` | No lint errors |
