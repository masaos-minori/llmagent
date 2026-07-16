#!/usr/bin/env python3
"""agent/memory/extract.py

Rule-based extraction of MemoryEntry candidates from conversation history.

Semantic memory triggers:
  - assistant messages containing decision/rule/policy keywords
  - long assistant messages (>= MIN_CONTENT_CHARS) about policies or constraints

Episodic memory triggers:
  - Q&A pairs where the assistant gives a substantial answer (>= MIN_CONTENT_CHARS)
  - failure/fix patterns (keywords: error, failed, fixed, resolved)

Guards:
  - Skip conversations shorter than MIN_TURNS
  - Cap extraction at MAX_ENTRIES per session to avoid noise accumulation
  - Assign importance based on message length and keyword density
"""

from __future__ import annotations

import logging
import re
import uuid
from dataclasses import dataclass

from shared.json_utils import now_iso

from agent.memory.enums import MemoryType
from agent.memory.models import HistoryMessage
from agent.memory.types import MemoryEntry, SourceType

logger = logging.getLogger(__name__)

# Minimum assistant message character count to consider for extraction
MIN_CONTENT_CHARS = 80

# Minimum user message character count to consider for rule extraction
MIN_USER_CONTENT_CHARS = 60

# Minimum number of non-system turns for extraction to run
MIN_TURNS = 2

# Maximum entries extracted per on_session_stop call
MAX_ENTRIES = 20

# Semantic classification thresholds
SEMANTIC_HITS_REQUIRED_STRONG = 2
SEMANTIC_CONTENT_THRESHOLD = 200

# Importance scoring divisor for length-based bonus
IMPORTANCE_LENGTH_DIVISOR = 2000.0

# Keywords indicating a design decision was made
_DECISION_KEYWORDS = re.compile(
    r"\b(rationale|trade.off|chose|opted|decided|decision|tradeoff)\b",
    re.IGNORECASE,
)

# Keywords that strongly suggest semantic (rule/policy/decision) content
_SEMANTIC_KEYWORDS = re.compile(
    r"\b(rule|policy|always|never|should|constraint|decided|decision"
    r"|guideline|standard|convention|principle|requirement|must not|must be"
    r"|best practice|invariant|mandatory|enforce|prohibit|forbidden|must)\b",
    re.IGNORECASE,
)

# Keywords suggesting episodic (failure/fix) content
_EPISODIC_FAILURE_KEYWORDS = re.compile(
    r"\b(error|failed|exception|traceback|fixed|resolved|bug|workaround"
    r"|issue|crash|timeout|retry|root.cause|mitigation|regression|deadlock"
    r"|memory.leak)\b",
    re.IGNORECASE,
)


@dataclass
class ExtractionPolicy:
    """Configurable thresholds for memory extraction.

    Pass to extract_memories() to override module-level defaults.
    """

    min_content_chars: int = MIN_CONTENT_CHARS
    min_user_content_chars: int = MIN_USER_CONTENT_CHARS
    min_turns: int = MIN_TURNS
    max_entries: int = MAX_ENTRIES


def _classify_content(
    content: str,
    semantic_hits: int,
    failure_hits: int,
) -> tuple[MemoryType, SourceType, list[str]] | None:
    """Return (memory_type, source_type, tags) classification, or None if not extractable."""
    if semantic_hits >= SEMANTIC_HITS_REQUIRED_STRONG or (
        semantic_hits >= 1 and len(content) >= SEMANTIC_CONTENT_THRESHOLD
    ):
        if _DECISION_KEYWORDS.search(content) and _SEMANTIC_KEYWORDS.search(content):
            return (
                MemoryType.SEMANTIC,
                SourceType.DECISION,
                ["auto-extracted", "decision"],
            )
        return MemoryType.SEMANTIC, SourceType.RULE, ["auto-extracted", "semantic"]
    if failure_hits >= 1:
        return MemoryType.EPISODIC, SourceType.FAILURE, ["auto-extracted", "failure"]
    if len(content) >= MIN_CONTENT_CHARS * 2:
        return MemoryType.EPISODIC, SourceType.CONVERSATION, ["auto-extracted", "qa"]
    return None


def _make_entry(
    *,
    memory_type: MemoryType,
    source_type: SourceType,
    tags: list[str],
    content: str,
    session_id: int | None,
    turn_id: str | None,
    project: str,
    repo: str,
    branch: str,
    importance: float,
    now: str,
) -> MemoryEntry:
    """Build a MemoryEntry with a new UUID and computed summary."""
    return MemoryEntry(
        memory_id=str(uuid.uuid4()),
        memory_type=memory_type,
        source_type=source_type,
        session_id=session_id,
        turn_id=turn_id,
        project=project,
        repo=repo,
        branch=branch,
        content=content,
        summary=_make_summary(content),
        tags=tags,
        importance=importance,
        pinned=False,
        created_at=now,
        updated_at=now,
    )


def _make_entry_with_importance(
    *,
    memory_type: MemoryType,
    source_type: SourceType,
    tags: list[str],
    content: str,
    importance: float,
    session_id: int | None,
    turn_id: str | None,
    project: str,
    repo: str,
    branch: str,
    now: str,
) -> MemoryEntry:
    """Build a MemoryEntry with pre-computed importance score."""
    return MemoryEntry(
        memory_id=str(uuid.uuid4()),
        memory_type=memory_type,
        source_type=source_type,
        session_id=session_id,
        turn_id=turn_id,
        project=project,
        repo=repo,
        branch=branch,
        content=content,
        summary=_make_summary(content),
        tags=tags,
        importance=importance,
        pinned=False,
        created_at=now,
        updated_at=now,
    )


def _importance_from_content(
    content: str, is_semantic: bool, source_type: SourceType | None = None
) -> float:
    """Heuristic importance score based on length, keyword density, and source type."""
    length_bonus = min(len(content) / IMPORTANCE_LENGTH_DIVISOR, 0.3)
    if is_semantic:
        keyword_hits = len(_SEMANTIC_KEYWORDS.findall(content))
        keyword_bonus = min(keyword_hits * 0.05, 0.2)
        base = _semantic_base(source_type)
        return min(base + length_bonus + keyword_bonus + 0.1, 1.0)
    # episodic: base by source type
    base = _episodic_base(source_type)
    return min(base + length_bonus, 0.8)


def _semantic_base(source_type: SourceType | None) -> float:
    """Return base importance for semantic memory type."""
    if source_type == SourceType.DECISION:
        return 0.55
    return 0.4


def _episodic_base(source_type: SourceType | None) -> float:
    """Return base importance for episodic memory type."""
    if source_type == SourceType.FAILURE:
        return 0.45
    return 0.4


def _make_summary(content: str, max_chars: int = 120) -> str:
    """Return the first sentence or first max_chars characters."""
    first_line = content.split("\n", maxsplit=1)[0].strip()
    if len(first_line) <= max_chars:
        return first_line
    return content[:max_chars].rstrip() + "\u2026"


def _try_extract_from_assistant(
    msg: HistoryMessage,
    *,
    policy: ExtractionPolicy,
    session_id: int | None,
    turn_id: str | None,
    project: str,
    repo: str,
    branch: str,
    max_content_chars: int,
    now: str,
) -> MemoryEntry | None:
    """Try to extract one MemoryEntry from an assistant message; return None when unqualified."""
    content = msg.content.strip()
    if len(content) < policy.min_content_chars:
        return None
    if max_content_chars > 0 and len(content) > max_content_chars:
        content = content[:max_content_chars]
    semantic_hits = len(_SEMANTIC_KEYWORDS.findall(content))
    failure_hits = len(_EPISODIC_FAILURE_KEYWORDS.findall(content))
    classification = _classify_content(content, semantic_hits, failure_hits)
    if classification is None:
        return None
    mem_type, source_type, tags = classification
    importance = _importance_from_content(
        content, is_semantic=(mem_type == MemoryType.SEMANTIC), source_type=source_type
    )
    return _make_entry_with_importance(
        memory_type=mem_type,
        source_type=source_type,
        tags=tags,
        content=content,
        importance=importance,
        session_id=session_id,
        turn_id=turn_id,
        project=project,
        repo=repo,
        branch=branch,
        now=now,
    )


def _try_extract_from_user(
    msg: HistoryMessage,
    *,
    policy: ExtractionPolicy,
    session_id: int | None,
    turn_id: str | None,
    project: str,
    repo: str,
    branch: str,
    now: str,
) -> MemoryEntry | None:
    """Extract a MemoryEntry from a user message containing explicit rules or constraints.

    Short messages and messages without rule/policy keywords are ignored.
    """
    content = msg.content.strip()
    if len(content) < policy.min_user_content_chars:
        return None
    if not _SEMANTIC_KEYWORDS.search(content):
        return None
    importance = _importance_from_content(content, is_semantic=True)
    return _make_entry_with_importance(
        memory_type=MemoryType.SEMANTIC,
        source_type=SourceType.RULE,
        tags=["auto-extracted", "user-rule"],
        content=content,
        importance=importance,
        session_id=session_id,
        turn_id=turn_id,
        project=project,
        repo=repo,
        branch=branch,
        now=now,
    )


def extract_memories(
    history: list[HistoryMessage],
    session_id: int | None = None,
    turn_id: str | None = None,
    project: str = "",
    repo: str = "",
    branch: str = "",
    max_content_chars: int = 500,
    policy: ExtractionPolicy | None = None,
) -> list[MemoryEntry]:
    """Extract MemoryEntry candidates from a conversation history list.

    Runs synchronously; called at Stop time before HistoryManager compression.
    Returns an empty list when the conversation is too short or has no substance.
    Pass a custom ExtractionPolicy to override extraction thresholds.
    """
    _policy = policy or ExtractionPolicy()
    non_system = [m for m in history if m.role != "system"]
    if len(non_system) < _policy.min_turns:
        logger.debug(
            "extract_memories: skipping — only %s non-system turns",
            len(non_system),
        )
        return []

    candidates: list[MemoryEntry] = []
    now = now_iso()
    for msg in history:
        role = msg.role
        if role == "assistant":
            entry = _try_extract_from_assistant(
                msg,
                policy=_policy,
                session_id=session_id,
                turn_id=turn_id,
                project=project,
                repo=repo,
                branch=branch,
                max_content_chars=max_content_chars,
                now=now,
            )
        elif role == "user":
            entry = _try_extract_from_user(
                msg,
                policy=_policy,
                session_id=session_id,
                turn_id=turn_id,
                project=project,
                repo=repo,
                branch=branch,
                now=now,
            )
        else:
            entry = None
        if entry is not None:
            candidates.append(entry)

    candidates.sort(key=lambda e: e.importance, reverse=True)
    entries = candidates[: _policy.max_entries]

    logger.debug(
        "extract_memories: extracted %s entries from %s history messages",
        len(entries),
        len(history),
    )
    return entries
