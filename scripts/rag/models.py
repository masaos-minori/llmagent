#!/usr/bin/env python3
"""rag/models.py — Re-export stub for backward compatibility.

Config DTOs:        rag/models_config.py
Data DTOs:          rag/models_data.py
Result DTOs:        rag/models_result.py
Audit DTOs:         rag/models_audit.py

All existing imports through this module continue to work:
    from rag.models import PipelineConfig, EmbeddingResponse, TwoStageFetchResult
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
