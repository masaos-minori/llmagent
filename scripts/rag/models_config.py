#!/usr/bin/env python3
"""rag/models_config.py

Config DTOs for the RAG pipeline and ingestion layers.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class MqeConfig:
    """Configuration for MQE (query expansion) feature."""

    use_mqe: bool = True
    mqe_url: str = ""
    mqe_timeout: float = 5.0


@dataclass
class FusionConfig:
    """Configuration for result fusion (RRF ranking)."""

    rrf_k: int = 60


@dataclass
class RerankConfig:
    """Configuration for document reranking."""

    use_rerank: bool = True
    rerank_url: str = ""
    rerank_timeout: float = 10.0
    rerank_max_tokens: int = 512


@dataclass
class SearchConfig:
    """Configuration for semantic search."""

    use_search: bool = True
    embed_url: str = ""
    embed_timeout: float = 5.0
    top_k_search: int = 10
    rag_min_score: float = 0.0
    use_rrf: bool = True


@dataclass
class ChunkSplitterConfig:
    """Configuration for text chunk splitting during ingestion."""

    chunk_size: int = 500
    chunk_overlap: int = 50
    lang: str = "en"
    md_index_enable: bool = False


@dataclass
class IngesterConfig:
    """Configuration for the RAG ingestion layer."""

    embed_url: str = ""
    embed_timeout: float = 5.0
    batch_size: int = 32


@dataclass
class PipelineConfig:
    """Top-level configuration for the RAG pipeline."""

    mqe: MqeConfig = field(default_factory=MqeConfig)
    fusion: FusionConfig = field(default_factory=FusionConfig)
    rerank: RerankConfig = field(default_factory=RerankConfig)
    search: SearchConfig = field(default_factory=SearchConfig)
