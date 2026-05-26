#!/usr/bin/env python3
"""
AgentREPL
Interactive REPL agent with RAG augmentation and MCP tool calling.
Imported by agent.py as the entry point.
Slash-command handlers live in agent_commands.CommandRegistry.
Turn-level orchestration (RAG, LLM loop, tool dispatch) lives in orchestrator.py.

Architecture (dependency injection via AgentContext):
  AgentContext   — shared mutable state container (agent_context.py)
  CLIView        — readline, multiline input, RAG progress display (cli_view.py)
  LLMClient      — HTTP retry, payload build, SSE stream (llm_client.py)
  RagPipeline    — MQE -> search -> RRF -> rerank orchestration (agent_rag.py)
  ToolExecutor   — MCP routing, error handling, TTL cache (tool_executor.py)
  HistoryManager — character counting, LLM-based compression (history_manager.py)
  CommandRegistry — slash-command dispatch (agent_commands.py)
  Orchestrator   — per-turn task control: RAG, LLM loop, tool dispatch (orchestrator.py)
  AgentConfig    — mutable runtime config dataclass (agent_config.py)

AgentREPL responsibilities:
  _repl_loop           — main input/dispatch loop
  _init_components     — DI wiring
  run                  — startup sequence
"""

import asyncio
from pathlib import Path

import httpx
import plugin_registry
from agent_commands import CommandRegistry
from agent_context import AgentContext
from agent_rag import RagPipeline
from agent_repl_health import (
    check_service_health,
    check_tool_definitions,
    watchdog_loop,
)
from cli_view import CLIView
from history_manager import HistoryManager
from llm_client import LLMClient
from logger import Logger
from orchestrator import Orchestrator
from sqlite_helper import SQLiteHelper
from tool_executor import StdioTransport, ToolExecutor

# LLM parameters for context compression summary.
_COMPRESS_TEMPERATURE: float = 0.3
_COMPRESS_MAX_TOKENS: int = 300

logger = Logger(__name__, "/opt/llm/logs/agent.log")


# ─────────────────────────────────────────────────────────────────────────────
# REPLAgent: thin coordinator over AgentContext components
# ─────────────────────────────────────────────────────────────────────────────


class AgentREPL:
    """Interactive REPL agent.

    Coordinates LLMClient, ToolExecutor, HistoryManager, RagPipeline,
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
        "/rag",
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
    def _mode(self) -> str:
        """Current LLM mode label: 'code' or 'chat'."""
        return "code" if self._ctx.llm_url == self._ctx.cfg.code_url else "chat"

    @property
    def _prompt(self) -> str:
        """Dynamic REPL prompt showing the active mode."""
        return f"agent[{self._mode}]> "

    @property
    def _n_tools(self) -> int:
        """Number of tools available (from config/agent.json tool_definitions)."""
        return len(self._ctx.cfg.tool_definitions)

    def _get_chunk_count(self) -> str:
        """Return formatted chunk count from DB, or '?' on error."""
        try:
            with SQLiteHelper().open() as db:
                rows = db.fetchall("SELECT COUNT(*) FROM chunks")
            count = rows[0][0] if rows else 0
            return f"{count:,}"
        except Exception as e:
            logger.debug(f"Failed to get chunk count: {e}")
            return "?"

    # ── Health checks / watchdog — delegated to agent_repl_health ─────────────

    async def _check_service_health(self) -> None:
        await check_service_health(self._ctx)

    async def _check_tool_definitions(self) -> None:
        await check_tool_definitions(self._ctx)

    async def _watchdog_loop(self) -> None:
        await watchdog_loop(self._ctx)

    async def _close_resources(self) -> None:
        """Close all session resources. Called in the run() finally block."""
        self._view.write_history()
        # Stop all stdio MCP server subprocesses before closing the HTTP client.
        for key, transport in self._ctx.services.stdio_procs.items():
            try:
                await transport.stop()
            except Exception as e:
                logger.warning(f"Error stopping stdio server {key!r}: {e}")
        if self._ctx.services.http is not None:
            await self._ctx.services.http.aclose()

    # ── Main REPL loop ─────────────────────────────────────────────────────────

    async def _repl_loop(self) -> None:
        """Process user input lines until /exit, EOF, or shutdown request."""
        ctx = self._ctx
        assert self._cmds is not None
        assert self._orchestrator is not None
        loop = asyncio.get_running_loop()
        while True:
            try:
                line = await loop.run_in_executor(None, lambda: input(self._prompt))
            except (EOFError, KeyboardInterrupt):
                print()
                break

            # Exit cleanly when a graceful shutdown was requested via signal
            if ctx.shutdown_requested:
                print("\nShutdown requested, exiting...")
                break

            line = line.strip()
            if not line:
                continue
            # Multiline: trailing backslash continues input on the next line
            if line.endswith("\\"):
                line = await self._view.read_multiline(loop, line)
                if not line.strip():
                    continue
            if line == "/exit":
                break
            if line.startswith("/"):
                matched = await self._cmds.dispatch(line)
                if not matched:
                    print(f"Unknown command: {line}  (type /help for commands)")
            else:
                await self._orchestrator.handle_turn(line)

    def _init_components(self) -> None:
        """Instantiate and inject all components into AgentContext."""
        ctx = self._ctx
        ctx.services.http = httpx.AsyncClient(timeout=ctx.cfg.http_timeout)
        ctx.services.llm = LLMClient(
            ctx.services.http,
            max_retries=ctx.cfg.llm_max_retries,
            retry_base_delay=ctx.cfg.llm_retry_base_delay,
            temperature=ctx.cfg.llm_temperature,
            max_tokens=ctx.cfg.llm_max_tokens,
            on_token=self._view.write_token,
        )
        ctx.services.tools = ToolExecutor(
            ctx.services.http,
            cache_ttl=ctx.cfg.tool_cache_ttl,
            server_configs=ctx.cfg.mcp_servers,
        )
        ctx.services.hist_mgr = HistoryManager(
            ctx.services.http,
            chat_url=ctx.cfg.chat_url,
            char_limit=ctx.cfg.context_char_limit,
            compress_turns=ctx.cfg.context_compress_turns,
            compress_temperature=_COMPRESS_TEMPERATURE,
            compress_max_tokens=_COMPRESS_MAX_TOKENS,
            on_compress=self._view.write_compress_notice,
        )
        ctx.services.rag = RagPipeline(
            ctx.services.http,
            ctx.cfg,
            on_status=self._view.rag_status,
            on_clear=self._view.rag_clear,
        )
        self._cmds = CommandRegistry(ctx)
        self._orchestrator = Orchestrator(
            ctx,
            self._cmds,
            on_turn_start=self._view.write_turn_start,
            on_turn_end=self._view.write_turn_end,
            on_error=self._view.write_llm_error,
        )

        # Load plugin files from plugins/ directory adjacent to scripts/
        plugin_dir = Path(__file__).parent.parent / "plugins"
        n_plugins = plugin_registry.load_plugins(plugin_dir)
        if n_plugins:
            logger.info(f"Loaded {n_plugins} plugin(s) from {plugin_dir}")

    async def _start_stdio_servers(self) -> None:
        """Spawn subprocess for each MCP server configured with transport='stdio'.

        Creates a StdioTransport, starts the process, registers it in ctx.services.tools
        and ctx.services.stdio_procs so the watchdog can monitor it.
        """
        ctx = self._ctx
        assert ctx.services.tools is not None
        for key, cfg in ctx.cfg.mcp_servers.items():
            if cfg.transport != "stdio" or not cfg.cmd:
                continue
            transport = StdioTransport(cfg.cmd, server_key=key)
            try:
                await transport.start()
                ctx.services.tools.set_transport(key, transport)
                ctx.services.stdio_procs[key] = transport
            except Exception as e:
                logger.error(f"Failed to start stdio MCP server {key!r}: {e}")
                print(f"[warn] stdio MCP server {key!r} failed to start: {e}")

    def _print_startup_banner(self) -> None:
        """Print the startup line showing DB chunks, tool count and LLM mode."""
        ctx = self._ctx
        chunk_count = self._get_chunk_count() if ctx.cfg.use_search else "disabled"
        print(f"DB: {chunk_count} chunks | Tools: {self._n_tools} | Mode: {self._mode}")
        print("Type /help for commands, /exit to quit.")

    async def run(self) -> None:
        """Start the interactive REPL.

        Initialises all components via AgentContext, creates a session record,
        processes user messages with RAG augmentation, and preserves conversation
        and readline history for the session.
        """
        ctx = self._ctx
        self._view.setup_readline()
        self._init_components()

        # Initialise LLM URL before accessing _mode / _prompt
        ctx.llm_url = (
            ctx.cfg.code_url if ctx.cfg.default_mode == "code" else ctx.cfg.chat_url
        )

        # Spawn stdio MCP server subprocesses before health/tool checks
        await self._start_stdio_servers()

        # Probe LLM / Embed service health; warnings only, REPL continues on failure
        await self._check_service_health()

        # Validate tool definitions against live MCP servers (warns or raises)
        await self._check_tool_definitions()

        _watchdog_task: asyncio.Task | None = None
        try:
            self._print_startup_banner()
            ctx.session.start()
            initial_prompt = ctx.cfg.system_prompts.get(
                ctx.system_prompt_name, ctx.cfg.system_prompt_tool
            )
            # Append persisted notes to system prompt when auto_inject_notes is enabled
            if ctx.cfg.auto_inject_notes:
                note_texts = ctx.session.get_all_note_contents()
                if note_texts:
                    notes_block = "\n\n[Notes]\n" + "\n".join(
                        f"- {t}" for t in note_texts
                    )
                    initial_prompt = initial_prompt + notes_block
            ctx.history = [{"role": "system", "content": initial_prompt}]
            if ctx.cfg.mcp_watchdog_interval > 0:
                _watchdog_task = asyncio.create_task(self._watchdog_loop())
            await self._repl_loop()
        finally:
            if _watchdog_task is not None:
                _watchdog_task.cancel()
                try:
                    await _watchdog_task
                except asyncio.CancelledError:
                    pass
            await self._close_resources()
