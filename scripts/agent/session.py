#!/usr/bin/env python3
"""scripts/agent/session.py

AgentSession facade — delegates to domain-specific repository modules.
"""

from __future__ import annotations

import logging
import sqlite3
from dataclasses import dataclass
from typing import TYPE_CHECKING

from db.config import DbConfig
from db.helper import SQLiteHelper
from shared.types import LLMMessage

from agent.config_builders import build_agent_config
from agent.diagnostic_store import DiagnosticStore
from agent.services.models import DeletedRow
from agent.session_message_repo import SessionMessageRepository
from agent.turn_persistence import TurnPersistence

if TYPE_CHECKING:
    from agent.config_dataclasses import DiagnosticsConfig
    from agent.context import ConversationState

logger = logging.getLogger(__name__)


class SchemaMissingError(RuntimeError):
    """Raised when required SQLite schema tables are missing."""


SESSION_TITLE_STORAGE_MAX_CHARS = 32
SESSION_TITLE_DISPLAY_MAX_CHARS = 32


@dataclass(frozen=True)
class SessionTarget:
    """Immutable identity of a session at one point in time.

    A task that must write into the session that created it carries a target and
    is refused when the live session id or generation no longer matches.
    """

    session_id: int | None
    generation: int


class AgentSession:
    """Manages REPL session and message persistence in SQLite.

    Owns session_id state and all DB operations related to sessions/messages.
    Imported by REPLAgent to decouple persistence from REPL logic.
    """

    _repo: SessionMessageRepository | None = None
    _session_id: int | None = None  # current session DB row ID
    _generation: int = 0

    @property
    def _message_repo(self) -> SessionMessageRepository:
        """Return the cached message repo, rebuilding it when its bound session_id
        no longer matches the current session_id (e.g. after a session restore)."""
        if self._repo is None or self._repo.session_id != self.session_id:
            self._repo = SessionMessageRepository(
                self.session_id,
                strict_mode=self._strict_mode,
                db_config=self._db_config,
            )
        return self._repo

    @_message_repo.setter
    def _message_repo(self, value: SessionMessageRepository) -> None:
        self._repo = value

    @property
    def session_id(self) -> int | None:
        """Return the current session DB row ID (None before ``start``)."""
        return self._session_id

    @session_id.setter
    def session_id(self, value: int | None) -> None:
        """Assign the session id; any change of id advances the generation."""
        if value != self._session_id:
            self._generation += 1
        self._session_id = value

    @property
    def generation(self) -> int:
        """Return the monotonically increasing session generation."""
        return self._generation

    def capture_target(self) -> SessionTarget:
        """Return the immutable (session id, generation) pair of the live session."""
        return SessionTarget(self._session_id, self._generation)

    def is_current_target(self, target: SessionTarget) -> bool:
        """Return True when ``target`` still names the live session and generation."""
        return (
            target.session_id == self._session_id
            and target.generation == self._generation
        )

    def memory_finalized_count(self, session_id: int) -> int:
        """Return how many history messages were already memory-finalized.

        Memory extraction creates fresh entries on every run, so a session
        finalized at a transition must not be finalized again from the same
        history at exit (0 when the session was never finalized).
        """
        return self._memory_finalized.get(session_id, 0)

    def record_memory_finalized(self, session_id: int, n_messages: int) -> None:
        """Record that ``session_id`` was memory-finalized over ``n_messages``."""
        self._memory_finalized[session_id] = n_messages

    def switch_session(self, session_id: int | None) -> None:
        """Make ``session_id`` current and always advance the generation.

        Used by the transition commit so tasks bound to the previous generation
        are rejected even when the same session id is loaded again.
        """
        self._session_id = session_id
        self._generation += 1

    def restore_identity(self, session_id: int | None, generation: int) -> None:
        """Put back a previously captured identity (transition rollback only).

        The generation is set to ``generation`` exactly; the caller guarantees
        ``generation`` was captured from this session, so it never moves backwards
        past a value another task already observed.
        """
        self._session_id = session_id
        self._generation = generation

    def __init__(
        self,
        *,
        strict_mode: bool = False,
        diagnostics_cfg: DiagnosticsConfig | None = None,
        db_config: DbConfig,
    ) -> None:
        """Initialize the session manager with optional strict mode and message repository.

        ``diagnostics_cfg`` is the validated snapshot owned by ``AgentContext``. When
        omitted (the ``AgentSession()`` call in ``context.py`` does not pass it), the
        validated config is built once here via ``build_agent_config()`` so the store
        never reads ``agent.toml`` per operation (REQ-001 / AC-6). A malformed
        ``[diagnostics]`` table fails closed during this build.
        """
        self._db_config = db_config
        self._session_id = None
        self._generation = 0
        self._strict_mode = strict_mode
        self._title_pending_ids: set[int | None] = set()
        self._memory_finalized: dict[int, int] = {}
        if diagnostics_cfg is None:
            diagnostics_cfg = build_agent_config().diagnostics
        self._diagnostic_store = DiagnosticStore(
            diagnostics_cfg=diagnostics_cfg, db_config=self._db_config
        )

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
        messages: list[tuple[str, str | None, list[dict] | None, str | None]],
    ) -> None:
        """Persist multiple messages in a single DB transaction."""
        self._message_repo.save_many(messages)

    def replace_messages(self, messages: list[LLMMessage]) -> int | None:
        """Persist compressed history snapshot back to DB.

        Skips silently if session_id is None (before session.start()).
        Returns the persisted /undo compression boundary (int) on success,
        or None when nothing was persisted.
        """
        if self.session_id is None:
            logger.warning(
                "replace_messages called before session.start(); skipping persist"
            )
            return None
        return self._message_repo.replace_messages(self.session_id, messages)

    def save_diagnostic(self, content: str) -> None:
        """Persist a diagnostic event to the session_diagnostics table via DiagnosticStore; never written to messages."""
        if self.session_id is None:
            logger.warning(
                "save_diagnostic called before session.start(); skipping persist"
            )
            return
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

    def fetch_messages(self, session_id: int) -> tuple[list[LLMMessage], bool, int]:
        """Fetch messages for a session from DB.

        Returns a 3-tuple of (messages, session_found, undo_floor_message_id).
        - messages: list of message dicts in insertion order. Empty list if none.
        - session_found: True if session exists in the sessions table, False otherwise.
        - undo_floor_message_id: the persisted /undo compression boundary (0 when none).
        """
        return self._message_repo.fetch_messages(session_id)

    def count_messages_up_to(self, session_id: int, message_id: int) -> int:
        """Delegate to the message repo (row 10): snapshot count at the boundary."""
        return self._message_repo.count_messages_up_to(session_id, message_id)

    async def turn_boundary(self, conv: ConversationState) -> TurnPersistence:
        """Materialize the turn-persistence boundary for the turn about to run.

        Captures the turn-start ``message_id`` marker (``MAX(message_id)``,
        ``0`` when the session has no rows yet) and takes a memory snapshot via
        :meth:`ConversationState.snapshot_messages`, then returns the
        :class:`TurnPersistence` boundary that owns every write of the turn.
        """
        marker = self._message_repo.turn_start_marker(self.session_id)
        snapshot = await conv.snapshot_messages()
        return TurnPersistence(self, conv, marker, snapshot)

    # ── Session lifecycle ────────────────────────────────────────────────────

    def start(self) -> None:
        """Create a new session record in DB and store its ID. Raises SchemaMissingError on missing schema."""
        with SQLiteHelper("session", db_config=self._db_config).open(
            write_mode=True
        ) as db:
            try:
                # Pre-flight check: verify required table exists before attempting INSERT
                cursor = db.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                    ("sessions",),
                )
                if cursor.fetchone() is None:
                    raise SchemaMissingError(
                        "Session schema missing. Run: bash deploy/init_db.sh to initialize the database."
                    )
                cur = db.execute("INSERT INTO sessions (title) VALUES (NULL)")
            except SchemaMissingError:
                raise
            except sqlite3.OperationalError as e:
                # Fallback: check the real extended result code / name for SQLITE_ERROR (1)
                err_code = getattr(e, "sqlite_errorcode", None)
                err_name = getattr(e, "sqlite_errorname", "")
                if (
                    err_code == 1
                    or err_name == "SQLITE_ERROR"
                    or "no such table: sessions" in str(e)
                ):
                    raise SchemaMissingError(
                        "Session schema missing. Run: bash deploy/init_db.sh to initialize the database."
                    ) from e
                raise
            self.session_id = cur.lastrowid
            db.commit()
        logger.info("Session started: id=%s", self.session_id)
        self._message_repo = SessionMessageRepository(
            self.session_id, strict_mode=self._strict_mode, db_config=self._db_config
        )

    def is_title_pending(self, session_id: int | None = None) -> bool:
        """Return True if title generation is in progress for a session.

        Without ``session_id`` the current session is checked.
        """
        key = self._session_id if session_id is None else session_id
        return key in self._title_pending_ids

    def set_title_pending(self, pending: bool, session_id: int | None = None) -> None:
        """Set title generation pending state for a session.

        Without ``session_id`` the current session is updated.
        """
        key = self._session_id if session_id is None else session_id
        if pending:
            self._title_pending_ids.add(key)
        else:
            self._title_pending_ids.discard(key)

    def set_title(self, title: str, *, target: SessionTarget | None = None) -> bool:
        """Set a session title (truncated to SESSION_TITLE_STORAGE_MAX_CHARS).

        With no ``target`` the current session is written. With a ``target`` the
        write happens only while the target still names the live session and
        generation; a stale target returns False without any write.

        Returns True when the title was persisted, False when there is no active
        session or the target is stale. Raises sqlite3.Error on DB failure.
        """
        if target is not None and not self.is_current_target(target):
            self.set_title_pending(False, target.session_id)
            return False
        self.set_title_pending(False)
        if self._session_id is None:
            return False
        with SQLiteHelper("session", db_config=self._db_config).open(
            write_mode=True
        ) as db:
            db.execute(
                "UPDATE sessions SET title = ? WHERE session_id = ?",
                (title[:SESSION_TITLE_STORAGE_MAX_CHARS], self._session_id),
            )
            db.commit()
        return True

    def list_sessions(self, limit: int = 20) -> list[dict]:
        """Return the most recent sessions from DB as structured data.

        Each dict: session_id, created_at, title, is_current (bool), message_count (int).
        Raises sqlite3.Error on DB failure.
        """
        with SQLiteHelper("session", db_config=self._db_config).open(
            row_factory=True
        ) as db:
            rows = db.fetchall(
                "SELECT s.session_id, s.created_at, s.title, COUNT(m.message_id) AS message_count FROM sessions s LEFT JOIN messages m ON m.session_id = s.session_id GROUP BY s.session_id, s.created_at, s.title ORDER BY s.session_id DESC LIMIT ?",
                (limit,),
            )
        return [
            {
                "session_id": r["session_id"],
                "created_at": r["created_at"],
                "title": r["title"],
                "is_current": r["session_id"] == self.session_id,
                "message_count": r["message_count"],
            }
            for r in rows
        ]

    def undo_last_turn(self) -> list[DeletedRow]:
        """Delete the last turn, gated by the /undo compression boundary.

        Delegates to SessionMessageRepository.undo_deleted_rows: the repo reads the
        persisted boundary (sessions.undo_floor_message_id), walks back to the last
        'user' role message, and deletes every message from that row onwards
        (message_id >= last_user_id) in one transaction, returning those rows
        ascending by message_id. Returns [] when nothing is undoable (no user
        message, or the last user turn is at/before the boundary). The deleted-row
        identity crosses to the service layer so memory trims to the same set.
        """
        if self.session_id is None:
            return []
        return self._message_repo.undo_deleted_rows(self.session_id)

    def delete_session(self, session_id: int) -> bool:
        """Delete a session and all its messages from DB.

        ON DELETE CASCADE removes messages automatically.
        Returns True when found and deleted, False when not found.
        """
        with SQLiteHelper("session", db_config=self._db_config).open(
            write_mode=True
        ) as db:
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
