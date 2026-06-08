#!/usr/bin/env python3
"""agent/session_message_repo.py
Session and message persistence repository.
"""

import logging

import orjson
from db.helper import SQLiteHelper
from rag.types import LLMMessage

logger = logging.getLogger(__name__)

_VALID_ROLES: frozenset[str] = frozenset({"user", "assistant", "tool", "system"})


class SessionMessageRepository:
    """Repository for session message operations."""

    def __init__(self, session_id: int | None = None) -> None:
        self.session_id = session_id

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
        if role not in _VALID_ROLES:
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
                if role in _VALID_ROLES
            ]
            if not rows:
                return
            with SQLiteHelper("session").open(write_mode=True) as db:
                db.executemany(
                    "INSERT INTO messages"
                    " (session_id, role, content, tool_calls, tool_call_id)"
                    " VALUES (?, ?, ?, ?, ?)",
                    rows,
                )
                db.commit()
        except Exception as e:
            logger.warning(f"save_many failed: {e}")

    def fetch_messages(self, session_id: int) -> list[LLMMessage] | None:
        """Fetch and parse messages for a session from DB.

        Returns a list of message dicts (role/content/tool_calls) in insertion order,
        or None if the session is not found or a DB error occurs.
        """
        try:
            with SQLiteHelper("session").open(row_factory=True) as db:
                rows = db.fetchall(
                    "SELECT message_id, role, content, tool_calls, tool_call_id"
                    " FROM messages WHERE session_id = ? ORDER BY message_id",
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
                    logger.warning(
                        orjson.dumps(
                            {
                                "event": "corrupt_record",
                                "session_id": session_id,
                                "message_id": r["message_id"],
                            }
                        ).decode()
                    )
            if r["tool_call_id"]:
                msg["tool_call_id"] = r["tool_call_id"]
            messages.append(msg)
        return messages
