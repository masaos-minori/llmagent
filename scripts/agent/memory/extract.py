#!/usr/bin/env python3
"""
agent/memory/extract.py
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

from agent.memory.types import MemoryEntry

logger = logging.getLogger(__name__)

# Minimum assistant message character count to consider for extraction
MIN_CONTENT_CHARS = 80

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


def _importance_from_content(content: str, is_semantic: bool) -> float:
    """Heuristic importance score based on length and keyword density."""
    base = 0.4
    length_bonus = min(len(content) / 2000.0, 0.3)
    if is_semantic:
        keyword_hits = len(_SEMANTIC_KEYWORDS.findall(content))
        keyword_bonus = min(keyword_hits * 0.05, 0.2)
        return min(base + length_bonus + keyword_bonus + 0.1, 1.0)
    else:
        # episodic: lower base importance
        return min(base + length_bonus, 0.8)


def _make_summary(content: str, max_chars: int = 120) -> str:
    """Return the first sentence or first max_chars characters."""
    first_line = content.split("\n")[0].strip()
    if len(first_line) <= max_chars:
        return first_line
    return content[:max_chars].rstrip() + "…"


def extract_memories(
    history: list[LLMMessage],
    session_id: int | None = None,
    turn_id: str | None = None,
    project: str = "",
    repo: str = "",
    branch: str = "",
) -> list[MemoryEntry]:
    """Extract MemoryEntry candidates from a conversation history list.

    Runs synchronously; called at Stop time before HistoryManager compression.
    Returns an empty list when the conversation is too short or has no substance.
    """
    # Filter to non-system messages for turn count check
    non_system = [m for m in history if m.get("role") != "system"]
    if len(non_system) < MIN_TURNS:
        logger.debug(
            f"extract_memories: skipping — only {len(non_system)} non-system turns"
        )
        return []

    entries: list[MemoryEntry] = []
    now = _now_iso()

    # Collect assistant messages paired with the preceding user message
    i = 0
    while i < len(history) and len(entries) < MAX_ENTRIES:
        msg = history[i]
        role = msg.get("role", "")
        content_raw = msg.get("content") or ""
        content = str(content_raw).strip() if content_raw else ""

        if role == "assistant" and len(content) >= MIN_CONTENT_CHARS:
            semantic_hits = len(_SEMANTIC_KEYWORDS.findall(content))
            failure_hits = len(_EPISODIC_FAILURE_KEYWORDS.findall(content))

            # Semantic: has rule/policy keywords and is substantive
            if semantic_hits >= 2 or (semantic_hits >= 1 and len(content) >= 200):
                importance = _importance_from_content(content, is_semantic=True)
                entries.append(
                    MemoryEntry(
                        memory_id=str(uuid.uuid4()),
                        memory_type="semantic",
                        source_type="decision"
                        if "decided" in content.lower()
                        else "rule",
                        session_id=session_id,
                        turn_id=turn_id,
                        project=project,
                        repo=repo,
                        branch=branch,
                        content=content,
                        summary=_make_summary(content),
                        tags=["auto-extracted", "semantic"],
                        importance=importance,
                        pinned=False,
                        created_at=now,
                        updated_at=now,
                    )
                )

            # Episodic with failure/fix pattern
            elif failure_hits >= 1 and len(content) >= MIN_CONTENT_CHARS:
                importance = _importance_from_content(content, is_semantic=False)
                entries.append(
                    MemoryEntry(
                        memory_id=str(uuid.uuid4()),
                        memory_type="episodic",
                        source_type="failure",
                        session_id=session_id,
                        turn_id=turn_id,
                        project=project,
                        repo=repo,
                        branch=branch,
                        content=content,
                        summary=_make_summary(content),
                        tags=["auto-extracted", "failure"],
                        importance=importance,
                        pinned=False,
                        created_at=now,
                        updated_at=now,
                    )
                )

            # Episodic Q&A: substantial assistant answer
            elif len(content) >= MIN_CONTENT_CHARS * 2:
                importance = _importance_from_content(content, is_semantic=False)
                entries.append(
                    MemoryEntry(
                        memory_id=str(uuid.uuid4()),
                        memory_type="episodic",
                        source_type="conversation",
                        session_id=session_id,
                        turn_id=turn_id,
                        project=project,
                        repo=repo,
                        branch=branch,
                        content=content,
                        summary=_make_summary(content),
                        tags=["auto-extracted", "qa"],
                        importance=importance,
                        pinned=False,
                        created_at=now,
                        updated_at=now,
                    )
                )

        i += 1

    logger.debug(
        f"extract_memories: extracted {len(entries)} entries"
        f" from {len(history)} history messages"
    )
    return entries
