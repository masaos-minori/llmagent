PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS events (
    seq                    INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id               TEXT    NOT NULL UNIQUE,
    topic                  TEXT    NOT NULL,
    payload                TEXT    NOT NULL,
    producer               TEXT    NOT NULL,
    published_at           TEXT    NOT NULL,
    redelivered_from       TEXT,
    dlq_requeue_count      INTEGER NOT NULL DEFAULT 0,
    dlq_at                 TEXT,
    consumer_id            TEXT
);

CREATE INDEX IF NOT EXISTS idx_events_topic ON events(topic);
CREATE INDEX IF NOT EXISTS idx_events_seq   ON events(seq);
CREATE INDEX IF NOT EXISTS idx_events_dlq_at ON events(dlq_at);
CREATE INDEX IF NOT EXISTS idx_events_dlq_seq ON events(dlq_at, seq);
-- One redelivery descendant per original: enforced at the database level.
CREATE UNIQUE INDEX IF NOT EXISTS idx_events_redelivered_from ON events(redelivered_from) WHERE redelivered_from IS NOT NULL;

-- Per-consumer delivery state: tracks ACK state per (consumer_id, event_id)
CREATE TABLE IF NOT EXISTS consumer_delivery (
    consumer_id                    TEXT    NOT NULL,
    event_id                       TEXT    NOT NULL,
    acked                          INTEGER NOT NULL DEFAULT 0,
    consumer_delivery_failure_count INTEGER NOT NULL DEFAULT 0,
    consumer_last_nack_attempt     TEXT,
    PRIMARY KEY (consumer_id, event_id)
);

-- Index for efficient low-water-mark query in get_resume_position()
CREATE INDEX IF NOT EXISTS idx_consumer_delivery_consumer_ack
    ON consumer_delivery(consumer_id, acked);

-- Per-consumer offset: tracks last-committed sequence offset per consumer
CREATE TABLE IF NOT EXISTS consumer_offsets (
    consumer_id          TEXT    PRIMARY KEY,
    offset               INTEGER NOT NULL DEFAULT 0
);

-- Forward-only migration ledger (REQ-006): records each applied migration id and
-- the version range it moved. New databases get this table here; existing
-- databases receive it through the eventbus registry's bootstrap step.
CREATE TABLE IF NOT EXISTS schema_migrations (
    id               TEXT    PRIMARY KEY,
    applied_at       TEXT,
    from_version     INTEGER,
    to_version       INTEGER
);

-- Schema version of this DDL. Bump it whenever the schema changes in a way that
-- requires recreating the database; open_db() refuses a database stamped otherwise.
PRAGMA user_version = 4;
