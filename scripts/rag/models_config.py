#!/usr/bin/env python3
"""scripts/rag/models_config.py

Config DTOs for the RAG pipeline and ingestion layers.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RagConfigImpl:
    """Concrete implementation of RagConfig Protocol."""

    semantic_cache_max_size: int
    semantic_cache_threshold: float
    use_mqe: bool
    top_k_search: int
    use_rerank: bool
    rag_top_k: int
    max_chunks_per_doc: int
    top_k_rerank: int
    rag_min_score: float
    use_rrf: bool
    rrf_k: int
    use_search: bool
    rag_service_url: str
    rag_auth_token: str | None
    use_refiner: bool
    refiner_max_tokens: int
    refiner_max_chars_per_chunk: int
    refiner_timeout: float
    use_semantic_cache: bool
    llm_url: str
    embed_url: str
    rag_db_path: str
    sqlite_vec_so: str
    sqlite_timeout: int
    sqlite_busy_timeout_ms: int
    embed_retry: int
    embed_workers: int
    rag_pipeline_service_url: str | None
    mqe_prompt_template: str
    mqe_n_queries: int
    rerank_prompt_template: str
