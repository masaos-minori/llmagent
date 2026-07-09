"""agent/factory.py
AgentContext assembly factory.
Service injection into ctx.services is separated from AgentREPL to enable testing.
CommandRegistry and Orchestrator remain on AgentREPL because they reference
REPL instance state directly.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import httpx
from agent.cli_view import CLIView
from agent.context import AgentContext, AppServices
from agent.history import HistoryManager
from agent.http_lifecycle import HttpServerLifecycleManager
from agent.lifecycle import LifecycleState, assert_valid_transition
from agent.lifecycle_protocol import LifecycleManagerProtocol
from agent.repository_gateway import RepositoryGateway
from agent.services.models import ProcessInfoSnapshot
from shared import plugin_registry
from shared.git_helper import get_repo_info
from shared.llm_client import LLMClient
from shared.logger import Logger
from shared.mcp_config import McpServerConfig, StartupMode, TransportType
from shared.mcp_health import McpServerHealthRegistry
from shared.otel_tracer import build_tracer
from shared.tool_executor import ToolExecutor

if TYPE_CHECKING:
    from agent.memory.services import MemoryServices

# LLM parameters used by HistoryManager for conversation compression
_COMPRESS_TEMPERATURE: float = 0.3
_COMPRESS_MAX_TOKENS: int = 300

_logger = logging.getLogger(__name__)


class _ServerLifecycleRouter:
    """Production implementation of LifecycleManagerProtocol for HTTP MCP servers.

    Delegates subprocess management to HttpServerLifecycleManager (_http_mgr) while
    adding:
    - Shutdown guard (_shutting_down): prevents start/restart after shutdown begins.
    - LifecycleState tracking (_states): provides get_transport_state() with real values.
    - Process snapshot API: get_process_info() and list_processes() for observability.
    """

    def __init__(
        self,
        server_configs: dict[str, McpServerConfig],
        tool_executor: ToolExecutor,
    ) -> None:
        self._server_configs = server_configs
        self._http_mgr = HttpServerLifecycleManager()
        self._shutting_down: bool = False
        self._states: dict[str, LifecycleState] = {}

    def _set_state(self, server_key: str, new_state: LifecycleState) -> None:
        current = self._states.get(server_key, LifecycleState.UNKNOWN)
        try:
            assert_valid_transition(current, new_state)
        except ValueError:
            _logger.warning(
                "Lifecycle: invalid state transition %r -> %r for %r",
                current,
                new_state,
                server_key,
            )
        self._states[server_key] = new_state

    async def ensure_ready(self, server_key: str) -> None:
        if self._shutting_down:
            _logger.debug(
                "Lifecycle: ensure_ready(%r) ignored — shutting down", server_key
            )
            return
        cfg = self._server_configs.get(server_key)
        if cfg is None:
            return
        if (
            cfg.transport != TransportType.HTTP
            or cfg.startup_mode != StartupMode.SUBPROCESS
        ):
            return
        if not self._http_mgr.verify_running(server_key):
            _logger.info(
                "Lifecycle: %r not running; starting via ensure_ready", server_key
            )
            self._set_state(server_key, LifecycleState.STARTING)
            try:
                await self._http_mgr.start(server_key, cfg)
                self._set_state(server_key, LifecycleState.RUNNING)
            except Exception:
                self._set_state(server_key, LifecycleState.FAILED)
                raise

    async def shutdown_all(self) -> None:
        self._shutting_down = True
        await self._http_mgr.shutdown_all()
        for key in self._server_configs:
            self._set_state(key, LifecycleState.STOPPED)

    async def start_http_subprocess(
        self,
        server_key: str,
        cfg: McpServerConfig,
    ) -> None:
        if self._shutting_down:
            _logger.debug(
                "Lifecycle: start_http_subprocess(%r) ignored — shutting down",
                server_key,
            )
            return
        self._set_state(server_key, LifecycleState.STARTING)
        try:
            await self._http_mgr.start(server_key, cfg)
            self._set_state(server_key, LifecycleState.RUNNING)
        except Exception:
            self._set_state(server_key, LifecycleState.FAILED)
            raise

    async def restart(self, server_key: str) -> None:
        if self._shutting_down:
            _logger.warning(
                "Lifecycle: restart(%r) ignored — shutting down", server_key
            )
            return
        cfg = self._server_configs.get(server_key)
        if cfg is None or cfg.startup_mode != StartupMode.SUBPROCESS:
            _logger.warning(
                "Lifecycle: restart %r: not a subprocess-mode server;"
                " manual restart required",
                server_key,
            )
            return
        self._set_state(server_key, LifecycleState.STARTING)
        try:
            await self._http_mgr.restart(server_key, cfg)
            self._set_state(server_key, LifecycleState.RUNNING)
        except Exception:
            self._set_state(server_key, LifecycleState.FAILED)
            raise

    async def shutdown_idle(self) -> None:
        if self._shutting_down:
            _logger.debug("Lifecycle: shutdown_idle ignored — shutting down")
            return

    def get_transport_state(self, server_key: str) -> LifecycleState:
        return self._states.get(server_key, LifecycleState.UNKNOWN)

    def get_process_snapshot(self, server_key: str) -> dict | None:
        """Return process snapshot dict for a managed subprocess server, or None."""
        return self._http_mgr.get_process_snapshot(server_key)

    def get_process_info(self, server_key: str) -> ProcessInfoSnapshot | None:
        """Return ProcessInfoSnapshot for a managed subprocess server, or None."""
        return self._http_mgr.get_process_info(server_key)

    def list_processes(self) -> list[ProcessInfoSnapshot]:
        """Return list of ProcessInfoSnapshot for all managed subprocess servers."""
        return self._http_mgr.list_processes()


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
) -> tuple[ToolExecutor, LifecycleManagerProtocol, McpServerHealthRegistry]:
    """Build ToolExecutor, lifecycle manager, and health registry; return all three."""
    tools = ToolExecutor(
        http,
        cache_ttl=ctx.cfg.tool.tool_cache_ttl,
        server_configs=ctx.cfg.mcp.mcp_servers,
        cache_max_size=ctx.cfg.tool.tool_cache_max_size,
        concurrency_limits=ctx.cfg.tool.tool_concurrency_limits,
    )
    registry = McpServerHealthRegistry()
    tools.set_health_registry(registry)
    lifecycle: LifecycleManagerProtocol = _ServerLifecycleRouter(
        ctx.cfg.mcp.mcp_servers,
        tools,
    )
    tools.set_lifecycle(lifecycle)
    return tools, lifecycle, registry


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

    # Resolve branch context at build time; default to "" (global) on any failure.
    _git = get_repo_info()
    _branch = ""
    if _git.success and _git.data:
        _raw = _git.data.get("branch", "")
        _branch = "" if _raw == "HEAD (detached)" else _raw

    injection = _build_injection_service(
        embed_client,
        retriever,
        ctx,
        InjectionPolicy,
        MemoryInjectionService,
        branch=_branch,
    )
    ingestion = _build_ingestion_service(
        store,
        jsonl,
        retriever,
        embed_client,
        ctx,
        DedupPolicy,
        MemoryIngestionService,
        branch=_branch,
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
    branch: str = "",
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
        branch=branch,
    )


def _build_ingestion_service(
    store: object,
    jsonl: object,
    retriever: object,
    embed_client: object,
    ctx: AgentContext,
    dedup_cls: type,
    service_cls: type,
    branch: str = "",
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
    from shared.tool_registry import get_registry

    plugin_dir = Path(__file__).parent.parent.parent / "plugins"
    override_policy = "allow" if ctx.cfg.tool.plugin_tool_override else "reject"

    if ctx.cfg.tool.plugin_tool_override:
        audit_logger.info(
            "Plugin tool override policy: allow (shadowing MCP tools permitted)"
        )

    known_tools = (
        get_registry().get_all_tool_names()
        if override_policy == "reject"
        else frozenset()
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
    from agent.commands.command_defs_list import _COMMANDS

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
                "[non-fatal] Plugin load failure: %s — %s", failure.path, failure.error
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
        result.command_shadows_rejected,
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
    audit_logger = _build_audit_logger(ctx)
    http, llm = _build_llm_client(ctx, view)
    tools, lifecycle, health_registry = _build_tool_executor(ctx, http)
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
        gateway=gateway,
        health_registry=health_registry,
    )

    _init_plugin_registry(ctx, audit_logger)
