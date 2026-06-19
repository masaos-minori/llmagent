"""agent/diagnostic_store.py
DiagnosticStore — dedicated storage for runtime diagnostics.
Diagnostic data is stored in the session_diagnostics table,
separate from normal conversation messages.
"""

from __future__ import annotations

import logging
from typing import Any

from db.helper import SQLiteHelper

logger = logging.getLogger(__name__)


class DiagnosticStore:
    """Dedicated store for diagnostic messages, separate from conversation history."""

    def __init__(self, session_id: int | None = None) -> None:
        self.session_id = session_id

    def save(
        self,
        session_id: int | None,
        kind: str,
        content: str,
        workflow_id: str | None = None,
        task_id: str | None = None,
    ) -> None:
        """Persist one diagnostic entry."""
        with SQLiteHelper("session").open(write_mode=True) as db:
            db.execute(
                "INSERT INTO session_diagnostics"
                " (session_id, kind, content, workflow_id, task_id)"
                " VALUES (?, ?, ?, ?, ?)",
                (session_id, kind, content, workflow_id, task_id),
            )
            db.commit()

    def fetch(self, session_id: int) -> list[dict[str, Any]]:
        """Return all diagnostics for a session, newest first."""
        with SQLiteHelper("session").open(row_factory=True) as db:
            rows = db.fetchall(
                "SELECT id, session_id, kind, content, created_at"
                " FROM session_diagnostics WHERE session_id = ?"
                " ORDER BY created_at DESC",
                (session_id,),
            )
        return [dict(r) for r in rows]

    def fetch_all(self, limit: int = 50) -> list[dict[str, Any]]:
        """Return most recent diagnostics across all sessions."""
        with SQLiteHelper("session").open(row_factory=True) as db:
            rows = db.fetchall(
                "SELECT id, session_id, kind, content, created_at"
                " FROM session_diagnostics"
                " ORDER BY created_at DESC LIMIT ?",
                (limit,),
            )
        return [dict(r) for r in rows]
