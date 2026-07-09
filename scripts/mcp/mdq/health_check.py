#!/usr/bin/env python3
"""mcp/mdq/health_check.py

Health check logic for mdq-mcp server.

Dependency direction: health_check → models
Import from here:  from mcp.mdq.health_check import check_health
"""

from __future__ import annotations

import os as _os
import sqlite3

from fastapi.responses import JSONResponse
from mcp.health_response import make_health_response
from shared.config_loader import ConfigLoader


def _degraded_response(
    deps: dict[str, str], details: dict[str, object]
) -> JSONResponse:
    return make_health_response(deps, details)


def _check_stale_documents(conn: sqlite3.Connection) -> int | None:
    """Check for documents with mtime_ns > indexed_at."""
    try:
        result = conn.execute(
            "SELECT COUNT(*) as cnt FROM documents"
            " WHERE mtime_ns > CAST(indexed_at * 1e9 AS INTEGER)"
        ).fetchone()
        return result["cnt"] if result is not None else 0
    except Exception:
        return None


def check_health() -> JSONResponse:
    """Check mdq-mcp health and return appropriate response."""
    deps: dict[str, str] = {}
    details: dict[str, object] = {"service": "mdq-mcp"}

    try:
        mdq_cfg = ConfigLoader().load("mdq_mcp_server.toml")
        db_path = mdq_cfg.get("db_path") or "/opt/llm/db/mdq.sqlite"
        details["database"] = db_path

        if not _os.path.isfile(db_path):
            deps["db_file"] = f"not found: {db_path}"
            return _degraded_response(deps, details)

        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        try:
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = {row[0] for row in cursor.fetchall()}

            if "documents" not in tables:
                deps["db_schema"] = "missing documents table"
                return _degraded_response(deps, details)

            if "chunks" not in tables:
                deps["db_schema"] = "missing chunks table"
                return _degraded_response(deps, details)
            if "chunks_fts" not in tables:
                deps["db_schema"] = "missing chunks_fts FTS5 table"
                return _degraded_response(deps, details)

            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='trigger'")
            triggers = {row[0] for row in cursor.fetchall()}
            expected_triggers = {"chunks_ai", "chunks_ad", "chunks_au"}
            missing_triggers = expected_triggers - triggers
            if missing_triggers:
                deps["db_schema"] = (
                    f"missing triggers: {', '.join(sorted(missing_triggers))}"
                )
                return _degraded_response(deps, details)

            try:
                cursor.execute(
                    "SELECT COUNT(*) FROM chunks_fts WHERE chunks_fts = 'delete' LIMIT 1"
                )
                cursor.fetchone()
            except sqlite3.OperationalError as e:
                deps["fts5"] = f"FTS5 query failed: {e}"
                return _degraded_response(deps, details)

            chunk_count = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
            doc_count = conn.execute(
                "SELECT COUNT(DISTINCT source_path) FROM documents"
            ).fetchone()[0]
            fts_count = conn.execute(
                "SELECT COUNT(*) FROM chunks_fts WHERE chunks_fts != 'delete'"
            ).fetchone()[0]

            row = conn.execute("SELECT MAX(indexed_at) FROM documents").fetchone()
            last_indexed = row[0] if row and row[0] is not None else None
            details["document_count"] = doc_count
            details["chunk_count"] = chunk_count
            details["fts_row_count"] = fts_count
            details["last_indexed"] = last_indexed

            stale_count = _check_stale_documents(conn)
            details["stale_document_count"] = stale_count

        finally:
            conn.close()

    except (FileNotFoundError, PermissionError, KeyError, TypeError) as e:
        deps["config"] = f"check failed: {e}"

    return make_health_response(deps, details)
