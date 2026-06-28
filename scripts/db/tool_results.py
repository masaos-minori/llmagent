#!/usr/bin/env python3
"""tool_results.py
SQLite-backed store for full tool execution results.

LLM history receives only summaries or truncations; the full text is persisted
here and retrievable via /tool show <id>.  DB errors are logged and re-raised so
callers can decide how to handle failures (e.g. log and continue in the REPL).
"""

import logging

from db.helper import SQLiteHelper
from db.models import ToolResultRow

logger = logging.getLogger(__name__)


class ToolResultStore:
    """Persists full tool call results to the tool_results table; each result has a stable integer id retrievable via /tool show <id>."""

    def _make_helper(
        self, *, write_mode: bool = False, row_factory: bool = False
    ) -> SQLiteHelper:
        """Return an open SQLiteHelper for session.sqlite.

        Overriding this method in tests allows injecting an alternative database
        without patching build_db_config globally.
        """
        return SQLiteHelper("session").open(
            write_mode=write_mode, row_factory=row_factory
        )

    def store(
        self,
        session_id: int | None,
        turn: int,
        tool_name: str,
        args_masked: str,
        full_text: str,
        summary: str | None,
        is_error: bool,
    ) -> int:
        """Insert one tool result row; return the new row id. Raises on DB error."""
        with self._make_helper(write_mode=True) as db:
            cur = db.execute(
                "INSERT INTO tool_results"
                " (session_id, turn, tool_name, args_masked,"
                "  full_text, summary, is_error)"
                " VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    session_id,
                    turn,
                    tool_name,
                    args_masked,
                    full_text,
                    summary,
                    int(is_error),
                ),
            )
            row_id = cur.lastrowid
            db.commit()
        if row_id is None:
            raise RuntimeError(
                "tool_results insert succeeded but lastrowid is None — "
                "unexpected DB state"
            )
        return row_id

    def get(self, result_id: int) -> ToolResultRow | None:
        """Fetch one tool result by id; return None when not found. Raises on DB error."""
        with self._make_helper(row_factory=True) as db:
            rows = db.fetchall(
                "SELECT id, session_id, turn, tool_name, args_masked,"
                " full_text, summary, is_error, created_at"
                " FROM tool_results WHERE id = ?",
                (result_id,),
            )
        if not rows:
            return None
        r = rows[0]
        return ToolResultRow(
            id=r["id"],
            session_id=r["session_id"],
            turn=r["turn"],
            tool_name=r["tool_name"],
            args_masked=r["args_masked"] or "",
            full_text=r["full_text"] or "",
            summary=r["summary"],
            is_error=bool(r["is_error"]),
            created_at=r["created_at"] or "",
        )

    def list_recent(self, session_id: int | None, n: int = 20) -> list[ToolResultRow]:
        """Return the n most recent tool results for session_id oldest first.

        Returns [] when session_id is None or n < 1. Raises on DB error.
        Rows contain id, tool_name, summary, is_error; other fields default to empty/0.
        """
        if session_id is None:
            return []
        if n < 1:
            return []
        with self._make_helper(row_factory=True) as db:
            rows = db.fetchall(
                "SELECT id, tool_name, summary, is_error"
                " FROM tool_results"
                " WHERE session_id = ?"
                " ORDER BY id DESC LIMIT ?",
                (session_id, n),
            )
        return [
            ToolResultRow(
                id=r["id"],
                tool_name=r["tool_name"],
                summary=r["summary"],
                is_error=bool(r["is_error"]),
            )
            for r in reversed(rows)
        ]
