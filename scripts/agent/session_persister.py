#!/usr/bin/env python3
"""scripts/agent/session_persister.py

SessionPersister — session data persistence at shutdown.

Responsibilities:
  - Persisting session diagnostics summary
  - Persisting session memories via memory layer
"""

from __future__ import annotations

import json
import logging
import sqlite3
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agent.context import AgentContext

from agent.cli_view import CLIView
from agent.diagnostic_store import DiagnosticStore
from agent.memory.models import HistoryMessage

logger = logging.getLogger(__name__)

# Lazy imports inside methods to avoid circular dependency at module level.
# StateStore is only needed when workflow tracking is active.


class SessionPersister:
    """Handles persistence of session-level data at shutdown.

    Encapsulates ``_persist_session_diagnostics`` and ``_persist_session_memories``
    extracted from AgentREPL.
    """

    def __init__(
        self,
        ctx: AgentContext,
        diagnostic_store: DiagnosticStore,
        view: CLIView,
    ) -> None:
        """Initialize with AgentContext, DiagnosticStore, and CLIView references."""
        self._ctx = ctx
        self._diagnostic_store = diagnostic_store
        self._view = view

    async def persist_session_diagnostics(self) -> None:
        """Persist a lightweight runtime diagnostics summary at session end."""
        try:
            stats = self._ctx.stats
            llm = self._ctx.services.llm if self._ctx.services is not None else None
            services = self._ctx.services
            hist_mgr = services.hist_mgr if services is not None else None
            session_id = self._ctx.session.session_id

            latency_summary = {}
            for step, samples in stats.stat_latency.items():
                if samples:
                    latency_summary[step] = {
                        "count": len(samples),
                        "mean_ms": round(sum(samples) / len(samples) * 1000, 2),
                        "max_ms": round(max(samples) * 1000, 2),
                    }

            workflow_count = 0
            task_count = 0
            approval_events = 0
            retry_count = 0
            artifacts: list[str] = []
            if session_id is not None:
                try:
                    from agent.workflow.state_store import StateStore

                    store = StateStore()
                    sid = str(session_id)
                    task_count = store.get_task_count(sid)
                    workflow_count = store.get_workflow_count(sid)
                    approval_events = store.get_approval_count(sid)
                    execute_attempts = store.get_execute_attempt_count(sid)
                    retry_count = max(0, execute_attempts - task_count)
                    artifacts = store.get_artifact_uris(sid)
                except (RuntimeError, sqlite3.Error):
                    pass

            rag_query_count = 0
            rag_stage_outcomes: list[dict] = []
            if session_id is not None:
                try:
                    entries = self._diagnostic_store.fetch(session_id)
                    rag_entries = [e for e in entries if e.get("kind") == "rag_query"]
                    rag_query_count = len(rag_entries)
                    for e in rag_entries:
                        try:
                            diag = json.loads(e["content"])
                            rag_stage_outcomes.extend(diag.get("stage_results", []))
                        except (json.JSONDecodeError, KeyError):
                            pass
                except (sqlite3.Error, RuntimeError):
                    pass

            summary = {
                "session_id": session_id,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "turns": stats.stat_turns,
                "tool_calls": stats.stat_tool_calls,
                "tool_errors": stats.stat_tool_errors,
                "partial_completions": stats.stat_partial_completions,
                "parse_errors": getattr(llm, "stat_parse_errors", 0),
                "heartbeat_timeouts": getattr(llm, "stat_heartbeat_timeouts", 0),
                "reconnects": getattr(llm, "stat_reconnects", 0),
                "semantic_cache_hits": stats.stat_semantic_cache_hits,
                "input_tokens": stats.stat_input_tokens,
                "output_tokens": stats.stat_output_tokens,
                "compress_count": getattr(hist_mgr, "stat_compress_count", 0),
                "fallback_truncate_count": getattr(
                    hist_mgr, "stat_fallback_truncate_count", 0
                ),
                "latency_summary": latency_summary,
                "workflow_count": workflow_count,
                "task_count": task_count,
                "approval_events": approval_events,
                "retry_count": retry_count,
                "artifacts": artifacts,
                "rag_query_count": rag_query_count,
                "rag_stage_outcomes": rag_stage_outcomes,
            }

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
                    content=json.dumps(summary),
                )
            except (RuntimeError, sqlite3.Error) as e:
                logger.debug("DiagnosticStore.save failed: %s", e)
                self._view.write_warning(f"Diagnostics could not be saved: {e}")

        except (OSError, sqlite3.Error):
            logger.debug("Failed to persist session diagnostics", exc_info=True)

    async def persist_session_memories(self) -> None:
        """Extract and persist session memories before compression or resource close."""
        if self._ctx.services is not None and self._ctx.services.memory is not None:
            try:
                history = []
                for m in self._ctx.conv.history:
                    expected_keys = {"role", "content"}
                    extra_keys = set(m.keys()) - expected_keys
                    if extra_keys:
                        logger.warning(
                            "Unexpected keys in history message: %s — full message: %s",
                            extra_keys,
                            m,
                        )
                    history.append(
                        HistoryMessage(role=m["role"], content=m.get("content") or "")
                    )
                await self._ctx.services.memory.on_session_stop(
                    session_id=self._ctx.session.session_id,
                    history=history,
                    turn_id=self._ctx.turn.current_turn_id,
                )
            except (RuntimeError, sqlite3.Error, OSError):
                logger.exception(
                    "Memory on_session_stop failed; session data may be incomplete"
                )
