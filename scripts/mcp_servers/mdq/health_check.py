#!/usr/bin/env python3
"""scripts/mcp_servers/mdq/health_check.py

Health check logic for mdq-mcp server.

Dependency direction: health_check → models
Import from here:  from mcp_servers.mdq.health_check import check_health
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from db.helper import apply_connection_pragmas
from fastapi.responses import JSONResponse
from shared.config_loader import ConfigLoader

from mcp_servers.health_response import make_health_response
from mcp_servers.mdq.mdq_models import STALE_SQL_CONDITION


def _degraded_response(
    deps: dict[str, str], details: dict[str, object]
) -> JSONResponse:
    """Build and return a degraded health response when checks fail."""
    result: JSONResponse = make_health_response(deps, details)
    return result


def _check_stale_documents(conn: sqlite3.Connection) -> int | None:
    """Check for documents with mtime_ns > indexed_at."""
    try:
        result = conn.execute(
            f"SELECT COUNT(*) as cnt FROM documents WHERE {STALE_SQL_CONDITION}"  # nosec B608 — STALE_SQL_CONDITION is a fixed string constant
        ).fetchone()
        return result["cnt"] if result is not None else 0
    except sqlite3.OperationalError:
        return None


def _check_schema_health(conn: sqlite3.Connection) -> tuple[str, str] | None:
    """Verify required tables, triggers, and FTS5 query health.

    Returns a `(dependency_key, message)` pair describing the failure, or
    `None` if the schema and FTS5 index are healthy.
    """
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {row[0] for row in cursor.fetchall()}

    if "documents" not in tables:
        return "db_schema", "missing documents table"
    if "chunks" not in tables:
        return "db_schema", "missing chunks table"
    if "chunks_fts" not in tables:
        return "db_schema", "missing chunks_fts FTS5 table"

    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='trigger'")
    triggers = {row[0] for row in cursor.fetchall()}
    expected_triggers = {"chunks_ai", "chunks_ad", "chunks_au"}
    missing_triggers = expected_triggers - triggers
    if missing_triggers:
        return (
            "db_schema",
            f"missing triggers: {', '.join(sorted(missing_triggers))}",
        )

    try:
        cursor.execute(
            "SELECT COUNT(*) FROM chunks_fts WHERE chunks_fts = 'delete' LIMIT 1"
        )
        cursor.fetchone()
    except sqlite3.OperationalError as e:
        return "fts5", f"FTS5 query failed: {e}"

    return None


def _collect_index_stats(conn: sqlite3.Connection) -> dict[str, object]:
    """Gather document/chunk/FTS row counts and staleness for the health payload."""
    chunk_count = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
    doc_count = conn.execute(
        "SELECT COUNT(DISTINCT source_path) FROM documents"
    ).fetchone()[0]
    fts_count = conn.execute(
        "SELECT COUNT(*) FROM chunks_fts WHERE chunks_fts != 'delete'"
    ).fetchone()[0]

    row = conn.execute("SELECT MAX(indexed_at) FROM documents").fetchone()
    last_indexed = row[0] if row and row[0] is not None else None

    return {
        "document_count": doc_count,
        "chunk_count": chunk_count,
        "fts_row_count": fts_count,
        "last_indexed": last_indexed,
        "stale_document_count": _check_stale_documents(conn),
    }


def check_health() -> JSONResponse:
    """Check mdq-mcp health and return appropriate response."""
    deps: dict[str, str] = {}
    details: dict[str, object] = {"service": "mdq-mcp"}

    try:
        mdq_cfg = ConfigLoader().load("mdq_mcp_server.toml")
        db_path = mdq_cfg.get("db_path") or "/opt/llm/db/mdq.sqlite"
        details["database"] = db_path
        allowed_dirs = mdq_cfg.get("allowed_dirs") or []
        details["allowed_dirs_count"] = len(allowed_dirs)
        details["deny_all"] = len(allowed_dirs) == 0

        if not Path(db_path).is_file():
            deps["db_file"] = f"not found: {db_path}"
            return _degraded_response(deps, details)

        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        apply_connection_pragmas(conn, write_mode=False)
        try:
            schema_error = _check_schema_health(conn)
            if schema_error is not None:
                error_key, error_message = schema_error
                deps[error_key] = error_message
                return _degraded_response(deps, details)

            details.update(_collect_index_stats(conn))

        finally:
            conn.close()

    except (FileNotFoundError, PermissionError, KeyError, TypeError) as e:
        deps["config"] = f"check failed: {e}"

    result: JSONResponse = make_health_response(deps, details)
    return result
