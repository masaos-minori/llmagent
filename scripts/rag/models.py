"""rag/models.py
Typed DTO, config, and result dataclasses for the RAG and ingestion layer.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from rag.enums import LanguageCode, MqeStatus

# ── Config DTOs ────────────────────────────────────────────────────────────────


@dataclass
class MqeConfig:
    use_mqe: bool = True
    mqe_url: str = ""
    mqe_timeout: float = 5.0


@dataclass
class FusionConfig:
    rrf_k: int = 60


@dataclass
class RerankConfig:
    use_rerank: bool = True
    rerank_url: str = ""
    rerank_timeout: float = 10.0
    rerank_max_tokens: int = 512


@dataclass
class SearchConfig:
    use_search: bool = True
    embed_url: str = ""
    embed_timeout: float = 5.0
    top_k_search: int = 10
    rag_min_score: float = 0.0
    use_rrf: bool = True


@dataclass
class ChunkSplitterConfig:
    chunk_size: int = 500
    chunk_overlap: int = 50
    lang: str = "en"
    md_index_enable: bool = False


@dataclass
class IngesterConfig:
    embed_url: str = ""
    embed_timeout: float = 5.0
    embed_dimension: int = 768
    batch_size: int = 32


@dataclass
class PipelineConfig:
    mqe: MqeConfig = field(default_factory=MqeConfig)
    fusion: FusionConfig = field(default_factory=FusionConfig)
    rerank: RerankConfig = field(default_factory=RerankConfig)
    search: SearchConfig = field(default_factory=SearchConfig)


# ── Data DTOs ──────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class EmbeddingResponse:
    embedding: list[float]
    model: str | None = None


@dataclass(frozen=True)
class CrawlTarget:
    url: str
    lang: LanguageCode


@dataclass(frozen=True)
class ChunkDocument:
    url: str
    title: str
    lang: str
    content: str
    code_blocks: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ChunkRecord:
    chunk_id: str
    url: str
    title: str
    lang: str
    content: str
    embedding: list[float] = field(default_factory=list)


@dataclass(frozen=True)
class RegisteredDocument:
    url: str
    lang: str
    chunk_count: int


@dataclass(frozen=True)
class CacheEntry:
    embedding: list[float]
    context_str: str
    history_context: str = ""


@dataclass(frozen=True)
class TwoStageFetchResult:
    """Typed result capturing reranked hits with applied filter/dedup parameters."""

    hits: list[Any]  # list[RagHit] in-process; list[dict] HTTP mode
    min_score_applied: float  # rag_min_score used (0.0 = no score filter)
    max_chunks_per_doc: int  # per-doc dedup limit applied


# ── Result DTOs ────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class ExpandedQuerySet:
    status: MqeStatus
    queries: list[str]


@dataclass(frozen=True)
class SkipInfo:
    path: str
    reason: str


@dataclass(frozen=True)
class RagSearchRequest:
    query: str
    top_k: int = 5


@dataclass(frozen=True)
class RagSearchResult:
    query: str
    hits: list[object]  # list[RankedHit] — typed after Phase 3-1
    context_str: str


@dataclass(frozen=True)
class PipelineExecutionResult:
    success: bool
    processed: int
    failed: int
    errors: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class SearchDocsResult:
    query: str
    results: list[str]
    total: int


@dataclass(frozen=True)
class SanitizeResult:
    text: str
    was_sanitized: bool
    patterns_detected: list[str] = field(default_factory=list)


# ── Audit DTOs ─────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class AuditLogRecord:
    tool_name: str
    args_masked: str
    result_summary: str
    is_error: bool
    session_id: int | None


@dataclass(frozen=True)
class ApprovalDecision:
    approved: bool
    reason: str
    risk_level: str
