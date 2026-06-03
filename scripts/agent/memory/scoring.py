"""agent/memory/scoring.py
ScoringPolicy dataclass for configurable memory retrieval scoring.

Injected into MemoryRetriever.__init__(policy=ScoringPolicy()) to allow
per-session or test-time override without changing module-level constants.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ScoringPolicy:
    """Tunable knobs for FTS5 + KNN memory scoring."""

    pin_boost: float = 0.3
    importance_boost_scale: float = 0.5
    recency_max_boost: float = 0.2
    context_match_boost: float = 0.1
    fts_candidate_limit: int = 50
    rrf_k: int = 60
    # memory_type-specific recency window
    semantic_recency_days: float = 30.0  # semantic: long-term, 30 days
    episodic_recency_days: float = 7.0   # episodic: short-term, 7 days
    # importance weight per memory_type
    semantic_importance_weight: float = 1.0
    episodic_importance_weight: float = 0.5
    # recency weight per memory_type
    semantic_recency_weight: float = 0.3  # semantic relies less on recency
    episodic_recency_weight: float = 1.0
