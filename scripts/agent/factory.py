"""agent/factory.py
AgentContext assembly factory.
Service injection into ctx.services is separated from AgentREPL to enable testing.
CommandRegistry and Orchestrator remain on AgentREPL because they reference
REPL instance state directly.
"""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import TYPE_CHECKING

import httpx
from shared import plugin_registry
from shared.llm_client import LLMClient
from shared.logger import Logger
from shared.mcp_config import McpServerConfig
from shared.otel_tracer import build_tracer
from shared.tool_executor import StdioTransport, ToolExecutor

from agent.cli_view import CLIView
from agent.context import AgentContext, AppServices
from agent.history import HistoryManager
from agent.http_lifecycle import HttpServerLifecycleManager
from agent.lifecycle import LifecycleState
from agent.lifecycle_protocol import LifecycleManagerProtocol
from agent.stdio_lifecycle import StdioServerLifecycleManager

if TYPE_CHECKING:
    from agent.memory.services import MemoryServices

# LLM parameters used by HistoryManager for conversation compression
_COMPRESS_TEMPERATURE: float = 0.3
_COMPRESS_MAX_TOKENS: int = 300

_logger = logging.getLogger(__name__)


class _ServerLifecycleRouter:
    """Routes lifecycle calls to the appropriate concrete manager.

    Implements LifecycleManagerProtocol by dispatching to
    HttpServerLifecycleManager and StdioServerLifecycleManager
    based on McpServerConfig transport type.
    """

    def __init__(
        self,
        server_configs: dict[str, McpServerConfig],
        tool_executor: ToolExecutor,
        stdio_procs: dict[str, StdioTransport],
    ) -> None:
        self._server_configs = server_configs
        self._last_called: dict[str, float] = {
            key: time.monotonic() for key in server_configs
        }
        self._http_mgr = HttpServerLifecycleManager()
        self._stdio_mgr = StdioServerLifecycleManager(
            server_configs,
            tool_executor,
            stdio_procs,
            self._last_called,
        )

    async def ensure_ready(self, server_key: str) -> None:
        self._last_called[server_key] = time.monotonic()
        cfg = self._server_configs.get(server_key)
        if cfg is None:
            return
        if cfg.transport == "http" and cfg.startup_mode == "subprocess":
            self._http_mgr.verify_running(server_key)
            return
        if cfg.transport != "stdio" or cfg.startup_mode == "persistent":
            return
        await self._stdio_mgr.ensure_ready(server_key)

    async def shutdown_all(self) -> None:
        await self._stdio_mgr.shutdown_all()
        await self._http_mgr.shutdown_all()

    async def start_http_subprocess(
        self,
        server_key: str,
        cfg: McpServerConfig,
    ) -> None:
        await self._http_mgr.start(server_key, cfg)

    async def restart(self, server_key: str) -> None:
        cfg = self._server_configs.get(server_key)
        if cfg is None or cfg.startup_mode != "subprocess":
            _logger.warning(
                f"Lifecycle: restart {server_key!r}: not a subprocess-mode server;"
                " manual restart required",
            )
            return
        await self._http_mgr.restart(server_key, cfg)

    async def shutdown_idle(self) -> None:
        await self._stdio_mgr.shutdown_idle()

    def get_transport_state(self, server_key: str) -> LifecycleState:
        cfg = self._server_configs.get(server_key)
        if cfg is None:
            return LifecycleState.UNKNOWN
        if cfg.transport == "http":
            return LifecycleState.UNKNOWN
        if cfg.transport == "stdio":
            return self._stdio_mgr.get_transport_state(server_key)
        return LifecycleState.UNKNOWN

    async def restart_stdio(self, server_key: str) -> None:
        cfg = self._server_configs.get(server_key)
        if cfg is None or cfg.transport != "stdio":
            _logger.warning(
                f"Lifecycle: restart_stdio {server_key!r}: not a stdio server",
            )
            return
        await self._stdio_mgr.restart(server_key)


def _build_audit_logger(ctx: AgentContext) -> Logger:
    """Build and return the audit logger."""
    return Logger(
        "audit",
        ctx.cfg.obs.audit_log_file,
        structured_log=True,
    )


def _build_llm_client(
    ctx: AgentContext,
    view: CLIView,
) -> tuple[httpx.AsyncClient, LLMClient]:
    """Build httpx.AsyncClient and LLMClient; return both."""

    def _on_llm_usage(prompt_tokens: int, completion_tokens: int) -> None:
        ctx.stats.stat_input_tokens = (ctx.stats.stat_input_tokens or 0) + prompt_tokens
        ctx.stats.stat_output_tokens = (
            ctx.stats.stat_output_tokens or 0
        ) + completion_tokens

    http = httpx.AsyncClient(timeout=ctx.cfg.llm.http_timeout)
    llm = LLMClient(
        http,
        max_retries=ctx.cfg.llm.llm_max_retries,
        retry_base_delay=ctx.cfg.llm.llm_retry_base_delay,
        temperature=ctx.cfg.llm.llm_temperature,
        max_tokens=ctx.cfg.llm.llm_max_tokens,
        on_token=view.write_token,
        on_usage=_on_llm_usage,
        sse_heartbeat_timeout=ctx.cfg.llm.sse_heartbeat_timeout,
        sse_malformed_retry=ctx.cfg.llm.sse_malformed_retry,
        sse_reconnect_max=ctx.cfg.llm.sse_reconnect_max,
        llm_stream_retry_on_heartbeat_timeout=ctx.cfg.llm.llm_stream_retry_on_heartbeat_timeout,
        llm_stream_retry_on_malformed_chunk=ctx.cfg.llm.llm_stream_retry_on_malformed_chunk,
    )
    return http, llm


def _build_tool_executor(
    ctx: AgentContext,
    http: httpx.AsyncClient,
    stdio_procs: dict,
) -> tuple[ToolExecutor, LifecycleManagerProtocol]:
    """Build ToolExecutor and lifecycle manager; return both."""
    tools = ToolExecutor(
        http,
        cache_ttl=ctx.cfg.tool.tool_cache_ttl,
        server_configs=ctx.cfg.mcp.mcp_servers,
        cache_max_size=ctx.cfg.tool.tool_cache_max_size,
        concurrency_limits=ctx.cfg.tool.tool_concurrency_limits,
    )
    lifecycle: LifecycleManagerProtocol = _ServerLifecycleRouter(
        ctx.cfg.mcp.mcp_servers,
        tools,
        stdio_procs,
    )
    tools.set_lifecycle(lifecycle)
    return tools, lifecycle


def _build_history_manager(
    ctx: AgentContext,
    view: CLIView,
    http: httpx.AsyncClient,
) -> HistoryManager:
    """Build and return HistoryManager."""
    return HistoryManager(
        http,
        llm_url=ctx.cfg.llm.llm_url,
        char_limit=ctx.cfg.llm.context_char_limit,
        compress_turns=ctx.cfg.llm.context_compress_turns,
        compress_temperature=_COMPRESS_TEMPERATURE,
        compress_max_tokens=_COMPRESS_MAX_TOKENS,
        on_compress=view.write_compress_notice,
        protect_turns=ctx.cfg.llm.history_protect_turns,
        token_limit=ctx.cfg.llm.context_token_limit,
        tokenize_url=ctx.cfg.llm.tokenize_url,
    )


def _build_memory_services(
    ctx: AgentContext,
    http: httpx.AsyncClient,
) -> MemoryServices | None:
    """Build and return MemoryServices when use_memory_layer=True, else None."""
    if not ctx.cfg.memory.use_memory_layer:
        return None
    # Deferred imports to reduce startup cost when memory is disabled
    from agent.memory.embedding_client import (
        EmbeddingClient,  # noqa: PLC0415 — lazy: reduces startup cost when use_memory_layer=false
        EmbeddingClientConfig,  # noqa: PLC0415 — lazy: reduces startup cost when use_memory_layer=false
    )
    from agent.memory.ingestion import (
        DedupPolicy,  # noqa: PLC0415 — lazy: reduces startup cost when use_memory_layer=false
        MemoryIngestionService,  # noqa: PLC0415 — lazy: reduces startup cost when use_memory_layer=false
    )
    from agent.memory.injection import (
        InjectionPolicy,  # noqa: PLC0415 — lazy: reduces startup cost when use_memory_layer=false
        MemoryInjectionService,  # noqa: PLC0415 — lazy: reduces startup cost when use_memory_layer=false
    )
    from agent.memory.jsonl_store import (
        JsonlMemoryStore,  # noqa: PLC0415 — lazy: reduces startup cost when use_memory_layer=false
    )
    from agent.memory.retriever import (
        HybridRetriever,  # noqa: PLC0415 — lazy: reduces startup cost when use_memory_layer=false
    )
    from agent.memory.services import (
        MemoryServices,  # noqa: PLC0415 — lazy: reduces startup cost when use_memory_layer=false
    )
    from agent.memory.store import (
        MemoryStore,  # noqa: PLC0415 — lazy: reduces startup cost when use_memory_layer=false
    )

    embed_cfg = EmbeddingClientConfig(
        embed_url=ctx.cfg.rag.embed_url,
        timeout=ctx.cfg.memory.memory_embed_timeout_sec,
    )
    embed_client = EmbeddingClient(
        embed_cfg, http, enabled=ctx.cfg.memory.memory_embed_enabled
    )
    retriever = HybridRetriever(
        fts_limit=ctx.cfg.memory.memory_fts_limit,
        rrf_k=ctx.cfg.memory.memory_rrf_k,
        recency_days=ctx.cfg.memory.memory_recency_days,
    )
    store = MemoryStore()
    jsonl = JsonlMemoryStore(f"{ctx.cfg.memory.memory_jsonl_dir}/memories.jsonl")
    injection = MemoryInjectionService(
        policy=InjectionPolicy(
            max_semantic=ctx.cfg.memory.memory_max_inject_semantic,
            max_episodic=ctx.cfg.memory.memory_max_inject_episodic,
            min_importance=ctx.cfg.memory.memory_min_importance,
        ),
        retriever=retriever,
        embed_client=embed_client,
    )
    ingestion = MemoryIngestionService(
        store=store,
        jsonl=jsonl,
        retriever=retriever,
        embed_client=embed_client,
        dedup_policy=DedupPolicy(threshold=ctx.cfg.memory.memory_dedup_threshold),
        max_content_chars=ctx.cfg.memory.memory_max_content_chars,
    )
    _build_audit_logger(ctx).info("MemoryServices initialised (use_memory_layer=True)")
    return MemoryServices(
        injection=injection,
        ingestion=ingestion,
        store=store,
        retriever=retriever,
    )


def _init_plugin_registry(audit_logger: Logger) -> None:
    """Load and register plugins from the plugins/ directory."""
    plugin_dir = Path(__file__).parent.parent.parent / "plugins"
    n_plugins = plugin_registry.load_plugins(plugin_dir)
    if n_plugins:
        audit_logger.info(f"Loaded {n_plugins} plugin(s) from {plugin_dir}")


def init_tracer(ctx: AgentContext) -> object:
    """Build and return an OTel tracer; returns a NoOp stub when otel_enabled=False."""
    return build_tracer(
        enabled=ctx.cfg.obs.otel_enabled,
        service_name=ctx.cfg.obs.otel_service_name,
        otlp_endpoint=ctx.cfg.obs.otel_endpoint,
    )


def build_agent_context(ctx: AgentContext, view: CLIView) -> None:
    """Inject all services into ctx.services.

    Builds services sequentially, then creates a fully-initialized AppServices
    and assigns it to ctx.services.  CommandRegistry and Orchestrator are wired
    by AgentREPL._init_components() after this returns.
    """
    # Shared stdio_procs dict — same object passed to ServerLifecycleManager
    # and AppServices so that _start_stdio_servers() mutations are reflected in both.
    stdio_procs: dict = {}

    audit_logger = _build_audit_logger(ctx)
    http, llm = _build_llm_client(ctx, view)
    tools, lifecycle = _build_tool_executor(ctx, http, stdio_procs)
    hist_mgr = _build_history_manager(ctx, view, http)
    memory = _build_memory_services(ctx, http)

    ctx.services = AppServices(
        http=http,
        llm=llm,
        tools=tools,
        lifecycle=lifecycle,
        hist_mgr=hist_mgr,
        audit_logger=audit_logger,
        memory=memory,
        stdio_procs=stdio_procs,
    )

    _init_plugin_registry(audit_logger)
