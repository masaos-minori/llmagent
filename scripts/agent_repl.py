#!/usr/bin/env python3
"""
AgentREPL
Interactive REPL agent with RAG augmentation and MCP tool calling.
Imported by agent.py as the entry point.
Slash-command handlers live in agent_commands.CommandRegistry.

Architecture (dependency injection via AgentContext):
  AgentContext   — shared mutable state container (agent_context.py)
  CLIView        — readline, multiline input, RAG progress display (cli_view.py)
  LLMClient      — HTTP retry, payload build, SSE stream (llm_client.py)
  RagPipeline    — MQE → search → RRF → rerank orchestration (agent_rag.py)
  ToolExecutor   — MCP routing, error handling, TTL cache (tool_executor.py)
  HistoryManager — character counting, LLM-based compression (history_manager.py)
  CommandRegistry — slash-command dispatch (agent_commands.py)
  AgentConfig    — mutable runtime config dataclass (agent_config.py)

AgentREPL responsibilities:
  _run_turn            — SSE streaming → tool loop → final answer
  _handle_user_message — RAG augment → history append → LLM turn
  _repl_loop           — main input/dispatch loop
"""

import asyncio
import time
from pathlib import Path

import httpx
import plugin_registry
from agent_commands import CommandRegistry, _budget_breakdown
from agent_config import BUDGET_WARN_RATIO
from agent_context import AgentContext
from agent_rag import RagPipeline
from agent_repl_debug import (
    _extract_history_context,
    _make_debug_fn,
    _needs_more_context,
)
from agent_repl_health import (
    check_service_health,
    check_tool_definitions,
    watchdog_loop,
)
from agent_repl_tool_exec import execute_all_tool_calls
from cli_view import CLIView
from history_manager import HistoryManager
from llm_client import LLMClient
from logger import Logger
from rag_llm import get_embedding
from rag_repository import fetch_full_document
from sqlite_helper import SQLiteHelper
from tool_executor import StdioTransport, ToolExecutor

# Default LLM generation parameters (documentation only; actual values from agent.json)
_LLM_TEMPERATURE: float = 0.2
_LLM_MAX_TOKENS: int = 1024

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

    # ── Tool execution — delegated to agent_repl_tool_exec ────────────────────

    async def _execute_all_tool_calls(self, tool_calls: list[dict], turn: int) -> None:
        await execute_all_tool_calls(self._ctx, tool_calls, turn)

    # ── LLM interaction ────────────────────────────────────────────────────────

    async def _fetch_two_stage_context(self) -> str:
        """Fetch full document context for the top reranked hits (second stage).

        Opens its own DB connection, expands up to two_stage_max_docs unique
        documents by calling fetch_full_document(), and returns a formatted
        context block to inject before the second LLM call.
        """
        ctx = self._ctx
        hits = ctx.services.rag.last_reranked if ctx.services.rag is not None else []
        if not hits:
            return ""
        max_docs = ctx.cfg.two_stage_max_docs
        try:
            db = SQLiteHelper().open(row_factory=True)
        except Exception as e:
            logger.warning(f"Two-stage fetch DB open failed: {e}")
            return ""
        blocks: list[str] = []
        seen_urls: set[str] = set()
        with db:
            for hit in hits:
                if len(seen_urls) >= max_docs:
                    break
                url = hit.get("url", "")
                if url in seen_urls:
                    continue
                seen_urls.add(url)
                chunk_id = hit.get("chunk_id")
                if chunk_id is None:
                    continue
                # Expand ±2 surrounding chunks for focused context
                full_hits = fetch_full_document(chunk_id, db, window=2)
                if full_hits:
                    content = "\n".join(h["content"] for h in full_hits)
                    blocks.append(f"[Source: {url}]\n{content}")
        result = "\n\n---\n\n".join(blocks)
        logger.info(f"Two-stage fetch: {len(blocks)} docs, {len(result)} chars")
        return result

    async def _maybe_two_stage_fetch(self, answer: str) -> str | None:
        """Inject full-document context when the LLM signals it needs more.

        Returns the extra context string when two-stage fetch is triggered,
        or None when conditions are not met (feature disabled, no hits, or the
        LLM did not request additional context).
        Called at most once per _run_turn() invocation.
        """
        ctx = self._ctx
        if not (
            ctx.cfg.use_two_stage_fetch
            and ctx.services.rag is not None
            and ctx.services.rag.last_reranked
            and _needs_more_context(answer)
        ):
            return None
        extra = await self._fetch_two_stage_context()
        if not extra:
            return None
        logger.info("Two-stage fetch: injecting full doc context")
        return extra

    async def _run_turn(self, llm_url: str) -> str:
        """Send ctx.history to LLM; execute any tool calls; return final answer.

        All turns use SSE streaming so tokens print as they arrive,
        including follow-up turns after tool execution.
        Appends all assistant and tool messages to ctx.history.
        When use_two_stage_fetch is enabled, detects LLM requests for more
        context and injects full document snippets before a second call.
        """
        ctx = self._ctx
        assert ctx.services.llm is not None
        tool_defs = ctx.cfg.tool_definitions
        # Guard: two-stage fetch runs at most once per turn
        two_stage_done = False

        for turn in range(ctx.cfg.max_tool_turns):
            print()
            # Warn when total input chars exceed BUDGET_WARN_RATIO of context_char_limit
            if turn == 0 and ctx.cfg.context_char_limit > 0:
                bd = _budget_breakdown(ctx.history)
                total_bd = sum(bd.values())
                if total_bd > ctx.cfg.context_char_limit * BUDGET_WARN_RATIO:
                    pct = int(total_bd * 100 / ctx.cfg.context_char_limit)
                    logger.warning(
                        f"Context budget {pct}% used"
                        f" (total={total_bd:,}"
                        f" limit={ctx.cfg.context_char_limit:,})"
                        f" sys={bd['system']:,} rag={bd['rag']:,}"
                        f" hist={bd['history']:,}"
                        f" tool={bd['tool_results']:,}"
                    )
            t0_llm = time.perf_counter()
            response = await ctx.services.llm.stream(llm_url, ctx.history, tool_defs)
            # Record LLM wall-clock time for the first (main) generation turn only
            if turn == 0:
                ctx.stat_latency.setdefault("llm", []).append(
                    time.perf_counter() - t0_llm
                )

            message, finish_reason = LLMClient.extract_message(response)

            has_tool_calls = bool(message.get("tool_calls"))
            is_done = (finish_reason != "tool_calls") or not has_tool_calls
            if is_done:
                ctx.history.append(message)
                print()
                answer = message.get("content") or ""
                # Two-stage: expand full document context when LLM signals need
                if not two_stage_done:
                    extra = await self._maybe_two_stage_fetch(answer)
                    if extra is not None:
                        two_stage_done = True
                        ctx.history.append(
                            {
                                "role": "user",
                                "content": (
                                    "[Additional context]\n"
                                    + extra
                                    + "\n\n(Please revise your answer using"
                                    " the above additional context.)"
                                ),
                            }
                        )
                        continue
                return answer

            ctx.history.append(message)
            await self._execute_all_tool_calls(message["tool_calls"], turn)

        logger.warning(f"Reached max_tool_turns={ctx.cfg.max_tool_turns}")
        return "Maximum tool turns reached."

    # ── Main REPL loop ─────────────────────────────────────────────────────────

    async def _augment_with_rag(self, line: str) -> tuple[str, bool]:
        """Run the RAG pipeline (or semantic cache) and return (context, cache_hit).

        Returns an empty string for context when use_search is False or when
        no relevant chunks are found.
        """
        ctx = self._ctx
        if not ctx.cfg.use_search or ctx.services.rag is None:
            return "", False

        history_context = _extract_history_context(ctx.history, n=2)
        debug_fn = _make_debug_fn() if ctx.debug_mode else None

        # Try semantic cache before running the full RAG pipeline
        _cached_emb: list[float] | None = None
        if ctx.cfg.use_semantic_cache and ctx.services.http is not None:
            try:
                _cached_emb = await get_embedding("query: " + line, ctx.services.http)
                _cached_ctx = ctx.services.rag.semantic_cache.lookup(_cached_emb)
                if _cached_ctx is not None:
                    ctx.stat_semantic_cache_hits += 1
                    logger.info("Semantic cache hit; skipping RAG pipeline")
                    return _cached_ctx, True
            except Exception as _e:
                logger.warning(f"Semantic cache lookup failed: {_e}")
                _cached_emb = None

        context = await ctx.services.rag.augment(
            line, debug_fn, history_context=history_context
        )
        # Store result in semantic cache for future reuse
        if ctx.cfg.use_semantic_cache and context and ctx.services.http is not None:
            try:
                emb_for_store = _cached_emb or await get_embedding(
                    "query: " + line, ctx.services.http
                )
                ctx.services.rag.semantic_cache.put(emb_for_store, context)
            except Exception as _e:
                logger.warning(f"Semantic cache put failed: {_e}")

        return context, False

    async def _handle_user_message(self, line: str) -> None:
        """Augment a user message with RAG context, call LLM, and persist to DB.

        Compresses conversation history before the LLM call when total chars
        exceed CONTEXT_CHAR_LIMIT.
        """
        ctx = self._ctx
        assert self._cmds is not None
        assert ctx.services.hist_mgr is not None

        context, cache_hit = await self._augment_with_rag(line)

        if context:
            ctx.stat_rag_hits += 1
            augmented = f"[Reference documents]\n{context}\n\nQuestion: {line}"
            # Accumulate per-step RAG latency samples (only on real pipeline runs)
            if ctx.services.rag is not None and not cache_hit:
                for step, secs in ctx.services.rag.last_timings.items():
                    ctx.stat_latency.setdefault(step, []).append(secs)
        else:
            augmented = line
        ctx.history.append({"role": "user", "content": augmented})
        ctx.stat_turns += 1

        # Generate session title asynchronously from the first user input
        if ctx.stat_turns == 1:
            asyncio.create_task(self._cmds._generate_session_title(line))
        ctx.session.save("user", augmented)

        # Compress history before sending to LLM when it exceeds the char limit
        ctx.history = await ctx.services.hist_mgr.compress(ctx.history)

        try:
            answer = await self._run_turn(ctx.llm_url)
            logger.info(f"LLM response: {answer}")
            ctx.session.save("assistant", answer)
        except Exception as e:
            logger.error(f"LLM request failed: {e}")
            print(f"\nError: {e}\n")
            # Remove failed user message to keep history consistent
            if ctx.history and ctx.history[-1]["role"] == "user":
                ctx.history.pop()

    async def _repl_loop(self) -> None:
        """Process user input lines until /exit, EOF, or shutdown request."""
        ctx = self._ctx
        assert self._cmds is not None
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
                await self._handle_user_message(line)

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
