#!/usr/bin/env python3
"""
AgentREPL
Interactive REPL agent with RAG augmentation and MCP tool calling.
Imported by agent.py as the entry point.
Slash-command handlers live in agent/commands/registry.CommandRegistry.
Turn-level orchestration (RAG, LLM loop, tool dispatch) lives in agent/orchestrator.py.

Architecture (dependency injection via AgentContext):
  AgentContext   — shared mutable state container (agent/context.py)
  CLIView        — readline, multiline input, RAG progress display (agent/cli_view.py)
  LLMClient      — HTTP retry, payload build, SSE stream (shared/llm_client.py)
  RagPipeline    — MQE -> search -> RRF -> rerank orchestration (rag/pipeline.py)
  ToolExecutor   — MCP routing, error handling, TTL cache (shared/tool_executor.py)
  HistoryManager — character counting, LLM-based compression (agent/history.py)
  CommandRegistry — slash-command dispatch (agent/commands/registry.py)
  Orchestrator   — per-turn task control: RAG, LLM loop, tool dispatch (agent/orchestrator.py)
  AgentConfig    — mutable runtime config dataclass (agent/config.py)

AgentREPL responsibilities:
  _repl_loop           — main input/dispatch loop
  _init_components     — DI wiring
  run                  — startup sequence
"""

import asyncio
from pathlib import Path
from typing import Any

import httpx
import shared.plugin_registry as plugin_registry
from rag.pipeline import RagPipeline
from shared.llm_client import LLMClient
from shared.logger import Logger
from shared.otel_tracer import build_tracer
from shared.tool_executor import StdioTransport, ToolExecutor

from agent.cli_view import CLIView
from agent.commands.registry import CommandRegistry
from agent.context import AgentContext
from agent.history import HistoryManager
from agent.lifecycle import ServerLifecycleManager
from agent.orchestrator import Orchestrator
from agent.repl_health import (
    check_service_health,
    check_tool_definitions,
    watchdog_loop,
)
from db.helper import SQLiteHelper

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
    def _prompt(self) -> str:
        """Dynamic REPL prompt showing current session ID."""
        sid = self._ctx.session.session_id
        sid_str = f":#{sid}" if sid is not None else ""
        return f"agent[{sid_str}]> " if sid_str else "agent> "

    @property
    def _n_tools(self) -> int:
        """Number of tools available (from config/agent.toml tool_definitions)."""
        return len(self._ctx.cfg.tool_definitions)

    def _get_chunk_count(self) -> str:
        """Return formatted chunk count from DB, or '?' on error."""
        try:
            with SQLiteHelper("rag").open() as db:
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
        # Delegate stdio server shutdown to ServerLifecycleManager when available.
        # Falls back to a no-op when lifecycle was never initialised (e.g. init failed).
        if self._ctx.services.lifecycle is not None:
            await self._ctx.services.lifecycle.shutdown_all()
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

    def _init_audit_logger(self, ctx: AgentContext) -> None:
        """Initialize audit logger."""
        # Audit logger writes JSON-lines turn events; structured_log=True forces JSON format
        ctx.services.audit_logger = Logger(
            "audit", ctx.cfg.audit_log_file, structured_log=True
        )

    def _init_llm_client(self, ctx: AgentContext) -> None:
        """Initialize LLM client."""

        def _on_llm_usage(prompt_tokens: int, completion_tokens: int) -> None:
            ctx.stat_input_tokens = (ctx.stat_input_tokens or 0) + prompt_tokens
            ctx.stat_output_tokens = (ctx.stat_output_tokens or 0) + completion_tokens

        ctx.services.http = httpx.AsyncClient(timeout=ctx.cfg.http_timeout)
        ctx.services.llm = LLMClient(
            ctx.services.http,
            max_retries=ctx.cfg.llm_max_retries,
            retry_base_delay=ctx.cfg.llm_retry_base_delay,
            temperature=ctx.cfg.llm_temperature,
            max_tokens=ctx.cfg.llm_max_tokens,
            on_token=self._view.write_token,
            on_usage=_on_llm_usage,
            sse_heartbeat_timeout=ctx.cfg.sse_heartbeat_timeout,
            sse_malformed_retry=ctx.cfg.sse_malformed_retry,
            sse_reconnect_max=ctx.cfg.sse_reconnect_max,
            llm_stream_retry_on_heartbeat_timeout=ctx.cfg.llm_stream_retry_on_heartbeat_timeout,
            llm_stream_retry_on_malformed_chunk=ctx.cfg.llm_stream_retry_on_malformed_chunk,
        )

    def _init_tool_executor(self, ctx: AgentContext) -> None:
        """Initialize tool executor."""
        assert ctx.services.http is not None
        ctx.services.tools = ToolExecutor(
            ctx.services.http,
            cache_ttl=ctx.cfg.tool_cache_ttl,
            server_configs=ctx.cfg.mcp_servers,
            cache_max_size=ctx.cfg.tool_cache_max_size,
            concurrency_limits=ctx.cfg.tool_concurrency_limits,
        )
        lifecycle = ServerLifecycleManager(
            ctx.cfg.mcp_servers,
            ctx.services.tools,
            ctx.services.stdio_procs,
        )
        ctx.services.lifecycle = lifecycle
        ctx.services.tools.set_lifecycle(lifecycle)

    def _init_history_manager(self, ctx: AgentContext) -> None:
        """Initialize history manager."""
        assert ctx.services.http is not None
        ctx.services.hist_mgr = HistoryManager(
            ctx.services.http,
            llm_url=ctx.cfg.llm_url,
            char_limit=ctx.cfg.context_char_limit,
            compress_turns=ctx.cfg.context_compress_turns,
            compress_temperature=_COMPRESS_TEMPERATURE,
            compress_max_tokens=_COMPRESS_MAX_TOKENS,
            on_compress=self._view.write_compress_notice,
            protect_turns=ctx.cfg.history_protect_turns,
            token_limit=ctx.cfg.context_token_limit,
        )

    def _init_rag_pipeline(self, ctx: AgentContext) -> None:
        """Initialize RAG pipeline."""
        assert ctx.services.http is not None
        ctx.services.rag = RagPipeline(
            ctx.services.http,
            ctx.cfg,
            on_status=self._view.rag_status,
            on_clear=self._view.rag_clear,
        )

    def _init_memory_layer(self, ctx: AgentContext) -> None:
        """Initialize memory layer."""
        # Inject MemoryLayer when use_memory_layer=True; otherwise leave ctx.services.memory=None
        if ctx.cfg.use_memory_layer:
            from agent.memory.jsonl_store import JsonlMemoryStore  # noqa: PLC0415
            from agent.memory.layer import MemoryLayer  # noqa: PLC0415
            from agent.memory.retriever import MemoryRetriever  # noqa: PLC0415
            from agent.memory.store import MemoryStore  # noqa: PLC0415

            ctx.services.memory = MemoryLayer(
                store=MemoryStore(),
                retriever=MemoryRetriever(),
                jsonl=JsonlMemoryStore(ctx.cfg.memory_jsonl_dir + "/memories.jsonl"),
                max_inject_semantic=ctx.cfg.memory_max_inject_semantic,
                max_inject_episodic=ctx.cfg.memory_max_inject_episodic,
                min_importance=ctx.cfg.memory_min_importance,
                http=ctx.services.http,
                embed_url=ctx.cfg.embed_url,
                embed_enabled=ctx.cfg.memory_embed_enabled,
                dedup_threshold=ctx.cfg.memory_dedup_threshold,
                embed_timeout=ctx.cfg.memory_embed_timeout_sec,
                max_content_chars=ctx.cfg.memory_max_content_chars,
            )
            logger.info("MemoryLayer initialised (use_memory_layer=True)")

    def _init_command_registry(self, ctx: AgentContext) -> None:
        """Initialize command registry."""
        self._cmds = CommandRegistry(ctx)

    def _init_tracer(self, ctx: AgentContext) -> Any:
        """Initialize OTel tracer."""
        # Build OTel tracer (or NoOp stand-in when otel_enabled=False)
        return build_tracer(
            enabled=ctx.cfg.otel_enabled,
            service_name=ctx.cfg.otel_service_name,
            otlp_endpoint=ctx.cfg.otel_endpoint,
        )

    def _init_orchestrator(self, ctx: AgentContext) -> None:
        """Initialize orchestrator."""
        assert self._cmds is not None
        tracer = self._init_tracer(ctx)
        self._orchestrator = Orchestrator(
            ctx,
            self._cmds,
            on_turn_start=self._view.write_turn_start,
            on_turn_end=self._view.write_turn_end,
            on_error=self._view.write_llm_error,
            tracer=tracer,
        )

    def _init_plugin_registry(self) -> None:
        """Initialize plugin registry."""
        # Load plugin files from plugins/ directory adjacent to scripts/
        plugin_dir = Path(__file__).parent.parent.parent / "plugins"
        n_plugins = plugin_registry.load_plugins(plugin_dir)
        if n_plugins:
            logger.info(f"Loaded {n_plugins} plugin(s) from {plugin_dir}")

    def _init_components(self) -> None:
        """Instantiate and inject all components into AgentContext."""
        ctx = self._ctx
        self._init_audit_logger(ctx)
        self._init_llm_client(ctx)
        self._init_tool_executor(ctx)
        self._init_history_manager(ctx)
        self._init_rag_pipeline(ctx)
        self._init_memory_layer(ctx)
        self._init_command_registry(ctx)
        self._init_orchestrator(ctx)
        self._init_plugin_registry()

    async def _start_stdio_servers(self) -> None:
        """Spawn subprocesses for persistent stdio MCP servers at agent startup.

        Ondemand servers (startup_mode='ondemand') are excluded here; they are
        started on first use by ServerLifecycleManager.ensure_ready().
        """
        ctx = self._ctx
        assert ctx.services.tools is not None
        for key, cfg in ctx.cfg.mcp_servers.items():
            if cfg.transport != "stdio" or not cfg.cmd:
                continue
            if cfg.startup_mode != "persistent":
                continue  # ondemand servers start on first tool call
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
            except Exception as e:
                logger.error(f"Failed to start stdio MCP server {key!r}: {e}")
                print(f"[warn] stdio MCP server {key!r} failed to start: {e}")

    def _print_startup_banner(self) -> None:
        """Print the startup line showing DB chunks and tool count."""
        ctx = self._ctx
        chunk_count = self._get_chunk_count() if ctx.cfg.use_search else "disabled"
        print(f"DB: {chunk_count} chunks | Tools: {self._n_tools}")
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

        ctx.llm_url = ctx.cfg.llm_url

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
            # SessionStart: inject top semantic memories into system prompt
            if ctx.services.memory is not None:
                memory_snippets = ctx.services.memory.on_session_start(
                    ctx.session.session_id
                )
                if memory_snippets:
                    memory_block = "\n\n[Relevant memories]\n" + "\n".join(
                        f"- {s}" for s in memory_snippets
                    )
                    initial_prompt = initial_prompt + memory_block
            ctx.history = [{"role": "system", "content": initial_prompt}]
            if ctx.cfg.mcp_watchdog_interval > 0:
                _watchdog_task = asyncio.create_task(self._watchdog_loop())
            await self._repl_loop()
        finally:
            # Stop: extract and persist memories before compression or resource close
            if ctx.services.memory is not None:
                await ctx.services.memory.on_session_stop(
                    session_id=ctx.session.session_id,
                    history=ctx.history,
                    turn_id=ctx.current_turn_id,
                )
            if _watchdog_task is not None:
                _watchdog_task.cancel()
                try:
                    await _watchdog_task
                except asyncio.CancelledError:
                    pass
            await self._close_resources()
