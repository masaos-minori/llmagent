"""agent/memory/enums.py

Domain enums for the persistent memory layer.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class MemoryType(StrEnum):
    SEMANTIC = "semantic"
    EPISODIC = "episodic"


class RetrievalMode(StrEnum):
    FTS = "fts"
    KNN = "knn"
    HYBRID = "hybrid"


class ExtractionDecision(StrEnum):
    ACCEPT = "accept"
    REJECT_TOO_SHORT = "reject_too_short"
    REJECT_NO_KEYWORDS = "reject_no_keywords"
    REJECT_DEDUP = "reject_dedup"


class DedupAction(StrEnum):
    SKIP_NEW = "skip_new"  # skip new entry when a near-duplicate already exists


@dataclass
class DedupPolicy:
    action: DedupAction = DedupAction.SKIP_NEW
    threshold: float = 0.3


DEDUP_THRESHOLDS: dict[str, float] = {
    "RULE": 0.98,
    "DECISION": 0.98,
    "FAILURE": 0.90,
    "CONVERSATION": 0.85,
}

RETENTION_DAYS: dict[str, int | None] = {
    "RULE": None,
    "DECISION": None,
    "FAILURE": 180,
    "CONVERSATION": 90,
}
