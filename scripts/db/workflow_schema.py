#!/usr/bin/env python3
"""db/workflow_schema.py
DDL for the Metadata DB (workflow.sqlite).

Tables: tasks, attempts, processed_events, artifacts.
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
    session_id       TEXT NOT NULL,
    turn_number      INTEGER NOT NULL,
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
"""


def init_schema(db_path: str) -> None:
    """Create workflow tables if they do not exist."""
    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(_DDL)
        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    cfg = build_db_config()
    Path(cfg.workflow_db_path).parent.mkdir(parents=True, exist_ok=True)
    init_schema(cfg.workflow_db_path)
    logger.info("workflow schema initialised: %s", cfg.workflow_db_path)
