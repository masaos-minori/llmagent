#!/usr/bin/env python3
"""migrate_db.py
One-shot migration: move session tables from rag.sqlite → session.sqlite.

Tables moved: sessions, messages, notes, tool_results, memory_entries, memory_vec

Steps:
  1. Ensure session.sqlite schema exists (create_session_schema)
  2. Copy rows from rag.sqlite session tables to session.sqlite
  3. Print row counts; does NOT delete source tables (safe to re-run)

Run once on the production server after deploying the DB-split change.
After verifying row counts, optionally drop session tables from rag.sqlite manually.
"""

import sqlite3
import sys

from shared.logger import Logger

from db.create_schema import create_session_schema
from db.helper import SQLiteHelper

logger = Logger(__name__, "/opt/llm/logs/migrate_db.log")

# Tables to copy from rag.sqlite → session.sqlite (in dependency order).
# memory_vec is a virtual table (vec0); it cannot be migrated via INSERT INTO SELECT.
# Re-embed entries are required after migration if memory_vec data is needed.
_SESSION_TABLES: list[str] = [
    "sessions",
    "messages",
    "notes",
    "tool_results",
    "memory_entries",
]


def _table_exists(db: SQLiteHelper, table: str) -> bool:
    rows = db.fetchall(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table,),
    )
    return len(rows) > 0


def _copy_table(
    src_conn: sqlite3.Connection,
    dst_conn: sqlite3.Connection,
    table: str,
) -> int:
    """Copy all rows from src to dst for the given table; return copied row count."""
    rows = src_conn.execute(f"SELECT * FROM {table}").fetchall()  # noqa: S608 -- table comes from _SESSION_TABLES hardcoded list
    if not rows:
        return 0
    placeholders = ", ".join("?" * len(rows[0]))
    dst_conn.executemany(f"INSERT OR IGNORE INTO {table} VALUES ({placeholders})", rows)  # noqa: S608 -- same: table is a trusted hardcoded constant
    return len(rows)


def migrate() -> None:
    """Copy session tables from rag.sqlite to session.sqlite."""
    logger.info("Starting DB migration: rag.sqlite → session.sqlite")

    # Ensure session.sqlite schema exists.
    create_session_schema()

    rag_db = SQLiteHelper("rag").open(row_factory=False)
    ses_db = SQLiteHelper("session").open(write_mode=True, row_factory=False)

    try:
        assert rag_db.conn is not None
        assert ses_db.conn is not None
        ses_db.conn.execute("BEGIN")
        total = 0
        for table in _SESSION_TABLES:
            if not _table_exists(rag_db, table):
                logger.warning(f"Table '{table}' not found in rag.sqlite — skipping")
                continue
            count = _copy_table(rag_db.conn, ses_db.conn, table)
            logger.info(f"  {table}: {count} rows copied")
            total += count
        ses_db.conn.execute("COMMIT")
        logger.info(f"Migration complete: {total} total rows copied to session.sqlite")
        print(f"Migration complete: {total} rows copied.")
        print(
            "Source tables in rag.sqlite are NOT deleted. Verify counts, then drop manually if desired.",
        )
    except Exception as e:
        if ses_db.conn:
            try:
                ses_db.conn.execute("ROLLBACK")
            except Exception:
                pass
        logger.exception(f"Migration failed: {e}")
        raise
    finally:
        rag_db.close()
        ses_db.close()


if __name__ == "__main__":
    try:
        migrate()
    except Exception as e:
        logger.exception(f"DB migration failed: {e}")
        sys.exit(1)
