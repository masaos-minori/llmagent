"""scripts/agent/services/session_transition.py

Session transition service — atomic session switch for /clear new and /session load.

REQ-002: build the new state off to the side, commit all fields together, and
restore the pre-transition snapshot on any failure. REQ-003: refuse while a
conversation turn is active.
"""

from __future__ import annotations

import copy
import dataclasses
import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

from agent.commands.mixin_base import refresh_session_correlation, reset_session_stats
from agent.services.session_restore import restore_session

if TYPE_CHECKING:
    from shared.types import LLMMessage

    from agent.context import AgentContext, RuntimeStats
    from agent.services.models import SessionRestoreResult
    from agent.session_persister import SessionPersister

logger = logging.getLogger(__name__)


class SessionTransitionRefusedError(RuntimeError):
    """Raised when a session transition is refused because a turn is active."""


@dataclass(frozen=True)
class SessionTransitionSnapshot:
    """Defensive copy of the full session state taken before a transition.

    Holds every field the commit step writes, so rollback can restore the
    previous session exactly: session id, generation, history, undo floor, and
    statistics. Correlation is not stored here — it is a push of the session id
    to MCP tools, re-pushed by ``refresh_session_correlation`` on rollback.
    """

    session_id: int | None
    generation: int
    history: list[LLMMessage]
    undo_floor: int
    stats: RuntimeStats


class SessionTransitionService:
    """Atomic transitions between sessions: idle check, finalize, build, commit.

    The context is untouched until the commit step; a failed build or commit
    restores every snapshotted field and re-raises the original error (AC-1).
    """

    def __init__(self, ctx: AgentContext, persister: SessionPersister) -> None:
        self._ctx = ctx
        self._persister = persister
        # UNK-03 guard: finalize a session at most once per process even though
        # memory extraction dedups repeated writes.
        self._finalized_sessions: set[int] = set()

    async def load(self, session_id: int) -> SessionRestoreResult:
        """Transition to a persisted session and return its load counts.

        Raises SessionNotFoundError / SessionNoMessagesError from the builder;
        on any failure the previous session state is left exactly as it was.
        """
        self._require_idle()
        snapshot = self._capture()
        await self._finalize_old_session()
        try:
            built = await restore_session(self._ctx, session_id)
            self._commit(
                session_id=built.result.session_id,
                history=built.history,
                undo_floor=built.undo_floor,
                bump_generation=True,
            )
        except BaseException:
            self._rollback(snapshot)
            raise
        return built.result

    async def clear_new(self) -> None:
        """Finalize the current session and start a fresh one (system prompt only)."""
        self._require_idle()
        snapshot = self._capture()
        await self._finalize_old_session()
        ctx = self._ctx
        try:
            ctx.session.start()  # assigns a new session id and bumps generation
            history: list[LLMMessage] = (
                [{"role": "system", "content": ctx.conv.system_prompt_content}]
                if ctx.conv.system_prompt_content
                else []
            )
            self._commit(
                session_id=ctx.session.session_id,
                history=history,
                undo_floor=0,
                bump_generation=False,  # start() already bumped generation
            )
        except BaseException:
            self._rollback(snapshot)
            raise
        logger.info("History cleared; new session %s started", ctx.session.session_id)

    # ── pipeline steps ─────────────────────────────────────────────────────────

    def _require_idle(self) -> None:
        """Refuse the transition while a conversation turn is running (REQ-003).

        Uses ``conv.is_processing`` and ``turn.current_turn_id``: both are set
        at turn start and reliably cleared at turn end. ``turn.persistence_boundary``
        is never cleared after its first assignment, so it is unusable here.
        """
        ctx = self._ctx
        if ctx.conv.is_processing or ctx.turn.current_turn_id is not None:
            raise SessionTransitionRefusedError(
                "Session transition refused: a conversation turn is in progress."
            )

    def _capture(self) -> SessionTransitionSnapshot:
        """Copy the current session state before any transition work starts."""
        ctx = self._ctx
        return SessionTransitionSnapshot(
            session_id=ctx.session.session_id,
            generation=ctx.session.generation,
            history=copy.deepcopy(ctx.conv.history),
            undo_floor=ctx.conv.undo_floor,
            stats=copy.deepcopy(ctx.stats),
        )

    async def _finalize_old_session(self) -> None:
        """Persist the old session's Memory and diagnostics through the persister.

        Failure warns and continues: the turn rows are already persisted, so a
        finalization error must not block the transition (UNK-02).
        """
        ctx = self._ctx
        session_id = ctx.session.session_id
        if session_id is None or session_id in self._finalized_sessions:
            return
        snapshot = self._persister.capture_snapshot()
        try:
            await self._persister.persist_session_memories(snapshot)
            await self._persister.persist_session_diagnostics(snapshot)
            self._finalized_sessions.add(session_id)
        except Exception:  # noqa: BLE001 — finalization failure must not block the transition
            logger.warning(
                "Old session %s finalization failed; continuing with transition",
                session_id,
                exc_info=True,
            )

    def _commit(
        self,
        *,
        session_id: int | None,
        history: list[LLMMessage],
        undo_floor: int,
        bump_generation: bool,
    ) -> None:
        """Assign all transition fields together; no partial commits."""
        ctx = self._ctx
        ctx.session.session_id = session_id
        if bump_generation:
            ctx.session.bump_generation()
        ctx.conv.history[:] = history
        ctx.conv.undo_floor = undo_floor
        reset_session_stats(ctx)
        refresh_session_correlation(ctx)

    def _rollback(self, snapshot: SessionTransitionSnapshot) -> None:
        """Restore every snapshotted field and re-arm MCP correlation."""
        ctx = self._ctx
        ctx.session.session_id = snapshot.session_id
        ctx.session.generation = snapshot.generation
        ctx.conv.history[:] = copy.deepcopy(snapshot.history)
        ctx.conv.undo_floor = snapshot.undo_floor
        for field in dataclasses.fields(ctx.stats):
            setattr(
                ctx.stats,
                field.name,
                copy.deepcopy(getattr(snapshot.stats, field.name)),
            )
        if ctx.session.session_id is not None:
            refresh_session_correlation(ctx)
        logger.warning(
            "Session transition failed; previous session %s state restored",
            snapshot.session_id,
        )
