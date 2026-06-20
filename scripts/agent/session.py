#!/usr/bin/env python3
"""agent/session.py
AgentSession facade — delegates to domain-specific repository modules.
"""

import logging

from db.helper import SQLiteHelper
from shared.types import LLMMessage

from agent.diagnostic_store import DiagnosticStore
from agent.note_repo import NoteRepository
from agent.session_message_repo import SessionMessageRepository

logger = logging.getLogger(__name__)


class AgentSession:
    """Manages REPL session and message persistence in SQLite.

    Owns session_id state and all DB operations related to sessions/messages.
    Imported by REPLAgent to decouple persistence from REPL logic.
    """

    def __init__(self, *, strict_mode: bool = False) -> None:
        self.session_id: int | None = None  # current session DB row ID
        self._strict_mode = strict_mode
        self._title_pending: bool = False
        self._message_repo = SessionMessageRepository(
            self.session_id, strict_mode=strict_mode
        )
        self._note_repo = NoteRepository()
        self._diagnostic_store = DiagnosticStore(self.session_id)

    # ── SessionMessageRepository delegation ──────────────────────────────────

    def save(
        self,
        role: str,
        content: str,
        tool_calls: list[dict] | None = None,
        tool_call_id: str | None = None,
    ) -> None:
        """Persist a single message under the current session."""
        self._message_repo.save(role, content, tool_calls, tool_call_id)

    def save_many(
        self,
        messages: list[tuple[str, str, list[dict] | None, str | None]],
    ) -> None:
        """Persist multiple messages in a single DB transaction."""
        self._message_repo.save_many(messages)

    def save_diagnostic(self, content: str) -> None:
        """Persist a diagnostic-only message; not included in normal history retrieval."""
        self._diagnostic_store.save(
            self.session_id, kind="llm_transport_error", content=content
        )

    @property
    def skipped_no_session_count(self) -> int:
        """Number of save calls skipped due to missing session_id."""
        return self._message_repo.stat_skipped_no_session

    @property
    def skipped_invalid_role_count(self) -> int:
        """Number of save calls skipped due to invalid role."""
        return self._message_repo.stat_skipped_invalid_role

    def fetch_messages(self, session_id: int) -> list[LLMMessage]:
        """Fetch messages for a session from DB. Returns [] when session has no messages."""
        return self._message_repo.fetch_messages(session_id)

    # ── NoteRepository delegation ─────────────────────────────────────────────

    def add_note(self, content: str) -> int:
        """Insert a new note and return its note_id. Raises sqlite3.Error on failure."""
        return self._note_repo.add_note(content)

    def list_notes(self) -> list[dict]:
        """Return all notes ordered by note_id ascending."""
        return self._note_repo.list_notes()

    def delete_note(self, note_id: int) -> bool:
        """Delete a note by ID. Returns True when found and deleted."""
        return self._note_repo.delete_note(note_id)

    def get_all_note_contents(self) -> list[str]:
        """Return all note content strings in creation order for prompt injection."""
        return self._note_repo.get_all_note_contents()

    def pin_note(self, note_id: int) -> bool:
        """Pin a note by ID."""
        return self._note_repo.pin_note(note_id)

    def unpin_note(self, note_id: int) -> bool:
        """Unpin a note by ID."""
        return self._note_repo.unpin_note(note_id)

    def get_pinned_notes(self) -> list[dict]:
        """Return all pinned notes."""
        return self._note_repo.get_pinned_notes()

    def search_notes(self, query: str, limit: int = 5) -> list[dict]:
        """Search notes by content LIKE query."""
        return self._note_repo.search_notes(query, limit)

    # ── Session lifecycle ────────────────────────────────────────────────────

    def start(self) -> None:
        """Create a new session record in DB and store its ID. Raises sqlite3.Error on failure."""
        with SQLiteHelper("session").open(write_mode=True) as db:
            cur = db.execute("INSERT INTO sessions (title) VALUES (NULL)")
            self.session_id = cur.lastrowid
            db.commit()
        logger.info("Session started: id=%s", self.session_id)
        self._message_repo = SessionMessageRepository(
            self.session_id, strict_mode=self._strict_mode
        )

    def is_title_pending(self) -> bool:
        """Return True if title generation is in progress."""
        return self._title_pending

    def set_title_pending(self, pending: bool) -> None:
        """Set title generation pending state."""
        self._title_pending = pending

    def set_title(self, title: str) -> None:
        """Set the session title using the first user input (truncated to 50 chars). Raises sqlite3.Error on failure."""
        self._title_pending = False
        if self.session_id is None:
            return
        with SQLiteHelper("session").open(write_mode=True) as db:
            db.execute(
                "UPDATE sessions SET title = ? WHERE session_id = ?",
                (title[:50], self.session_id),
            )
            db.commit()

    def list_sessions(self, limit: int = 20) -> list[dict]:
        """Return the most recent sessions from DB as structured data.

        Each dict: session_id, created_at, title, is_current (bool).
        Raises sqlite3.Error on DB failure.
        """
        with SQLiteHelper("session").open(row_factory=True) as db:
            rows = db.fetchall(
                "SELECT session_id, created_at, title FROM sessions"
                " ORDER BY session_id DESC LIMIT ?",
                (limit,),
            )
        return [
            {
                "session_id": r["session_id"],
                "created_at": r["created_at"],
                "title": r["title"],
                "is_current": r["session_id"] == self.session_id,
            }
            for r in rows
        ]

    def delete_last_turn(self) -> None:
        """Delete the last user+assistant message pair from DB for the current session.

        Deletes the two highest message_id rows so that both the user message
        and the assistant reply are removed together.  If only one message exists
        (e.g. LLM failed before saving the assistant reply), that one is removed.
        """
        if self.session_id is None:
            return
        with SQLiteHelper("session").open(write_mode=True) as db:
            rows = db.fetchall(
                "SELECT message_id FROM messages"
                " WHERE session_id = ?"
                " ORDER BY message_id DESC LIMIT 2",
                (self.session_id,),
            )
            if not rows:
                return
            ids = [r[0] for r in rows]
            placeholders = ",".join("?" * len(ids))
            db.execute(
                f"DELETE FROM messages WHERE message_id IN ({placeholders})",  # nosec B608 — placeholders is "?" * n, not user input
                tuple(ids),
            )
            db.commit()
        logger.info(
            "Deleted last turn from session %s: %s messages",
            self.session_id,
            len(ids),
        )

    def undo_last_turn(self) -> int:
        """Delete all DB messages from the last user message onwards.

        Handles turns with tool_call and injection messages correctly by
        walking back to the last 'user' role message and deleting everything
        from that point (inclusive).  Returns the number of rows deleted.
        """
        if self.session_id is None:
            return 0
        with SQLiteHelper("session").open(write_mode=True) as db:
            rows = db.fetchall(
                "SELECT message_id, role FROM messages"
                " WHERE session_id = ? ORDER BY message_id DESC",
                (self.session_id,),
            )
            if not rows:
                return 0
            last_user_id: int | None = None
            for r in rows:
                if r[1] == "user":
                    last_user_id = r[0]
                    break
            if last_user_id is None:
                return 0
            deleted: int = db.execute(
                "SELECT COUNT(*) FROM messages"
                " WHERE session_id = ? AND message_id >= ?",
                (self.session_id, last_user_id),
            ).fetchone()[0]
            db.execute(
                "DELETE FROM messages WHERE session_id = ? AND message_id >= ?",
                (self.session_id, last_user_id),
            )
            db.commit()
        logger.info(
            "Undo: deleted %s messages from session %s",
            deleted,
            self.session_id,
        )
        return deleted

    def delete_session(self, session_id: int) -> bool:
        """Delete a session and all its messages from DB.

        ON DELETE CASCADE removes messages automatically.
        Returns True when found and deleted, False when not found.
        """
        with SQLiteHelper("session").open(write_mode=True) as db:
            row = db.execute(
                "SELECT session_id FROM sessions WHERE session_id = ?",
                (session_id,),
            ).fetchone()
            if row is None:
                return False
            db.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
            db.commit()
        logger.info("Session %s deleted", session_id)
        return True
