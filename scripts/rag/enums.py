"""rag/enums.py

StrEnum definitions for the RAG and ingestion layer.
"""

from __future__ import annotations

from enum import StrEnum


class LanguageCode(StrEnum):
    """Supported language codes for document processing."""

    EN = "en"
    JA = "ja"


class PipelineStageName(StrEnum):
    """Names of stages in the RAG pipeline execution flow."""

    MQE = "mqe"
    SEARCH = "search"
    FUSION = "fusion"
    RERANK = "rerank"
    AUGMENT = "augment"


class HitKind(StrEnum):
    """Classification of how a search hit was produced."""

    VECTOR = "vector"
    FTS = "fts"
    MERGED = "merged"
    RANKED = "ranked"


class SearchBackend(StrEnum):
    """Search backend type used for retrieval."""

    VECTOR = "vector"
    FTS = "fts"
    HYBRID = "hybrid"


class MqeStatus(StrEnum):
    """Status of the MQE (query expansion) phase."""

    EXPANDED = "expanded"
    DISABLED = "disabled"
    FAILED = "failed"
