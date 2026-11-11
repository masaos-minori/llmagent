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
  create_schema()            — convenience wrapper calling all three
"""

import logging
import sqlite3
import sys

from shared.schema_fingerprint import assert_matches

from db.helper import SQLiteHelper
from db.schema_sql import (
    build_rag_schema_sql,
    build_session_schema_sql,
    build_workflow_schema_sql,
)
from db.store_protocols import get_embedding_dims

logger = logging.getLogger(__name__)

# Primary table per domain: its presence marks the file as an existing database
# (same signal eventbus/schema.py keys off "events").
_PRIMARY_TABLES: dict[str, str] = {
    "rag": "documents",
    "session": "sessions",
    "workflow": "tasks",
}


def _refuse_existing_drift(
    db: SQLiteHelper, domain: str, canonical_ddl: str, label: str
) -> None:
    """Validate-first gate (REQ-003): fingerprint an existing database before
    executing any DDL.

    If the domain's primary table already exists the file is an existing
    database: its shape must equal the canonical DDL or this raises RuntimeError
    before any write, leaving the file untouched (archive-and-recreate path).
    A fresh file (no primary table) returns without a check.
    """
    row = db.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (_PRIMARY_TABLES[domain],),
    ).fetchone()
    if row is None:
        return
    conn = db.conn
    if conn is None:
        raise RuntimeError(f"{label}: no open connection for fingerprint check")
    assert_matches(conn, canonical_ddl, label=label)


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
    ddl = build_rag_schema_sql(dims)
    with SQLiteHelper("rag").open(write_mode=True) as db:
        _refuse_existing_drift(db, "rag", ddl, "rag.sqlite")
        _execute_schema_ddl(db, ddl, "RAG")
    logger.info("RAG schema created successfully.")


def create_session_schema() -> None:
    """Create session.sqlite tables for conversations and memory."""
    dims = get_embedding_dims()
    ddl = build_session_schema_sql(dims)
    with SQLiteHelper("session").open(write_mode=True, load_vec=True) as db:
        _refuse_existing_drift(db, "session", ddl, "session.sqlite")
        _execute_schema_ddl(db, ddl, "session")
    logger.info("Session schema created successfully.")


def create_workflow_schema() -> None:
    """Create workflow.sqlite tables (tasks, attempts, processed_events, artifacts).

    Idempotent current-schema DDL only: no version row, no ledger row, no
    baseline write. Legacy marker tables on an existing database are rejected
    by the workflow shape gate (agent/services/workflow_schema.py), not here.
    """
    ddl = build_workflow_schema_sql()
    with SQLiteHelper("workflow").open(write_mode=True) as db:
        _refuse_existing_drift(db, "workflow", ddl, "workflow.sqlite")
        _execute_schema_ddl(db, ddl, "workflow")
        db.commit()
    logger.info("Workflow schema created successfully.")


def create_schema() -> None:
    """Create schemas for rag.sqlite, session.sqlite, and workflow.sqlite."""
    create_rag_schema()
    create_session_schema()
    create_workflow_schema()
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
