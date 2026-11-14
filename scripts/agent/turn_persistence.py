#!/usr/bin/env python3
"""scripts/agent/turn_persistence.py

Turn-persistence boundary — makes one agent turn's session-DB persistence
all-or-nothing. On any persistence failure inside a turn the
boundary compensates (restores the captured pre-rewrite row image when the
turn's compression rewrite succeeded, otherwise deletes the turn's partial
DB rows via the repository's compensation delete), restores
``ConversationState`` memory to its turn-start snapshot, and raises
:class:`ConversationPersistenceError` wrapping the underlying ``sqlite3.Error``.

Write routing is realized at the repository: each phase-group (e.g. a
tool round's assistant + tool-result messages) is persisted in a single
``begin_immediate`` transaction on a single connection via
:meth:`SessionMessageRepository.save_phase_grouped`. The boundary delegates its
writes to the repository so every turn write flows through one object; no
turn-path component may call ``ctx.session.save*`` directly (AC-001).

The boundary itself never touches SQLite: it offloads every repository write
(and the compensation delete) to a worker thread with :func:`asyncio.to_thread`. Each repository call opens its own short-lived connection, so the
connection is used exclusively inside one worker thread; the loop-thread SQLite
usage (``session_message_repo.read*``, snapshot queries) is unaffected.
"""

from __future__ import annotations

import asyncio
import logging
import sqlite3
from typing import TYPE_CHECKING, NoReturn

if TYPE_CHECKING:
    from shared.types import LLMMessage

    from agent.context import ConversationState
    from agent.session import AgentSession

logger = logging.getLogger(__name__)


class ConversationPersistenceError(Exception):
    """Raised when a turn's session-DB persistence fails and is compensated.

    Wraps the underlying ``sqlite3.Error``; the original is preserved on both
    ``__cause__`` (via ``raise... from``) and the public ``cause`` attribute. Subclasses the plain ``Exception`` base, matching the
    subsystem-local error placement of ``shared.llm_exceptions.LLMTransportError``.
    """

    def __init__(self, message: str, *, cause: sqlite3.Error) -> None:
        super().__init__(f"{message}: {cause}")
        self.cause = cause


class TurnPersistence:
    """Owns all session-DB writes of one agent turn (all-or-nothing).

    Constructed once per turn by :meth:`AgentSession.turn_boundary`. Holds the
    turn-start ``message_id`` marker (``0`` for a fresh session), a defensive
    turn-start memory snapshot, and the owning session. Every turn write is
    delegated to the session's message repository so a whole turn is either
    fully persisted or fully compensated.
    """

    def __init__(
        self,
        session: AgentSession,
        conv: ConversationState,
        turn_start_message_id: int,
        snapshot: list[LLMMessage],
    ) -> None:
        """Bind the boundary to the session, its conversation memory, and the marker.

        Args:
            session: The :class:`AgentSession` owning the turn's message repo.
            conv: The ``ConversationState`` whose history is snapshotted at turn
                start and restored on a compensated failure.
            turn_start_message_id: ``MAX(message_id)`` for the session at turn
                start (``0`` when fresh); the append-only compensation deletes
                rows strictly after this marker, and an image restore re-inserts
                only captured rows at or below it — never prior-turn rows.
            snapshot: Defensive copy of ``conv.history`` captured at turn start.
        """
        self.session = session
        self.conv = conv
        self.session_id = session.session_id
        self.turn_start_message_id = turn_start_message_id
        self._snapshot = snapshot
        self._undo_floor_at_turn_start = conv.undo_floor
        self._pre_rewrite_image: tuple | None = None

    async def save(
        self,
        role: str,
        content: str | None,
        tool_calls: list[dict] | None = None,
        tool_call_id: str | None = None,
    ) -> None:
        """Persist a single turn message (one phase transaction).

        The repository call runs on a worker thread; its
        ``sqlite3.Error`` propagates back to the caller unchanged.
        """
        try:
            await asyncio.to_thread(
                self.session._message_repo.save, role, content, tool_calls, tool_call_id
            )
        except sqlite3.Error as exc:
            await self._fail_from_error(exc)

    async def save_many(
        self,
        messages: list[tuple[str, str | None, list[dict] | None, str | None]],
    ) -> None:
        """Persist several turn messages in one repository transaction.

        The repository call runs on a worker thread; its
        ``sqlite3.Error`` propagates back to the caller unchanged.
        """
        try:
            await asyncio.to_thread(self.session._message_repo.save_many, messages)
        except sqlite3.Error as exc:
            await self._fail_from_error(exc)

    async def save_phase_grouped(
        self,
        messages: list[tuple[str, str | None, list[dict] | None, str | None]],
    ) -> None:
        """Persist a phase-group (e.g. an assistant message + its tool results) atomically.

        Runs in a single ``begin_immediate`` transaction on a single connection,
        so a single injected failure leaves either all or none of the round's
        rows (AC-005). The repository call runs on a worker thread; its ``sqlite3.Error`` propagates back to the caller unchanged.
        """
        try:
            await asyncio.to_thread(
                self.session._message_repo.save_phase_grouped, messages
            )
        except sqlite3.Error as exc:
            await self._fail_from_error(exc)

    async def replace_messages(self, messages: list[LLMMessage]) -> int | None:
        """Persist a compressed snapshot back to DB.

        Captures the session's pre-rewrite row image on the worker thread before
        the rewrite, so a later failure in the same turn can restore the
        turn-start rows instead of only deleting rows above the marker.
        The repository call runs on a worker thread; its
        ``sqlite3.Error`` propagates back to the caller unchanged.
        """
        if self.session_id is None:
            return None
        try:
            return await asyncio.to_thread(
                self._rewrite_with_pre_image_capture, messages
            )
        except sqlite3.Error as exc:
            await self._fail_from_error(exc)
            return None  # unreachable: _fail_from_error always raises

    def _rewrite_with_pre_image_capture(self, messages: list[LLMMessage]) -> int | None:
        """Capture the pre-rewrite image, then rewrite (sync, worker thread).

        The image is captured before the rewrite but stored on ``self`` only
        after the rewrite returns, so a failed rewrite leaves no image and
        compensation keeps the delete-above-marker path (its transaction already
        rolled back atomically). First-image-only: a second rewrite in the same
        turn reuses the first image and cannot move the restored state past the
        turn-start image. A capture failure propagates
        before any rewrite happens.
        """
        if self.session_id is None:
            return None  # defensive: replace_messages guards before dispatching
        image = self._pre_rewrite_image
        if image is None:
            image = self.session._message_repo.capture_session_image(self.session_id)
        result = self.session._message_repo.replace_messages(self.session_id, messages)
        self._pre_rewrite_image = image  # stored only after the rewrite returns
        return result

    async def _compensate(self) -> int:
        """Undo the turn's DB changes in one transaction.

        When the turn rewrote the session (a compression) a captured pre-rewrite
        image exists: restore it with :meth:`restore_session_image`, so the
        turn-start rows and the persisted ``/undo`` boundary come back even
        though ``replace_messages`` succeeded earlier. Without an image the
        append-only path keeps deleting rows strictly above the marker.
        Offloaded to a worker thread like the writes.
        """
        if self.session_id is None:
            return 0
        image = self._pre_rewrite_image
        if image is not None:
            return await asyncio.to_thread(
                self.session._message_repo.restore_session_image,
                self.session_id,
                image,
                image[1],
                self.turn_start_message_id,
            )
        return await asyncio.to_thread(
            self.session._message_repo.delete_messages_from,
            self.session_id,
            self.turn_start_message_id,
        )

    async def _fail_from_error(self, exc: sqlite3.Error) -> NoReturn:
        """Compensate, restore memory, and raise the persistence error.

        Deletes the turn's partial rows, restores ``conv.history`` to the
        turn-start snapshot element-wise, then raises
        :class:`ConversationPersistenceError` chaining ``exc``. A compensation-delete failure is logged and does not mask the
        original error.
        """
        try:
            await self._compensate()
        except sqlite3.Error as comp_exc:
            logger.error(
                "Turn compensation failed after persistence error: %s", comp_exc
            )
        finally:
            await self.conv.restore_messages(self._snapshot)
            self.conv.undo_floor = self._undo_floor_at_turn_start
        raise ConversationPersistenceError(
            "turn not persisted; history rolled back", cause=exc
        ) from exc
