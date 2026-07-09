#!/usr/bin/env python3
"""shared/token_estimation.py — Category-aware token estimation for LLM messages."""

import logging
from typing import cast

import orjson
from shared.types import LLMMessage, ToolCallDict

logger = logging.getLogger(__name__)

# Character-to-token ratios by content category.
# Values tuned for typical English text and JSON-structured tool calls.
RATIO_TEXT: float = 4.0
RATIO_TOOL_CALL: float = 2.5
RATIO_SYSTEM: float = 3.5


def estimate_tokens_for_text(
    text: str,
    breakdown_key: str,
    ratio: float,
    breakdown: dict[str, int],
) -> int:
    """Estimate tokens for a text category. Returns added total."""
    n = int(len(text) / ratio)
    breakdown[breakdown_key] += n
    return n


def estimate_tokens_for_assistant_with_tool_calls(
    text: str,
    tool_calls: list[ToolCallDict],
    breakdown: dict[str, int],
) -> int:
    """Estimate tokens for an assistant message that contains tool calls. Returns added total."""
    total = 0
    if text:
        n = estimate_tokens_for_text(text, "text", RATIO_TEXT, breakdown)
        total += n
    for tc in tool_calls:
        n = int(len(orjson.dumps(tc)) / RATIO_TOOL_CALL)
        breakdown["tool_calls"] += n
        total += n
    return total


def estimate_tokens(history: list[LLMMessage]) -> tuple[int, dict[str, int]]:
    """Estimate token count using category-aware character-to-token ratios.

    Returns ``(total_tokens, breakdown)`` where *breakdown* maps category names
    to estimated token counts.  Categories:

    - ``"text"`` — natural language content (user messages, assistant text, tool results)
    - ``"tool_calls"`` — serialised JSON from assistant tool_calls
    - ``"system"`` — system prompt content

    Ratios:

    ======  =====  ============================================
    Category   Ratio  Rationale
    ======  =====  ============================================
    text       4.0    English natural language ~4 chars/token
    tool_calls 2.5    JSON is verbose (braces, quotes, keywords)
    system     3.5    Mixed format: instructions + code snippets
    ======  =====  ============================================

    This replaces the legacy ``chars // 4`` fallback with a more accurate estimate
    that accounts for structured vs unstructured content.
    """
    total = 0
    breakdown: dict[str, int] = {"text": 0, "tool_calls": 0, "system": 0}
    for msg in history:
        role = msg.get("role", "")
        content_raw = msg.get("content")
        text = content_raw if isinstance(content_raw, str) else ""
        tool_calls_raw = msg.get("tool_calls")
        tool_calls: list[ToolCallDict] = cast(
            "list[ToolCallDict]", tool_calls_raw if tool_calls_raw is not None else []
        )

        if role == "system":
            if text:
                total += estimate_tokens_for_text(
                    text, "system", RATIO_SYSTEM, breakdown
                )
        elif role == "assistant" and tool_calls:
            total += estimate_tokens_for_assistant_with_tool_calls(
                text, tool_calls, breakdown
            )
        else:
            if text:
                total += estimate_tokens_for_text(text, "text", RATIO_TEXT, breakdown)
    return total, breakdown
