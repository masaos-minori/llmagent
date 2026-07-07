"""scoring.py — Memory entry scoring functions for FTS5 search results."""

from __future__ import annotations

import datetime

from agent.memory.enums import MemoryType
from agent.memory.exceptions import MemorySchemaError
from agent.memory.types import MemoryEntry

# Boost amounts
_PIN_BOOST = 0.3
_IMPORTANCE_BOOST_SCALE = 0.5  # importance (0–1) x scale
_RECENCY_MAX_BOOST = 0.2  # applied to entries within 7 days
_CONTEXT_MATCH_BOOST = 0.1

# Seconds per day
_SECS_PER_DAY = 86_400.0
_RECENCY_DAYS = 7.0


def recency_boost(created_at: str, recency_days: float = _RECENCY_DAYS) -> float:
    """Return 0.0–_RECENCY_MAX_BOOST based on age in days (newer = higher)."""
    try:
        dt = datetime.datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        now = datetime.datetime.now(datetime.UTC)
        age_days = (now - dt).total_seconds() / _SECS_PER_DAY
        if age_days >= recency_days:
            return 0.0
        return _RECENCY_MAX_BOOST * (1.0 - age_days / recency_days)
    except (ValueError, OverflowError) as e:
        raise MemorySchemaError(
            f"recency_boost: invalid created_at {created_at!r}: {e}"
        ) from e


def context_boost(
    entry: MemoryEntry, project: str, repo: str, branch: str = ""
) -> float:
    """Return a context match boost based on branch, project, or repo match."""
    if branch and entry.branch == branch:
        return _CONTEXT_MATCH_BOOST + 0.05
    if (project and entry.project == project) or (repo and entry.repo == repo):
        return _CONTEXT_MATCH_BOOST
    return 0.0


def score(
    bm25_rank: float,
    entry: MemoryEntry,
    project: str,
    repo: str,
    recency_days: float = _RECENCY_DAYS,
    branch: str = "",
) -> float:
    """Combined score; higher is better.

    Scoring formula:
      score = -bm25_rank                  # BM25 from FTS5 (negative = higher is better)
            + importance_boost             # 0.0–0.5 based on entry.importance
            + pin_boost                    # 0.3 when pinned
            + recency_decay                # 0.0–0.2 based on age (newer = higher)
            + context_match                # 0.1 when project/repo match

    semantic  : importance_weight = 1.0, recency_weight = 0.5
    episodic  : importance_weight = 0.5, recency_weight = 1.0
    """
    importance_w = 1.0 if entry.memory_type == MemoryType.SEMANTIC else 0.5
    recency_w = 0.5 if entry.memory_type == MemoryType.SEMANTIC else 1.0

    return (
        -bm25_rank  # FTS5 rank is negative (lower magnitude = better match)
        + importance_w * entry.importance * _IMPORTANCE_BOOST_SCALE
        + (_PIN_BOOST if entry.pinned else 0.0)
        + recency_w * recency_boost(entry.created_at, recency_days)
        + context_boost(entry, project, repo, branch)
    )
