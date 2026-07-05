"""
tests/test_agent_factory.py
Unit tests for agent/factory.py:
  - build_agent_context: ctx.services.* にすべてのサービスが注入されること
  - init_tracer: build_tracer を正しく呼ぶこと
  - use_memory_layer フラグによる MemoryServices の有無
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

from agent.factory import build_agent_context, init_tracer

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
    "agent.factory.plugin_registry.load_plugins",
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

    def test_plugin_registry_loaded(self, monkeypatch: Any) -> None:
        mocks = _apply_patches(monkeypatch)
        ctx = _make_ctx()
        view = _make_view()

        build_agent_context(ctx, view)

        mocks["agent.factory.plugin_registry.load_plugins"].assert_called_once()

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
