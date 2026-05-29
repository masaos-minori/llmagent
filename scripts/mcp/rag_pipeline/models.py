#!/usr/bin/env python3
"""
rag_pipeline_mcp_models.py
Pydantic request/response models and config adapter for rag-pipeline-mcp.

Dependency direction: rag_pipeline_mcp_models → rag_pipeline_mcp_service → rag_mcp_server
"""

from __future__ import annotations

import logging
from types import SimpleNamespace
from typing import Any

from pydantic import BaseModel, Field
from shared.config_loader import ConfigLoader

logger = logging.getLogger(__name__)

_cfg: dict | None = None


def _get_cfg() -> dict:
    """Load rag_pipeline_mcp_server.toml on first call; cached for the module lifetime."""
    global _cfg
    if _cfg is None:
        try:
            _cfg = ConfigLoader().load("rag_pipeline_mcp_server.toml")
        except Exception as e:
            logger.warning(f"rag_pipeline_mcp: config load failed: {e}")
            _cfg = {}
    return _cfg


def build_rag_cfg_adapter(cfg: dict) -> SimpleNamespace:
    """Build a SimpleNamespace that satisfies RagPipeline's cfg.* access pattern.

    RagPipeline accesses AgentConfig fields via cfg.* attributes.  This adapter
    populates only the fields RagPipeline reads, sourced from rag_pipeline_mcp_server.toml
    instead of the full AgentConfig.
    """
    return SimpleNamespace(
        use_mqe=bool(cfg.get("use_mqe", True)),
        use_rrf=bool(cfg.get("use_rrf", True)),
        use_rerank=bool(cfg.get("use_rerank", True)),
        use_refiner=bool(cfg.get("use_refiner", False)),
        use_search=True,  # always True in MCP mode; checked in augment()
        rag_service_url="",  # prevent HTTP loop when augment() is called in-process
        top_k_search=int(cfg.get("top_k_search", 5)),
        top_k_rerank=int(cfg.get("top_k_rerank", 10)),
        rag_top_k=int(cfg.get("rag_top_k", 5)),
        rag_min_score=float(cfg.get("rag_min_score", 0.0)),
        max_chunks_per_doc=int(cfg.get("max_chunks_per_doc", 3)),
        semantic_cache_max_size=int(cfg.get("semantic_cache_max_size", 128)),
        semantic_cache_threshold=float(cfg.get("semantic_cache_threshold", 0.92)),
        refiner_max_tokens=int(cfg.get("refiner_max_tokens", 512)),
        refiner_max_chars_per_chunk=int(cfg.get("refiner_max_chars_per_chunk", 800)),
        refiner_timeout=float(cfg.get("refiner_timeout", 30.0)),
    )


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
        description="Formatted RAG context block for LLM injection."
    )
    selected_hits: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Final selected chunks; consumed by two-stage fetch callers.",
    )


class RagDebugResponse(RagRunResponse):
    queries: list[str] = Field(
        default_factory=list, description="MQE-expanded queries."
    )
    merged_hits: list[dict[str, Any]] = Field(
        default_factory=list, description="Hits after RRF merge."
    )
    reranked_hits: list[dict[str, Any]] = Field(
        default_factory=list, description="Hits after cross-encoder rerank."
    )
    elapsed: dict[str, float] = Field(
        default_factory=dict, description="Per-step wall-clock seconds."
    )


class RagSearchRequest(BaseModel):
    """Backward-compat schema for POST /v1/search used by agent_rag.augment()."""

    query: str
    history_context: str = ""


class RagSearchResponse(BaseModel):
    """Backward-compat response for POST /v1/search.

    Extends the original {context: str} response with selected_hits so that
    agent_rag.augment() can populate self.last_reranked for two-stage fetch.
    """

    context: str
    selected_hits: list[dict[str, Any]] = Field(default_factory=list)
