"""agent/factory.py
AgentContext 組み立てファクトリ。
ctx.services.* へのサービス注入を AgentREPL から分離し、テスト可能にする。
CommandRegistry と Orchestrator は AgentREPL 自身のインスタンス変数に対して
設定する必要があるため、AgentREPL 側に残している。
"""

from __future__ import annotations

import logging
from pathlib import Path

import httpx
from shared import plugin_registry
from shared.llm_client import LLMClient
from shared.logger import Logger
from shared.otel_tracer import build_tracer
from shared.tool_executor import ToolExecutor

from agent.cli_view import CLIView
from agent.context import AgentContext
from agent.history import HistoryManager
from agent.lifecycle import ServerLifecycleManager

# LLM パラメータ (HistoryManager の圧縮用)
_COMPRESS_TEMPERATURE: float = 0.3
_COMPRESS_MAX_TOKENS: int = 300

_logger = logging.getLogger(__name__)
_audit_logger_instance = Logger(__name__, "/opt/llm/logs/agent.log")


def _init_audit_logger(ctx: AgentContext) -> None:
    """監査ロガーを初期化して ctx.services.audit_logger にセットする。"""
    # structured_log=True で JSON-lines 形式のターンイベントを出力する
    ctx.services.audit_logger = Logger(
        "audit",
        ctx.cfg.audit_log_file,
        structured_log=True,
    )


def _init_llm_client(ctx: AgentContext, view: CLIView) -> None:
    """httpx.AsyncClient と LLMClient を初期化して ctx.services にセットする。"""

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
        on_token=view.write_token,
        on_usage=_on_llm_usage,
        sse_heartbeat_timeout=ctx.cfg.sse_heartbeat_timeout,
        sse_malformed_retry=ctx.cfg.sse_malformed_retry,
        sse_reconnect_max=ctx.cfg.sse_reconnect_max,
        llm_stream_retry_on_heartbeat_timeout=ctx.cfg.llm_stream_retry_on_heartbeat_timeout,
        llm_stream_retry_on_malformed_chunk=ctx.cfg.llm_stream_retry_on_malformed_chunk,
    )


def _init_tool_executor(ctx: AgentContext) -> None:
    """ToolExecutor と ServerLifecycleManager を初期化して ctx.services にセットする。"""
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


def _init_history_manager(ctx: AgentContext, view: CLIView) -> None:
    """HistoryManager を初期化して ctx.services.hist_mgr にセットする。"""
    assert ctx.services.http is not None
    ctx.services.hist_mgr = HistoryManager(
        ctx.services.http,
        llm_url=ctx.cfg.llm_url,
        char_limit=ctx.cfg.context_char_limit,
        compress_turns=ctx.cfg.context_compress_turns,
        compress_temperature=_COMPRESS_TEMPERATURE,
        compress_max_tokens=_COMPRESS_MAX_TOKENS,
        on_compress=view.write_compress_notice,
        protect_turns=ctx.cfg.history_protect_turns,
        token_limit=ctx.cfg.context_token_limit,
        tokenize_url=ctx.cfg.tokenize_url,
    )


def _init_memory_layer(ctx: AgentContext) -> None:
    """use_memory_layer=True のとき MemoryLayer を初期化して ctx.services.memory にセットする。"""
    # use_memory_layer=False のときはインポートもスキップして起動コストを下げる
    if not ctx.cfg.use_memory_layer:
        return
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
    _audit_logger_instance.info("MemoryLayer initialised (use_memory_layer=True)")


def _init_plugin_registry() -> None:
    """plugins/ ディレクトリからプラグインをロードして登録する。"""
    # plugins/ は scripts/ と同じ親ディレクトリ (repo root) に置かれる
    plugin_dir = Path(__file__).parent.parent.parent / "plugins"
    n_plugins = plugin_registry.load_plugins(plugin_dir)
    if n_plugins:
        _audit_logger_instance.info(f"Loaded {n_plugins} plugin(s) from {plugin_dir}")


def init_tracer(ctx: AgentContext) -> object:
    """OTel トレーサーを構築して返す。otel_enabled=False のとき NoOp スタブを返す。"""
    return build_tracer(
        enabled=ctx.cfg.otel_enabled,
        service_name=ctx.cfg.otel_service_name,
        otlp_endpoint=ctx.cfg.otel_endpoint,
    )


def build_agent_context(ctx: AgentContext, view: CLIView) -> None:
    """ctx.services.* にすべてのサービスを注入する。

    CommandRegistry と Orchestrator は AgentREPL のインスタンス変数なので
    ここでは設定しない。AgentREPL._init_components() が続けて設定する。
    """
    _init_audit_logger(ctx)
    _init_llm_client(ctx, view)
    _init_tool_executor(ctx)
    _init_history_manager(ctx, view)
    _init_memory_layer(ctx)
    _init_plugin_registry()
