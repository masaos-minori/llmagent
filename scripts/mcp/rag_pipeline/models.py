#!/usr/bin/env python3
"""rag_pipeline_mcp_models.py
Pydantic request/response models and config adapter for rag-pipeline-mcp.

Dependency direction: rag_pipeline_mcp_models → rag_pipeline_mcp_service → rag_mcp_server
"""

from __future__ import annotations

import dataclasses
import logging
from types import SimpleNamespace
from typing import Any, TypedDict

from pydantic import BaseModel, Field
from shared.config_loader import ConfigLoader

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# Domain exceptions
# ──────────────────────────────────────────────────────────────────────────────


class RagPipelineServiceError(RuntimeError):
    """Raised when the RAG pipeline service is not ready."""


# ──────────────────────────────────────────────────────────────────────────────
# Typed config object
# ──────────────────────────────────────────────────────────────────────────────


@dataclasses.dataclass
class RagPipelineConfig:
    """Typed configuration for the RAG Pipeline MCP server."""

    use_mqe: bool = True
    use_rrf: bool = True
    rrf_k: int = 60
    use_rerank: bool = True
    use_refiner: bool = False
    top_k_search: int = 5
    top_k_rerank: int = 10
    rag_top_k: int = 5
    rag_min_score: float = 0.0
    max_chunks_per_doc: int = 3
    semantic_cache_max_size: int = 128
    semantic_cache_threshold: float = 0.92
    use_semantic_cache: bool = False
    refiner_max_tokens: int = 512
    refiner_max_chars_per_chunk: int = 800
    refiner_timeout: float = 30.0
    rag_auth_token: str = ""

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> RagPipelineConfig:
        """Construct from a raw config dict (e.g. loaded from TOML)."""
        return cls(
            use_mqe=bool(d.get("use_mqe", True)),
            use_rrf=bool(d.get("use_rrf", True)),
            rrf_k=int(d.get("rrf_k", 60)),
            use_rerank=bool(d.get("use_rerank", True)),
            use_refiner=bool(d.get("use_refiner", False)),
            top_k_search=int(d.get("top_k_search", 5)),
            top_k_rerank=int(d.get("top_k_rerank", 10)),
            rag_top_k=int(d.get("rag_top_k", 5)),
            rag_min_score=float(d.get("rag_min_score", 0.0)),
            max_chunks_per_doc=int(d.get("max_chunks_per_doc", 3)),
            semantic_cache_max_size=int(d.get("semantic_cache_max_size", 128)),
            semantic_cache_threshold=float(d.get("semantic_cache_threshold", 0.92)),
            use_semantic_cache=bool(d.get("use_semantic_cache", False)),
            refiner_max_tokens=int(d.get("refiner_max_tokens", 512)),
            refiner_max_chars_per_chunk=int(d.get("refiner_max_chars_per_chunk", 800)),
            refiner_timeout=float(d.get("refiner_timeout", 30.0)),
            rag_auth_token=str(d.get("rag_auth_token", "")),
        )

    @classmethod
    def load(cls) -> RagPipelineConfig:
        """Load from rag_pipeline_mcp_server.toml; raises on failure (fail-fast)."""
        return cls.from_dict(ConfigLoader().load("rag_pipeline_mcp_server.toml"))


def build_rag_cfg_adapter(cfg: RagPipelineConfig) -> SimpleNamespace:
    """Build a SimpleNamespace that satisfies RagPipeline's cfg.* access pattern.

    RagPipeline accesses AgentConfig fields via cfg.* attributes.  This adapter
    populates only the fields RagPipeline reads, sourced from RagPipelineConfig.
    """
    return SimpleNamespace(
        use_mqe=bool(cfg.use_mqe),
        use_rrf=bool(cfg.use_rrf),
        rrf_k=int(cfg.rrf_k),
        use_rerank=bool(cfg.use_rerank),
        use_refiner=bool(cfg.use_refiner),
        use_search=True,  # always True in MCP mode; checked in augment()
        rag_service_url="",  # prevent HTTP loop when augment() is called in-process
        rag_auth_token="",
        top_k_search=int(cfg.top_k_search),
        top_k_rerank=int(cfg.top_k_rerank),
        rag_top_k=int(cfg.rag_top_k),
        rag_min_score=float(cfg.rag_min_score),
        max_chunks_per_doc=int(cfg.max_chunks_per_doc),
        semantic_cache_max_size=int(cfg.semantic_cache_max_size),
        semantic_cache_threshold=float(cfg.semantic_cache_threshold),
        use_semantic_cache=bool(cfg.use_semantic_cache),
        refiner_max_tokens=int(cfg.refiner_max_tokens),
        refiner_max_chars_per_chunk=int(cfg.refiner_max_chars_per_chunk),
        refiner_timeout=float(cfg.refiner_timeout),
    )


# ── Hit dict type for response models ─────────────────────────────────────────


# TypedDict for hit data returned in response models.
# Fields correspond to RagHit dataclass fields (RawHit / MergedHit / RankedHit)
# plus optional rrf_score and rerank_score from derived classes.
# All fields are optional because HTTP mode returns dicts with varied schemas.
class HitDict(TypedDict, total=False):
    chunk_id: int | str | None
    content: str | None
    url: str | None
    title: str | None
    distance: float | None
    bm25_score: float | None
    rrf_score: float | None
    rerank_score: float | None

# Note: Response models use dict[str, Any] for hit lists because TypedDict
# field types conflict with Pydantic validation when data sources vary.


# ── Document list item type ───────────────────────────────────────────────────


class DocumentItem(TypedDict):
    """Typed return value for list_documents."""

    url: str
    title: str
    lang: str
    fetched_at: str
    chunking_strategy: str
    chunk_count: int


# ── Pipeline debug capture type ───────────────────────────────────────────────


class PipelineCapture(TypedDict):
    """Return value of RagPipelineMCPService._make_capture_fn()."""

    queries: list[str]
    merged: list[dict[str, Any]]
    reranked: list[dict[str, Any]]


# ── Request / Response models ─────────────────────────────────────────────────


class RagRunRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Original user query.")
    history_context: list[str] = Field(
        default_factory=list,
        description="Recent user utterances passed to MQE for disambiguation.",
    )
    debug: bool = Field(
        default=False,
        description="Return intermediate pipeline outputs when true.",
    )


class RagRunResponse(BaseModel):
    query: str
    augmented_text: str = Field(
        description="Formatted RAG context block for LLM injection.",
    )
    selected_hits: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Final selected chunks; consumed by two-stage fetch callers.",
    )


class RagDebugResponse(RagRunResponse):
    queries: list[str] = Field(
        default_factory=list,
        description="MQE-expanded queries.",
    )
    merged_hits: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Hits after RRF merge.",
    )
    reranked_hits: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Hits after cross-encoder rerank.",
    )
    elapsed: dict[str, float] = Field(
        default_factory=dict,
        description="Per-step wall-clock seconds.",
    )


class RagSearchRequest(BaseModel):
    """Backward-compat schema for POST /v1/search used by agent_rag.augment()."""

    query: str
    history_context: str = ""


class RagSearchResponse(BaseModel):
    """Backward-compat response for POST /v1/search.

    Extends the original {context: str} response with selected_hits so that
    agent_rag.augment() can populate self.last_fetch_result for two-stage fetch.
    """

    context: str
    selected_hits: list[dict[str, Any]] = Field(default_factory=list)
