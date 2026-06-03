#!/usr/bin/env python3
"""agent/session.py
SQLite-backed REPL session persistence manager.
Handles session and message records for REPLAgent.
"""

import logging
from typing import Any

import orjson
from db.helper import SQLiteHelper
from rag.types import LLMMessage

logger = logging.getLogger(__name__)


class AgentSession:
    """Manages REPL session and message persistence in SQLite.

    Owns session_id state and all DB operations related to sessions/messages.
    Imported by REPLAgent to decouple persistence from REPL logic.
    """

    def __init__(self) -> None:
        self.session_id: int | None = None  # current session DB row ID

    def start(self) -> None:
        """Create a new session record in DB and store its ID."""
        try:
            with SQLiteHelper("session").open(write_mode=True) as db:
                cur = db.execute("INSERT INTO sessions (title) VALUES (NULL)")
                self.session_id = cur.lastrowid
                db.commit()
            logger.info(f"Session started: id={self.session_id}")
        except Exception as e:
            logger.warning(
                f"Session create failed (history will not be persisted): {e}",
            )
            self.session_id = None

    _VALID_ROLES: frozenset[str] = frozenset({"user", "assistant", "tool", "system"})

    def save(
        self,
        role: str,
        content: str,
        tool_calls: list[dict] | None = None,
        tool_call_id: str | None = None,
    ) -> None:
        """Persist a single message to DB under the current session."""
        if self.session_id is None:
            return
        if role not in self._VALID_ROLES:
            logger.warning(f"Invalid role {role!r}; message not saved")
            return
        try:
            tc_json = orjson.dumps(tool_calls).decode() if tool_calls else None
            with SQLiteHelper("session").open(write_mode=True) as db:
                db.execute(
                    "INSERT INTO messages"
                    " (session_id, role, content, tool_calls, tool_call_id)"
                    " VALUES (?, ?, ?, ?, ?)",
                    (self.session_id, role, content, tc_json, tool_call_id),
                )
                db.commit()
        except Exception as e:
            logger.warning(f"Message save failed: {e}")

    def save_many(
        self,
        messages: list[tuple[str, str, list[dict] | None, str | None]],
    ) -> None:
        """Persist multiple messages in a single DB transaction.

        Each tuple: (role, content, tool_calls, tool_call_id).
        Rows with invalid roles are silently skipped.
        Opens exactly one DB connection regardless of the number of messages.
        """
        if self.session_id is None or not messages:
            return
        try:
            rows = [
                (
                    self.session_id,
                    role,
                    content,
                    orjson.dumps(tc).decode() if tc else None,
                    tc_id,
                )
                for role, content, tc, tc_id in messages
                if role in self._VALID_ROLES
            ]
            if not rows:
                return
            with SQLiteHelper("session").open(write_mode=True) as db:
                for row in rows:
                    db.execute(
                        "INSERT INTO messages"
                        " (session_id, role, content, tool_calls, tool_call_id)"
                        " VALUES (?, ?, ?, ?, ?)",
                        row,
                    )
                db.commit()
        except Exception as e:
            logger.warning(f"save_many failed: {e}")

    def set_title(self, title: str) -> None:
        """Set the session title using the first user input (truncated to 50 chars)."""
        if self.session_id is None:
            return
        try:
            with SQLiteHelper("session").open(write_mode=True) as db:
                db.execute(
                    "UPDATE sessions SET title = ? WHERE session_id = ?",
                    (title[:50], self.session_id),
                )
                db.commit()
        except Exception as e:
            logger.warning(f"Session title update failed: {e}")

    def list_sessions(self, limit: int = 20) -> list[dict]:
        """Return the most recent sessions from DB as structured data.

        Each dict: session_id, created_at, title, is_current (bool).
        Returns [] on error or when no sessions exist.
        """
        try:
            with SQLiteHelper("session").open(row_factory=True) as db:
                rows = db.fetchall(
                    "SELECT session_id, created_at, title FROM sessions"
                    " ORDER BY session_id DESC LIMIT ?",
                    (limit,),
                )
        except Exception as e:
            logger.warning(f"Session list query failed: {e}")
            return []
        return [
            {
                "session_id": r["session_id"],
                "created_at": r["created_at"],
                "title": r["title"],
                "is_current": r["session_id"] == self.session_id,
            }
            for r in rows
        ]

    def list_documents(self, lang: str | None = None, limit: int = 20) -> list[dict]:
        """Return registered documents as structured data.

        lang: filter by language ('ja' or 'en'); None means all.
        limit: maximum number of rows to return (default: 20).
        Each dict: url, title, lang, fetched_at, chunk_count.
        Returns [] on error or when no documents exist.
        """
        sql = (
            "SELECT d.url, d.title, d.lang, d.fetched_at,"
            " COUNT(c.chunk_id) AS n"
            " FROM documents d"
            " LEFT JOIN chunks c USING(doc_id)"
        )
        params: list[Any] = []
        if lang:
            sql += " WHERE d.lang = ?"
            params.append(lang)
        sql += " GROUP BY d.doc_id ORDER BY d.fetched_at DESC LIMIT ?"
        params.append(limit)
        try:
            with SQLiteHelper("session").open(row_factory=True) as db:
                rows = db.fetchall(sql, tuple(params))
        except Exception as e:
            logger.warning(f"list_documents failed: {e}")
            return []
        return [
            {
                "url": r["url"],
                "title": r["title"],
                "lang": r["lang"],
                "fetched_at": r["fetched_at"],
                "chunk_count": r["n"],
            }
            for r in rows
        ]

    def delete_document(self, url: str) -> bool:
        """Delete a document and its chunks from DB by URL.

        Removes chunks_vec first (no FK to chunks), then deletes the document
        record which cascades to chunks and chunks_fts via ON DELETE CASCADE.
        Returns True when found and deleted, False when not found.
        """
        try:
            with SQLiteHelper("session").open(write_mode=True) as db:
                row = db.execute(
                    "SELECT doc_id FROM documents WHERE url = ?",
                    (url,),
                ).fetchone()
                if row is None:
                    return False
                doc_id = row[0]
                db.execute(
                    "DELETE FROM chunks_vec"
                    " WHERE chunk_id IN"
                    " (SELECT chunk_id FROM chunks WHERE doc_id = ?)",
                    (doc_id,),
                )
                db.execute("DELETE FROM documents WHERE doc_id = ?", (doc_id,))
                db.commit()
            logger.info(f"Document deleted: url={url!r} doc_id={doc_id}")
            return True
        except Exception as e:
            logger.warning(f"delete_document failed (url={url!r}): {e}")
            return False

    def delete_last_turn(self) -> None:
        """Delete the last user+assistant message pair from DB for the current session.

        Deletes the two highest message_id rows so that both the user message
        and the assistant reply are removed together.  If only one message exists
        (e.g. LLM failed before saving the assistant reply), that one is removed.
        """
        if self.session_id is None:
            return
        try:
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
                    f"DELETE FROM messages WHERE message_id IN ({placeholders})",
                    tuple(ids),
                )
                db.commit()
            logger.info(
                f"Deleted last turn from session {self.session_id}: {len(ids)} messages",
            )
        except Exception as e:
            logger.warning(f"delete_last_turn failed: {e}")

    def delete_session(self, session_id: int) -> bool:
        """Delete a session and all its messages from DB.

        ON DELETE CASCADE removes messages automatically.
        Returns True when found and deleted, False when not found.
        """
        try:
            with SQLiteHelper("session").open(write_mode=True) as db:
                row = db.execute(
                    "SELECT session_id FROM sessions WHERE session_id = ?",
                    (session_id,),
                ).fetchone()
                if row is None:
                    return False
                db.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
                db.commit()
            logger.info(f"Session {session_id} deleted")
            return True
        except Exception as e:
            logger.warning(f"delete_session failed (id={session_id}): {e}")
            return False

    def fetch_messages(self, session_id: int) -> list[LLMMessage] | None:
        """Fetch and parse messages for a session from DB.

        Returns a list of message dicts (role/content/tool_calls) in insertion order,
        or None if the session is not found or a DB error occurs.
        """
        try:
            with SQLiteHelper("session").open(row_factory=True) as db:
                rows = db.fetchall(
                    "SELECT role, content, tool_calls, tool_call_id FROM messages"
                    " WHERE session_id = ? ORDER BY message_id",
                    (session_id,),
                )
        except Exception as e:
            logger.warning(f"Session fetch failed (id={session_id}): {e}")
            return None
        if not rows:
            return None
        messages: list[LLMMessage] = []
        for r in rows:
            msg: LLMMessage = {"role": r["role"], "content": r["content"]}
            if r["tool_calls"]:
                try:
                    msg["tool_calls"] = orjson.loads(r["tool_calls"])
                except orjson.JSONDecodeError as e:
                    logger.warning(
                        f"Invalid tool_calls JSON in session {session_id}: {e}",
                    )
            if r["tool_call_id"]:
                msg["tool_call_id"] = r["tool_call_id"]
            messages.append(msg)
        return messages

    # ── Notes (cross-session persistent memos) ────────────────────────────────

    def add_note(self, content: str) -> int | None:
        """Insert a new note and return its note_id; None on failure."""
        try:
            with SQLiteHelper("session").open(write_mode=True) as db:
                cur = db.execute("INSERT INTO notes (content) VALUES (?)", (content,))
                note_id = cur.lastrowid
                db.commit()
            logger.info(f"Note added: note_id={note_id}")
            return note_id
        except Exception as e:
            logger.warning(f"add_note failed: {e}")
            return None

    def list_notes(self) -> list[dict]:
        """Return all notes ordered by note_id ascending."""
        try:
            with SQLiteHelper("session").open(row_factory=True) as db:
                rows = db.fetchall(
                    "SELECT note_id, content, created_at FROM notes ORDER BY note_id",
                )
            return [dict(r) for r in rows]
        except Exception as e:
            logger.warning(f"list_notes failed: {e}")
            return []

    def delete_note(self, note_id: int) -> bool:
        """Delete a note by ID. Returns True when found and deleted."""
        try:
            with SQLiteHelper("session").open(write_mode=True) as db:
                row = db.execute(
                    "SELECT note_id FROM notes WHERE note_id = ?",
                    (note_id,),
                ).fetchone()
                if row is None:
                    return False
                db.execute("DELETE FROM notes WHERE note_id = ?", (note_id,))
                db.commit()
            logger.info(f"Note deleted: note_id={note_id}")
            return True
        except Exception as e:
            logger.warning(f"delete_note failed (id={note_id}): {e}")
            return False

    def get_all_note_contents(self) -> list[str]:
        """Return all note content strings in creation order for prompt injection."""
        try:
            with SQLiteHelper("session").open(row_factory=True) as db:
                rows = db.fetchall("SELECT content FROM notes ORDER BY note_id")
            return [r["content"] for r in rows]
        except Exception as e:
            logger.warning(f"get_all_note_contents failed: {e}")
            return []
