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
from datetime import UTC, datetime

from shared.types import LLMMessage

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

# Keywords that strongly suggest semantic (rule/policy/decision) content
_SEMANTIC_KEYWORDS = re.compile(
    r"\b(rule|policy|always|never|should|constraint|decided|decision"
    r"|guideline|standard|convention|principle|requirement|must not|must be"
    r"|best practice|invariant)\b",
    re.IGNORECASE,
)

# Keywords suggesting episodic (failure/fix) content
_EPISODIC_FAILURE_KEYWORDS = re.compile(
    r"\b(error|failed|exception|traceback|fixed|resolved|bug|workaround"
    r"|issue|crash|timeout|retry)\b",
    re.IGNORECASE,
)


def _now_iso() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _classify_content(
    content: str,
    semantic_hits: int,
    failure_hits: int,
) -> tuple[str, SourceType, list[str]] | None:
    """Return (memory_type, source_type, tags) classification, or None if not extractable."""
    if semantic_hits >= 2 or (semantic_hits >= 1 and len(content) >= 200):
        source = (
            SourceType.DECISION if "decided" in content.lower() else SourceType.RULE
        )
        return "semantic", source, ["auto-extracted", "semantic"]
    if failure_hits >= 1:
        return "episodic", SourceType.FAILURE, ["auto-extracted", "failure"]
    if len(content) >= MIN_CONTENT_CHARS * 2:
        return "episodic", SourceType.CONVERSATION, ["auto-extracted", "qa"]
    return None


def _make_entry(
    *,
    memory_type: str,
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


def _importance_from_content(content: str, is_semantic: bool) -> float:
    """Heuristic importance score based on length and keyword density."""
    base = 0.4
    length_bonus = min(len(content) / 2000.0, 0.3)
    if is_semantic:
        keyword_hits = len(_SEMANTIC_KEYWORDS.findall(content))
        keyword_bonus = min(keyword_hits * 0.05, 0.2)
        return min(base + length_bonus + keyword_bonus + 0.1, 1.0)
    # episodic: lower base importance
    return min(base + length_bonus, 0.8)


def _make_summary(content: str, max_chars: int = 120) -> str:
    """Return the first sentence or first max_chars characters."""
    first_line = content.split("\n", maxsplit=1)[0].strip()
    if len(first_line) <= max_chars:
        return first_line
    return content[:max_chars].rstrip() + "…"


def _try_extract_from_assistant(
    msg: LLMMessage,
    *,
    session_id: int | None,
    turn_id: str | None,
    project: str,
    repo: str,
    branch: str,
    max_content_chars: int,
    now: str,
) -> MemoryEntry | None:
    """Try to extract one MemoryEntry from an assistant message; return None when unqualified."""
    content_raw = msg.get("content") or ""
    content = str(content_raw).strip() if content_raw else ""
    if len(content) < MIN_CONTENT_CHARS:
        return None
    if max_content_chars > 0 and len(content) > max_content_chars:
        content = content[:max_content_chars]
    semantic_hits = len(_SEMANTIC_KEYWORDS.findall(content))
    failure_hits = len(_EPISODIC_FAILURE_KEYWORDS.findall(content))
    classification = _classify_content(content, semantic_hits, failure_hits)
    if classification is None:
        return None
    mem_type, source_type, tags = classification
    importance = _importance_from_content(content, is_semantic=(mem_type == "semantic"))
    return _make_entry(
        memory_type=mem_type,
        source_type=source_type,
        tags=tags,
        content=content,
        session_id=session_id,
        turn_id=turn_id,
        project=project,
        repo=repo,
        branch=branch,
        importance=importance,
        now=now,
    )


def _try_extract_from_user(
    msg: LLMMessage,
    *,
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
    content_raw = msg.get("content") or ""
    content = str(content_raw).strip() if content_raw else ""
    if len(content) < MIN_USER_CONTENT_CHARS:
        return None
    if not _SEMANTIC_KEYWORDS.search(content):
        return None
    importance = _importance_from_content(content, is_semantic=True)
    return _make_entry(
        memory_type="semantic",
        source_type=SourceType.RULE,
        tags=["auto-extracted", "user-rule"],
        content=content,
        session_id=session_id,
        turn_id=turn_id,
        project=project,
        repo=repo,
        branch=branch,
        importance=importance,
        now=now,
    )


def extract_memories(
    history: list[LLMMessage],
    session_id: int | None = None,
    turn_id: str | None = None,
    project: str = "",
    repo: str = "",
    branch: str = "",
    max_content_chars: int = 500,
) -> list[MemoryEntry]:
    """Extract MemoryEntry candidates from a conversation history list.

    Runs synchronously; called at Stop time before HistoryManager compression.
    Returns an empty list when the conversation is too short or has no substance.
    """
    non_system = [m for m in history if m.get("role") != "system"]
    if len(non_system) < MIN_TURNS:
        logger.debug(
            f"extract_memories: skipping — only {len(non_system)} non-system turns",
        )
        return []

    candidates: list[MemoryEntry] = []
    now = _now_iso()
    for msg in history:
        role = msg.get("role")
        if role == "assistant":
            entry = _try_extract_from_assistant(
                msg,
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
    entries = candidates[:MAX_ENTRIES]

    logger.debug(
        f"extract_memories: extracted {len(entries)} entries"
        f" from {len(history)} history messages",
    )
    return entries
