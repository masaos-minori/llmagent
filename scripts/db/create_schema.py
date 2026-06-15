#!/usr/bin/env python3
"""create_schema.py
Initialize SQLite schemas for rag.sqlite (RAG pipeline) and session.sqlite (sessions/memory).

Creates the latest schema only. No migration logic.
Existing tables are protected by IF NOT EXISTS for idempotent re-runs.

SQL templates are in db/schema_sql.py.

Functions:
  create_rag_schema()     — rag.sqlite: documents, chunks, chunks_vec, chunks_fts, triggers
  create_session_schema() — session.sqlite: sessions, messages, notes, tool_results, memory
  create_schema()         — convenience wrapper calling both
"""

import sqlite3
import sys

from shared.config_loader import (
    ConfigLoader,  # noqa: PLC0415 — used in _get_schema_log_path
)
from shared.logger import Logger

from db.helper import SQLiteHelper
from db.schema_sql import build_rag_schema_sql, build_session_schema_sql
from db.store_protocols import get_embedding_dims


def _get_schema_log_path() -> str:
    """Return the schema log file path from config."""
    cfg = ConfigLoader().load("common.toml")
    log_dir = cfg.get("log_dir", "/opt/llm/logs")
    return f"{log_dir}/create_schema.log"


_logger: Logger | None = None


def _get_logger() -> Logger:
    global _logger
    if _logger is None:
        _logger = Logger(__name__, _get_schema_log_path())
    return _logger


def create_rag_schema() -> None:
    """Create rag.sqlite tables, virtual tables, and triggers."""
    dims = get_embedding_dims()
    with SQLiteHelper("rag").open(write_mode=True) as db:
        try:
            db.conn.executescript(build_rag_schema_sql(dims))  # type: ignore[union-attr]  # conn is set by open()
        except (sqlite3.OperationalError, sqlite3.DatabaseError) as e:
            _get_logger().error(f"Failed to execute RAG schema DDL: {e}")
            raise
    _get_logger().info("RAG schema created successfully.")


def create_session_schema() -> None:
    """Create session.sqlite tables for conversations, notes, tool results, and memory."""
    dims = get_embedding_dims()
    with SQLiteHelper("session").open(write_mode=True) as db:
        try:
            db.conn.executescript(build_session_schema_sql(dims))  # type: ignore[union-attr]  # conn is set by open()
        except (sqlite3.OperationalError, sqlite3.DatabaseError) as e:
            _get_logger().error(f"Failed to execute session schema DDL: {e}")
            raise
    _get_logger().info("Session schema created successfully.")


def create_schema() -> None:
    """Create schemas for both rag.sqlite and session.sqlite."""
    create_rag_schema()
    create_session_schema()
    _get_logger().info("All schemas created successfully.")


if __name__ == "__main__":
    try:
        create_schema()
    except (
        RuntimeError,
        sqlite3.OperationalError,
        sqlite3.DatabaseError,
        OSError,
    ) as e:
        _get_logger().exception(f"Schema creation failed: {e}")
        sys.exit(1)
