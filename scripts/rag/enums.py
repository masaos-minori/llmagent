"""rag/enums.py

StrEnum definitions for the RAG and ingestion layer.
"""

from __future__ import annotations

from enum import StrEnum


class LanguageCode(StrEnum):
    EN = "en"
    JA = "ja"


class PipelineStageName(StrEnum):
    MQE = "mqe"
    SEARCH = "search"
    FUSION = "fusion"
    RERANK = "rerank"
    AUGMENT = "augment"


class HitKind(StrEnum):
    VECTOR = "vector"
    FTS = "fts"
    MERGED = "merged"
    RANKED = "ranked"


class SearchBackend(StrEnum):
    VECTOR = "vector"
    FTS = "fts"
    HYBRID = "hybrid"


class MqeStatus(StrEnum):
    EXPANDED = "expanded"
    DISABLED = "disabled"
    FAILED = "failed"
