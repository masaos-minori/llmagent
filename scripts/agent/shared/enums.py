"""agent/shared/enums.py
Cross-cutting StrEnum definitions for the agent layer.
"""

from __future__ import annotations

from enum import StrEnum


class ExtractionDecision(StrEnum):
    """Outcome of a memory extraction evaluation."""

    ACCEPT = "accept"
    REJECT_TOO_SHORT = "reject_too_short"
    REJECT_NO_KEYWORDS = "reject_no_keywords"
    REJECT_DEDUP = "reject_dedup"


class RetrievalMode(StrEnum):
    """Memory retrieval strategy."""

    FTS = "fts"
    KNN = "knn"
    HYBRID = "hybrid"


class ToolSafetyTier(StrEnum):
    """Risk classification for tool calls."""

    READ_ONLY = "READ_ONLY"
    WRITE_SAFE = "WRITE_SAFE"
    DESTRUCTIVE = "DESTRUCTIVE"
    SHELL = "SHELL"


class WorkflowStage(StrEnum):
    """Stage of a document ingestion workflow."""

    CRAWL = "crawl"
    SPLIT = "split"
    INGEST = "ingest"
    DONE = "done"
