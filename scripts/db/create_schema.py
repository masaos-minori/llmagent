#!/usr/bin/env python3
"""scripts/db/create_schema.py

現行スキーマをDDLのみで作成する。スキーマ変更が必要な場合はDBを再作成すること。

既存テーブルはIF NOT EXISTSで保護され、冪等再実行が可能。

SQLテンプレートはdb/schema_sql.pyに定義（正規DDLソース）。

dbmig001: 新規作成の workflow.sqlite / eventbus.sqlite は追加で migration ledger
と baseline row を受け取る。既存 DB は従来の fail-closed 拒否を維持。

Functions:
  create_rag_schema()        — rag.sqlite: documents, chunks, chunks_vec, chunks_fts, triggers
  create_session_schema()    — session.sqlite: sessions, messages, memory
  create_workflow_schema()   — workflow.sqlite: tasks, attempts, processed_events, artifacts, workflow_schema_version
  create_eventbus_schema()   — eventbus.sqlite: events
  create_schema()            — convenience wrapper calling all four
"""

import logging
import sqlite3
import sys

from shared.db_migrations import ensure_ledger
from shared.eventbus_schema_fingerprint import assert_matches

from db.helper import SQLiteHelper
from db.migrations_workflow import ensure_baseline
from db.schema_sql import (
    WORKFLOW_SCHEMA_VERSION,
    build_eventbus_schema_sql,
    build_rag_schema_sql,
    build_session_schema_sql,
    build_workflow_schema_sql,
    eventbus_schema_version,
)
from db.store_protocols import get_embedding_dims

logger = logging.getLogger(__name__)


def _execute_schema_ddl(db: SQLiteHelper, sql: str, error_label: str) -> None:
    """Execute schema DDL, logging and re-raising on SQLite errors.

    Args:
        db: Open SQLiteHelper connection to execute the script against.
        sql: DDL script to execute.
        error_label: Schema name used in the log message on failure (e.g. "RAG").
    """
    try:
        db.executescript(sql)
    except (sqlite3.OperationalError, sqlite3.DatabaseError) as e:
        logger.error("Failed to execute %s schema DDL: %s", error_label, e)
        raise


def _record_workflow_schema_version(db: SQLiteHelper) -> None:
    """Record WORKFLOW_SCHEMA_VERSION on a new database; refuse a different one.

    An empty version log records the current version, the current version is a
    no-op, and any other latest version raises: an older database is recreated,
    never stamped as current.
    """
    row = db.execute(
        "SELECT version FROM workflow_schema_version ORDER BY applied_at DESC LIMIT 1"
    ).fetchone()
    current = row[0] if row else None
    if current is None:
        db.execute(
            "INSERT INTO workflow_schema_version (version) VALUES (?)",
            (WORKFLOW_SCHEMA_VERSION,),
        )
    elif current != WORKFLOW_SCHEMA_VERSION:
        logger.error(
            "workflow_schema_version records %s, expected %s",
            current,
            WORKFLOW_SCHEMA_VERSION,
        )
        raise RuntimeError(
            f"workflow.sqlite schema version {current!r} differs from "
            f"{WORKFLOW_SCHEMA_VERSION!r}; recreate the database"
        )


def _record_eventbus_baseline(conn: sqlite3.Connection) -> None:
    """Insert the eventbus baseline ledger row idempotently.

    Called on the fresh and already-stamped create paths so a freshly created
    eventbus database carries the ledger baseline row. Uses INSERT OR IGNORE
    against the row-01 ledger table so re-running create_schema.py stays safe.
    The baseline stamps ``from_version == to_version`` (a fresh database is at
    the target version, never migrated), matching the "no migration executed"
    convention. ``ensure_ledger`` (row-01 ledger primitive) guarantees the ledger
    table exists even against a schema that predates it.
    """
    ensure_ledger(conn)
    conn.execute(
        "INSERT OR IGNORE INTO schema_migrations "
        "(id, from_version, to_version) VALUES ('eventbus_ledger_baseline', ?, ?)",
        (eventbus_schema_version(), eventbus_schema_version()),
    )


def create_rag_schema() -> None:
    """Create rag.sqlite tables, virtual tables, and triggers."""
    dims = get_embedding_dims()
    with SQLiteHelper("rag").open(write_mode=True) as db:
        _execute_schema_ddl(db, build_rag_schema_sql(dims), "RAG")
    logger.info("RAG schema created successfully.")


def create_session_schema() -> None:
    """Create session.sqlite tables for conversations and memory."""
    dims = get_embedding_dims()
    with SQLiteHelper("session").open(write_mode=True, load_vec=True) as db:
        _execute_schema_ddl(db, build_session_schema_sql(dims), "session")
    logger.info("Session schema created successfully.")


def create_workflow_schema() -> None:
    """Create workflow.sqlite tables (tasks, attempts, processed_events, artifacts).

    A freshly created database additionally receives the migration ledger and its
    baseline row (dbmig001 row 08); an existing database keeps today's
    fail-closed string-version refusal in ``_record_workflow_schema_version``.
    """
    with SQLiteHelper("workflow").open(write_mode=True) as db:
        _execute_schema_ddl(db, build_workflow_schema_sql(), "workflow")
        _record_workflow_schema_version(db)
        if db.conn is not None:
            ensure_baseline(db.conn)
        db.commit()
    logger.info("Workflow schema created successfully.")


def create_eventbus_schema() -> None:
    """Create eventbus.sqlite tables (events, consumer_delivery, consumer_offsets)."""
    with SQLiteHelper("eventbus").open(write_mode=True) as db:
        existing = db.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='events'"
        ).fetchone()
        before = int(db.execute("PRAGMA user_version").fetchone()[0])
        if existing and before not in (0, eventbus_schema_version()):
            raise RuntimeError(
                f"eventbus.sqlite schema version {before} differs from "
                f"{eventbus_schema_version()}; recreate the database"
            )
        try:
            db.executescript(build_eventbus_schema_sql())
        except (sqlite3.OperationalError, sqlite3.DatabaseError) as e:
            logger.error("Failed to execute Event Bus schema DDL: %s", e)
            raise
        if existing and before == 0:
            # Leave an unverified legacy database unstamped; the EventBus service
            # stamps it only after checking its tables against schema.sql. No
            # baseline row lands on this path.
            db.execute("PRAGMA user_version = 0")
        elif existing:
            # A database already stamped with the current version must still match
            # the canonical shape; fail closed before committing (REQ-003), then
            # stamp the ledger baseline row.
            if db.conn is not None:
                assert_matches(db.conn)
                _record_eventbus_baseline(db.conn)
        else:
            # Fresh database: schema.sql stamped user_version to the current
            # version; stamp the ledger baseline row.
            if db.conn is not None:
                _record_eventbus_baseline(db.conn)
        db.commit()
    logger.info("Event Bus schema created successfully.")


def create_schema() -> None:
    """Create schemas for rag.sqlite, session.sqlite, workflow.sqlite, and eventbus.sqlite."""
    create_rag_schema()
    create_session_schema()
    create_workflow_schema()
    create_eventbus_schema()
    logger.info("All schemas created successfully.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        create_schema()
    except (
        RuntimeError,
        sqlite3.OperationalError,
        sqlite3.DatabaseError,
        OSError,
    ) as e:
        logger.exception("Schema creation failed: %s", e)
        sys.exit(1)
