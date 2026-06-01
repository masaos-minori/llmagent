#!/usr/bin/env python3
"""mcp/rag_pipeline/service.py
RagPipelineMCPService: wraps RagPipeline for use in rag-pipeline-mcp server.

Dependency direction: rag.mcp.models → rag.mcp.service → rag.mcp.server
"""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from typing import Any

import httpx
from rag.types import RagHit

from mcp.rag_pipeline.models import (
    RagDebugResponse,
    RagRunRequest,
    RagRunResponse,
    RagSearchRequest,
    RagSearchResponse,
    _get_cfg,
    build_rag_cfg_adapter,
)
from mcp.server import ToolArgs

logger = logging.getLogger(__name__)


class RagPipelineMCPService:
    """HTTP-accessible wrapper around RagPipeline.

    Lifecycle: call start() in FastAPI lifespan before serving requests.
    Overrides module-level _cfg caches in rag.pipeline, rag.llm, and db.helper
    so that all sub-modules read from rag_pipeline_mcp_server.toml instead of
    agent.toml / common.toml.  Safe because each MCP server runs as a separate process.
    """

    def __init__(self) -> None:
        self._http: httpx.AsyncClient | None = None
        self._pipeline: Any | None = (
            None  # RagPipeline; typed as Any to avoid circular import
        )

    async def start(self) -> None:
        """Initialize shared resources; must be called once before first request."""
        import rag.llm as rag_llm  # noqa: PLC0415
        import rag.pipeline as agent_rag  # noqa: PLC0415 — lazy import avoids module-load side effects
        from rag.pipeline import RagPipeline  # noqa: PLC0415

        import db.helper as sqlite_helper  # noqa: PLC0415

        cfg = _get_cfg()

        # Override module-level config caches so RagLLM and SQLiteHelper read from
        # rag_pipeline_mcp_server.toml.  Process-scoped; no cross-process contamination.
        agent_rag._cfg = cfg  # noqa: SLF001 — override module cache for process-scoped config
        rag_llm._cfg = cfg  # noqa: SLF001
        sqlite_helper._cfg = cfg  # noqa: SLF001
        # Force SQLiteHelper to re-read DB_PATH from the new cfg on next open()
        sqlite_helper.SQLiteHelper._config_loaded = False  # noqa: SLF001

        rag_cfg = build_rag_cfg_adapter(cfg)
        http_timeout = float(cfg.get("http_timeout", 120.0))
        self._http = httpx.AsyncClient(timeout=http_timeout)
        # SimpleNamespace satisfies RagPipeline's cfg.* attribute access pattern
        self._pipeline = RagPipeline(self._http, rag_cfg)
        logger.info("RagPipelineMCPService started")

    async def stop(self) -> None:
        if self._http is not None:
            await self._http.aclose()
        logger.info("RagPipelineMCPService stopped")

    def _pipeline_or_raise(self) -> Any:
        if self._pipeline is None:
            raise RuntimeError("RagPipelineMCPService not started — call start() first")
        return self._pipeline

    @staticmethod
    def _make_capture_fn() -> tuple[
        Callable[[list[str], list[list[RagHit]], list[RagHit], list[RagHit]], None],
        dict[str, list[Any]],
    ]:
        """Return a (debug_fn, captured) pair; debug_fn populates captured when called."""
        captured: dict[str, list[Any]] = {}

        def _fn(
            queries: list[str],
            _all_results: list[list[RagHit]],
            merged: list[RagHit],
            reranked: list[RagHit],
        ) -> None:
            captured["queries"] = list(queries)
            captured["merged"] = list(merged)
            captured["reranked"] = list(reranked)

        return _fn, captured

    async def run_pipeline(self, req: RagRunRequest) -> RagRunResponse:
        """Execute MQE→Search→RRF→Rerank→Dedup→Augment and return formatted result."""
        pipeline = self._pipeline_or_raise()
        history_str = "\n".join(req.history_context)
        capture_fn, _ = self._make_capture_fn()
        augmented_text = await pipeline.augment(
            req.query,
            debug_fn=capture_fn if req.debug else None,
            history_context=history_str,
        )
        selected_hits: list[dict[str, Any]] = [dict(h) for h in pipeline.last_reranked]
        return RagRunResponse(
            query=req.query,
            augmented_text=augmented_text,
            selected_hits=selected_hits,
        )

    async def run_debug_pipeline(self, req: RagRunRequest) -> RagDebugResponse:
        """Execute pipeline capturing all intermediate stage outputs."""
        pipeline = self._pipeline_or_raise()
        history_str = "\n".join(req.history_context)
        capture_fn, captured = self._make_capture_fn()
        augmented_text = await pipeline.augment(
            req.query,
            debug_fn=capture_fn,
            history_context=history_str,
        )
        selected_hits: list[dict[str, Any]] = [dict(h) for h in pipeline.last_reranked]

        return RagDebugResponse(
            query=req.query,
            augmented_text=augmented_text,
            selected_hits=selected_hits,
            queries=captured.get("queries", []),
            merged_hits=[dict(h) for h in captured.get("merged", [])],
            reranked_hits=[dict(h) for h in captured.get("reranked", [])],
            elapsed=dict(pipeline.last_timings),
        )

    async def run_search(self, req: RagSearchRequest) -> RagSearchResponse:
        """/v1/search backward-compat handler for agent_rag.augment() integration.

        Accepts {query, history_context: str} and returns {context, selected_hits}
        so that augment() can store selected_hits in self.last_reranked for
        two-stage fetch without requiring REPL-side changes.
        """
        run_req = RagRunRequest(
            query=req.query,
            history_context=[req.history_context] if req.history_context else [],
        )
        result = await self.run_pipeline(run_req)
        return RagSearchResponse(
            context=result.augmented_text,
            selected_hits=result.selected_hits,
        )

    # ── MCP tool dispatch formatters ──────────────────────────────────────────

    async def fmt_run_pipeline(self, args: ToolArgs) -> str:
        """Format rag_run_pipeline result as plain text for LLM tool result."""
        req = RagRunRequest(**args)
        result = await self.run_pipeline(req)
        if not result.augmented_text:
            return "(No relevant documents found in the knowledge base.)"
        return result.augmented_text

    async def fmt_debug_pipeline(self, args: ToolArgs) -> str:
        """Format rag_debug_pipeline result as JSON summary for LLM tool result."""
        import orjson  # noqa: PLC0415

        req = RagRunRequest(**args)
        result = await self.run_debug_pipeline(req)
        raw: bytes = orjson.dumps(
            {
                "query": result.query,
                "queries": result.queries,
                "merged_count": len(result.merged_hits),
                "reranked_count": len(result.reranked_hits),
                "selected_count": len(result.selected_hits),
                "elapsed": result.elapsed,
                "augmented_text": result.augmented_text,
            },
            option=orjson.OPT_INDENT_2,
        )
        return raw.decode()

    def get_dispatch_table(
        self,
    ) -> dict[str, Callable[[ToolArgs], Awaitable[str]]]:
        return {
            "rag_run_pipeline": self.fmt_run_pipeline,
            "rag_debug_pipeline": self.fmt_debug_pipeline,
        }


class _LazyRagPipelineMCPService:
    """Lazy singleton proxy; actual service is created on first attribute access."""

    _instance: RagPipelineMCPService | None = None

    def __getattr__(self, name: str) -> Any:
        if _LazyRagPipelineMCPService._instance is None:
            _LazyRagPipelineMCPService._instance = RagPipelineMCPService()
        return getattr(_LazyRagPipelineMCPService._instance, name)


# NOTE: type: ignore[assignment] -- _LazyRagPipelineMCPService is a proxy whose __getattr__
# delegates to the real RagPipelineMCPService instance; mypy sees a type mismatch.
_service: RagPipelineMCPService = _LazyRagPipelineMCPService()  # type: ignore[assignment]
