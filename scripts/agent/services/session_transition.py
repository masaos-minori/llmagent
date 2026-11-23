"""scripts/agent/services/session_transition.py

Atomic session transitions — one pipeline for ``/clear new`` and ``/session load``.

One pipeline serves both: refuse when a turn is running, snapshot the live session,
build the new state off to the side, finalize the old session (Memory and
diagnostics), then commit every field together. Any failure before or during the
commit restores the snapshot, so a transition either completes or leaves the old
session intact.

Idle check (UNK-01): ``ctx.turn.persistence_boundary`` is assigned at turn start and
never cleared, so it cannot tell an idle session from a running turn. A turn is
active while ``ctx.turn.current_turn_id`` is set (cleared by the turn-end audit
event) or a workflow runs; slash commands run between turns, so both are clear then.

Finalization (UNK-02, UNK-03): a failed old-session finalization only warns, because
the old session's rows are already persisted. Memory extraction creates fresh entries
on every run, so ``AgentSession`` records the finalized history length and the
persister skips an unchanged history; a transition that fails after finalizing
therefore cannot duplicate Memory entries at exit.
"""

from __future__ import annotations

import copy
import dataclasses
import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

from agent.commands.mixin_base import refresh_session_correlation, reset_session_stats
from agent.diagnostic_store import DiagnosticStore
from agent.services.session_restore import RestoredSessionState, restore_session
from agent.session_persister import SessionPersister

if TYPE_CHECKING:
    from shared.types import LLMMessage

    from agent.context import AgentContext, RuntimeStats
    from agent.services.models import SessionRestoreResult

logger = logging.getLogger(__name__)


class SessionTransitionRefusedError(RuntimeError):
    """Raised when a transition is requested while a turn is running."""


class _LogWarningSink:
    """Warning sink for finalization output when no CLI view is available."""

    def write_warning(self, msg: str) -> None:
        """Log the warning (never raises)."""
        logger.warning("Session finalization: %s", msg)


@dataclass(frozen=True)
class SessionTransitionSnapshot:
    """Immutable copy of every field a transition commit changes."""

    session_id: int | None
    generation: int
    history: tuple[LLMMessage, ...]
    undo_floor: int
    correlation_id: str | None
    stats: RuntimeStats


def _capture(ctx: AgentContext) -> SessionTransitionSnapshot:
    """Snapshot the live session fields (a synchronous, atomic read)."""
    session_id = ctx.session.session_id
    return SessionTransitionSnapshot(
        session_id=session_id,
        generation=ctx.session.generation,
        history=tuple(copy.deepcopy(m) for m in ctx.conv.history),
        undo_floor=ctx.conv.undo_floor,
        correlation_id=None if session_id is None else str(session_id),
        stats=copy.deepcopy(ctx.stats),
    )


def _refresh_correlation(ctx: AgentContext) -> None:
    """Re-point the MCP transport correlation id at the current session."""
    if ctx.services is not None:
        refresh_session_correlation(ctx)


class SessionTransitionService:
    """Runs ``/clear new`` and ``/session load`` as one atomic transition."""

    def __init__(self, ctx: AgentContext, persister: SessionPersister) -> None:
        """Bind the service to a context and the persister used for finalization."""
        self._ctx = ctx
        self._persister = persister

    @classmethod
    def for_context(cls, ctx: AgentContext) -> SessionTransitionService:
        """Build a service whose finalization uses the context's diagnostic store."""
        store = ctx.diagnostics or DiagnosticStore(
            diagnostics_cfg=ctx.cfg.diagnostics, db_config=ctx.cfg.db
        )
        return cls(ctx, SessionPersister(ctx, store, _LogWarningSink()))

    # ── Public API ───────────────────────────────────────────────────────────

    async def load(self, session_id: int) -> SessionRestoreResult:
        """Switch to a stored session; raises and leaves the old one on failure."""
        self._ensure_idle()
        snapshot = _capture(self._ctx)
        try:
            # Read-only: validates the target before the old session is finalized.
            state = await restore_session(self._ctx, session_id)
            await self._finalize_old_session()
            await self._commit(state, session_id)
        except BaseException:
            await self._rollback(snapshot)
            raise
        logger.info("Session transition: loaded session %s", session_id)
        return state.result

    async def clear_new(self) -> int | None:
        """Finalize the current session and switch to a fresh, empty one."""
        self._ensure_idle()
        snapshot = _capture(self._ctx)
        new_session_id: int | None = None
        try:
            await self._finalize_old_session()
            self._ctx.session.start()
            new_session_id = self._ctx.session.session_id
            await self._commit_clear()
        except BaseException:
            await self._rollback(snapshot)
            self._discard_unused_session(new_session_id, snapshot.session_id)
            raise
        logger.info("Session transition: started new session %s", new_session_id)
        return new_session_id

    # ── Pipeline steps ───────────────────────────────────────────────────────

    def _ensure_idle(self) -> None:
        """Refuse the transition while a turn or workflow is running (REQ-003)."""
        ctx = self._ctx
        if ctx.turn.current_turn_id is not None or ctx.workflow.active:
            raise SessionTransitionRefusedError(
                "A turn is still running; wait for it to finish before switching "
                "sessions."
            )

    async def _finalize_old_session(self) -> None:
        """Persist the old session's Memory and diagnostics from one snapshot.

        A failure only warns: the old session's rows are already persisted.
        """
        if self._ctx.session.session_id is None:
            return
        try:
            snapshot = self._persister.capture_snapshot()
            await self._persister.persist_session_memories(snapshot)
            await self._persister.persist_session_diagnostics(snapshot)
        except Exception as exc:  # noqa: BLE001 — finalization is best effort; the transition must not abort on it
            logger.warning(
                "Old-session finalization failed (%s); continuing the transition",
                type(exc).__name__,
            )

    async def _commit(self, state: RestoredSessionState, session_id: int) -> None:
        """Apply the built state to the context, all fields together."""
        ctx = self._ctx
        ctx.session.switch_session(session_id)
        await ctx.conv.restore_messages(list(state.history))
        ctx.conv.undo_floor = state.undo_floor
        _refresh_correlation(ctx)
        reset_session_stats(ctx)

    async def _commit_clear(self) -> None:
        """Apply the empty-history state for ``/clear new`` (new session already set)."""
        ctx = self._ctx
        await ctx.conv.restore_messages(list(ctx.conv.history[:1]))
        ctx.conv.undo_floor = 0
        _refresh_correlation(ctx)
        reset_session_stats(ctx)

    async def _rollback(self, snapshot: SessionTransitionSnapshot) -> None:
        """Put every snapshotted field back; never raises over the original error."""
        ctx = self._ctx
        try:
            await ctx.conv.restore_messages(list(snapshot.history))
            ctx.conv.undo_floor = snapshot.undo_floor
            ctx.session.restore_identity(snapshot.session_id, snapshot.generation)
            for field in dataclasses.fields(snapshot.stats):
                setattr(ctx.stats, field.name, getattr(snapshot.stats, field.name))
            _refresh_correlation(ctx)
        except Exception as exc:  # noqa: BLE001 — rollback must not mask the error that triggered it
            logger.error("Session transition rollback failed: %s", type(exc).__name__)

    def _discard_unused_session(
        self, new_session_id: int | None, old_session_id: int | None
    ) -> None:
        """Delete the empty row ``clear_new`` created when its transition failed."""
        if new_session_id is None or new_session_id == old_session_id:
            return
        try:
            self._ctx.session.delete_session(new_session_id)
        except Exception as exc:  # noqa: BLE001 — cleanup of an empty row is best effort
            logger.warning(
                "Could not remove unused session %s: %s",
                new_session_id,
                type(exc).__name__,
            )
