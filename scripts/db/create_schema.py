#!/usr/bin/env python3
"""create_schema.py
現行スキーマをDDLのみで作成する。スキーマ変更が必要な場合はDBを再作成すること。

既存テーブルはIF NOT EXISTSで保護され、冪等再実行が可能。

SQLテンプレートはdb/schema_sql.pyに定義（正規DDLソース）。

Functions:
  create_rag_schema()        — rag.sqlite: documents, chunks, chunks_vec, chunks_fts, triggers
  create_session_schema()    — session.sqlite: sessions, messages, tool_results, memory
  create_workflow_schema()   — workflow.sqlite: tasks, attempts, processed_events, artifacts, approvals
  create_eventbus_schema()   — eventbus.sqlite: events
  create_schema()            — convenience wrapper calling all four
"""

import logging
import sqlite3
import sys

from db.helper import SQLiteHelper
from db.schema_sql import (
    _WORKFLOW_MIGRATIONS,
    build_eventbus_schema_sql,
    build_rag_schema_sql,
    build_session_schema_sql,
    build_workflow_schema_sql,
)
from db.store_protocols import get_embedding_dims

logger = logging.getLogger(__name__)


def create_rag_schema() -> None:
    """Create rag.sqlite tables, virtual tables, and triggers."""
    dims = get_embedding_dims()
    with SQLiteHelper("rag").open(write_mode=True) as db:
        try:
            db.executescript(build_rag_schema_sql(dims))
        except (sqlite3.OperationalError, sqlite3.DatabaseError) as e:
            logger.error("Failed to execute RAG schema DDL: %s", e)
            raise
    logger.info("RAG schema created successfully.")


def create_session_schema() -> None:
    """Create session.sqlite tables for conversations, tool results, and memory."""
    dims = get_embedding_dims()
    with SQLiteHelper("session").open(write_mode=True, load_vec=True) as db:
        try:
            db.executescript(build_session_schema_sql(dims))
        except (sqlite3.OperationalError, sqlite3.DatabaseError) as e:
            logger.error("Failed to execute session schema DDL: %s", e)
            raise
    logger.info("Session schema created successfully.")


def create_workflow_schema() -> None:
    """Create workflow.sqlite tables (tasks, attempts, processed_events, artifacts, approvals)."""
    with SQLiteHelper("workflow").open(write_mode=True) as db:
        try:
            db.executescript(build_workflow_schema_sql())
        except (sqlite3.OperationalError, sqlite3.DatabaseError) as e:
            logger.error("Failed to execute workflow schema DDL: %s", e)
            raise
        for stmt in _WORKFLOW_MIGRATIONS:
            try:
                db.execute(stmt)
            except sqlite3.OperationalError:
                pass  # column already exists
        db.commit()
    logger.info("Workflow schema created successfully.")


def create_eventbus_schema() -> None:
    """Create eventbus.sqlite tables (events)."""
    with SQLiteHelper("eventbus").open(write_mode=True) as db:
        try:
            db.executescript(build_eventbus_schema_sql())
        except (sqlite3.OperationalError, sqlite3.DatabaseError) as e:
            logger.error("Failed to execute Event Bus schema DDL: %s", e)
            raise
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
