PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS events (
    seq          INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id     TEXT    NOT NULL UNIQUE,
    topic        TEXT    NOT NULL,
    payload      TEXT    NOT NULL,
    producer     TEXT    NOT NULL,
    published_at TEXT    NOT NULL,
    acked_at     TEXT, -- reserved; not currently set by any code path
    retry_count  INTEGER NOT NULL DEFAULT 0,
    dlq_at       TEXT
);

CREATE INDEX IF NOT EXISTS idx_events_topic ON events(topic);
CREATE INDEX IF NOT EXISTS idx_events_seq   ON events(seq);
