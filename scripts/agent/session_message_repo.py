#!/usr/bin/env python3
"""scripts/agent/session_message_repo.py

Session and message persistence repository.
"""

import logging

import orjson
from db.helper import SQLiteHelper
from shared.json_utils import dumps as _json_dumps
from shared.types import LLMMessage

from agent.services.models import DeletedRow

logger = logging.getLogger(__name__)

_DEFAULT_VALID_ROLES: frozenset[str] = frozenset(
    {"user", "assistant", "tool", "system"}
)

_INSERT_MESSAGE_SQL = (
    "INSERT INTO messages (session_id, role, content, tool_calls, tool_call_id)"
    " VALUES (?, ?, ?, ?, ?)"
)


def _tool_calls_json(tool_calls: object | None) -> str | None:
    """Return tool_calls serialized to JSON, or None when empty/absent."""
    return _json_dumps(tool_calls) if tool_calls else None


class SessionMessageRepository:
    """Repository for session message operations."""

    def __init__(
        self,
        session_id: int | None = None,
        *,
        strict_mode: bool = False,
        roles_source: frozenset[str] | None = None,
    ) -> None:
        """Initialize the session message repository with session ID and strict mode flag.

        Args:
            session_id: The session identifier for message persistence.
            strict_mode: When True, raises RuntimeError on invalid operations instead of skipping.
            roles_source: Optional custom set of valid roles; falls back to default if None.
        """
        self.session_id = session_id
        self.strict_mode = strict_mode
        self._valid_roles = (
            roles_source if roles_source is not None else _DEFAULT_VALID_ROLES
        )
        self.stat_skipped_no_session: int = 0
        self.stat_skipped_invalid_role: int = 0

    def save(
        self,
        role: str,
        content: str | None,
        tool_calls: list[dict] | None = None,
        tool_call_id: str | None = None,
    ) -> None:
        """Persist a single message to DB under the current session.

        Normalizes ``content`` before insert: ``None`` is stored as ``""``.
        """
        if self.session_id is None:
            self.stat_skipped_no_session += 1
            logger.warning("Persistence skipped: no session_id (role=%r)", role)
            if self.strict_mode:
                raise RuntimeError("Cannot save message: no session_id (strict mode)")
            return
        if role not in self._valid_roles:
            self.stat_skipped_invalid_role += 1
            logger.warning("Invalid role %r; message not saved", role)
            if self.strict_mode:
                raise RuntimeError(
                    f"Cannot save message with invalid role {role!r} (strict mode)"
                )
            return
        norm_content = content if content is not None else ""
        tc_json = _tool_calls_json(tool_calls)
        with SQLiteHelper("session").open(write_mode=True) as db:
            db.execute(
                _INSERT_MESSAGE_SQL,
                (self.session_id, role, norm_content, tc_json, tool_call_id),
            )
            db.commit()
        # sqlite3.Error propagates to caller

    def save_many(
        self,
        messages: list[tuple[str, str | None, list[dict] | None, str | None]],
    ) -> None:
        """Persist multiple messages in a single DB transaction.

        Each tuple: (role, content, tool_calls, tool_call_id).
        Rows with invalid roles are skipped with a warning and counted.
        Opens exactly one DB connection regardless of the number of messages.
        Normalizes ``content`` before insert: ``None`` is stored as ``""``.
        """
        if self.session_id is None or not messages:
            if self.session_id is None and messages:
                self.stat_skipped_no_session += 1
                logger.warning(
                    "Persistence skipped: no session_id (save_many, %d messages)",
                    len(messages),
                )
                if self.strict_mode:
                    raise RuntimeError(
                        "Cannot save messages: no session_id (strict mode)"
                    )
            return
        invalid_count = sum(
            1 for role, _, _, _ in messages if role not in self._valid_roles
        )
        rows = [
            (
                self.session_id,
                role,
                content if content is not None else "",
                _tool_calls_json(tc),
                tc_id,
            )
            for role, content, tc, tc_id in messages
            if role in self._valid_roles
        ]
        if invalid_count:
            self.stat_skipped_invalid_role += invalid_count
            logger.warning(
                "Persistence skipped: %d messages had invalid roles", invalid_count
            )
        if not rows:
            return
        with SQLiteHelper("session").open(write_mode=True) as db:
            db.executemany(_INSERT_MESSAGE_SQL, rows)
            db.commit()
        # sqlite3.Error propagates to caller

    def replace_messages(
        self, session_id: int, messages: list[LLMMessage]
    ) -> int | None:
        """Atomically clear and re-insert all messages for a session.

        Used after history compression to persist the compressed snapshot.
        Runs in a single transaction: DELETE + executemany INSERT + UPDATE the
        /undo boundary. Returns the persisted boundary (MAX message_id), or None
        when nothing was persisted.
        """
        if not messages:
            return None
        rows = []
        for msg in messages:
            role = msg.get("role", "user")
            if role not in self._valid_roles:
                logger.warning("replace_messages: skipping invalid role %r", role)
                continue
            content = msg.get("content") or ""
            tc_json = _tool_calls_json(msg.get("tool_calls"))
            tool_call_id = msg.get("tool_call_id")
            rows.append((session_id, role, content, tc_json, tool_call_id))
        with SQLiteHelper("session").open(write_mode=True) as db:
            db.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
            db.executemany(_INSERT_MESSAGE_SQL, rows)
            boundary = db.execute(
                "SELECT COALESCE(MAX(message_id), 0) FROM messages WHERE session_id = ?",
                (session_id,),
            ).fetchone()[0]
            db.execute(
                "UPDATE sessions SET undo_floor_message_id = ? WHERE session_id = ?",
                (boundary, session_id),
            )
            db.commit()
        return int(boundary)

    @staticmethod
    def turn_start_marker(session_id: int | None) -> int:
        """Return the largest ``message_id`` for a session (``0`` when none yet).

        Used as the turn-start marker: compensation deletes rows strictly after
        this id, so a fresh session (no rows) yields ``0``. Raises ``sqlite3.Error``
        on DB failure.
        """
        if session_id is None:
            return 0
        with SQLiteHelper("session").open() as db:
            row = db.execute(
                "SELECT COALESCE(MAX(message_id), 0) FROM messages WHERE session_id = ?",
                (session_id,),
            ).fetchone()
        return int(row[0])

    def delete_messages_from(self, session_id: int, marker: int) -> int:
        """Compensation delete: remove every message strictly after ``marker`` for a session.

        One transaction. Returns the number of rows deleted. Used by the
        turn-persistence boundary to roll back a failed turn; earlier rows
        (at/below ``marker``, i.e. prior turns) are left intact (AC-002). The
        marker is ``MAX(message_id)`` at turn start, so ``> marker`` deletes
        exactly this turn's rows and never a prior turn's row. Raises
        ``sqlite3.Error`` on DB failure; the boundary wraps it into
        ``ConversationPersistenceError`` and compensates (REQ-002).
        """
        if session_id is None:
            return 0
        with SQLiteHelper("session").open(write_mode=True) as db:
            deleted = db.execute(
                "DELETE FROM messages WHERE session_id = ? AND message_id > ?",
                (session_id, marker),
            ).rowcount
            db.commit()
        # sqlite3.Error propagates to the boundary, which wraps and compensates
        return int(deleted)

    def undo_deleted_rows(self, session_id: int | None) -> list[DeletedRow]:
        """Return the rows deleted by a /undo, ascending message_id (REQ-001).

        One transaction: read the /undo boundary, find the last user row, gate on
        `last_user_id > undo_floor`, then SELECT and DELETE every row at/after it.
        Returns [] when there is no session, no user row, or the last user turn is
        at/before the boundary (nothing undoable). Raises sqlite3.Error on DB failure.
        """
        if session_id is None:
            return []
        with SQLiteHelper("session").open(write_mode=True, row_factory=True) as db:
            floor_row = db.execute(
                "SELECT undo_floor_message_id FROM sessions WHERE session_id = ?",
                (session_id,),
            ).fetchone()
            undo_floor = floor_row[0] if floor_row else 0
            rows = db.fetchall(
                "SELECT message_id, role FROM messages WHERE session_id = ? "
                "ORDER BY message_id DESC",
                (session_id,),
            )
            last_user_id = None
            for r in rows:
                if r["role"] == "user":
                    last_user_id = r["message_id"]
                    break
            if last_user_id is None or last_user_id <= undo_floor:
                return []  # nothing undoable: at/before the boundary
            deleted_rows = db.fetchall(
                "SELECT message_id, role, content, tool_call_id "
                "FROM messages WHERE session_id = ? AND message_id >= ? "
                "ORDER BY message_id",
                (session_id, last_user_id),
            )
            db.execute(
                "DELETE FROM messages WHERE session_id = ? AND message_id >= ?",
                (session_id, last_user_id),
            )
            db.commit()
        return [
            DeletedRow(
                message_id=r["message_id"],
                role=r["role"],
                content=r["content"],
                tool_call_id=r["tool_call_id"],
            )
            for r in deleted_rows
        ]

    def save_phase_grouped(
        self,
        messages: list[tuple[str, str | None, list[dict] | None, str | None]],
    ) -> None:
        """Persist a phase-group of messages in one BEGIN IMMEDIATE transaction.

        Unlike :meth:`save_many` (implicit autocommit per call), this runs the
        whole group in a single ``begin_immediate`` transaction on a single
        connection, so a single injected failure leaves either all or none of
        the round's rows (REQ-005, AC-005). Invalid roles are skipped. The
        ``begin_immediate`` block rolls back on failure and re-raises
        ``sqlite3.Error``; the boundary wraps it into
        ``ConversationPersistenceError`` and compensates (REQ-002).
        """
        if self.session_id is None or not messages:
            return
        rows = [
            (
                self.session_id,
                role,
                content if content is not None else "",
                _tool_calls_json(tc),
                tc_id,
            )
            for role, content, tc, tc_id in messages
            if role in self._valid_roles
        ]
        if not rows:
            return
        with SQLiteHelper("session").open(write_mode=True) as db:
            with db.begin_immediate():
                db.executemany(_INSERT_MESSAGE_SQL, rows)
        # sqlite3.Error propagates to the boundary, which wraps and compensates

    def get_valid_roles(self) -> frozenset[str]:
        """Return the currently active valid roles set."""
        return self._valid_roles

    def count_messages_up_to(self, session_id: int, message_id: int) -> int:
        """Count messages for a session whose ``message_id`` is <= ``message_id``.

        Messages are stored in insertion order, so this is the number of
        snapshot messages at the /undo boundary (row 10): messages with an id at
        or below the boundary belong to the compressed snapshot; later ids are
        turns added after compression. Raises sqlite3.Error on DB failure.
        """
        with SQLiteHelper("session").open() as db:
            return int(
                db.execute(
                    "SELECT COUNT(*) FROM messages WHERE session_id = ? AND message_id <= ?",
                    (session_id, message_id),
                ).fetchone()[0]
            )

    def fetch_messages(self, session_id: int) -> tuple[list[LLMMessage], bool, int]:
        """Fetch and parse messages for a session from DB.

        Returns a 3-tuple of (messages, session_found, undo_floor_message_id).
        - messages: list of message dicts (role/content/tool_calls) in insertion order.
          Empty list if no messages exist for this session.
        - session_found: True if session exists in the sessions table, False otherwise.
        - undo_floor_message_id: the persisted /undo compression boundary (0 when none).
        Returns ([], False, 0) when session does not exist.
        Returns ([], True, 0) when session exists but has no messages.
        Raises sqlite3.Error on DB failure.
        """
        with SQLiteHelper("session").open(row_factory=True) as db:
            session_rows = db.fetchall(
                "SELECT undo_floor_message_id FROM sessions WHERE session_id = ?",
                (session_id,),
            )
            undo_floor = session_rows[0][0] if session_rows else 0
            session_found = len(session_rows) > 0
            # Query inside the block: the connection is closed on exit.
            rows = (
                db.fetchall(
                    "SELECT message_id, role, content, tool_calls, tool_call_id"
                    " FROM messages WHERE session_id = ? ORDER BY message_id",
                    (session_id,),
                )
                if session_found
                else []
            )
        if not session_found:
            return ([], False, 0)
        if not rows:
            return ([], True, 0)
        messages: list[LLMMessage] = []
        for r in rows:
            msg: LLMMessage = {"role": r["role"], "content": r["content"]}
            if r["tool_calls"]:
                try:
                    msg["tool_calls"] = orjson.loads(r["tool_calls"])
                except orjson.JSONDecodeError as e:
                    logger.warning(
                        "Invalid tool_calls JSON in session %s: %s",
                        session_id,
                        e,
                    )
                    logger.warning(
                        _json_dumps(
                            {
                                "event": "corrupt_record",
                                "session_id": session_id,
                                "message_id": r["message_id"],
                            }
                        )
                    )
            if r["tool_call_id"]:
                msg["tool_call_id"] = r["tool_call_id"]
            messages.append(msg)
        return (messages, True, undo_floor)
