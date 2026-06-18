#!/usr/bin/env python3
"""agent/session_message_repo.py
Session and message persistence repository.
"""

import logging

import orjson
from db.helper import SQLiteHelper
from shared.json_utils import dumps as _json_dumps
from shared.types import LLMMessage

logger = logging.getLogger(__name__)

_VALID_ROLES: frozenset[str] = frozenset({"user", "assistant", "tool", "system"})


class SessionMessageRepository:
    """Repository for session message operations."""

    def __init__(
        self, session_id: int | None = None, *, strict_mode: bool = False
    ) -> None:
        self.session_id = session_id
        self.strict_mode = strict_mode
        self.stat_skipped_no_session: int = 0
        self.stat_skipped_invalid_role: int = 0

    def save(
        self,
        role: str,
        content: str,
        tool_calls: list[dict] | None = None,
        tool_call_id: str | None = None,
    ) -> None:
        """Persist a single message to DB under the current session."""
        if self.session_id is None:
            self.stat_skipped_no_session += 1
            logger.warning("Persistence skipped: no session_id (role=%r)", role)
            if self.strict_mode:
                raise RuntimeError("Cannot save message: no session_id (strict mode)")
            return
        if role not in _VALID_ROLES:
            self.stat_skipped_invalid_role += 1
            logger.warning("Invalid role %r; message not saved", role)
            if self.strict_mode:
                raise RuntimeError(
                    f"Cannot save message with invalid role {role!r} (strict mode)"
                )
            return
        tc_json = _json_dumps(tool_calls) if tool_calls else None
        with SQLiteHelper("session").open(write_mode=True) as db:
            db.execute(
                "INSERT INTO messages"
                " (session_id, role, content, tool_calls, tool_call_id)"
                " VALUES (?, ?, ?, ?, ?)",
                (self.session_id, role, content, tc_json, tool_call_id),
            )
            db.commit()
        # sqlite3.Error propagates to caller

    def save_many(
        self,
        messages: list[tuple[str, str, list[dict] | None, str | None]],
    ) -> None:
        """Persist multiple messages in a single DB transaction.

        Each tuple: (role, content, tool_calls, tool_call_id).
        Rows with invalid roles are skipped with a warning and counted.
        Opens exactly one DB connection regardless of the number of messages.
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
        invalid_count = sum(1 for role, _, _, _ in messages if role not in _VALID_ROLES)
        rows = [
            (
                self.session_id,
                role,
                content,
                _json_dumps(tc) if tc else None,
                tc_id,
            )
            for role, content, tc, tc_id in messages
            if role in _VALID_ROLES
        ]
        if invalid_count:
            self.stat_skipped_invalid_role += invalid_count
            logger.warning(
                "Persistence skipped: %d messages had invalid roles", invalid_count
            )
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
        # sqlite3.Error propagates to caller

    def fetch_messages(self, session_id: int) -> list[LLMMessage]:
        """Fetch and parse messages for a session from DB.

        Returns a list of message dicts (role/content/tool_calls) in insertion order.
        Returns [] if no messages exist. Raises sqlite3.Error on DB failure.
        """
        with SQLiteHelper("session").open(row_factory=True) as db:
            rows = db.fetchall(
                "SELECT message_id, role, content, tool_calls, tool_call_id"
                " FROM messages WHERE session_id = ? ORDER BY message_id",
                (session_id,),
            )
        if not rows:
            return []
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
