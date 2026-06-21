#!/usr/bin/env python3
"""rag/__init__.py — Re-export stubs for backward compatibility.

All existing imports through this module continue to work:
    from rag import PipelineConfig, EmbeddingResponse, TwoStageFetchResult
"""

from rag.models_audit import ApprovalDecision, AuditLogRecord
from rag.models_config import (
    ChunkSplitterConfig,
    FusionConfig,
    IngesterConfig,
    MqeConfig,
    PipelineConfig,
    RerankConfig,
    SearchConfig,
)
from rag.models_data import (
    CacheEntry,
    ChunkDocument,
    ChunkRecord,
    CrawlTarget,
    EmbeddingResponse,
    RegisteredDocument,
    TwoStageFetchResult,
)
from rag.models_result import (
    ExpandedQuerySet,
    PipelineExecutionResult,
    RagSearchRequest,
    RagSearchResult,
    SanitizeResult,
    SearchDocsResult,
    SkipInfo,
)

__all__ = [
    "ApprovalDecision",
    "AuditLogRecord",
    "CacheEntry",
    "ChunkDocument",
    "ChunkRecord",
    "ChunkSplitterConfig",
    "CrawlTarget",
    "EmbeddingResponse",
    "ExpandedQuerySet",
    "FusionConfig",
    "IngesterConfig",
    "MqeConfig",
    "PipelineConfig",
    "PipelineExecutionResult",
    "RagSearchRequest",
    "RagSearchResult",
    "RerankConfig",
    "RegisteredDocument",
    "SanitizeResult",
    "SearchConfig",
    "SearchDocsResult",
    "SkipInfo",
    "TwoStageFetchResult",
]
