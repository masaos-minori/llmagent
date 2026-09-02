"""tests/rag/test_augment_refiner.py

Integration tests for scripts/rag/augment.py — AugmentRefiner class.

Tests constructor-injection pattern, HTTP augment delegation, and refiner delegation.
"""

from __future__ import annotations

import dataclasses
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from rag.augment import AugmentRefiner
from rag.models_config import RagConfigImpl
from rag.models_data import TwoStageFetchResult
from rag.models_result import HttpResultKind, SearchDiagnostics
from shared.types import RagConfig

# ── Fixtures ──────────────────────────────────────────────────────────────────


def _make_cfg(**overrides: object) -> RagConfig:
    """Create a minimal RagConfigImpl with defaults."""
    base = RagConfigImpl(
        llm_url="http://localhost:8000/v1/chat/completions",
        embed_url="http://localhost:8000/v1/embeddings",
        rag_db_path=":memory:",
        sqlite_vec_so="/opt/llm/sqlite-vec/vec0.so",
        sqlite_timeout=5,
        sqlite_busy_timeout_ms=5000,
        embed_retry=3,
        embed_workers=4,
        rag_pipeline_service_url=None,
        mqe_prompt_template="Expand query: {query}",
        mqe_n_queries=3,
        rerank_prompt_template="Rerank results for: {query}",
        use_search=True,
        rag_service_url=None,
        use_refiner=False,
        use_mqe=False,
        use_rerank=False,
        use_rrf=True,
        rrf_k=60,
        use_semantic_cache=False,
        top_k_search=5,
        rag_top_k=3,
        top_k_rerank=10,
        rag_min_score=0.0,
        max_chunks_per_doc=3,
        semantic_cache_max_size=100,
        semantic_cache_threshold=0.0,
        refiner_max_tokens=256,
        refiner_max_chars_per_chunk=500,
        refiner_timeout=10.0,
        rag_auth_token="",
    )
    if overrides:
        base = dataclasses.replace(base, **{k: v for k, v in overrides.items()})
    return base  # type: ignore[return-value] — dataclasses.replace with **overrides spreads unknown keys into TypedDict fields


def _make_refiner(**kwargs: object) -> AugmentRefiner:
    """Create an AugmentRefiner with minimal dependencies."""
    cfg = kwargs.pop("cfg", _make_cfg())
    on_status = kwargs.pop("on_status", lambda _: None)
    set_fetch_result = kwargs.pop("set_fetch_result", lambda _: None)
    set_fallback_reason = kwargs.pop("set_fallback_reason", lambda _: None)
    search_diagnostics = kwargs.pop("search_diagnostics", SearchDiagnostics())
    llm = kwargs.pop("llm", None)
    http = kwargs.pop("http", MagicMock())
    return AugmentRefiner(
        http=http,
        cfg=cfg,
        on_status=on_status,
        set_fetch_result=set_fetch_result,
        set_fallback_reason=set_fallback_reason,
        search_diagnostics=search_diagnostics,
        llm=llm,
    )


# ── Constructor injection ─────────────────────────────────────────────────────


class TestAugmentRefinerConstructor:
    def test_default_callbacks_are_noops(self) -> None:
        """Default callbacks should be no-op lambdas."""
        refiner = _make_refiner()
        refiner._on_status("test")
        refiner._set_fetch_result(MagicMock())
        refiner._set_fallback_reason("reason")

    def test_custom_on_status_callback(self) -> None:
        """Custom on_status callback should be called."""
        status_calls: list[str] = []
        refiner = _make_refiner(on_status=status_calls.append)
        refiner._on_status("hello")
        assert status_calls == ["hello"]

    def test_custom_set_fetch_result_callback(self) -> None:
        """Custom set_fetch_result callback should be called."""
        fetch_results: list[TwoStageFetchResult] = []
        refiner = _make_refiner(set_fetch_result=lambda fr: fetch_results.append(fr))
        mock_fr = MagicMock(spec=TwoStageFetchResult)
        refiner._set_fetch_result(mock_fr)
        assert fetch_results == [mock_fr]

    def test_custom_set_fallback_reason_callback(self) -> None:
        """Custom set_fallback_reason callback should be called."""
        fallback_reasons: list[str] = []
        refiner = _make_refiner(
            set_fallback_reason=lambda r: fallback_reasons.append(r)
        )
        refiner._set_fallback_reason("timeout")
        assert fallback_reasons == ["timeout"]

    def test_last_stage_results_returns_empty_when_no_diagnostics(self) -> None:
        """last_stage_results returns empty list when search_diagnostics is None."""
        refiner = _make_refiner(search_diagnostics=None)
        assert refiner.last_stage_results == []

    def test_search_diagnostics_property(self) -> None:
        """search_diagnostics property should get/set diagnostics."""
        diagnostics = SearchDiagnostics()
        refiner = _make_refiner(search_diagnostics=diagnostics)
        assert refiner.search_diagnostics is diagnostics
        new_diag = SearchDiagnostics(embed_ok=1, embed_failed=0, fts_errors=0)
        refiner.search_diagnostics = new_diag
        assert refiner.search_diagnostics.embed_ok == 1

    @pytest.mark.asyncio
    async def test_llm_required_for_refiner(self) -> None:
        """run_refiner should raise ValueError when llm is not injected."""
        refiner = _make_refiner(llm=None)
        with pytest.raises(ValueError, match="RagLLM dependency not injected"):
            await refiner.run_refiner([], "query")


# ── map_http_result_kind ──────────────────────────────────────────────────────


class TestMapHttpResultKind:
    @pytest.mark.parametrize(
        ("input_val, expected"),
        [
            (None, HttpResultKind.NOT_USED),
            ("remote_nonempty", HttpResultKind.SUCCESS),
            ("remote_empty", HttpResultKind.EMPTY),
            ("in_process_fallback", HttpResultKind.ERROR),
        ],
    )
    def test_maps_known_values(
        self, input_val: str | None, expected: HttpResultKind
    ) -> None:
        result = AugmentRefiner.map_http_result_kind(input_val)
        assert result is expected

    def test_static_method_signature(self) -> None:
        """map_http_result_kind should accept str | None and return HttpResultKind."""
        from typing import get_type_hints

        hints = get_type_hints(AugmentRefiner.map_http_result_kind)
        param_hint = hints.get("kind")
        assert param_hint is not None
        # Check that it accepts both str and None
        assert hasattr(param_hint, "__args__") or param_hint is str
        # Return type should be HttpResultKind
        ret_hint = hints.get("return")
        assert ret_hint is HttpResultKind


# ── run_http_augment ──────────────────────────────────────────────────────────


class TestRunHttpAugment:
    @pytest.mark.asyncio
    async def test_delegates_to_http_augment(self) -> None:
        """run_http_augment should delegate to HttpAugment."""
        mock_http = MagicMock()
        cfg = _make_cfg(rag_service_url="http://example.com/api")
        refiner = _make_refiner(http=mock_http, cfg=cfg)

        mock_result = MagicMock()
        mock_result.result = "augmented context"
        mock_result.http_result_kind = "remote_nonempty"
        mock_result.status_code = 200
        mock_result.latency_ms = 100

        with patch("rag.augment.HttpAugment") as MockHttpAugment:
            mock_instance = MagicMock()
            mock_instance.run = AsyncMock(return_value=mock_result)
            mock_instance.stage_result = None
            MockHttpAugment.return_value = mock_instance

            result = await refiner.run_http_augment(
                "query", "", "http://example.com/api"
            )

        assert result == "augmented context"
        args, kwargs = MockHttpAugment.call_args
        assert args[0] is mock_http
        assert args[1] == "http://example.com/api"
        assert kwargs["auth_token"] == ""
        assert callable(kwargs["set_fetch_result"])
        assert callable(kwargs["set_fallback_reason"])

    @pytest.mark.asyncio
    async def test_returns_none_when_http_augment_fails(self) -> None:
        """run_http_augment should return None when HttpAugment returns None."""
        mock_http = MagicMock()
        cfg = _make_cfg(rag_service_url="http://example.com/api")
        refiner = _make_refiner(http=mock_http, cfg=cfg)

        mock_result = MagicMock()
        mock_result.result = None
        mock_result.http_result_kind = "in_process_fallback"
        mock_result.status_code = 500
        mock_result.latency_ms = 200

        with patch("rag.augment.HttpAugment") as MockHttpAugment:
            mock_instance = MagicMock()
            mock_instance.run = AsyncMock(return_value=mock_result)
            mock_instance.stage_result = None
            MockHttpAugment.return_value = mock_instance

            result = await refiner.run_http_augment(
                "query", "", "http://example.com/api"
            )

        assert result is None

    @pytest.mark.asyncio
    async def test_updates_search_diagnostics(self) -> None:
        """run_http_augment should update search_diagnostics with HTTP result info."""
        mock_http = MagicMock()
        cfg = _make_cfg(rag_service_url="http://example.com/api")
        diagnostics = SearchDiagnostics()
        refiner = _make_refiner(
            http=mock_http,
            cfg=cfg,
            search_diagnostics=diagnostics,
        )

        mock_result = MagicMock()
        mock_result.result = "context"
        mock_result.http_result_kind = "remote_nonempty"
        mock_result.status_code = 200
        mock_result.latency_ms = 150

        with patch("rag.augment.HttpAugment") as MockHttpAugment:
            mock_instance = MagicMock()
            mock_instance.run = AsyncMock(return_value=mock_result)
            mock_instance.stage_result = None
            MockHttpAugment.return_value = mock_instance

            await refiner.run_http_augment("query", "", "http://example.com/api")

        updated_diag = refiner.search_diagnostics
        assert updated_diag.result_source is not None
        assert updated_diag.remote_status_code == 200
        assert updated_diag.remote_latency_ms == 150

    @pytest.mark.asyncio
    async def test_sets_remote_result_source(self) -> None:
        """When result.result is not None, result_source should be REMOTE."""
        mock_http = MagicMock()
        cfg = _make_cfg(rag_service_url="http://example.com/api")
        diagnostics = SearchDiagnostics()
        refiner = _make_refiner(
            http=mock_http,
            cfg=cfg,
            search_diagnostics=diagnostics,
        )

        mock_result = MagicMock()
        mock_result.result = "context"
        mock_result.http_result_kind = "remote_nonempty"
        mock_result.status_code = 200
        mock_result.latency_ms = 100

        with patch("rag.augment.HttpAugment") as MockHttpAugment:
            mock_instance = MagicMock()
            mock_instance.run = AsyncMock(return_value=mock_result)
            mock_instance.stage_result = None
            MockHttpAugment.return_value = mock_instance

            await refiner.run_http_augment("query", "", "http://example.com/api")

        assert refiner.search_diagnostics.result_source is not None
        assert refiner.search_diagnostics.result_source.value == "remote"

    @pytest.mark.asyncio
    async def test_sets_fallback_result_source(self) -> None:
        """When result.result is None, result_source should be FALLBACK."""
        mock_http = MagicMock()
        cfg = _make_cfg(rag_service_url="http://example.com/api")
        diagnostics = SearchDiagnostics()
        refiner = _make_refiner(
            http=mock_http,
            cfg=cfg,
            search_diagnostics=diagnostics,
        )

        mock_result = MagicMock()
        mock_result.result = None
        mock_result.http_result_kind = "in_process_fallback"
        mock_result.status_code = 500
        mock_result.latency_ms = 200

        with patch("rag.augment.HttpAugment") as MockHttpAugment:
            mock_instance = MagicMock()
            mock_instance.run = AsyncMock(return_value=mock_result)
            mock_instance.stage_result = None
            MockHttpAugment.return_value = mock_instance

            await refiner.run_http_augment("query", "", "http://example.com/api")

        assert refiner.search_diagnostics.result_source is not None
        assert refiner.search_diagnostics.result_source.value == "fallback"

    @pytest.mark.asyncio
    async def test_empty_string_result_is_valid(self) -> None:
        """Empty string '' from HTTP should be treated as valid result (not None)."""
        mock_http = MagicMock()
        cfg = _make_cfg(rag_service_url="http://example.com/api")
        refiner = _make_refiner(http=mock_http, cfg=cfg)

        mock_result = MagicMock()
        mock_result.result = ""
        mock_result.http_result_kind = "remote_nonempty"
        mock_result.status_code = 200
        mock_result.latency_ms = 100

        with patch("rag.augment.HttpAugment") as MockHttpAugment:
            mock_instance = MagicMock()
            mock_instance.run = AsyncMock(return_value=mock_result)
            mock_instance.stage_result = None
            MockHttpAugment.return_value = mock_instance

            result = await refiner.run_http_augment(
                "query", "", "http://example.com/api"
            )

        assert result == ""

    @pytest.mark.asyncio
    async def test_auth_token_passed_to_http_augment(self) -> None:
        """auth_token should be passed to HttpAugment constructor."""
        mock_http = MagicMock()
        cfg = _make_cfg(
            rag_service_url="http://example.com/api", rag_auth_token="secret-token"
        )
        refiner = _make_refiner(http=mock_http, cfg=cfg)

        mock_result = MagicMock()
        mock_result.result = "context"
        mock_result.http_result_kind = "remote_nonempty"
        mock_result.status_code = 200
        mock_result.latency_ms = 100

        with patch("rag.augment.HttpAugment") as MockHttpAugment:
            mock_instance = MagicMock()
            mock_instance.run = AsyncMock(return_value=mock_result)
            mock_instance.stage_result = None
            MockHttpAugment.return_value = mock_instance

            await refiner.run_http_augment("query", "", "http://example.com/api")

        call_kwargs = MockHttpAugment.call_args.kwargs
        assert call_kwargs["auth_token"] == "secret-token"

    @pytest.mark.asyncio
    async def test_empty_auth_token_defaults_to_empty_string(self) -> None:
        """Empty auth_token should default to empty string."""
        mock_http = MagicMock()
        cfg = _make_cfg(rag_service_url="http://example.com/api", rag_auth_token="")
        refiner = _make_refiner(http=mock_http, cfg=cfg)

        mock_result = MagicMock()
        mock_result.result = "context"
        mock_result.http_result_kind = "remote_nonempty"
        mock_result.status_code = 200
        mock_result.latency_ms = 100

        with patch("rag.augment.HttpAugment") as MockHttpAugment:
            mock_instance = MagicMock()
            mock_instance.run = AsyncMock(return_value=mock_result)
            mock_instance.stage_result = None
            MockHttpAugment.return_value = mock_instance

            await refiner.run_http_augment("query", "", "http://example.com/api")

        call_kwargs = MockHttpAugment.call_args.kwargs
        assert call_kwargs["auth_token"] == ""

    @pytest.mark.asyncio
    async def test_null_auth_token_defaults_to_empty_string(self) -> None:
        """Null auth_token should default to empty string."""
        mock_http = MagicMock()
        cfg = _make_cfg(rag_service_url="http://example.com/api", rag_auth_token=None)  # type: ignore[arg-type] — test verifies None defaults to empty string
        refiner = _make_refiner(http=mock_http, cfg=cfg)

        mock_result = MagicMock()
        mock_result.result = "context"
        mock_result.http_result_kind = "remote_nonempty"
        mock_result.status_code = 200
        mock_result.latency_ms = 100

        with patch("rag.augment.HttpAugment") as MockHttpAugment:
            mock_instance = MagicMock()
            mock_instance.run = AsyncMock(return_value=mock_result)
            mock_instance.stage_result = None
            MockHttpAugment.return_value = mock_instance

            await refiner.run_http_augment("query", "", "http://example.com/api")

        call_kwargs = MockHttpAugment.call_args.kwargs
        assert call_kwargs["auth_token"] == ""

    @pytest.mark.asyncio
    async def test_http_result_kind_mapping_preserved(self) -> None:
        """_map_http_result_kind mapping should be preserved in diagnostics."""
        mock_http = MagicMock()
        cfg = _make_cfg(rag_service_url="http://example.com/api")
        diagnostics = SearchDiagnostics()
        refiner = _make_refiner(
            http=mock_http,
            cfg=cfg,
            search_diagnostics=diagnostics,
        )

        mock_result = MagicMock()
        mock_result.result = "context"
        mock_result.http_result_kind = "remote_empty"
        mock_result.status_code = 200
        mock_result.latency_ms = 100

        with patch("rag.augment.HttpAugment") as MockHttpAugment:
            mock_instance = MagicMock()
            mock_instance.run = AsyncMock(return_value=mock_result)
            mock_instance.stage_result = None
            MockHttpAugment.return_value = mock_instance

            await refiner.run_http_augment("query", "", "http://example.com/api")

        assert refiner.search_diagnostics.http_result_kind is not None
        assert refiner.search_diagnostics.http_result_kind.value == "empty"

    @pytest.mark.asyncio
    async def test_http_result_kind_none_maps_to_not_used(self) -> None:
        """None http_result_kind should map to NOT_USED."""
        mock_http = MagicMock()
        cfg = _make_cfg(rag_service_url="http://example.com/api")
        diagnostics = SearchDiagnostics()
        refiner = _make_refiner(
            http=mock_http,
            cfg=cfg,
            search_diagnostics=diagnostics,
        )

        mock_result = MagicMock()
        mock_result.result = "context"
        mock_result.http_result_kind = None
        mock_result.status_code = 200
        mock_result.latency_ms = 100

        with patch("rag.augment.HttpAugment") as MockHttpAugment:
            mock_instance = MagicMock()
            mock_instance.run = AsyncMock(return_value=mock_result)
            mock_instance.stage_result = None
            MockHttpAugment.return_value = mock_instance

            await refiner.run_http_augment("query", "", "http://example.com/api")

        assert refiner.search_diagnostics.http_result_kind is not None
        assert refiner.search_diagnostics.http_result_kind.value == "not_used"

    @pytest.mark.asyncio
    async def test_http_augment_exception_propagates(self) -> None:
        """Exceptions from HttpAugment should propagate."""
        mock_http = MagicMock()
        cfg = _make_cfg(rag_service_url="http://example.com/api")
        refiner = _make_refiner(http=mock_http, cfg=cfg)

        with patch("rag.augment.HttpAugment") as MockHttpAugment:
            mock_instance = MagicMock()
            mock_instance.run = AsyncMock(
                side_effect=httpx.RequestError("connection failed")
            )
            mock_instance.stage_result = None
            MockHttpAugment.return_value = mock_instance

            with pytest.raises(httpx.RequestError):
                await refiner.run_http_augment("query", "", "http://example.com/api")

    @pytest.mark.asyncio
    async def test_set_fetch_result_callback_called_with_result(self) -> None:
        """set_fetch_result callback should be called with augment result string."""
        captured_results: list[str] = []
        mock_http = MagicMock(spec=httpx.AsyncClient)
        cfg = _make_cfg(rag_service_url="http://example.com/api")
        refiner = _make_refiner(
            http=mock_http,
            cfg=cfg,
            set_fetch_result=lambda fr: captured_results.append(fr),
        )

        with patch("rag.http_augment.call_rag_service") as mock_call_rag_service:
            mock_call_rag_service.return_value = ("context", 200, 100.0)

            result = await refiner.run_http_augment(
                "query", "", "http://example.com/api"
            )

        assert result == "context"
        assert len(captured_results) == 1
        assert captured_results[0] == "context"

    @pytest.mark.asyncio
    async def test_set_fallback_reason_callback_called(self) -> None:
        """set_fallback_reason callback should be called with reason string."""
        captured_reasons: list[str] = []
        mock_http = MagicMock(spec=httpx.AsyncClient)
        cfg = _make_cfg(rag_service_url="http://example.com/api")
        refiner = _make_refiner(
            http=mock_http,
            cfg=cfg,
            set_fallback_reason=lambda r: captured_reasons.append(r),
        )

        with patch("rag.http_augment.call_rag_service") as mock_call_rag_service:

            def side_effect(*args, **kwargs):
                set_fallback_reason = kwargs.get("set_fallback_reason")
                if set_fallback_reason:
                    set_fallback_reason("http_max_retries: 3 attempts failed")
                return (None, None, 0.0)

            mock_call_rag_service.side_effect = side_effect

            result = await refiner.run_http_augment(
                "query", "", "http://example.com/api"
            )

        assert result is None
        assert len(captured_reasons) >= 1
