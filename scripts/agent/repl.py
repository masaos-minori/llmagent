#!/usr/bin/env python3
"""AgentREPL
Interactive REPL agent with MCP tool calling.
Imported by agent.py as the entry point.
Slash-command handlers live in agent/commands/registry.CommandRegistry.
Turn-level orchestration (LLM loop, tool dispatch) lives in agent/orchestrator.py.

Architecture (dependency injection via AgentContext):
  AgentContext   — shared mutable state container (agent/context.py)
  CLIView        — readline, multiline input display (agent/cli_view.py)
  LLMClient      — HTTP retry, payload build, SSE stream (shared/llm_client.py)
  ToolExecutor   — MCP routing, error handling, TTL cache (shared/tool_executor.py)
  HistoryManager — character counting, LLM-based compression (agent/history.py)
  CommandRegistry — slash-command dispatch (agent/commands/registry.py)
  Orchestrator   — per-turn task control: LLM loop, tool dispatch (agent/orchestrator.py)
  AgentConfig    — mutable runtime config dataclass (agent/config.py)

AgentREPL responsibilities:
  _repl_loop           — main input/dispatch loop
  _init_components     — DI wiring
  run                  — startup sequence
"""

import asyncio
import json
import signal
import sqlite3
import time
from pathlib import Path
from typing import TYPE_CHECKING

from db.helper import SQLiteHelper
from shared.logger import Logger

from agent.cli_view import CLIView
from agent.commands.registry import CommandRegistry
from agent.context import AgentContext
from agent.diagnostic_store import DiagnosticStore
from agent.repl_health import watchdog_loop
from agent.services.rag_maintenance_service import RagMaintenanceService

if TYPE_CHECKING:
    from agent.orchestrator import Orchestrator

logger = Logger(__name__, "/opt/llm/logs/agent.log")


# ─────────────────────────────────────────────────────────────────────────────
# REPLAgent: thin coordinator over AgentContext components
# ─────────────────────────────────────────────────────────────────────────────


class AgentREPL:
    """Interactive REPL agent.

    Coordinates LLMClient, ToolExecutor, HistoryManager,
    CommandRegistry, and CLIView via AgentContext dependency injection.
    All persistent session state is held in self._ctx (AgentContext).
    """

    SLASH_COMMANDS = [
        "/help",
        "/mcp",
        "/config",
        "/stats",
        "/context",
        "/compact",
        "/clear",
        "/session",
        "/debug",
        "/export",
        "/undo",
        "/history",
        "/system",
        "/db",
        "/set",
        "/reload",
        "/approve",
        "/reject",
        "/exit",
    ]

    def __init__(self) -> None:
        self._ctx = AgentContext()
        self._view = CLIView(AgentREPL.SLASH_COMMANDS)
        self._cmds: CommandRegistry | None = None
        self._orchestrator: Orchestrator | None = None
        self._diagnostic_store = DiagnosticStore()
        self._turn_active: bool = False
        self._shutdown_event: asyncio.Event | None = None

    @property
    def _prompt(self) -> str:
        return "> "

    @property
    def _n_tools(self) -> int:
        """Number of tools available (from config/agent.toml tool_definitions)."""
        return len(self._ctx.cfg.tool.tool_definitions)

    def _get_chunk_count(self) -> str:
        """Return formatted chunk count from DB, or '?' on error."""
        try:
            count = RagMaintenanceService().stats_rag()[1]
            return f"{count:,}"
        except (sqlite3.Error, OSError, RuntimeError) as e:
            logger.debug("Failed to get chunk count: %s", e)
            return "?"

    # ── Watchdog — delegated to agent_repl_health ─────────────────────────────

    async def _watchdog_loop(self) -> None:
        await watchdog_loop(self._ctx)

    async def _start_watchdog(self, ctx: AgentContext) -> "asyncio.Task | None":
        """Create the watchdog task if watchdog_interval > 0."""
        watchdog_interval = ctx.cfg.mcp.mcp_watchdog_interval
        if watchdog_interval > 0:
            logger.info(
                "Watchdog enabled: interval=%ss, max_restarts=%s",
                watchdog_interval,
                ctx.cfg.mcp.mcp_watchdog_max_restarts,
            )
            return asyncio.create_task(self._watchdog_loop())
        logger.info("Watchdog disabled (mcp_watchdog_interval=0)")
        return None

    async def _stop_watchdog(self, task: "asyncio.Task | None") -> None:
        """Cancel and await the watchdog task, suppressing CancelledError."""
        if task is not None:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

    async def _persist_session_memories(self, ctx: AgentContext) -> None:
        """Extract and persist session memories before compression or resource close."""
        if ctx.services.memory is not None:
            try:
                await ctx.services.memory.on_session_stop(
                    session_id=ctx.session.session_id,
                    history=ctx.conv.history,
                    turn_id=ctx.turn.current_turn_id,
                )
            except (RuntimeError, sqlite3.Error, OSError):
                logger.exception(
                    "Memory on_session_stop failed; session data may be incomplete"
                )

    def _persist_session_diagnostics(self, ctx: AgentContext) -> None:
        """Persist a lightweight runtime diagnostics summary at session end."""
        try:
            stats = ctx.stats
            llm = ctx.services.llm if ctx.services is not None else None
            hist_mgr = ctx.services.hist_mgr if ctx.services is not None else None
            tool_results = ctx.tool_result_store
            session_id = ctx.session.session_id

            latency_summary = {}
            for step, samples in stats.stat_latency.items():
                if samples:
                    latency_summary[step] = {
                        "count": len(samples),
                        "mean_ms": round(sum(samples) / len(samples) * 1000, 2),
                        "max_ms": round(max(samples) * 1000, 2),
                    }

            tool_result_summary: dict[str, int] = {}
            if session_id is not None and tool_results is not None:
                try:
                    with SQLiteHelper("session").open(row_factory=True) as db:
                        rows = db.fetchall(
                            "SELECT COUNT(*) as cnt, SUM(is_error) as errs"
                            " FROM tool_results WHERE session_id = ?",
                            (session_id,),
                        )
                        if rows:
                            row = rows[0]
                            tool_result_summary = {
                                "total": row["cnt"],
                                "errors": row["errs"] or 0,
                            }
                except sqlite3.Error:
                    pass

            workflow_count = 0
            task_count = 0
            approval_events = 0
            retry_count = 0
            artifacts: list[str] = []
            if session_id is not None:
                try:
                    with SQLiteHelper("workflow").open(row_factory=True) as wdb:
                        sid = str(session_id)
                        rows = wdb.fetchall(
                            "SELECT COUNT(*) as cnt FROM tasks WHERE session_id=?",
                            (sid,),
                        )
                        task_count = int(rows[0]["cnt"]) if rows else 0
                        rows = wdb.fetchall(
                            "SELECT COUNT(DISTINCT workflow_id) as cnt"
                            " FROM tasks WHERE session_id=? AND workflow_id IS NOT NULL",
                            (sid,),
                        )
                        workflow_count = int(rows[0]["cnt"]) if rows else 0
                        rows = wdb.fetchall(
                            "SELECT COUNT(*) as cnt FROM approvals"
                            " WHERE task_id IN (SELECT task_id FROM tasks WHERE session_id=?)",
                            (sid,),
                        )
                        approval_events = int(rows[0]["cnt"]) if rows else 0
                        rows = wdb.fetchall(
                            "SELECT COUNT(*) as cnt FROM attempts"
                            " WHERE task_id IN (SELECT task_id FROM tasks WHERE session_id=?)"
                            " AND stage_id='execute'",
                            (sid,),
                        )
                        retry_count = (
                            max(0, int(rows[0]["cnt"]) - task_count) if rows else 0
                        )
                        art_rows = wdb.fetchall(
                            "SELECT uri FROM artifacts"
                            " WHERE task_id IN (SELECT task_id FROM tasks WHERE session_id=?)",
                            (sid,),
                        )
                        artifacts = [
                            uri for r in art_rows if (uri := dict(r).get("uri"))
                        ]
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
                "partial_completions": (
                    llm.stat_partial_completions if llm is not None else 0
                ),
                "parse_errors": llm.stat_parse_errors if llm is not None else 0,
                "heartbeat_timeouts": (
                    llm.stat_heartbeat_timeouts if llm is not None else 0
                ),
                "reconnects": llm.stat_reconnects if llm is not None else 0,
                "semantic_cache_hits": stats.stat_semantic_cache_hits,
                "input_tokens": stats.stat_input_tokens,
                "output_tokens": stats.stat_output_tokens,
                "compress_count": (
                    hist_mgr.stat_compress_count if hist_mgr is not None else 0
                ),
                "fallback_truncate_count": (
                    hist_mgr.stat_fallback_truncate_count if hist_mgr is not None else 0
                ),
                "latency_summary": latency_summary,
                "tool_result_summary": tool_result_summary,
                "workflow_count": workflow_count,
                "task_count": task_count,
                "approval_events": approval_events,
                "retry_count": retry_count,
                "artifacts": artifacts,
                "rag_query_count": rag_query_count,
                "rag_stage_outcomes": rag_stage_outcomes,
            }

            # Persist to queryable DiagnosticStore
            try:
                self._diagnostic_store.save(
                    session_id,
                    kind="session_summary",
                    content=json.dumps(summary),
                )
            except (RuntimeError, sqlite3.Error) as e:
                logger.debug("DiagnosticStore.save failed: %s", e)

        except (OSError, sqlite3.Error):
            logger.debug("Failed to persist session diagnostics", exc_info=True)

    async def _close_resources(self) -> None:
        """Close all session resources. Called in the run() finally block."""
        self._view.write_history()
        # WAL checkpoint before closing connections
        try:
            with SQLiteHelper("session").open(write_mode=True) as db:
                db.checkpoint("TRUNCATE")
            logger.info("WAL checkpoint completed on shutdown")
        except sqlite3.Error as e:
            logger.warning("WAL checkpoint failed on shutdown: %s", e)
        # ctx.services is None when build_agent_context() never completed (e.g. init failed).
        svc = self._ctx.services
        if svc is not None:
            await svc.lifecycle.shutdown_all()
            await svc.http.aclose()

    # ── Main REPL loop ─────────────────────────────────────────────────────────

    async def _repl_loop(self) -> None:
        """Process user input lines until /exit, EOF, or shutdown request."""
        ctx = self._ctx
        if self._cmds is None:
            raise RuntimeError("_repl_loop called before _init_components()")
        if self._orchestrator is None:
            raise RuntimeError("_repl_loop called before _init_components()")
        loop = asyncio.get_running_loop()
        _GRACEFUL_TIMEOUT: float = 10.0
        while True:
            line = await self._read_input(loop)
            if line is None:
                break
            if not line:
                continue
            if self._should_exit(line, ctx):
                break
            self._turn_active = True
            ctx.conv.is_processing = True
            try:
                await asyncio.wait_for(
                    self._dispatch_line(line, ctx),
                    timeout=_GRACEFUL_TIMEOUT if ctx.conv.shutdown_requested else None,
                )
            except TimeoutError:
                logger.warning(
                    "Graceful shutdown: turn did not complete within %.1fs; forcing exit",
                    _GRACEFUL_TIMEOUT,
                )
                break
            finally:
                self._turn_active = False
                ctx.conv.is_processing = False
            if ctx.conv.shutdown_requested:
                break

    async def _read_input(self, loop: asyncio.AbstractEventLoop) -> str | None:
        """Read a single input line, handling EOF/keyboard interrupt and multiline continuation."""
        try:
            raw = await loop.run_in_executor(None, lambda: input(self._prompt))
        except (EOFError, KeyboardInterrupt):
            self._view.write_turn_end()
            return None
        line = raw.strip()
        if line.endswith("\\"):
            line = await self._view.read_multiline(loop, line)
            line = line.strip()
        return line

    def _should_exit(self, line: str, ctx: AgentContext) -> bool:
        """Return True when the REPL loop should terminate."""
        if ctx.conv.shutdown_requested:
            self._view.write_warning("Shutdown requested, exiting...")
            return True
        if line == "/exit":
            return True
        return False

    async def _dispatch_line(self, line: str, ctx: AgentContext) -> None:
        """Dispatch a non-empty, non-exit line to commands or the orchestrator."""
        if self._cmds is None:
            raise RuntimeError("_dispatch_line called before _init_components()")
        if self._orchestrator is None:
            raise RuntimeError("_dispatch_line called before _init_components()")
        if line.startswith("/"):
            matched = await self._cmds.dispatch(line)
            if not matched:
                self._view.write_warning(
                    f"Unknown command: {line}  (type /help for commands)"
                )
        else:
            llm = ctx.services.llm
            _prev_partial = llm.stat_partial_completions if llm is not None else 0
            await self._orchestrator.handle_turn(line)
            if llm is not None and llm.stat_partial_completions > _prev_partial:
                self._view.write_warning(
                    "Partial LLM completion stored."
                    " Use /stats to see count or query tool_results"
                    " (tool_name='llm_partial_completion')."
                )

    def _get_workflow_status(self) -> str:
        """Return a human-readable workflow status string for the startup banner."""
        if self._orchestrator is None:
            return "unknown"
        status = self._orchestrator.workflow_status()
        mode = status["mode"]
        if mode == "disabled":
            return "disabled"
        if status["tracking"] == "enabled":
            return f"{mode} (tracking enabled)"
        return f"{mode} (definition not loaded)"

    def _print_startup_banner(self) -> None:
        """Print the startup line showing DB chunks, tool count, and workflow status."""
        chunk_count = self._get_chunk_count()
        workflow_status = self._get_workflow_status()
        self._view.write_startup_banner(
            chunk_count,
            self._n_tools,
            workflow_status,
            memory_enabled=self._ctx.cfg.memory.use_memory_layer,
        )

    async def _run_repl_loop(self) -> None:
        """Run the main REPL loop with watchdog if enabled."""
        ctx = self._ctx
        _watchdog_task = await self._start_watchdog(ctx)
        try:
            self._print_startup_banner()
            ctx.session.start()
            if ctx.services.tools is not None and ctx.session.session_id is not None:
                ctx.services.tools.set_session_id(str(ctx.session.session_id))
            await self._repl_loop()
        finally:
            self._persist_session_diagnostics(ctx)
            await self._persist_session_memories(ctx)
            await self._stop_watchdog(_watchdog_task)
            await self._close_resources()

    async def run(self) -> None:
        """Start the interactive REPL.

        Delegates startup orchestration to StartupOrchestrator (component init,
        MCP server spawning, health checks, security audit, initial prompt setup),
        then enters the main input loop.
        """
        from agent.startup import (
            StartupOrchestrator,  # noqa: PLC0415 — lazy: avoids circular import at module level
        )

        loop = asyncio.get_running_loop()
        self._shutdown_event = asyncio.Event()

        def _sigterm_handler() -> None:
            self._ctx.conv.shutdown_requested = True
            if self._shutdown_event is not None:
                self._shutdown_event.set()
            logger.info("SIGTERM received; graceful shutdown initiated")

        try:
            loop.add_signal_handler(signal.SIGTERM, _sigterm_handler)
        except NotImplementedError:
            import signal as _signal

            _signal.signal(_signal.SIGTERM, lambda *_: _sigterm_handler())

        startup = StartupOrchestrator(self._ctx, self._view)
        self._cmds, self._orchestrator = await startup.run()
        await self._run_repl_loop()
