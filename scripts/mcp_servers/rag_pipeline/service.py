#!/usr/bin/env python3
"""mcp_servers/rag_pipeline/service.py
RagPipelineMCPService: wraps RagPipeline for use in rag-pipeline-mcp server.

Dependency direction: mcp_servers.rag_pipeline.models → mcp_servers.rag_pipeline.service → mcp_servers.rag_pipeline.server
"""

from __future__ import annotations

import dataclasses
import logging
from collections.abc import Awaitable, Callable
from typing import Any, Protocol, cast

import httpx
import orjson
from mcp_servers.rag_pipeline.document_manager import DocumentManager
from mcp_servers.rag_pipeline.models import (
    PipelineCapture,
    RagDebugResponse,
    RagPipelineConfig,
    RagRunRequest,
    RagRunResponse,
    build_rag_cfg_adapter,
)
from mcp_servers.server import ToolArgs
from shared.types import RagHit

logger = logging.getLogger(__name__)


class RagPipelineLike(Protocol):
    """Structural protocol for the pipeline object; avoids circular imports."""

    async def augment(
        self,
        query: str,
        debug_fn: Callable[..., None] | None = ...,
        history_context: str = ...,
    ) -> str: ...

    last_fetch_result: Any  # TwoStageFetchResult
    last_timings: dict[str, float]

    def invalidate_cache(self) -> None: ...


def _hit_to_dict(hit: RagHit | dict[str, Any]) -> dict[str, Any]:
    """Safely convert a hit to a dict; supports dataclass and dict inputs."""
    if isinstance(hit, dict):
        return hit
    if dataclasses.is_dataclass(hit) and not isinstance(hit, type):
        return dataclasses.asdict(hit)
    raise TypeError(f"Unsupported hit type: {type(hit)}")


class RagPipelineMCPService:
    """HTTP-accessible wrapper around RagPipeline.

    Lifecycle: call start() in FastAPI lifespan before serving requests.
    """

    def __init__(self) -> None:
        self._http: httpx.AsyncClient | None = None
        self._pipeline: RagPipelineLike | None = None
        self._doc_mgr: DocumentManager = DocumentManager()

    async def start(self) -> None:
        """Initialize shared resources; must be called once before first request."""
        from rag.pipeline import (
            RagPipeline,  # noqa: PLC0415 — lazy: avoids circular import (_pipeline typed as Any)
        )

        cfg = RagPipelineConfig.load()

        rag_cfg = build_rag_cfg_adapter(cfg)
        module_cfg: dict[str, object] = {
            "llm_url": cfg.llm_url,
            "embed_url": cfg.embed_url,
            "rag_db_path": cfg.rag_db_path,
            "sqlite_vec_so": cfg.sqlite_vec_so,
            "sqlite_timeout": cfg.sqlite_timeout,
            "sqlite_busy_timeout_ms": cfg.sqlite_busy_timeout_ms,
            "mqe_n_queries": cfg.mqe_n_queries,
            "mqe_prompt_template": cfg.mqe_prompt_template,
            "rerank_prompt_template": cfg.rerank_prompt_template,
        }
        http_timeout = 120.0  # process-level HTTP client timeout
        self._http = httpx.AsyncClient(timeout=http_timeout)
        # SimpleNamespace satisfies RagPipeline's cfg.* attribute access pattern
        # module_cfg bypasses _ModuleConfig.get() / agent.toml loading
        self._pipeline = RagPipeline(self._http, rag_cfg, module_cfg=module_cfg)
        self._doc_mgr = DocumentManager(rag_db_path=cfg.rag_db_path)
        logger.info("RagPipelineMCPService started")

    async def stop(self) -> None:
        if self._http is not None:
            await self._http.aclose()
        logger.info("RagPipelineMCPService stopped")

    def _pipeline_or_raise(self) -> RagPipelineLike:
        if self._pipeline is None:
            raise RuntimeError("RagPipelineMCPService not started — call start() first")
        return self._pipeline

    @staticmethod
    def _make_capture_fn() -> tuple[
        Callable[[list[str], list[list[RagHit]], list[RagHit], list[RagHit]], None],
        PipelineCapture,
    ]:
        """Return a (debug_fn, captured) pair; debug_fn populates captured when called."""
        captured: dict[str, list] = {
            "queries": [],
            "merged": [],
            "reranked": [],
        }

        def _fn(
            queries: list[str],
            _all_results: list[list[RagHit]],
            merged: list[RagHit],
            reranked: list[RagHit],
        ) -> None:
            captured["queries"] = [q for q in queries]
            captured["merged"] = [_hit_to_dict(h) for h in merged]
            captured["reranked"] = [_hit_to_dict(h) for h in reranked]

        return _fn, cast(PipelineCapture, captured)

    def _build_selected_hits(
        self, last_fetch_result: Any | None
    ) -> list[dict[str, Any]]:
        """Build selected_hits list from pipeline fetch result."""
        _fetch = last_fetch_result
        return [_hit_to_dict(h) for h in _fetch.hits] if _fetch is not None else []

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
        selected_hits = self._build_selected_hits(pipeline.last_fetch_result)
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
        selected_hits = self._build_selected_hits(pipeline.last_fetch_result)

        return RagDebugResponse(
            query=req.query,
            augmented_text=augmented_text,
            selected_hits=selected_hits,
            queries=captured.get("queries", []),
            merged_hits=[_hit_to_dict(h) for h in captured.get("merged", [])],
            reranked_hits=[_hit_to_dict(h) for h in captured.get("reranked", [])],
            elapsed=dict(pipeline.last_timings),
        )

    # ── MCP tool dispatch formatters ──────────────────────────────────────────

    async def fmt_run_pipeline(self, args: ToolArgs) -> str:
        """Format rag_run_pipeline result as plain text for LLM tool result."""
        req = RagRunRequest(**args)
        result = await self.run_pipeline(req)
        if not result.augmented_text:
            return "(No relevant documents found in the knowledge base.)"
        text: str = result.augmented_text
        return text

    async def fmt_list_documents(self, args: ToolArgs) -> str:
        lang = args.get("lang")
        limit = int(args.get("limit", 20))
        rows = self._doc_mgr.list_documents(
            lang if isinstance(lang, str) else None, limit
        )
        if not rows:
            return "No documents found."
        return "\n".join(
            f"{r['url']} [{r['lang']}] {r['chunk_count']} chunks" for r in rows
        )

    async def fmt_delete_document(self, args: ToolArgs) -> str:
        raw_url = args.get("url")
        if not isinstance(raw_url, str):
            return "Error: url must be a string."
        url = raw_url.strip()
        if not url:
            return "Error: url is required."
        ok = self._doc_mgr.delete_document(url)
        if ok:
            self._pipeline_or_raise().invalidate_cache()
            logger.info("Semantic cache invalidated after deleting %r", url)
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
