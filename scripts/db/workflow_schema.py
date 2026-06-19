#!/usr/bin/env python3
"""db/workflow_schema.py
DDL for the Metadata DB (workflow.sqlite).

Tables: tasks, attempts, processed_events, artifacts, approvals.
Run as: PYTHONPATH=scripts python -m db.workflow_schema
"""

from __future__ import annotations

import logging
import sqlite3
from pathlib import Path

from db.config import build_db_config

logger = logging.getLogger(__name__)

_DDL = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS tasks (
    task_id          TEXT PRIMARY KEY,
    session_id       TEXT,
    workflow_id      TEXT,
    turn_number      INTEGER,
    workflow_version TEXT NOT NULL,
    status           TEXT NOT NULL DEFAULT 'pending',
    idempotency_key  TEXT UNIQUE NOT NULL,
    created_at       TEXT NOT NULL,
    updated_at       TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS attempts (
    attempt_id  TEXT PRIMARY KEY,
    task_id     TEXT NOT NULL REFERENCES tasks(task_id) ON DELETE CASCADE,
    stage_id    TEXT NOT NULL,
    status      TEXT NOT NULL DEFAULT 'running',
    started_at  TEXT NOT NULL,
    ended_at    TEXT,
    error_msg   TEXT
);

CREATE TABLE IF NOT EXISTS processed_events (
    event_id    TEXT PRIMARY KEY,
    task_id     TEXT NOT NULL REFERENCES tasks(task_id) ON DELETE CASCADE,
    stage_id    TEXT NOT NULL,
    recorded_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS artifacts (
    artifact_id TEXT PRIMARY KEY,
    task_id     TEXT NOT NULL REFERENCES tasks(task_id) ON DELETE CASCADE,
    stage_id    TEXT NOT NULL,
    uri         TEXT NOT NULL,
    created_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS approvals (
    approval_id TEXT PRIMARY KEY,
    task_id     TEXT NOT NULL REFERENCES tasks(task_id) ON DELETE CASCADE,
    stage_id    TEXT,
    status      TEXT NOT NULL DEFAULT 'pending',
    reason      TEXT,
    created_at  TEXT NOT NULL,
    resolved_at TEXT
);
"""


def init_schema(db_path: str) -> None:
    """Create workflow tables if they do not exist."""
    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(_DDL)
        conn.commit()
        # Migration: add workflow_id column to tasks if missing
        cursor = conn.execute("PRAGMA table_info(tasks)")
        columns = [row[1] for row in cursor.fetchall()]
        if "workflow_id" not in columns:
            conn.execute("ALTER TABLE tasks ADD COLUMN workflow_id TEXT")
            conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    cfg = build_db_config()
    Path(cfg.workflow_db_path).parent.mkdir(parents=True, exist_ok=True)
    init_schema(cfg.workflow_db_path)
    logger.info("workflow schema initialised: %s", cfg.workflow_db_path)
