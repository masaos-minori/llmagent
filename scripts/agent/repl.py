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
import sqlite3
import time
from pathlib import Path

from db.config import build_db_config
from db.helper import SQLiteHelper
from shared.logger import Logger
from shared.mcp_config import SecurityProfile
from shared.tool_executor import StdioTransport

from agent.cli_view import CLIView
from agent.commands.registry import CommandRegistry
from agent.context import AgentContext
from agent.factory import build_agent_context, init_tracer
from agent.orchestrator import Orchestrator
from agent.repl_health import (
    audit_security_defaults,
    check_readiness,
    check_tool_definitions_runtime,
    watchdog_loop,
)
from agent.services.db_maintenance_service import DbMaintenanceService

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
        "/ingest",
        "/debug",
        "/export",
        "/undo",
        "/history",
        "/system",
        "/db",
        "/set",
        "/reload",
        "/exit",
    ]

    def __init__(self) -> None:
        self._ctx = AgentContext()
        self._view = CLIView(AgentREPL.SLASH_COMMANDS)
        self._cmds: CommandRegistry | None = None
        self._orchestrator: Orchestrator | None = None

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
            count = DbMaintenanceService().stats().chunks
            return f"{count:,}"
        except (sqlite3.Error, OSError, RuntimeError) as e:
            logger.debug("Failed to get chunk count: %s", e)
            return "?"

    # ── Health checks / watchdog — delegated to agent_repl_health ─────────────

    async def _check_tool_definitions(self) -> None:
        result = await check_tool_definitions_runtime(self._ctx)
        for msg in result.warning_messages():
            self._view.write_warning(msg)

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
                "latency_summary": latency_summary,
                "tool_result_summary": tool_result_summary,
            }

            db_cfg = build_db_config()
            diag_path = Path(db_cfg.session_db_path).parent / "diagnostics.jsonl"
            with open(diag_path, "a") as f:
                f.write(json.dumps(summary) + "\n")

        except (OSError, sqlite3.Error):
            logger.debug("Failed to persist session diagnostics", exc_info=True)

    async def _close_resources(self) -> None:
        """Close all session resources. Called in the run() finally block."""
        self._view.write_history()
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
        while True:
            line = await self._read_input(loop)
            if line is None:
                break
            if not line:
                continue
            if self._should_exit(line, ctx):
                break
            await self._dispatch_line(line, ctx)

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
            await self._orchestrator.handle_turn(line)

    def _init_command_registry(self, ctx: AgentContext) -> None:
        """Instantiate CommandRegistry and assign to self._cmds."""
        self._cmds = CommandRegistry(ctx)

    def _init_orchestrator(self, ctx: AgentContext) -> None:
        """Instantiate Orchestrator and assign to self._orchestrator."""
        if self._cmds is None:
            raise RuntimeError("_init_orchestrator requires _cmds to be set first")
        tracer = init_tracer(ctx)
        self._orchestrator = Orchestrator(
            ctx,
            on_turn_start=self._view.write_turn_start,
            on_turn_end=self._view.write_turn_end,
            on_error=self._view.write_llm_error,
            on_first_turn=self._cmds._generate_session_title,
            tracer=tracer,
            workflow_mode=ctx.cfg.workflow_mode,
        )

    def _init_components(self) -> None:
        """Inject services via factory.build_agent_context(), then wire CommandRegistry and Orchestrator."""
        ctx = self._ctx
        build_agent_context(ctx, self._view)
        self._init_command_registry(ctx)
        self._init_orchestrator(ctx)

    async def _start_subprocess_servers(self) -> None:
        """Spawn subprocesses for persistent stdio and HTTP subprocess MCP servers.

        Handles:
        - stdio + startup_mode='persistent': start StdioTransport subprocess
        - http  + startup_mode='subprocess': start HTTP server subprocess, poll /health
        Ondemand servers are excluded; they start on first tool call via ensure_ready().
        """
        ctx = self._ctx
        if ctx.services.tools is None:
            raise RuntimeError("tools service not initialized")
        if ctx.services.lifecycle is None:
            raise RuntimeError("lifecycle service not initialized")
        for key, cfg in ctx.cfg.mcp.mcp_servers.items():
            if cfg.startup_mode == "subprocess" and cfg.transport == "http":
                try:
                    await ctx.services.lifecycle.start_http_subprocess(key, cfg)
                except (OSError, RuntimeError) as e:
                    logger.error(
                        "Failed to start HTTP subprocess MCP server %r: %s",
                        key,
                        e,
                    )
                    self._view.write_warning(
                        f"HTTP subprocess MCP server {key!r} failed to start: {e}"
                    )
                continue
            # ondemand and non-stdio servers are excluded: they start on first tool call
            if (
                cfg.transport != "stdio"
                or not cfg.cmd
                or cfg.startup_mode != "persistent"
            ):
                continue
            transport = StdioTransport(
                cfg.cmd,
                server_key=key,
                working_dir=cfg.working_dir,
                env=cfg.env or None,
            )
            try:
                await transport.start()
                ctx.services.tools.set_transport(key, transport)
                ctx.services.stdio_procs[key] = transport
            except (OSError, RuntimeError) as e:
                logger.error("Failed to start stdio MCP server %r: %s", key, e)
                self._view.write_warning(
                    f"stdio MCP server {key!r} failed to start: {e}"
                )

    def _get_workflow_status(self) -> str:
        """Return a human-readable workflow status string for the startup banner."""
        if self._orchestrator is None:
            return "unknown"
        mode = self._orchestrator._workflow_mode
        if mode == "disabled":
            return "disabled"
        if self._orchestrator._workflow_def is not None:
            return f"{mode} (tracking enabled)"
        return f"{mode} (definition not loaded)"

    def _print_startup_banner(self) -> None:
        """Print the startup line showing DB chunks, tool count, and workflow status."""
        chunk_count = self._get_chunk_count()
        workflow_status = self._get_workflow_status()
        self._view.write_startup_banner(chunk_count, self._n_tools, workflow_status)

    async def _initialize_session(self) -> None:
        """Initialize session and setup components."""
        ctx = self._ctx
        self._view.setup_readline()
        self._init_components()
        ctx.conv.llm_url = ctx.cfg.llm.llm_url

    async def _start_mcp_servers(self) -> None:
        """Spawn stdio/HTTP subprocess MCP servers before health/tool checks."""
        await self._start_subprocess_servers()

    async def _check_services(self) -> None:
        """Probe LLM / Embed service health, validate tool definitions, and audit security defaults."""
        # Audit security-related configuration defaults (warns on risky settings; raises in production mode)
        production_mode = (
            self._ctx.cfg.mcp.security_profile == SecurityProfile.PRODUCTION
        )
        audit_security_defaults(self._ctx, production_mode=production_mode)

        # Readiness check: raises in production mode if critical services are down
        result = await check_readiness(self._ctx, production_mode=production_mode)
        for msg in result.warning_messages():
            self._view.write_warning(msg)

        # Validate tool definitions against live MCP servers (warns or raises)
        await self._check_tool_definitions()

    async def _setup_initial_prompt(self) -> None:
        """Setup initial system prompt with notes and memories."""
        ctx = self._ctx
        initial_prompt = ctx.cfg.tool.system_prompts.get(
            ctx.conv.system_prompt_name,
            ctx.cfg.tool.system_prompt_tool,
        )
        # Inject pinned notes into system prompt at session start
        if ctx.cfg.tool.auto_inject_notes:
            pinned_notes = ctx.session.get_pinned_notes()
            if pinned_notes:
                notes_block = "\n\n[Pinned Notes]\n" + "\n".join(
                    f"- {n['content']}" for n in pinned_notes
                )
                initial_prompt = initial_prompt + notes_block
        # SessionStart: inject top semantic memories into system prompt
        if ctx.services.memory is not None:
            memory_snippets = ctx.services.memory.on_session_start(
                ctx.session.session_id,
            )
            if memory_snippets:
                memory_block = "\n\n[Relevant memories]\n" + "\n".join(
                    f"- {snippet.text}" for snippet in memory_snippets
                )
                initial_prompt = initial_prompt + memory_block
        ctx.conv.system_prompt_content = initial_prompt
        ctx.conv.history = [{"role": "system", "content": initial_prompt}]

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

        Initialises all components via AgentContext, creates a session record,
        processes user messages with RAG augmentation, and preserves conversation
        and readline history for the session.
        """
        await self._initialize_session()
        await self._start_mcp_servers()
        await self._check_services()
        await self._setup_initial_prompt()
        await self._run_repl_loop()
