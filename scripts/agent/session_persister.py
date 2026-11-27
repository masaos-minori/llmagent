#!/usr/bin/env python3
"""scripts/agent/session_persister.py

SessionPersister — session data persistence at shutdown.

Responsibilities:
  - Persisting session diagnostics summary
  - Persisting session memories via memory layer

Both steps skip (logging the reason) when ctx.session.session_id is None, i.e. no
session was started; otherwise they write before resource close. Failures are
contained and reported as non-fatal.

Both steps accept one ``SessionPersistenceSnapshot`` so shutdown and the
pre-transition finalization evaluate the same state; a snapshot whose generation no
longer matches the live session is rejected without any write. When a snapshot is
supplied it is never re-captured: the persist calls read only from it.

The synchronous store reads take an optional monotonic deadline. A read group that
cannot start before the deadline is skipped and named in the result, so a bounded
shutdown step produces a labeled partial summary instead of an unbounded wait.
"""

from __future__ import annotations

import logging
import sqlite3
import time
from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING, Protocol, cast

import orjson

if TYPE_CHECKING:
    from shared.types import LLMMessage

    from agent.context import AgentContext
    from agent.workflow.state_store import StateStore

from agent.diagnostic_store import DiagnosticStore
from agent.memory.models import HistoryMessage
from agent.message_schema import unexpected_message_keys
from agent.output_tags import OutputTag
from agent.wal_checkpoint_manager import format_sqlite_error

logger = logging.getLogger(__name__)

# Lazy imports inside methods to avoid circular dependency at module level.
# StateStore is only needed when workflow tracking is active.


class WarningSink(Protocol):
    """Where non-fatal persistence warnings are written (``CLIView`` satisfies it)."""

    def write_warning(self, msg: str) -> None:
        """Write one warning line."""
        ...


@dataclass(frozen=True)
class SessionStatsSnapshot:
    """Immutable copy of the session statistics the persisted summary reads."""

    turns: int
    tool_calls: int
    tool_errors: int
    partial_completions: int
    input_tokens: int | None
    output_tokens: int | None
    latency: Mapping[str, tuple[float, ...]]


@dataclass(frozen=True)
class SessionPersistenceSnapshot:
    """Immutable view of the session state taken once for persistence.

    ``history`` is a tuple of per-message copies, so later mutation of the live
    history cannot change what a persist step reads.
    """

    session_id: int | None
    generation: int
    history: tuple[LLMMessage, ...]
    turn_id: str | None
    stats: SessionStatsSnapshot


def _deadline_spent(deadline: float | None) -> bool:
    """Return True when a monotonic deadline has already passed (None is no deadline)."""
    return deadline is not None and time.monotonic() >= deadline


def _latency_summary(
    latency: Mapping[str, tuple[float, ...]],
) -> dict[str, dict[str, float | int]]:
    """Return per-step count, mean and max latency in milliseconds."""
    summary: dict[str, dict[str, float | int]] = {}
    for step, samples in latency.items():
        if samples:
            summary[step] = {
                "count": len(samples),
                "mean_ms": round(sum(samples) / len(samples) * 1000, 2),
                "max_ms": round(max(samples) * 1000, 2),
            }
    return summary


class SessionPersister:
    """Handles persistence of session-level data at shutdown.

    Encapsulates ``_persist_session_diagnostics`` and ``_persist_session_memories``
    extracted from AgentREPL. Each skips when no session was started
    (``ctx.session.session_id is None``) and otherwise writes before resource close.
    """

    def __init__(
        self,
        ctx: AgentContext,
        diagnostic_store: DiagnosticStore,
        view: WarningSink,
    ) -> None:
        """Initialize with AgentContext, DiagnosticStore, and a warning sink."""
        self._ctx = ctx
        self._diagnostic_store = diagnostic_store
        self._view = view

    def capture_snapshot(self) -> SessionPersistenceSnapshot:
        """Read session id, generation, history, turn id and statistics once."""
        ctx = self._ctx
        stats = ctx.stats
        return SessionPersistenceSnapshot(
            session_id=ctx.session.session_id,
            generation=ctx.session.generation,
            history=tuple(cast("LLMMessage", dict(m)) for m in ctx.conv.history),
            turn_id=ctx.turn.current_turn_id,
            stats=SessionStatsSnapshot(
                turns=stats.stat_turns,
                tool_calls=stats.stat_tool_calls,
                tool_errors=stats.stat_tool_errors,
                partial_completions=stats.stat_partial_completions,
                input_tokens=stats.stat_input_tokens,
                output_tokens=stats.stat_output_tokens,
                latency=MappingProxyType(
                    {k: tuple(v) for k, v in stats.stat_latency.items()}
                ),
            ),
        )

    def _snapshot_is_live(
        self, snapshot: SessionPersistenceSnapshot, step: str
    ) -> bool:
        """Return False (and log) when the session generation changed."""
        if snapshot.generation == self._ctx.session.generation:
            return True
        logger.warning(
            "Skipping %s: snapshot generation %s no longer matches the live session",
            step,
            snapshot.generation,
        )
        return False

    def _workflow_counts(
        self, session_id: int, deadline: float | None = None
    ) -> tuple[int, int, int, list[str], bool]:
        """Return (workflow, task, retry counts, artifact URIs, skipped) from the state store.

        ``skipped`` is True when the deadline had already passed: the counts are then
        absent, not zero, and the summary says which sections it does not hold. The
        deadline is checked before the read group starts, never inside a query.
        """
        if _deadline_spent(deadline):
            return 0, 0, 0, [], True
        workflow_count = 0
        task_count = 0
        retry_count = 0
        artifacts: list[str] = []
        store: StateStore | None = None
        try:
            from agent.workflow.state_store import StateStore

            store = StateStore(db_config=self._ctx.cfg.db)
            sid = str(session_id)
            task_count = store.get_task_count(sid)
            workflow_count = store.get_workflow_count(sid)
            execute_attempts = store.get_execute_attempt_count(sid)
            # Defensive: _scalar_count() always returns int, but guard against
            # future modifications that might change this contract.
            if execute_attempts is None:
                logger.warning(
                    "get_execute_attempt_count returned None for session %s; "
                    "defaulting retry_count to 0",
                    sid,
                )
                execute_attempts = 0
            retry_count = max(0, execute_attempts - task_count)
            artifacts = store.get_artifact_uris(sid)
        except (RuntimeError, sqlite3.Error):
            pass
        finally:
            if store is not None:
                try:
                    store.close()
                except (sqlite3.Error, OSError) as exc:
                    logger.warning(
                        "Failed to close workflow StateStore for session %s: %s",
                        session_id,
                        format_sqlite_error(exc),
                    )
        return workflow_count, task_count, retry_count, artifacts, False

    def _rag_summary(
        self, session_id: int, deadline: float | None = None
    ) -> tuple[int, list[dict], bool]:
        """Return (rag query count, stage outcomes, skipped) from the diagnostic store.

        ``skipped`` is True when the deadline had already passed, exactly as in
        ``_workflow_counts``: a bounded step reports what it did not read.
        """
        if _deadline_spent(deadline):
            return 0, [], True
        rag_query_count = 0
        rag_stage_outcomes: list[dict] = []
        try:
            entries = self._diagnostic_store.fetch(session_id)
            rag_entries = [e for e in entries if e.get("kind") == "rag_query"]
            rag_query_count = len(rag_entries)
            for e in rag_entries:
                try:
                    diag = orjson.loads(e["content"])
                    rag_stage_outcomes.extend(diag.get("stage_results", []))
                except (orjson.JSONDecodeError, KeyError):
                    pass
        except (sqlite3.Error, RuntimeError):
            pass
        return rag_query_count, rag_stage_outcomes, False

    async def persist_session_diagnostics(
        self,
        snapshot: SessionPersistenceSnapshot | None = None,
        *,
        deadline: float | None = None,
    ) -> None:
        """Persist a lightweight runtime diagnostics summary at session end.

        Reads every session value from ``snapshot``, which is never re-captured when
        one is supplied (REQ-007). Skips (logging the reason) when no session was
        started or the snapshot generation is stale; any failure while building or
        saving the summary is reported as non-fatal. ``deadline`` is a monotonic
        instant: a read group that cannot start before it is skipped and named in
        the persisted summary as a partial capture.
        """
        snap = snapshot if snapshot is not None else self.capture_snapshot()
        session_id = snap.session_id
        if session_id is None:
            logger.info("Skipping session diagnostics: no started session")
            return
        if not self._snapshot_is_live(snap, "session diagnostics"):
            return
        try:
            stats = snap.stats
            llm = self._ctx.services.llm if self._ctx.services is not None else None
            services = self._ctx.services
            hist_mgr = services.hist_mgr if services is not None else None
            (
                workflow_count,
                task_count,
                retry_count,
                artifacts,
                workflow_skipped,
            ) = self._workflow_counts(session_id, deadline)
            rag_query_count, rag_stage_outcomes, rag_skipped = self._rag_summary(
                session_id, deadline
            )
            partial_sections = [
                name
                for name, skipped in (
                    ("workflow_counts", workflow_skipped),
                    ("rag_summary", rag_skipped),
                )
                if skipped
            ]

            summary = {
                "session_id": session_id,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "turns": stats.turns,
                "tool_calls": stats.tool_calls,
                "tool_errors": stats.tool_errors,
                "partial_completions": stats.partial_completions,
                "parse_errors": getattr(llm, "stat_parse_errors", 0),
                "heartbeat_timeouts": getattr(llm, "stat_heartbeat_timeouts", 0),
                "reconnects": getattr(llm, "stat_reconnects", 0),
                "input_tokens": stats.input_tokens,
                "output_tokens": stats.output_tokens,
                "compress_count": getattr(hist_mgr, "stat_compress_count", 0),
                "fallback_truncate_count": getattr(
                    hist_mgr, "stat_fallback_truncate_count", 0
                ),
                "latency_summary": _latency_summary(stats.latency),
                "workflow_count": workflow_count,
                "task_count": task_count,
                "retry_count": retry_count,
                "artifacts": artifacts,
                "rag_query_count": rag_query_count,
                "rag_stage_outcomes": rag_stage_outcomes,
            }

            if partial_sections:
                # REQ-012: a bounded step says what it did not read instead of
                # presenting the shortened summary as a complete one.
                summary["partial_sections"] = partial_sections
                self._view.write_warning(
                    f"{OutputTag.NON_FATAL} Session diagnostics captured partially: "
                    f"{', '.join(partial_sections)}"
                )

            if artifacts or rag_stage_outcomes:
                logger.warning(
                    "Session diagnostics contain sensitive fields (artifacts=%d, "
                    "rag_stage_outcomes=%d) that will be filtered before persistence",
                    len(artifacts),
                    len(rag_stage_outcomes),
                )

            try:
                self._diagnostic_store.save(
                    session_id,
                    kind="session_summary",
                    content=orjson.dumps(summary).decode(),
                )
            except (RuntimeError, sqlite3.Error) as e:
                logger.debug("DiagnosticStore.save failed: %s", format_sqlite_error(e))
                self._view.write_warning(
                    f"Diagnostics could not be saved: {format_sqlite_error(e)}"
                )

        except Exception as e:  # noqa: BLE001 — whole step is non-fatal, payload defects included
            logger.debug("Failed to persist session diagnostics", exc_info=True)
            self._view.write_warning(
                f"{OutputTag.NON_FATAL} Session persistence failed: {format_sqlite_error(e)}"
            )

    @staticmethod
    def _history_messages(snap: SessionPersistenceSnapshot) -> list[HistoryMessage]:
        """Convert snapshot history to memory-layer messages, warning on odd keys."""
        history: list[HistoryMessage] = []
        for m in snap.history:
            unexpected = unexpected_message_keys(dict(m))
            if unexpected:
                logger.warning(
                    "Unexpected keys in history message for role '%s': %s",
                    m.get("role"),
                    sorted(unexpected),
                )
            history.append(
                HistoryMessage(role=m["role"], content=m.get("content") or "")
            )
        return history

    def _already_finalized(self, snap: SessionPersistenceSnapshot) -> bool:
        """Return True when this session's unchanged history was already finalized."""
        if snap.session_id is None:
            return False
        finalized = self._ctx.session.memory_finalized_count(snap.session_id)
        if finalized and len(snap.history) <= finalized:
            logger.info(
                "Skipping session memories: session %s already finalized",
                snap.session_id,
            )
            return True
        return False

    async def persist_session_memories(
        self,
        snapshot: SessionPersistenceSnapshot | None = None,
        *,
        deadline: float | None = None,
    ) -> None:
        """Extract and persist session memories before compression or resource close.

        Reads session id, history and turn id from ``snapshot``, which is never
        re-captured when one is supplied (REQ-007). Skips (logging the reason) when
        no session was started, the snapshot generation is stale, the same history
        was already finalized, or ``deadline`` — a monotonic instant — has already
        passed, in which case the memory write is reported rather than started.
        """
        snap = snapshot if snapshot is not None else self.capture_snapshot()
        if snap.session_id is None:
            logger.info("Skipping session memories: no started session")
            return
        if not self._snapshot_is_live(snap, "session memories"):
            return
        if _deadline_spent(deadline):
            logger.warning(
                "Skipping session memories: the persist step deadline of %s is spent",
                deadline,
            )
            self._view.write_warning(
                f"{OutputTag.NON_FATAL} Session memories were not persisted: "
                "the shutdown deadline was spent"
            )
            return
        if self._already_finalized(snap):
            return
        if self._ctx.services is not None and self._ctx.services.memory is not None:
            try:
                history = self._history_messages(snap)
                await self._ctx.services.memory.on_session_stop(
                    session_id=snap.session_id,
                    history=history,
                    turn_id=snap.turn_id,
                )
                self._ctx.session.record_memory_finalized(
                    snap.session_id, len(snap.history)
                )
            except (RuntimeError, sqlite3.Error, OSError):
                logger.exception(
                    "Memory on_session_stop failed; session data may be incomplete"
                )
