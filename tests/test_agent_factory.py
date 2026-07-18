"""
tests/test_agent_factory.py
Unit tests for agent/factory.py:
  - build_agent_context: ctx.services.* にすべてのサービスが注入されること
  - init_tracer: build_tracer を正しく呼ぶこと
  - use_memory_layer フラグによる MemoryServices の有無
"""

from __future__ import annotations

import logging
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from agent.factory import _ServerLifecycleRouter, build_agent_context, init_tracer
from agent.lifecycle import LifecycleState
from shared.mcp_config import McpServerConfig, StartupMode, TransportType
from shared.mcp_health import McpServerHealthRegistry, McpServerHealthState

# ── Fixtures ──────────────────────────────────────────────────────────────────


def _make_ctx(*, use_memory_layer: bool = False, otel_enabled: bool = False) -> Any:
    """AgentContext を MagicMock で生成する。cfg の主要フィールドをセットする。"""
    ctx = MagicMock()
    ctx.cfg.memory.use_memory_layer = use_memory_layer
    ctx.cfg.obs.otel_enabled = otel_enabled
    ctx.cfg.obs.otel_service_name = "test-agent"
    ctx.cfg.obs.otel_endpoint = ""
    ctx.cfg.obs.audit_log_file = "/dev/null"
    ctx.cfg.llm.http_timeout = 30.0
    ctx.cfg.llm.llm_max_retries = 3
    ctx.cfg.llm.llm_retry_base_delay = 1.0
    ctx.cfg.llm.llm_temperature = 0.2
    ctx.cfg.llm.llm_max_tokens = 1024
    ctx.cfg.llm.sse_heartbeat_timeout = 30.0
    ctx.cfg.llm.sse_malformed_retry = False
    ctx.cfg.llm.sse_reconnect_max = 3
    ctx.cfg.llm.llm_stream_retry_on_heartbeat_timeout = True
    ctx.cfg.llm.llm_stream_retry_on_malformed_chunk = True
    ctx.cfg.tool.tool_cache_ttl = 300.0
    ctx.cfg.tool.tool_cache_max_size = 128
    ctx.cfg.tool.tool_concurrency_limits = {}
    ctx.cfg.mcp.mcp_servers = {}
    ctx.cfg.llm.llm_url = "http://localhost:8080"
    ctx.cfg.llm.context_char_limit = 8000
    ctx.cfg.llm.context_compress_turns = 5
    ctx.cfg.llm.history_protect_turns = 2
    ctx.cfg.llm.context_token_limit = 0
    ctx.cfg.llm.tokenize_url = ""
    ctx.cfg.memory.memory_jsonl_dir = "/tmp/test_memories"
    ctx.cfg.memory.memory_max_inject_semantic = 5
    ctx.cfg.memory.memory_max_inject_episodic = 5
    ctx.cfg.memory.memory_min_importance = 0.5
    ctx.cfg.rag.embed_url = ""
    ctx.cfg.memory.memory_embed_enabled = False
    ctx.cfg.memory.memory_dedup_threshold = 0.9
    ctx.cfg.memory.memory_embed_timeout_sec = 5.0
    ctx.cfg.memory.memory_max_content_chars = 2000
    # services は初期状態で None
    ctx.services.http = None
    ctx.services.llm = None
    ctx.services.tools = None
    ctx.services.lifecycle = None
    ctx.services.hist_mgr = None
    ctx.services.memory = None
    ctx.services.audit_logger = None
    return ctx


def _make_view() -> Any:
    """CLIView を MagicMock で生成する。コールバックはすべてモック。"""
    view = MagicMock()
    return view


# ── build_agent_context ───────────────────────────────────────────────────────

_FACTORY_PATCHES = [
    "agent.factory.Logger",
    "agent.factory.httpx.AsyncClient",
    "agent.factory.LLMClient",
    "agent.factory.ToolExecutor",
    "agent.factory._ServerLifecycleRouter",
    "agent.factory.HistoryManager",
    "agent.factory.build_tracer",
]


def _apply_patches(monkeypatch: Any) -> dict[str, Any]:
    """_FACTORY_PATCHES で定義した依存を MonkeyPatch で差し替え、モック辞書を返す。"""
    mocks: dict[str, Any] = {}
    for target in _FACTORY_PATCHES:
        mock = MagicMock()
        monkeypatch.setattr(target, mock)
        mocks[target] = mock
    return mocks


class TestBuildAgentContext:
    def test_audit_logger_is_set(self, monkeypatch: Any) -> None:
        _apply_patches(monkeypatch)
        ctx = _make_ctx()
        view = _make_view()

        build_agent_context(ctx, view)

        # Logger が "audit" 名で呼ばれ、ctx.services.audit_logger にセットされていること
        assert ctx.services.audit_logger is not None

    def test_http_client_is_set(self, monkeypatch: Any) -> None:
        mocks = _apply_patches(monkeypatch)
        ctx = _make_ctx()
        view = _make_view()

        build_agent_context(ctx, view)

        # httpx.AsyncClient が作成されて ctx.services.http にセットされること
        mocks["agent.factory.httpx.AsyncClient"].assert_called_once()
        assert ctx.services.http is not None

    def test_llm_client_is_set(self, monkeypatch: Any) -> None:
        mocks = _apply_patches(monkeypatch)
        ctx = _make_ctx()
        view = _make_view()

        build_agent_context(ctx, view)

        mocks["agent.factory.LLMClient"].assert_called_once()
        assert ctx.services.llm is not None

    def test_tool_executor_is_set(self, monkeypatch: Any) -> None:
        mocks = _apply_patches(monkeypatch)
        ctx = _make_ctx()
        view = _make_view()

        build_agent_context(ctx, view)

        mocks["agent.factory.ToolExecutor"].assert_called_once()
        assert ctx.services.tools is not None

    def test_lifecycle_is_set(self, monkeypatch: Any) -> None:
        mocks = _apply_patches(monkeypatch)
        ctx = _make_ctx()
        view = _make_view()

        build_agent_context(ctx, view)

        mocks["agent.factory._ServerLifecycleRouter"].assert_called_once()
        assert ctx.services.lifecycle is not None

    def test_history_manager_is_set(self, monkeypatch: Any) -> None:
        mocks = _apply_patches(monkeypatch)
        ctx = _make_ctx()
        view = _make_view()

        build_agent_context(ctx, view)

        mocks["agent.factory.HistoryManager"].assert_called_once()
        assert ctx.services.hist_mgr is not None

    def test_memory_layer_not_set_when_disabled(self, monkeypatch: Any) -> None:
        # use_memory_layer=False → ctx.services.memory は None のまま
        _apply_patches(monkeypatch)
        ctx = _make_ctx(use_memory_layer=False)
        view = _make_view()

        build_agent_context(ctx, view)

        assert ctx.cfg.memory.use_memory_layer is False

    def test_memory_layer_set_when_enabled(self, monkeypatch: Any) -> None:
        # use_memory_layer=True → MemoryServices が作成されて ctx.services.memory にセットされること
        _apply_patches(monkeypatch)
        ctx = _make_ctx(use_memory_layer=True)
        view = _make_view()
        build_agent_context(ctx, view)
        assert ctx.services.memory is not None

    def test_build_agent_context_has_health_registry(self, monkeypatch: Any) -> None:
        _apply_patches(monkeypatch)
        ctx = _make_ctx()
        view = _make_view()
        build_agent_context(ctx, view)
        assert ctx.services.health_registry is not None
        assert isinstance(ctx.services.health_registry, McpServerHealthRegistry)

    def test_health_registry_shared_between_tool_executor_and_services(
        self, monkeypatch: Any
    ) -> None:
        mocks = _apply_patches(monkeypatch)
        ctx = _make_ctx()
        view = _make_view()
        build_agent_context(ctx, view)
        tool_executor_instance = mocks["agent.factory.ToolExecutor"].return_value
        tool_executor_instance.set_health_registry.assert_called_once()
        call_arg = tool_executor_instance.set_health_registry.call_args[0][0]
        assert call_arg is ctx.services.health_registry

    def test_health_state_shared_via_registry(self, monkeypatch: Any) -> None:
        _apply_patches(monkeypatch)
        ctx = _make_ctx()
        view = _make_view()
        build_agent_context(ctx, view)
        registry = ctx.services.health_registry
        assert isinstance(registry, McpServerHealthRegistry)
        assert registry.get_state("test_server") == McpServerHealthState.HEALTHY
        for _ in range(3):
            registry.record_failure("test_server")
        assert registry.get_state("test_server") != McpServerHealthState.HEALTHY

    def test_on_llm_usage_callback_accumulates_tokens(self, monkeypatch: Any) -> None:
        # _on_llm_usage コールバックが stat_input/output_tokens を正しく蓄積すること
        mocks = _apply_patches(monkeypatch)
        ctx = _make_ctx()
        view = _make_view()
        ctx.stats.stat_input_tokens = None
        ctx.stats.stat_output_tokens = None

        # LLMClient のコンストラクタに渡された on_usage コールバックを取り出して直接呼ぶ
        build_agent_context(ctx, view)
        llm_client_call_kwargs = mocks["agent.factory.LLMClient"].call_args.kwargs
        on_usage = llm_client_call_kwargs["on_usage"]

        on_usage(100, 50)
        assert ctx.stats.stat_input_tokens == 100
        assert ctx.stats.stat_output_tokens == 50

        on_usage(200, 80)
        assert ctx.stats.stat_input_tokens == 300
        assert ctx.stats.stat_output_tokens == 130


# ── _build_jsonl_store ────────────────────────────────────────────────────────


class TestBuildJsonlStore:
    def test_uses_path_based_construction(self, monkeypatch: Any) -> None:
        from pathlib import Path

        from agent.factory import _build_jsonl_store

        jsonl_cls_mock = MagicMock()
        ctx = _make_ctx()
        ctx.cfg.memory.memory_jsonl_dir = "/opt/llm/memory"

        result = _build_jsonl_store(ctx, jsonl_cls_mock)

        expected_path = Path("/opt/llm/memory") / "memories.jsonl"
        jsonl_cls_mock.assert_called_once_with(expected_path)
        assert result is not None

    def test_does_not_use_hardcoded_fstring(self, monkeypatch: Any) -> None:
        from pathlib import Path

        from agent.factory import _build_jsonl_store

        jsonl_cls_mock = MagicMock()
        ctx = _make_ctx()
        ctx.cfg.memory.memory_jsonl_dir = "/tmp/test_memories"

        _build_jsonl_store(ctx, jsonl_cls_mock)

        # Verify the path does not start with "/memories.jsonl" (no hardcoded root)
        call_arg = jsonl_cls_mock.call_args[0][0]
        assert not str(call_arg).startswith("/memories.jsonl")
        assert call_arg == Path("/tmp/test_memories") / "memories.jsonl"

    def test_path_join_with_trailing_slash(self, monkeypatch: Any) -> None:
        from pathlib import Path

        from agent.factory import _build_jsonl_store

        jsonl_cls_mock = MagicMock()
        ctx = _make_ctx()
        ctx.cfg.memory.memory_jsonl_dir = "/opt/llm/memory/"

        _build_jsonl_store(ctx, jsonl_cls_mock)

        # Path / handles trailing slashes correctly
        expected_path = Path("/opt/llm/memory") / "memories.jsonl"
        jsonl_cls_mock.assert_called_once_with(expected_path)


# ── init_tracer ───────────────────────────────────────────────────────────────


class TestInitTracer:
    def test_calls_build_tracer_with_cfg_fields(self, monkeypatch: Any) -> None:
        mock_build_tracer = MagicMock(return_value="mock_tracer")
        monkeypatch.setattr("agent.factory.build_tracer", mock_build_tracer)

        ctx = _make_ctx(otel_enabled=True)
        result = init_tracer(ctx)

        mock_build_tracer.assert_called_once_with(
            enabled=True,
            service_name="test-agent",
            otlp_endpoint="",
        )
        assert result == "mock_tracer"

    def test_otel_disabled_passes_false(self, monkeypatch: Any) -> None:
        mock_build_tracer = MagicMock(return_value="noop_tracer")
        monkeypatch.setattr("agent.factory.build_tracer", mock_build_tracer)

        ctx = _make_ctx(otel_enabled=False)
        result = init_tracer(ctx)

        mock_build_tracer.assert_called_once_with(
            enabled=False,
            service_name="test-agent",
            otlp_endpoint="",
        )
        assert result == "noop_tracer"


# ── _ServerLifecycleRouter shutdown guard ────────────────────────────────────


def _make_router(server_key: str = "srv") -> _ServerLifecycleRouter:
    cfg = McpServerConfig(
        transport=TransportType.HTTP,
        url="http://localhost:9999",
        auth_token="",
        startup_mode=StartupMode.SUBPROCESS,
        cmd=["echo", "hi"],
    )
    router = _ServerLifecycleRouter(
        server_configs={server_key: cfg},
        tool_executor=MagicMock(),
    )
    router._http_mgr = AsyncMock()
    return router


class TestShutdownGuard:
    @pytest.mark.asyncio
    async def test_shutdown_guard_blocks_restart(self) -> None:
        router = _make_router()
        await router.shutdown_all()
        await router.restart("srv")
        router._http_mgr.restart.assert_not_called()

    @pytest.mark.asyncio
    async def test_shutdown_guard_blocks_ensure_ready(self) -> None:
        router = _make_router()
        await router.shutdown_all()
        await router.ensure_ready("srv")
        router._http_mgr.start.assert_not_called()

    @pytest.mark.asyncio
    async def test_repeated_shutdown_all_is_idempotent(self) -> None:
        router = _make_router()
        await router.shutdown_all()
        await router.shutdown_all()

    @pytest.mark.asyncio
    async def test_shutdown_guard_restart_emits_warning(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        router = _make_router()
        await router.shutdown_all()
        with caplog.at_level(logging.WARNING, logger="agent.factory"):
            await router.restart("srv")
        assert any("shutting down" in r.message for r in caplog.records)
        assert any(r.levelno == logging.WARNING for r in caplog.records)


# ── ensure_ready() auto-start behavior ───────────────────────────────────────


def _make_router_with_mock_mgr(
    startup_mode: StartupMode = StartupMode.SUBPROCESS,
    verify_running_result: bool = False,
) -> tuple[_ServerLifecycleRouter, AsyncMock]:
    cfg = McpServerConfig(
        transport=TransportType.HTTP,
        url="http://localhost:9999",
        auth_token="",
        startup_mode=startup_mode,
        cmd=["echo", "hi"],
    )
    router = _ServerLifecycleRouter(
        server_configs={"srv": cfg},
        tool_executor=MagicMock(),
    )
    mock_mgr = AsyncMock()
    mock_mgr.verify_running = MagicMock(return_value=verify_running_result)
    router._http_mgr = mock_mgr
    return router, mock_mgr


class TestEnsureReadyAutoStart:
    @pytest.mark.asyncio
    async def test_ensure_ready_starts_when_not_running(self) -> None:
        router, mock_mgr = _make_router_with_mock_mgr(verify_running_result=False)
        await router.ensure_ready("srv")
        mock_mgr.start.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_ensure_ready_skips_start_when_running(self) -> None:
        router, mock_mgr = _make_router_with_mock_mgr(verify_running_result=True)
        await router.ensure_ready("srv")
        mock_mgr.start.assert_not_called()

    @pytest.mark.asyncio
    async def test_ensure_ready_skips_persistent_mode(self) -> None:
        router, mock_mgr = _make_router_with_mock_mgr(
            startup_mode=StartupMode.PERSISTENT
        )
        await router.ensure_ready("srv")
        mock_mgr.start.assert_not_called()
        mock_mgr.verify_running.assert_not_called()

    @pytest.mark.asyncio
    async def test_ensure_ready_unknown_key_no_error(self) -> None:
        router, mock_mgr = _make_router_with_mock_mgr()
        await router.ensure_ready("unknown_key")
        mock_mgr.start.assert_not_called()

    @pytest.mark.asyncio
    async def test_ensure_ready_respects_shutdown_guard(self) -> None:
        router, mock_mgr = _make_router_with_mock_mgr(verify_running_result=False)
        router._shutting_down = True
        await router.ensure_ready("srv")
        mock_mgr.start.assert_not_called()


# ── H-9: LifecycleState tracking ─────────────────────────────────────────────


class TestLifecycleStateTracking:
    @pytest.mark.asyncio
    async def test_state_running_after_start(self) -> None:
        router = _make_router()
        cfg = router._server_configs["srv"]
        await router.start_http_subprocess("srv", cfg)
        assert router.get_transport_state("srv") == LifecycleState.RUNNING

    @pytest.mark.asyncio
    async def test_state_failed_when_start_raises(self) -> None:
        router = _make_router()
        router._http_mgr.start.side_effect = RuntimeError("startup error")
        cfg = router._server_configs["srv"]
        with pytest.raises(RuntimeError):
            await router.start_http_subprocess("srv", cfg)
        assert router.get_transport_state("srv") == LifecycleState.FAILED

    @pytest.mark.asyncio
    async def test_state_running_after_restart(self) -> None:
        router = _make_router()
        await router.restart("srv")
        assert router.get_transport_state("srv") == LifecycleState.RUNNING

    @pytest.mark.asyncio
    async def test_state_stopped_after_shutdown(self) -> None:
        router = _make_router()
        await router.shutdown_all()
        assert router.get_transport_state("srv") == LifecycleState.STOPPED

    def test_state_unknown_for_unknown_key(self) -> None:
        router = _make_router()
        assert router.get_transport_state("nonexistent") == LifecycleState.UNKNOWN

    @pytest.mark.asyncio
    async def test_state_starting_before_start_completes(self) -> None:
        router = _make_router()
        states_during_start: list[LifecycleState] = []

        async def capture_state_start(server_key: str, cfg: McpServerConfig) -> None:
            states_during_start.append(router.get_transport_state(server_key))

        router._http_mgr.start.side_effect = capture_state_start
        cfg = router._server_configs["srv"]

        await router.start_http_subprocess("srv", cfg)

        assert LifecycleState.STARTING in states_during_start
        assert router.get_transport_state("srv") == LifecycleState.RUNNING
