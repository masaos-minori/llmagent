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
import orjson
from db.helper import SQLiteHelper
from rag.types import MergedHit, RankedHit, RawHit

from mcp.rag_pipeline.models import (
    RagDebugResponse,
    RagPipelineConfig,
    RagRunRequest,
    RagRunResponse,
    RagSearchRequest,
    RagSearchResponse,
    build_rag_cfg_adapter,
)
from mcp.server import ToolArgs

RagHit = RawHit | MergedHit | RankedHit

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
        import rag.pipeline as agent_rag  # noqa: PLC0415 — lazy import avoids module-load side effects
        from rag.pipeline import (
            RagPipeline,  # noqa: PLC0415 — lazy: avoids circular import (_pipeline typed as Any)
        )

        cfg = RagPipelineConfig.load()

        # Override module-level config caches so RagLLM and RagPipeline read from
        # rag_pipeline_mcp_server.toml.  Process-scoped; no cross-process contamination.
        import dataclasses as _dc

        agent_rag._cfg = _dc.asdict(cfg)  # type: ignore[attr-defined]  # noqa: SLF001 -- dynamic module attr; rag.pipeline exposes _cfg for process-scoped MCP config override
        # db.helper resolves config per-instance in __init__; no class-level cache to reset.
        # rag.llm no longer has a module-level _cfg cache; RagLLM receives cfg via constructor.

        rag_cfg = build_rag_cfg_adapter(cfg)
        http_timeout = 120.0  # process-level HTTP client timeout
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
        _fetch = pipeline.last_fetch_result
        selected_hits: list[dict[str, Any]] = (
            [dict(h) for h in _fetch.hits] if _fetch is not None else []
        )
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
        _fetch = pipeline.last_fetch_result
        selected_hits: list[dict[str, Any]] = (
            [dict(h) for h in _fetch.hits] if _fetch is not None else []
        )

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
        so that augment() can store selected_hits in self.last_fetch_result for
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

    # ── Document management (sync; wrap SQLiteHelper directly) ───────────────

    def list_documents(self, lang: str | None = None, limit: int = 20) -> list[dict]:
        sql = (
            "SELECT d.url, d.title, d.lang, d.fetched_at, d.chunking_strategy,"
            " COUNT(c.chunk_id) AS n"
            " FROM documents d"
            " LEFT JOIN chunks c USING(doc_id)"
        )
        params: list[str | int] = []
        if lang:
            sql += " WHERE d.lang = ?"
            params.append(lang)
        sql += " GROUP BY d.doc_id ORDER BY d.fetched_at DESC LIMIT ?"
        params.append(limit)
        with SQLiteHelper("rag").open(row_factory=True) as db:
            rows = db.fetchall(sql, tuple(params))
        return [
            {
                "url": r["url"],
                "title": r["title"],
                "lang": r["lang"],
                "fetched_at": r["fetched_at"],
                "chunking_strategy": r["chunking_strategy"],
                "chunk_count": r["n"],
            }
            for r in rows
        ]

    def delete_document(self, url: str) -> bool:
        with SQLiteHelper("rag").open(write_mode=True) as db:
            row = db.execute(
                "SELECT doc_id FROM documents WHERE url = ?", (url,)
            ).fetchone()
            if row is None:
                return False
            doc_id = row[0]
            db.execute(
                "DELETE FROM chunks_vec"
                " WHERE chunk_id IN"
                " (SELECT chunk_id FROM chunks WHERE doc_id = ?)",
                (doc_id,),
            )
            db.execute("DELETE FROM documents WHERE doc_id = ?", (doc_id,))
            db.commit()
        return True

    # ── MCP tool dispatch formatters ──────────────────────────────────────────

    async def fmt_run_pipeline(self, args: ToolArgs) -> str:
        """Format rag_run_pipeline result as plain text for LLM tool result."""
        req = RagRunRequest(**args)
        result = await self.run_pipeline(req)
        if not result.augmented_text:
            return "(No relevant documents found in the knowledge base.)"
        return result.augmented_text

    async def fmt_list_documents(self, args: ToolArgs) -> str:
        lang = args.get("lang")
        limit = int(args.get("limit", 20))
        rows = self.list_documents(lang if isinstance(lang, str) else None, limit)
        if not rows:
            return "No documents found."
        return "\n".join(
            f"{r['url']} [{r['lang']}] {r['chunk_count']} chunks" for r in rows
        )

    async def fmt_delete_document(self, args: ToolArgs) -> str:
        url = str(args.get("url", "")).strip()
        if not url:
            return "Error: url is required."
        ok = self.delete_document(url)
        return f"Deleted: {url}" if ok else f"Not found: {url}"

    async def fmt_debug_pipeline(self, args: ToolArgs) -> str:
        """Format rag_debug_pipeline result as JSON summary for LLM tool result."""
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
            "rag_list_documents": self.fmt_list_documents,
            "rag_delete_document": self.fmt_delete_document,
        }


_service: RagPipelineMCPService = RagPipelineMCPService()
