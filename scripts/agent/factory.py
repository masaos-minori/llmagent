"""agent/factory.py
AgentContext assembly factory.
Service injection into ctx.services is separated from AgentREPL to enable testing.
CommandRegistry and Orchestrator remain on AgentREPL because they reference
REPL instance state directly.
"""

from __future__ import annotations

import logging
import sys
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
from agent.repository_gateway import RepositoryGateway
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
                "Lifecycle: restart %r: not a subprocess-mode server;"
                " manual restart required",
                server_key,
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
                "Lifecycle: restart_stdio %r: not a stdio server",
                server_key,
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
    from agent.memory.embedding_client import (  # noqa: PLC0415 — lazy
        EmbeddingClient,
        EmbeddingClientConfig,
    )
    from agent.memory.enums import DedupPolicy  # noqa: PLC0415 — lazy
    from agent.memory.ingestion import (  # noqa: PLC0415 — lazy
        MemoryIngestionService,
    )
    from agent.memory.injection import (  # noqa: PLC0415 — lazy
        InjectionPolicy,
        MemoryInjectionService,
    )
    from agent.memory.jsonl_store import JsonlMemoryStore  # noqa: PLC0415 — lazy
    from agent.memory.retriever import HybridRetriever  # noqa: PLC0415 — lazy
    from agent.memory.services import MemoryServices  # noqa: PLC0415 — lazy
    from agent.memory.store import MemoryStore  # noqa: PLC0415 — lazy

    embed_client = _build_embedding_client(
        ctx, http, EmbeddingClient, EmbeddingClientConfig
    )
    retriever = _build_retriever(ctx, HybridRetriever, embed_client=embed_client)
    store = MemoryStore(embed_dim=ctx.cfg.memory.memory_embed_dim)
    jsonl = _build_jsonl_store(ctx, JsonlMemoryStore)
    injection = _build_injection_service(
        embed_client, retriever, ctx, InjectionPolicy, MemoryInjectionService
    )
    ingestion = _build_ingestion_service(
        store, jsonl, retriever, embed_client, ctx, DedupPolicy, MemoryIngestionService
    )

    _build_audit_logger(ctx).info("MemoryServices initialised (use_memory_layer=True)")
    return MemoryServices(
        injection=injection,  # type: ignore[arg-type]  # builder returns object; lazy factory pattern, correct at runtime
        ingestion=ingestion,  # type: ignore[arg-type]  # builder returns object; lazy factory pattern, correct at runtime
        store=store,
        retriever=retriever,  # type: ignore[arg-type]  # builder returns object; lazy factory pattern, correct at runtime
    )


def _build_embedding_client(
    ctx: AgentContext,
    http: httpx.AsyncClient,
    client_cls: type,
    config_cls: type,
) -> object:
    """Build and return the embedding client instance."""
    cfg = config_cls(
        embed_url=ctx.cfg.rag.embed_url,
        timeout=ctx.cfg.memory.memory_embed_timeout_sec,
        embed_dim=ctx.cfg.memory.memory_embed_dim,
        local_only=ctx.cfg.memory.memory_local_only,
    )
    return client_cls(cfg, http, enabled=ctx.cfg.memory.memory_embed_enabled)


def _build_retriever(
    ctx: AgentContext, retriever_cls: type, *, embed_client: object = None
) -> object:
    """Build and return the hybrid retriever instance."""
    return retriever_cls(
        fts_limit=ctx.cfg.memory.memory_fts_limit,
        rrf_k=ctx.cfg.memory.memory_rrf_k,
        recency_days=ctx.cfg.memory.memory_recency_days,
        embed_client=embed_client,
    )


def _build_jsonl_store(ctx: AgentContext, jsonl_cls: type) -> object:
    """Build and return the JSONL memory store instance."""
    return jsonl_cls(Path(ctx.cfg.memory.memory_jsonl_dir) / "memories.jsonl")


def _build_injection_service(
    embed_client: object,
    retriever: object,
    ctx: AgentContext,
    policy_cls: type,
    service_cls: type,
) -> object:
    """Build and return the memory injection service."""
    policy = policy_cls(
        max_semantic=ctx.cfg.memory.memory_max_inject_semantic,
        max_episodic=ctx.cfg.memory.memory_max_inject_episodic,
        min_importance=ctx.cfg.memory.memory_min_importance,
    )
    return service_cls(
        policy=policy,
        retriever=retriever,
        embed_client=embed_client,
    )


def _build_ingestion_service(
    store: object,
    jsonl: object,
    retriever: object,
    embed_client: object,
    ctx: AgentContext,
    dedup_cls: type,
    service_cls: type,
) -> object:
    """Build and return the memory ingestion service."""
    dedup_policy = dedup_cls(threshold=ctx.cfg.memory.memory_dedup_threshold)
    return service_cls(
        store=store,
        jsonl=jsonl,
        retriever=retriever,
        embed_client=embed_client,
        dedup_policy=dedup_policy,
        max_content_chars=ctx.cfg.memory.memory_max_content_chars,
    )


def _init_plugin_registry(ctx: AgentContext, audit_logger: Logger) -> None:
    """Load and register plugins from the plugins/ directory."""
    from shared.tool_constants import get_all_mcp_tool_names

    plugin_dir = Path(__file__).parent.parent.parent / "plugins"
    override_policy = "allow" if ctx.cfg.tool.plugin_tool_override else "reject"

    if ctx.cfg.tool.plugin_tool_override:
        audit_logger.info(
            "Plugin tool override policy: allow (shadowing MCP tools permitted)"
        )

    known_tools = (
        get_all_mcp_tool_names() if override_policy == "reject" else frozenset()
    )
    mode_str = "strict" if ctx.cfg.tool.plugin_strict else "fail-open"
    audit_logger.info("Plugin loading mode: %s", mode_str)

    # Route plugin INFO logs to stdout so diagnostics are visible at startup.
    plugin_logger = logging.getLogger("shared.plugin_registry")
    if not any(
        isinstance(h, logging.StreamHandler) and h.stream is sys.stdout
        for h in plugin_logger.handlers
    ):
        _stdout_handler = logging.StreamHandler(sys.stdout)
        _stdout_handler.setFormatter(logging.Formatter("%(message)s"))
        _stdout_handler.setLevel(logging.INFO)
        plugin_logger.addHandler(_stdout_handler)

    # Register builtin command names for conflict detection.
    from agent.commands.command_defs import _COMMANDS

    builtin_names = frozenset(cmd.name for cmd in _COMMANDS)
    plugin_registry.register_builtin_commands(builtin_names)

    result = plugin_registry.load_plugins(
        plugin_dir,
        known_tools=known_tools,
        override_policy=override_policy,
        strict_mode=ctx.cfg.tool.plugin_strict,
    )

    if result.failed:
        for failure in result.failed:
            audit_logger.warning(
                "Plugin load failure: %s — %s", failure.path, failure.error
            )

    total_discovered = result.loaded_count + len(result.failed)
    audit_logger.info(
        "Plugin startup: discovered=%d, loaded=%d, skipped=%d,"
        " tool_conflicts_shadowed=%d, tool_conflicts_allowed=%d, command_shadows=%d",
        total_discovered,
        result.loaded_count,
        len(result.failed),
        result.tool_conflicts_shadowed,
        result.tool_conflicts_allowed,
        result.command_shadows,
    )


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
    # Shared stdio_procs dict — same object passed to _ServerLifecycleRouter
    # and AppServices so that _start_stdio_servers() mutations are reflected in both.
    stdio_procs: dict = {}

    audit_logger = _build_audit_logger(ctx)
    http, llm = _build_llm_client(ctx, view)
    tools, lifecycle = _build_tool_executor(ctx, http, stdio_procs)
    hist_mgr = _build_history_manager(ctx, view, http)
    memory = _build_memory_services(ctx, http)
    gateway = RepositoryGateway(executor=tools, cfg=ctx.cfg, audit_logger=audit_logger)

    ctx.services = AppServices(
        http=http,
        llm=llm,
        tools=tools,
        lifecycle=lifecycle,
        hist_mgr=hist_mgr,
        audit_logger=audit_logger,
        memory=memory,
        stdio_procs=stdio_procs,
        gateway=gateway,
    )

    _init_plugin_registry(ctx, audit_logger)
