#!/usr/bin/env python3
"""scripts/db/create_schema.py

現行スキーマをDDLのみで作成する。スキーマ変更が必要な場合はDBを再作成すること。

既存テーブルはIF NOT EXISTSで保護され、冪等再実行が可能。

SQLテンプレートはdb/schema_sql.pyに定義（正規DDLソース）。

既存 DB は従来の fail-closed 拒否を維持。自動 migration と version stamping は
サポートしない: 現行スキーマに一致する DB のみ受け付け、それ以外は書き込み前に拒否する。

Functions:
  create_rag_schema()        — rag.sqlite: documents, chunks, chunks_vec, chunks_fts, triggers
  create_session_schema()    — session.sqlite: sessions, messages, memory
  create_workflow_schema()   — workflow.sqlite: tasks, attempts, processed_events, artifacts
  create_eventbus_schema()   — eventbus.sqlite: events
  create_schema()            — convenience wrapper calling all four
"""

import logging
import sqlite3
import sys

from shared.eventbus_schema_fingerprint import validate_canonical

from db.helper import SQLiteHelper
from db.schema_sql import (
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

    Idempotent current-schema DDL only: no version row, no ledger row, no
    baseline write. Legacy marker tables on an existing database are rejected
    by the workflow shape gate (agent/services/workflow_schema.py), not here.
    """
    with SQLiteHelper("workflow").open(write_mode=True) as db:
        _execute_schema_ddl(db, build_workflow_schema_sql(), "workflow")
        db.commit()
    logger.info("Workflow schema created successfully.")


def create_eventbus_schema() -> None:
    """Create or validate eventbus.sqlite (events, consumer_delivery, consumer_offsets).

    Three mutually exclusive, validate-first paths (REQ-003/REQ-004): a fresh
    database receives the canonical DDL once (schema.sql stamps the current
    user_version); an existing database at the current version is validated
    (version + shape) BEFORE any mutation; every other existing database —
    including an unstamped (version 0) one — is refused before any write and
    left byte-unchanged. Automatic migration and version stamping are not
    supported: the operator archives and recreates.
    """
    refusal = (
        "The database does not match the current schema. Automatic migration and "
        "version stamping are not supported. Stop the service, archive the existing "
        "database if required, remove or rename it, and create a new database using "
        "the current schema."
    )
    with SQLiteHelper("eventbus").open(write_mode=True) as db:
        existing = db.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='events'"
        ).fetchone()
        before = int(db.execute("PRAGMA user_version").fetchone()[0])
        if not existing:
            # Fresh database: canonical DDL once (schema.sql stamps the current
            # user_version). No validation needed.
            _execute_schema_ddl(db, build_eventbus_schema_sql(), "Event Bus")
        elif before == eventbus_schema_version():
            # Current version: validate version + shape BEFORE any DDL (zero
            # executescript, zero writes). A refusal here leaves the database
            # byte-unchanged.
            if db.conn is None:
                raise RuntimeError("eventbus.sqlite: connection missing at validation")
            validate_canonical(db.conn)
        elif before == 0:
            # Unstamped existing database: refused and left unstamped (REQ-003).
            # Shape match does not matter: version 0 is not a current-schema marker.
            raise RuntimeError(
                f"eventbus.sqlite is unstamped (user_version 0): {refusal}"
            )
        else:
            # Any other version: refused unchanged. Numeric versions are schema
            # facts; the message carries no table/column/row content.
            raise RuntimeError(
                f"eventbus.sqlite schema version {before} differs from "
                f"{eventbus_schema_version()}: {refusal}"
            )
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
