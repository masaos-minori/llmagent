#!/usr/bin/env python3
"""
tool_result_store.py
SQLite-backed store for full tool execution results.

LLM history receives only summaries or truncations; the full text is persisted
here and retrievable via /tool show <id>.  Falls back silently on DB errors so
the REPL continues working even without a valid database connection.
"""

import logging

from db.helper import SQLiteHelper

logger = logging.getLogger(__name__)


class ToolResultStore:
    """Persists full tool call results to the tool_results table.

    Each result is stored once and assigned a stable integer id.
    The caller passes that id back to the LLM history so the user can retrieve
    the full text with /tool show <id>.
    """

    def store(
        self,
        session_id: int | None,
        turn: int,
        tool_name: str,
        args_json: str,
        full_text: str,
        summary: str | None,
        is_error: bool,
    ) -> int | None:
        """Insert one tool result row; return the new row id or None on error."""
        try:
            with SQLiteHelper("session").open(write_mode=True) as db:
                cur = db.execute(
                    "INSERT INTO tool_results"
                    " (session_id, turn, tool_name, args_json,"
                    "  full_text, summary, is_error)"
                    " VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (
                        session_id,
                        turn,
                        tool_name,
                        args_json,
                        full_text,
                        summary,
                        int(is_error),
                    ),
                )
                row_id = cur.lastrowid
                db.commit()
            return row_id
        except Exception as e:
            logger.warning(f"ToolResultStore.store failed: {e}")
            return None

    def get(self, result_id: int) -> dict | None:
        """Fetch one tool result by id; return None when not found."""
        try:
            with SQLiteHelper("session").open(row_factory=True) as db:
                rows = db.fetchall(
                    "SELECT id, session_id, turn, tool_name, args_json,"
                    " full_text, summary, is_error, created_at"
                    " FROM tool_results WHERE id = ?",
                    (result_id,),
                )
            if not rows:
                return None
            return dict(rows[0])
        except Exception as e:
            logger.warning(f"ToolResultStore.get failed (id={result_id}): {e}")
            return None

    def list_recent(self, session_id: int | None, n: int = 20) -> list[dict]:
        """Return the n most recent tool results for session_id, oldest first.

        Returns an empty list when session_id is None or on DB error.
        """
        if session_id is None:
            return []
        try:
            with SQLiteHelper("session").open(row_factory=True) as db:
                rows = db.fetchall(
                    "SELECT id, tool_name, full_text, summary, is_error"
                    " FROM tool_results"
                    " WHERE session_id = ?"
                    " ORDER BY id DESC LIMIT ?",
                    (session_id, n),
                )
            # Reverse so the oldest result is displayed first
            return [dict(r) for r in reversed(rows)]
        except Exception as e:
            logger.warning(f"ToolResultStore.list_recent failed: {e}")
            return []
