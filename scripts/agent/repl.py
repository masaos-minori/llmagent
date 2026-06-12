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
import sqlite3

from db.helper import SQLiteHelper
from shared.logger import Logger
from shared.tool_executor import StdioTransport

from agent.cli_view import CLIView
from agent.commands.registry import CommandRegistry
from agent.context import AgentContext
from agent.factory import build_agent_context, init_tracer
from agent.orchestrator import Orchestrator
from agent.repl_health import (
    check_service_health,
    check_tool_definitions_runtime,
    watchdog_loop,
)

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
            with SQLiteHelper("rag").open() as db:
                rows = db.fetchall("SELECT COUNT(*) FROM chunks")
            count = rows[0][0] if rows else 0
            return f"{count:,}"
        except (sqlite3.Error, OSError, RuntimeError) as e:
            logger.debug(f"Failed to get chunk count: {e}")
            return "?"

    # ── Health checks / watchdog — delegated to agent_repl_health ─────────────

    async def _check_service_health(self) -> None:
        for msg in await check_service_health(self._ctx):
            self._view.write_warning(msg)

    async def _check_tool_definitions(self) -> None:
        for msg in await check_tool_definitions_runtime(self._ctx):
            self._view.write_warning(msg)

    async def _watchdog_loop(self) -> None:
        await watchdog_loop(self._ctx)

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
            print()
            return None
        line = raw.strip()
        if line.endswith("\\"):
            line = await self._view.read_multiline(loop, line)
            line = line.strip()
        return line

    def _should_exit(self, line: str, ctx: AgentContext) -> bool:
        """Return True when the REPL loop should terminate."""
        if ctx.conv.shutdown_requested:
            print("\nShutdown requested, exiting...")
            return True
        if line == "/exit":
            return True
        return False

    async def _dispatch_line(self, line: str, ctx: AgentContext) -> None:
        """Dispatch a non-empty, non-exit line to commands or the orchestrator."""
        assert self._cmds is not None, "_dispatch_line called before _init_components()"
        assert self._orchestrator is not None, "_dispatch_line called before _init_components()"
        if line.startswith("/"):
            matched = await self._cmds.dispatch(line)
            if not matched:
                print(f"Unknown command: {line}  (type /help for commands)")
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
                        f"Failed to start HTTP subprocess MCP server {key!r}: {e}"
                    )
                    print(
                        f"[warn] HTTP subprocess MCP server {key!r} failed to start: {e}"
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
                logger.error(f"Failed to start stdio MCP server {key!r}: {e}")
                print(f"[warn] stdio MCP server {key!r} failed to start: {e}")

    def _print_startup_banner(self) -> None:
        """Print the startup line showing DB chunks and tool count."""
        chunk_count = self._get_chunk_count()
        self._view.write_startup_banner(chunk_count, self._n_tools)

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
        """Probe LLM / Embed service health and validate tool definitions."""
        # Probe LLM / Embed service health; warnings only, REPL continues on failure
        await self._check_service_health()

        # Validate tool definitions against live MCP servers (warns or raises)
        await self._check_tool_definitions()

    async def _setup_initial_prompt(self) -> None:
        """Setup initial system prompt with notes and memories."""
        ctx = self._ctx
        initial_prompt = ctx.cfg.tool.system_prompts.get(
            ctx.conv.system_prompt_name,
            ctx.cfg.tool.system_prompt_tool,
        )
        # Append persisted notes to system prompt when auto_inject_notes is enabled
        if ctx.cfg.tool.auto_inject_notes:
            note_texts = ctx.session.get_all_note_contents()
            if note_texts:
                notes_block = "\n\n[Notes]\n" + "\n".join(f"- {t}" for t in note_texts)
                initial_prompt = initial_prompt + notes_block
        # SessionStart: inject top semantic memories into system prompt
        if ctx.services.memory is not None:
            memory_snippets = ctx.services.memory.on_session_start(
                ctx.session.session_id,
            )
            if memory_snippets:
                memory_block = "\n\n[Relevant memories]\n" + "\n".join(
                    f"- {s}" for s in memory_snippets
                )
                initial_prompt = initial_prompt + memory_block
        ctx.conv.system_prompt_content = initial_prompt
        ctx.conv.history = [{"role": "system", "content": initial_prompt}]

    async def _run_repl_loop(self) -> None:
        """Run the main REPL loop with watchdog if enabled."""
        ctx = self._ctx
        _watchdog_task: asyncio.Task | None = None
        try:
            self._print_startup_banner()
            ctx.session.start()
            if ctx.services.tools is not None and ctx.session.session_id is not None:
                ctx.services.tools.set_session_id(str(ctx.session.session_id))
            if ctx.cfg.mcp.mcp_watchdog_interval > 0:
                _watchdog_task = asyncio.create_task(self._watchdog_loop())
            await self._repl_loop()
        finally:
            # Stop: extract and persist memories before compression or resource close
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
            if _watchdog_task is not None:
                _watchdog_task.cancel()
                try:
                    await _watchdog_task
                except asyncio.CancelledError:
                    pass
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
