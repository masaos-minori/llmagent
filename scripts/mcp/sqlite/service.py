#!/usr/bin/env python3
"""mcp/sqlite/service.py
SqliteMCPService: read-only SQLite query execution with allowlist and row limit.

Security guards:
  - db_allowlist: only named databases are accessible
  - SELECT-only: non-SELECT statements are rejected before any DB connection
  - PRAGMA query_only=ON: OS-level write protection on each connection
  - max_rows: result set is capped to prevent large data dumps
"""

from __future__ import annotations

import logging
import re
import sqlite3
from collections.abc import Awaitable, Callable
from typing import Any

import orjson

from mcp.server import ToolArgs
from mcp.sqlite.models import _get_cfg

logger = logging.getLogger(__name__)

# Regex matches the first significant keyword after stripping SQL comments.
# Used to detect non-SELECT statements in _validate_sql().
_FIRST_WORD_RE = re.compile(r"\b([A-Z]+)\b")


def _strip_comments(sql: str) -> str:
    """Remove single-line (--) and block (/* */) SQL comments."""
    sql = re.sub(r"--[^\n]*", "", sql)
    sql = re.sub(r"/\*.*?\*/", "", sql, flags=re.DOTALL)
    return sql


def _validate_sql(sql: str) -> tuple[bool, str]:
    """Return (ok, error_message); ok=True only for single SELECT statements."""
    normalized = _strip_comments(sql).strip()
    if not normalized:
        return False, "SQL statement is empty"
    # Reject multiple statements: strip trailing semicolon and check for internal ones
    without_trailing = normalized.rstrip(";").rstrip()
    if ";" in without_trailing:
        return False, "Multiple SQL statements are not allowed"
    first = _FIRST_WORD_RE.search(normalized.upper())
    if not first or first.group(1) != "SELECT":
        keyword = first.group(1) if first else "(empty)"
        return False, f"Only SELECT statements are allowed; got {keyword!r}"
    return True, ""


class SqliteMCPService:
    """Executes read-only SELECT queries against an allowlisted set of SQLite databases."""

    def __init__(
        self,
        db_allowlist: list[str],
        db_paths: dict[str, str],
        max_rows: int = 100,
    ) -> None:
        self._db_allowlist = db_allowlist
        self._db_paths = db_paths
        self._max_rows = max_rows

    def _execute_query(self, db: str, sql: str) -> str:
        """Open a read-only connection, execute sql, return JSON-encoded result string."""
        db_path = self._db_paths.get(db, "")
        if not db_path:
            raise ValueError(f"No path configured for DB {db!r}")

        conn = sqlite3.connect(db_path, check_same_thread=False, timeout=5)
        try:
            # Prevent any accidental write at the SQLite engine level
            conn.execute("PRAGMA query_only=ON")
            cursor = conn.execute(sql)
            columns = [desc[0] for desc in (cursor.description or [])]
            rows: list[list[Any]] = []
            truncated = False
            for row in cursor:
                if len(rows) >= self._max_rows:
                    truncated = True
                    break
                rows.append(list(row))
        finally:
            conn.close()

        result = {
            "columns": columns,
            "rows": rows,
            "row_count": len(rows),
            "truncated": truncated,
        }
        encoded: bytes = orjson.dumps(result)
        return encoded.decode()

    async def handle_query_sqlite(self, args: ToolArgs) -> str:
        """Dispatch handler: validates args, executes query, returns JSON string."""
        db = str(args.get("db", ""))
        sql = str(args.get("sql", ""))

        if db not in self._db_allowlist:
            raise ValueError(
                f"DB {db!r} is not in the allowlist {self._db_allowlist!r}",
            )

        ok, err = _validate_sql(sql)
        if not ok:
            raise ValueError(err)

        try:
            return self._execute_query(db, sql)
        except sqlite3.Error as e:
            logger.error(f"SQLite error db={db!r}: {e}")
            raise ValueError(f"SQLite error: {e}") from e

    def get_dispatch_table(
        self,
    ) -> dict[str, Callable[[ToolArgs], Awaitable[str]]]:
        return {
            "query_sqlite": self.handle_query_sqlite,
        }


class _LazySqliteMCPService:
    """Lazy singleton proxy: defers SqliteMCPService init until first attribute access."""

    _instance: SqliteMCPService | None = None

    def __getattr__(self, name: str) -> Any:
        if _LazySqliteMCPService._instance is None:
            cfg = _get_cfg()
            db_paths: dict[str, str] = dict(cfg.get("db_paths", {}))
            db_allowlist: list[str] = list(cfg.get("db_allowlist", []))
            max_rows: int = int(cfg.get("max_rows", 100))
            if not db_allowlist:
                logger.warning(
                    "sqlite-mcp: db_allowlist is empty — all DB requests will be rejected",
                )
            _LazySqliteMCPService._instance = SqliteMCPService(
                db_allowlist=db_allowlist,
                db_paths=db_paths,
                max_rows=max_rows,
            )
        return getattr(_LazySqliteMCPService._instance, name)


# _LazySqliteMCPService is a proxy whose __getattr__ delegates to SqliteMCPService.
_service: SqliteMCPService = _LazySqliteMCPService()  # type: ignore[assignment]
