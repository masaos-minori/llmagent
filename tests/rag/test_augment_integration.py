"""tests/rag/test_augment_integration.py

Integration tests for scripts/rag/augment.py — AugmentRefiner class.

Tests constructor-injection pattern and refiner delegation.
"""

from __future__ import annotations

import dataclasses

import pytest
from rag.augment import AugmentRefiner
from rag.models_config import RagConfigImpl
from rag.models_result import SearchDiagnostics
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
        mqe_prompt_template="Expand query: {query}",
        mqe_n_queries=3,
        rerank_prompt_template="Rerank results for: {query}",
        use_search=True,
        use_refiner=False,
        use_mqe=False,
        use_rerank=False,
        use_rrf=True,
        rrf_k=60,
        top_k_search=5,
        rag_top_k=3,
        top_k_rerank=10,
        rag_min_score=0.0,
        max_chunks_per_doc=3,
        refiner_max_tokens=256,
        refiner_max_chars_per_chunk=500,
        refiner_timeout=10.0,
    )
    if overrides:
        base = dataclasses.replace(base, **{k: v for k, v in overrides.items()})
    return base  # type: ignore[return-value] — dataclasses.replace with **overrides spreads unknown keys into TypedDict fields


def _make_refiner(**kwargs: object) -> AugmentRefiner:
    """Create an AugmentRefiner with minimal dependencies."""
    cfg = kwargs.pop("cfg", _make_cfg())
    on_status = kwargs.pop("on_status", lambda _: None)
    search_diagnostics = kwargs.pop("search_diagnostics", SearchDiagnostics())
    llm = kwargs.pop("llm", None)
    return AugmentRefiner(
        cfg=cfg,
        on_status=on_status,
        search_diagnostics=search_diagnostics,
        llm=llm,
    )


# ── Constructor injection ─────────────────────────────────────────────────────


class TestAugmentRefinerConstructor:
    def test_default_callbacks_are_noops(self) -> None:
        """Default callbacks should be no-op lambdas."""
        refiner = _make_refiner()
        refiner._on_status("test")

    def test_custom_on_status_callback(self) -> None:
        """Custom on_status callback should be called."""
        status_calls: list[str] = []
        refiner = _make_refiner(on_status=status_calls.append)
        refiner._on_status("hello")
        assert status_calls == ["hello"]

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
