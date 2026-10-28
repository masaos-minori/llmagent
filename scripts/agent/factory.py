"""scripts/agent/factory.py

AgentContext assembly factory.

Service injection into ctx.services is separated from AgentREPL to enable testing.
CommandRegistry and Orchestrator remain on AgentREPL because they reference
REPL instance state directly.

Lifecycle classes live in agent/lifecycle_router.py:
  _ServerLifecycleRouter — coordinator (state tracking, cooldown, shutdown guard)
  _SubprocessLifecycleManager — subprocess operations (start/restart/shutdown)
Both implement LifecycleManagerProtocol.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, cast

import httpx
from db.store_protocols import get_embedding_dims
from shared.git_helper import get_repo_info
from shared.llm_client import LLMClient, build_embed_url, build_llm_url
from shared.logger import Logger
from shared.mcp_health import McpServerHealthRegistry
from shared.otel_tracer import build_tracer
from shared.tool_executor import ToolExecutor

from agent.cli_view import CLIView
from agent.context import AgentContext, AppServices
from agent.history import HistoryManager
from agent.lifecycle_protocol import LifecycleManagerProtocol
from agent.lifecycle_router import _ServerLifecycleRouter
from agent.repository_gateway import RepositoryGateway

if TYPE_CHECKING:
    from agent.memory.embedding_client import EmbeddingClient
    from agent.memory.jsonl_store import JsonlMemoryStore
    from agent.memory.retriever import HybridRetriever
    from agent.memory.services import MemoryServices
    from agent.memory.store import MemoryStore

_logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class LlmClientResult:
    """Result of building httpx.AsyncClient and LLMClient."""

    http: httpx.AsyncClient
    llm: LLMClient


@dataclass(frozen=True)
class ToolExecutorResult:
    """Result of building ToolExecutor, lifecycle manager, and health registry."""

    tools: ToolExecutor
    lifecycle: LifecycleManagerProtocol
    health_registry: McpServerHealthRegistry


@dataclass(frozen=True)
class HistoryManagerResult:
    """Result of building HistoryManager."""

    history_manager: HistoryManager


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
) -> LlmClientResult:
    """Build httpx.AsyncClient and LLMClient; return both."""

    def _on_llm_usage(prompt_tokens: int, completion_tokens: int) -> None:
        """Callback to accumulate token usage statistics."""
        ctx.stats.stat_input_tokens = (ctx.stats.stat_input_tokens or 0) + prompt_tokens
        ctx.stats.stat_output_tokens = (
            ctx.stats.stat_output_tokens or 0
        ) + completion_tokens

    http = httpx.AsyncClient(timeout=ctx.cfg.llm.http_timeout)
    llm = LLMClient(
        http,
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
    return LlmClientResult(http=http, llm=llm)


def _build_tool_executor(
    ctx: AgentContext,
    http: httpx.AsyncClient,
) -> ToolExecutorResult:
    """Build ToolExecutor, lifecycle manager, and health registry; return all three."""
    registry = McpServerHealthRegistry()
    tools = ToolExecutor(
        http,
        server_configs=ctx.cfg.mcp.mcp_servers,
        concurrency_limits=ctx.cfg.tool.tool_concurrency_limits,
        health_registry=registry,
    )
    lifecycle: LifecycleManagerProtocol = _ServerLifecycleRouter(
        ctx.cfg.mcp.mcp_servers,
        tools,
    )
    tools.set_lifecycle(lifecycle)
    return ToolExecutorResult(
        tools=tools, lifecycle=lifecycle, health_registry=registry
    )


def _build_history_manager(
    ctx: AgentContext,
    view: CLIView,
    http: httpx.AsyncClient,
) -> HistoryManagerResult:
    """Build and return HistoryManager."""
    return HistoryManagerResult(
        history_manager=HistoryManager(
            http,
            llm_url=build_llm_url(ctx.cfg.llm.llm_url),
            char_limit=ctx.cfg.llm.context_char_limit,
            compress_turns=ctx.cfg.llm.context_compress_turns,
            compress_temperature=ctx.cfg.llm.llm_compress_temperature,
            compress_max_tokens=ctx.cfg.llm.llm_compress_max_tokens,
            on_compress=view.write_compress_notice,
            protect_turns=ctx.cfg.llm.history_protect_turns,
            token_limit=ctx.cfg.llm.context_token_limit,
            tokenize_url=ctx.cfg.llm.tokenize_url,
        )
    )


def _resolve_branch_for_memory() -> str:
    """Resolve git branch for memory layer; returns "" (global) on any failure."""
    _git = get_repo_info()
    if _git.success and _git.data:
        _raw = _git.data.get("branch", "")
        return "" if _raw == "HEAD (detached)" else _raw
    _logger.warning(
        "Memory branch resolution failed: %s; falling back to global scope",
        _git.failure_reason if _git.failure_reason else "unknown",
    )
    return ""


def _build_memory_services(
    ctx: AgentContext,
    http: httpx.AsyncClient,
) -> MemoryServices | None:
    """Build and return MemoryServices when use_memory_layer=True, else None."""
    if not ctx.cfg.memory.use_memory_layer:
        return None

    # Deferred imports to reduce startup cost when memory is disabled
    from agent.memory.embedding_client import (  # lazy
        EmbeddingClient,
        EmbeddingClientConfig,
    )
    from agent.memory.enums import DedupPolicy  # lazy
    from agent.memory.ingestion import (  # lazy
        MemoryIngestionService,
    )
    from agent.memory.injection import (  # lazy
        InjectionPolicy,
        MemoryInjectionService,
    )
    from agent.memory.jsonl_store import JsonlMemoryStore  # lazy
    from agent.memory.retriever import HybridRetriever  # lazy
    from agent.memory.services import MemoryServices  # lazy
    from agent.memory.store import MemoryStore  # lazy

    embed_client = _build_embedding_client(
        ctx, http, EmbeddingClient, EmbeddingClientConfig
    )
    retriever = _build_retriever(ctx, HybridRetriever, embed_client=embed_client)
    store = MemoryStore(embed_dim=get_embedding_dims())
    jsonl = _build_jsonl_store(ctx, JsonlMemoryStore)

    _branch = _resolve_branch_for_memory()

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
        injection=injection,
        ingestion=ingestion,
        store=store,
        retriever=retriever,
    )


def _build_embedding_client(
    ctx: AgentContext,
    http: httpx.AsyncClient,
    client_cls: type[EmbeddingClient],
    config_cls: type,
) -> EmbeddingClient:
    """Build and return the embedding client instance."""
    cfg = config_cls(
        embed_url=build_embed_url(ctx.cfg.rag.embed_url),
        timeout=ctx.cfg.memory.memory_embed_timeout_sec,
        local_only=ctx.cfg.memory.memory_local_only,
    )
    return client_cls(cfg, http, enabled=ctx.cfg.memory.memory_embed_enabled)


def _build_retriever[T](
    ctx: AgentContext, retriever_cls: type[T], *, embed_client: EmbeddingClient
) -> T:
    """Build and return the hybrid retriever instance."""
    ctor = cast("Callable[..., T]", retriever_cls)
    return ctor(
        fts_limit=ctx.cfg.memory.memory_fts_limit,
        rrf_k=ctx.cfg.memory.memory_rrf_k,
        recency_days=ctx.cfg.memory.memory_recency_days,
        embed_client=embed_client,
    )


def _build_jsonl_store(
    ctx: AgentContext, jsonl_cls: type[JsonlMemoryStore]
) -> JsonlMemoryStore:
    """Build and return the JSONL memory store instance."""
    return jsonl_cls(Path(ctx.cfg.memory.memory_jsonl_dir) / "memories.jsonl")


def _build_injection_service[T](
    embed_client: EmbeddingClient,
    retriever: HybridRetriever,
    ctx: AgentContext,
    policy_cls: type,
    service_cls: type[T],
    branch: str = "",
) -> T:
    """Build and return the memory injection service."""
    policy = policy_cls(
        max_semantic=ctx.cfg.memory.memory_max_inject_semantic,
        max_episodic=ctx.cfg.memory.memory_max_inject_episodic,
        min_importance=ctx.cfg.memory.memory_min_importance,
    )
    ctor = cast("Callable[..., T]", service_cls)
    return ctor(
        policy=policy,
        retriever=retriever,
        embed_client=embed_client,
        branch=branch,
    )


def _build_ingestion_service[T](
    store: MemoryStore,
    jsonl: JsonlMemoryStore,
    retriever: HybridRetriever,
    embed_client: EmbeddingClient,
    ctx: AgentContext,
    dedup_cls: type,
    service_cls: type[T],
    branch: str = "",
) -> T:
    """Build and return the memory ingestion service."""
    dedup_policy = dedup_cls(threshold=ctx.cfg.memory.memory_dedup_threshold)
    ctor = cast("Callable[..., T]", service_cls)
    return ctor(
        store=store,
        jsonl=jsonl,
        retriever=retriever,
        embed_client=embed_client,
        dedup_policy=dedup_policy,
        max_content_chars=ctx.cfg.memory.memory_max_content_chars,
        branch=branch,
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
    llm_result = _build_llm_client(ctx, view)
    http = llm_result.http
    tools_result = _build_tool_executor(ctx, http)
    hist_result = _build_history_manager(ctx, view, http)
    memory = _build_memory_services(ctx, http)

    ctx.services = AppServices(
        http=http,
        llm=llm_result.llm,
        tools=tools_result.tools,
        lifecycle=tools_result.lifecycle,
        hist_mgr=hist_result.history_manager,
        audit_logger=audit_logger,
        memory=memory,
        gateway=RepositoryGateway(
            executor=tools_result.tools, cfg=ctx.cfg, audit_logger=audit_logger
        ),
        health_registry=tools_result.health_registry,
    )
