#!/usr/bin/env python3
"""scripts/shared/token_estimation.py — Category-aware token estimation for LLM messages."""

import logging
from typing import cast

from shared.json_utils import tool_call_serialized_length
from shared.types import LLMMessage, ToolCallDict

logger = logging.getLogger(__name__)

# Character-to-token ratios by content category.
# Values tuned for typical English text and JSON-structured tool calls.
RATIO_TEXT: float = 4.0
RATIO_TOOL_CALL: float = 2.5
RATIO_SYSTEM: float = 3.5


from mutmut.mutation.trampoline import wrap_in_trampoline as _mutmut_mutated, MutantDict
mutants_x_estimate_tokens_for_text__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x_estimate_tokens_for_text__mutmut)
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


def x_estimate_tokens_for_text__mutmut_orig(
    text: str,
    breakdown_key: str,
    ratio: float,
    breakdown: dict[str, int],
) -> int:
    """Estimate tokens for a text category. Returns added total."""
    n = int(len(text) / ratio)
    breakdown[breakdown_key] += n
    return n


def x_estimate_tokens_for_text__mutmut_1(
    text: str,
    breakdown_key: str,
    ratio: float,
    breakdown: dict[str, int],
) -> int:
    """Estimate tokens for a text category. Returns added total."""
    n = None
    breakdown[breakdown_key] += n
    return n


def x_estimate_tokens_for_text__mutmut_2(
    text: str,
    breakdown_key: str,
    ratio: float,
    breakdown: dict[str, int],
) -> int:
    """Estimate tokens for a text category. Returns added total."""
    n = int(None)
    breakdown[breakdown_key] += n
    return n


def x_estimate_tokens_for_text__mutmut_3(
    text: str,
    breakdown_key: str,
    ratio: float,
    breakdown: dict[str, int],
) -> int:
    """Estimate tokens for a text category. Returns added total."""
    n = int(len(text) * ratio)
    breakdown[breakdown_key] += n
    return n


def x_estimate_tokens_for_text__mutmut_4(
    text: str,
    breakdown_key: str,
    ratio: float,
    breakdown: dict[str, int],
) -> int:
    """Estimate tokens for a text category. Returns added total."""
    n = int(len(text) / ratio)
    breakdown[breakdown_key] = n
    return n


def x_estimate_tokens_for_text__mutmut_5(
    text: str,
    breakdown_key: str,
    ratio: float,
    breakdown: dict[str, int],
) -> int:
    """Estimate tokens for a text category. Returns added total."""
    n = int(len(text) / ratio)
    breakdown[breakdown_key] -= n
    return n

mutants_x_estimate_tokens_for_text__mutmut['_mutmut_orig'] = x_estimate_tokens_for_text__mutmut_orig # type: ignore # mutmut generated
mutants_x_estimate_tokens_for_text__mutmut['x_estimate_tokens_for_text__mutmut_1'] = x_estimate_tokens_for_text__mutmut_1 # type: ignore # mutmut generated
mutants_x_estimate_tokens_for_text__mutmut['x_estimate_tokens_for_text__mutmut_2'] = x_estimate_tokens_for_text__mutmut_2 # type: ignore # mutmut generated
mutants_x_estimate_tokens_for_text__mutmut['x_estimate_tokens_for_text__mutmut_3'] = x_estimate_tokens_for_text__mutmut_3 # type: ignore # mutmut generated
mutants_x_estimate_tokens_for_text__mutmut['x_estimate_tokens_for_text__mutmut_4'] = x_estimate_tokens_for_text__mutmut_4 # type: ignore # mutmut generated
mutants_x_estimate_tokens_for_text__mutmut['x_estimate_tokens_for_text__mutmut_5'] = x_estimate_tokens_for_text__mutmut_5 # type: ignore # mutmut generated
mutants_x_estimate_tokens_for_assistant_with_tool_calls__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x_estimate_tokens_for_assistant_with_tool_calls__mutmut)
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
        n = int(tool_call_serialized_length(tc) / RATIO_TOOL_CALL)
        breakdown["tool_calls"] += n
        total += n
    return total


def x_estimate_tokens_for_assistant_with_tool_calls__mutmut_orig(
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
        n = int(tool_call_serialized_length(tc) / RATIO_TOOL_CALL)
        breakdown["tool_calls"] += n
        total += n
    return total


def x_estimate_tokens_for_assistant_with_tool_calls__mutmut_1(
    text: str,
    tool_calls: list[ToolCallDict],
    breakdown: dict[str, int],
) -> int:
    """Estimate tokens for an assistant message that contains tool calls. Returns added total."""
    total = None
    if text:
        n = estimate_tokens_for_text(text, "text", RATIO_TEXT, breakdown)
        total += n
    for tc in tool_calls:
        n = int(tool_call_serialized_length(tc) / RATIO_TOOL_CALL)
        breakdown["tool_calls"] += n
        total += n
    return total


def x_estimate_tokens_for_assistant_with_tool_calls__mutmut_2(
    text: str,
    tool_calls: list[ToolCallDict],
    breakdown: dict[str, int],
) -> int:
    """Estimate tokens for an assistant message that contains tool calls. Returns added total."""
    total = 1
    if text:
        n = estimate_tokens_for_text(text, "text", RATIO_TEXT, breakdown)
        total += n
    for tc in tool_calls:
        n = int(tool_call_serialized_length(tc) / RATIO_TOOL_CALL)
        breakdown["tool_calls"] += n
        total += n
    return total


def x_estimate_tokens_for_assistant_with_tool_calls__mutmut_3(
    text: str,
    tool_calls: list[ToolCallDict],
    breakdown: dict[str, int],
) -> int:
    """Estimate tokens for an assistant message that contains tool calls. Returns added total."""
    total = 0
    if text:
        n = None
        total += n
    for tc in tool_calls:
        n = int(tool_call_serialized_length(tc) / RATIO_TOOL_CALL)
        breakdown["tool_calls"] += n
        total += n
    return total


def x_estimate_tokens_for_assistant_with_tool_calls__mutmut_4(
    text: str,
    tool_calls: list[ToolCallDict],
    breakdown: dict[str, int],
) -> int:
    """Estimate tokens for an assistant message that contains tool calls. Returns added total."""
    total = 0
    if text:
        n = estimate_tokens_for_text(None, "text", RATIO_TEXT, breakdown)
        total += n
    for tc in tool_calls:
        n = int(tool_call_serialized_length(tc) / RATIO_TOOL_CALL)
        breakdown["tool_calls"] += n
        total += n
    return total


def x_estimate_tokens_for_assistant_with_tool_calls__mutmut_5(
    text: str,
    tool_calls: list[ToolCallDict],
    breakdown: dict[str, int],
) -> int:
    """Estimate tokens for an assistant message that contains tool calls. Returns added total."""
    total = 0
    if text:
        n = estimate_tokens_for_text(text, None, RATIO_TEXT, breakdown)
        total += n
    for tc in tool_calls:
        n = int(tool_call_serialized_length(tc) / RATIO_TOOL_CALL)
        breakdown["tool_calls"] += n
        total += n
    return total


def x_estimate_tokens_for_assistant_with_tool_calls__mutmut_6(
    text: str,
    tool_calls: list[ToolCallDict],
    breakdown: dict[str, int],
) -> int:
    """Estimate tokens for an assistant message that contains tool calls. Returns added total."""
    total = 0
    if text:
        n = estimate_tokens_for_text(text, "text", None, breakdown)
        total += n
    for tc in tool_calls:
        n = int(tool_call_serialized_length(tc) / RATIO_TOOL_CALL)
        breakdown["tool_calls"] += n
        total += n
    return total


def x_estimate_tokens_for_assistant_with_tool_calls__mutmut_7(
    text: str,
    tool_calls: list[ToolCallDict],
    breakdown: dict[str, int],
) -> int:
    """Estimate tokens for an assistant message that contains tool calls. Returns added total."""
    total = 0
    if text:
        n = estimate_tokens_for_text(text, "text", RATIO_TEXT, None)
        total += n
    for tc in tool_calls:
        n = int(tool_call_serialized_length(tc) / RATIO_TOOL_CALL)
        breakdown["tool_calls"] += n
        total += n
    return total


def x_estimate_tokens_for_assistant_with_tool_calls__mutmut_8(
    text: str,
    tool_calls: list[ToolCallDict],
    breakdown: dict[str, int],
) -> int:
    """Estimate tokens for an assistant message that contains tool calls. Returns added total."""
    total = 0
    if text:
        n = estimate_tokens_for_text("text", RATIO_TEXT, breakdown)
        total += n
    for tc in tool_calls:
        n = int(tool_call_serialized_length(tc) / RATIO_TOOL_CALL)
        breakdown["tool_calls"] += n
        total += n
    return total


def x_estimate_tokens_for_assistant_with_tool_calls__mutmut_9(
    text: str,
    tool_calls: list[ToolCallDict],
    breakdown: dict[str, int],
) -> int:
    """Estimate tokens for an assistant message that contains tool calls. Returns added total."""
    total = 0
    if text:
        n = estimate_tokens_for_text(text, RATIO_TEXT, breakdown)
        total += n
    for tc in tool_calls:
        n = int(tool_call_serialized_length(tc) / RATIO_TOOL_CALL)
        breakdown["tool_calls"] += n
        total += n
    return total


def x_estimate_tokens_for_assistant_with_tool_calls__mutmut_10(
    text: str,
    tool_calls: list[ToolCallDict],
    breakdown: dict[str, int],
) -> int:
    """Estimate tokens for an assistant message that contains tool calls. Returns added total."""
    total = 0
    if text:
        n = estimate_tokens_for_text(text, "text", breakdown)
        total += n
    for tc in tool_calls:
        n = int(tool_call_serialized_length(tc) / RATIO_TOOL_CALL)
        breakdown["tool_calls"] += n
        total += n
    return total


def x_estimate_tokens_for_assistant_with_tool_calls__mutmut_11(
    text: str,
    tool_calls: list[ToolCallDict],
    breakdown: dict[str, int],
) -> int:
    """Estimate tokens for an assistant message that contains tool calls. Returns added total."""
    total = 0
    if text:
        n = estimate_tokens_for_text(text, "text", RATIO_TEXT, )
        total += n
    for tc in tool_calls:
        n = int(tool_call_serialized_length(tc) / RATIO_TOOL_CALL)
        breakdown["tool_calls"] += n
        total += n
    return total


def x_estimate_tokens_for_assistant_with_tool_calls__mutmut_12(
    text: str,
    tool_calls: list[ToolCallDict],
    breakdown: dict[str, int],
) -> int:
    """Estimate tokens for an assistant message that contains tool calls. Returns added total."""
    total = 0
    if text:
        n = estimate_tokens_for_text(text, "XXtextXX", RATIO_TEXT, breakdown)
        total += n
    for tc in tool_calls:
        n = int(tool_call_serialized_length(tc) / RATIO_TOOL_CALL)
        breakdown["tool_calls"] += n
        total += n
    return total


def x_estimate_tokens_for_assistant_with_tool_calls__mutmut_13(
    text: str,
    tool_calls: list[ToolCallDict],
    breakdown: dict[str, int],
) -> int:
    """Estimate tokens for an assistant message that contains tool calls. Returns added total."""
    total = 0
    if text:
        n = estimate_tokens_for_text(text, "TEXT", RATIO_TEXT, breakdown)
        total += n
    for tc in tool_calls:
        n = int(tool_call_serialized_length(tc) / RATIO_TOOL_CALL)
        breakdown["tool_calls"] += n
        total += n
    return total


def x_estimate_tokens_for_assistant_with_tool_calls__mutmut_14(
    text: str,
    tool_calls: list[ToolCallDict],
    breakdown: dict[str, int],
) -> int:
    """Estimate tokens for an assistant message that contains tool calls. Returns added total."""
    total = 0
    if text:
        n = estimate_tokens_for_text(text, "text", RATIO_TEXT, breakdown)
        total = n
    for tc in tool_calls:
        n = int(tool_call_serialized_length(tc) / RATIO_TOOL_CALL)
        breakdown["tool_calls"] += n
        total += n
    return total


def x_estimate_tokens_for_assistant_with_tool_calls__mutmut_15(
    text: str,
    tool_calls: list[ToolCallDict],
    breakdown: dict[str, int],
) -> int:
    """Estimate tokens for an assistant message that contains tool calls. Returns added total."""
    total = 0
    if text:
        n = estimate_tokens_for_text(text, "text", RATIO_TEXT, breakdown)
        total -= n
    for tc in tool_calls:
        n = int(tool_call_serialized_length(tc) / RATIO_TOOL_CALL)
        breakdown["tool_calls"] += n
        total += n
    return total


def x_estimate_tokens_for_assistant_with_tool_calls__mutmut_16(
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
        n = None
        breakdown["tool_calls"] += n
        total += n
    return total


def x_estimate_tokens_for_assistant_with_tool_calls__mutmut_17(
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
        n = int(None)
        breakdown["tool_calls"] += n
        total += n
    return total


def x_estimate_tokens_for_assistant_with_tool_calls__mutmut_18(
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
        n = int(tool_call_serialized_length(tc) * RATIO_TOOL_CALL)
        breakdown["tool_calls"] += n
        total += n
    return total


def x_estimate_tokens_for_assistant_with_tool_calls__mutmut_19(
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
        n = int(tool_call_serialized_length(None) / RATIO_TOOL_CALL)
        breakdown["tool_calls"] += n
        total += n
    return total


def x_estimate_tokens_for_assistant_with_tool_calls__mutmut_20(
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
        n = int(tool_call_serialized_length(tc) / RATIO_TOOL_CALL)
        breakdown["tool_calls"] = n
        total += n
    return total


def x_estimate_tokens_for_assistant_with_tool_calls__mutmut_21(
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
        n = int(tool_call_serialized_length(tc) / RATIO_TOOL_CALL)
        breakdown["tool_calls"] -= n
        total += n
    return total


def x_estimate_tokens_for_assistant_with_tool_calls__mutmut_22(
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
        n = int(tool_call_serialized_length(tc) / RATIO_TOOL_CALL)
        breakdown["XXtool_callsXX"] += n
        total += n
    return total


def x_estimate_tokens_for_assistant_with_tool_calls__mutmut_23(
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
        n = int(tool_call_serialized_length(tc) / RATIO_TOOL_CALL)
        breakdown["TOOL_CALLS"] += n
        total += n
    return total


def x_estimate_tokens_for_assistant_with_tool_calls__mutmut_24(
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
        n = int(tool_call_serialized_length(tc) / RATIO_TOOL_CALL)
        breakdown["tool_calls"] += n
        total = n
    return total


def x_estimate_tokens_for_assistant_with_tool_calls__mutmut_25(
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
        n = int(tool_call_serialized_length(tc) / RATIO_TOOL_CALL)
        breakdown["tool_calls"] += n
        total -= n
    return total

mutants_x_estimate_tokens_for_assistant_with_tool_calls__mutmut['_mutmut_orig'] = x_estimate_tokens_for_assistant_with_tool_calls__mutmut_orig # type: ignore # mutmut generated
mutants_x_estimate_tokens_for_assistant_with_tool_calls__mutmut['x_estimate_tokens_for_assistant_with_tool_calls__mutmut_1'] = x_estimate_tokens_for_assistant_with_tool_calls__mutmut_1 # type: ignore # mutmut generated
mutants_x_estimate_tokens_for_assistant_with_tool_calls__mutmut['x_estimate_tokens_for_assistant_with_tool_calls__mutmut_2'] = x_estimate_tokens_for_assistant_with_tool_calls__mutmut_2 # type: ignore # mutmut generated
mutants_x_estimate_tokens_for_assistant_with_tool_calls__mutmut['x_estimate_tokens_for_assistant_with_tool_calls__mutmut_3'] = x_estimate_tokens_for_assistant_with_tool_calls__mutmut_3 # type: ignore # mutmut generated
mutants_x_estimate_tokens_for_assistant_with_tool_calls__mutmut['x_estimate_tokens_for_assistant_with_tool_calls__mutmut_4'] = x_estimate_tokens_for_assistant_with_tool_calls__mutmut_4 # type: ignore # mutmut generated
mutants_x_estimate_tokens_for_assistant_with_tool_calls__mutmut['x_estimate_tokens_for_assistant_with_tool_calls__mutmut_5'] = x_estimate_tokens_for_assistant_with_tool_calls__mutmut_5 # type: ignore # mutmut generated
mutants_x_estimate_tokens_for_assistant_with_tool_calls__mutmut['x_estimate_tokens_for_assistant_with_tool_calls__mutmut_6'] = x_estimate_tokens_for_assistant_with_tool_calls__mutmut_6 # type: ignore # mutmut generated
mutants_x_estimate_tokens_for_assistant_with_tool_calls__mutmut['x_estimate_tokens_for_assistant_with_tool_calls__mutmut_7'] = x_estimate_tokens_for_assistant_with_tool_calls__mutmut_7 # type: ignore # mutmut generated
mutants_x_estimate_tokens_for_assistant_with_tool_calls__mutmut['x_estimate_tokens_for_assistant_with_tool_calls__mutmut_8'] = x_estimate_tokens_for_assistant_with_tool_calls__mutmut_8 # type: ignore # mutmut generated
mutants_x_estimate_tokens_for_assistant_with_tool_calls__mutmut['x_estimate_tokens_for_assistant_with_tool_calls__mutmut_9'] = x_estimate_tokens_for_assistant_with_tool_calls__mutmut_9 # type: ignore # mutmut generated
mutants_x_estimate_tokens_for_assistant_with_tool_calls__mutmut['x_estimate_tokens_for_assistant_with_tool_calls__mutmut_10'] = x_estimate_tokens_for_assistant_with_tool_calls__mutmut_10 # type: ignore # mutmut generated
mutants_x_estimate_tokens_for_assistant_with_tool_calls__mutmut['x_estimate_tokens_for_assistant_with_tool_calls__mutmut_11'] = x_estimate_tokens_for_assistant_with_tool_calls__mutmut_11 # type: ignore # mutmut generated
mutants_x_estimate_tokens_for_assistant_with_tool_calls__mutmut['x_estimate_tokens_for_assistant_with_tool_calls__mutmut_12'] = x_estimate_tokens_for_assistant_with_tool_calls__mutmut_12 # type: ignore # mutmut generated
mutants_x_estimate_tokens_for_assistant_with_tool_calls__mutmut['x_estimate_tokens_for_assistant_with_tool_calls__mutmut_13'] = x_estimate_tokens_for_assistant_with_tool_calls__mutmut_13 # type: ignore # mutmut generated
mutants_x_estimate_tokens_for_assistant_with_tool_calls__mutmut['x_estimate_tokens_for_assistant_with_tool_calls__mutmut_14'] = x_estimate_tokens_for_assistant_with_tool_calls__mutmut_14 # type: ignore # mutmut generated
mutants_x_estimate_tokens_for_assistant_with_tool_calls__mutmut['x_estimate_tokens_for_assistant_with_tool_calls__mutmut_15'] = x_estimate_tokens_for_assistant_with_tool_calls__mutmut_15 # type: ignore # mutmut generated
mutants_x_estimate_tokens_for_assistant_with_tool_calls__mutmut['x_estimate_tokens_for_assistant_with_tool_calls__mutmut_16'] = x_estimate_tokens_for_assistant_with_tool_calls__mutmut_16 # type: ignore # mutmut generated
mutants_x_estimate_tokens_for_assistant_with_tool_calls__mutmut['x_estimate_tokens_for_assistant_with_tool_calls__mutmut_17'] = x_estimate_tokens_for_assistant_with_tool_calls__mutmut_17 # type: ignore # mutmut generated
mutants_x_estimate_tokens_for_assistant_with_tool_calls__mutmut['x_estimate_tokens_for_assistant_with_tool_calls__mutmut_18'] = x_estimate_tokens_for_assistant_with_tool_calls__mutmut_18 # type: ignore # mutmut generated
mutants_x_estimate_tokens_for_assistant_with_tool_calls__mutmut['x_estimate_tokens_for_assistant_with_tool_calls__mutmut_19'] = x_estimate_tokens_for_assistant_with_tool_calls__mutmut_19 # type: ignore # mutmut generated
mutants_x_estimate_tokens_for_assistant_with_tool_calls__mutmut['x_estimate_tokens_for_assistant_with_tool_calls__mutmut_20'] = x_estimate_tokens_for_assistant_with_tool_calls__mutmut_20 # type: ignore # mutmut generated
mutants_x_estimate_tokens_for_assistant_with_tool_calls__mutmut['x_estimate_tokens_for_assistant_with_tool_calls__mutmut_21'] = x_estimate_tokens_for_assistant_with_tool_calls__mutmut_21 # type: ignore # mutmut generated
mutants_x_estimate_tokens_for_assistant_with_tool_calls__mutmut['x_estimate_tokens_for_assistant_with_tool_calls__mutmut_22'] = x_estimate_tokens_for_assistant_with_tool_calls__mutmut_22 # type: ignore # mutmut generated
mutants_x_estimate_tokens_for_assistant_with_tool_calls__mutmut['x_estimate_tokens_for_assistant_with_tool_calls__mutmut_23'] = x_estimate_tokens_for_assistant_with_tool_calls__mutmut_23 # type: ignore # mutmut generated
mutants_x_estimate_tokens_for_assistant_with_tool_calls__mutmut['x_estimate_tokens_for_assistant_with_tool_calls__mutmut_24'] = x_estimate_tokens_for_assistant_with_tool_calls__mutmut_24 # type: ignore # mutmut generated
mutants_x_estimate_tokens_for_assistant_with_tool_calls__mutmut['x_estimate_tokens_for_assistant_with_tool_calls__mutmut_25'] = x_estimate_tokens_for_assistant_with_tool_calls__mutmut_25 # type: ignore # mutmut generated
mutants_x_estimate_tokens__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x_estimate_tokens__mutmut)
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

    This provides a more accurate estimate than a simple ``chars // 4`` heuristic,
    accounting for structured vs unstructured content.
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

        if role == "system" and text:
            total += estimate_tokens_for_text(text, "system", RATIO_SYSTEM, breakdown)
        elif role == "assistant" and tool_calls:
            total += estimate_tokens_for_assistant_with_tool_calls(
                text, tool_calls, breakdown
            )
        elif text:
            total += estimate_tokens_for_text(text, "text", RATIO_TEXT, breakdown)
    return total, breakdown


def x_estimate_tokens__mutmut_orig(history: list[LLMMessage]) -> tuple[int, dict[str, int]]:
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

    This provides a more accurate estimate than a simple ``chars // 4`` heuristic,
    accounting for structured vs unstructured content.
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

        if role == "system" and text:
            total += estimate_tokens_for_text(text, "system", RATIO_SYSTEM, breakdown)
        elif role == "assistant" and tool_calls:
            total += estimate_tokens_for_assistant_with_tool_calls(
                text, tool_calls, breakdown
            )
        elif text:
            total += estimate_tokens_for_text(text, "text", RATIO_TEXT, breakdown)
    return total, breakdown


def x_estimate_tokens__mutmut_1(history: list[LLMMessage]) -> tuple[int, dict[str, int]]:
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

    This provides a more accurate estimate than a simple ``chars // 4`` heuristic,
    accounting for structured vs unstructured content.
    """
    total = None
    breakdown: dict[str, int] = {"text": 0, "tool_calls": 0, "system": 0}
    for msg in history:
        role = msg.get("role", "")
        content_raw = msg.get("content")
        text = content_raw if isinstance(content_raw, str) else ""
        tool_calls_raw = msg.get("tool_calls")
        tool_calls: list[ToolCallDict] = cast(
            "list[ToolCallDict]", tool_calls_raw if tool_calls_raw is not None else []
        )

        if role == "system" and text:
            total += estimate_tokens_for_text(text, "system", RATIO_SYSTEM, breakdown)
        elif role == "assistant" and tool_calls:
            total += estimate_tokens_for_assistant_with_tool_calls(
                text, tool_calls, breakdown
            )
        elif text:
            total += estimate_tokens_for_text(text, "text", RATIO_TEXT, breakdown)
    return total, breakdown


def x_estimate_tokens__mutmut_2(history: list[LLMMessage]) -> tuple[int, dict[str, int]]:
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

    This provides a more accurate estimate than a simple ``chars // 4`` heuristic,
    accounting for structured vs unstructured content.
    """
    total = 1
    breakdown: dict[str, int] = {"text": 0, "tool_calls": 0, "system": 0}
    for msg in history:
        role = msg.get("role", "")
        content_raw = msg.get("content")
        text = content_raw if isinstance(content_raw, str) else ""
        tool_calls_raw = msg.get("tool_calls")
        tool_calls: list[ToolCallDict] = cast(
            "list[ToolCallDict]", tool_calls_raw if tool_calls_raw is not None else []
        )

        if role == "system" and text:
            total += estimate_tokens_for_text(text, "system", RATIO_SYSTEM, breakdown)
        elif role == "assistant" and tool_calls:
            total += estimate_tokens_for_assistant_with_tool_calls(
                text, tool_calls, breakdown
            )
        elif text:
            total += estimate_tokens_for_text(text, "text", RATIO_TEXT, breakdown)
    return total, breakdown


def x_estimate_tokens__mutmut_3(history: list[LLMMessage]) -> tuple[int, dict[str, int]]:
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

    This provides a more accurate estimate than a simple ``chars // 4`` heuristic,
    accounting for structured vs unstructured content.
    """
    total = 0
    breakdown: dict[str, int] = None
    for msg in history:
        role = msg.get("role", "")
        content_raw = msg.get("content")
        text = content_raw if isinstance(content_raw, str) else ""
        tool_calls_raw = msg.get("tool_calls")
        tool_calls: list[ToolCallDict] = cast(
            "list[ToolCallDict]", tool_calls_raw if tool_calls_raw is not None else []
        )

        if role == "system" and text:
            total += estimate_tokens_for_text(text, "system", RATIO_SYSTEM, breakdown)
        elif role == "assistant" and tool_calls:
            total += estimate_tokens_for_assistant_with_tool_calls(
                text, tool_calls, breakdown
            )
        elif text:
            total += estimate_tokens_for_text(text, "text", RATIO_TEXT, breakdown)
    return total, breakdown


def x_estimate_tokens__mutmut_4(history: list[LLMMessage]) -> tuple[int, dict[str, int]]:
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

    This provides a more accurate estimate than a simple ``chars // 4`` heuristic,
    accounting for structured vs unstructured content.
    """
    total = 0
    breakdown: dict[str, int] = {"XXtextXX": 0, "tool_calls": 0, "system": 0}
    for msg in history:
        role = msg.get("role", "")
        content_raw = msg.get("content")
        text = content_raw if isinstance(content_raw, str) else ""
        tool_calls_raw = msg.get("tool_calls")
        tool_calls: list[ToolCallDict] = cast(
            "list[ToolCallDict]", tool_calls_raw if tool_calls_raw is not None else []
        )

        if role == "system" and text:
            total += estimate_tokens_for_text(text, "system", RATIO_SYSTEM, breakdown)
        elif role == "assistant" and tool_calls:
            total += estimate_tokens_for_assistant_with_tool_calls(
                text, tool_calls, breakdown
            )
        elif text:
            total += estimate_tokens_for_text(text, "text", RATIO_TEXT, breakdown)
    return total, breakdown


def x_estimate_tokens__mutmut_5(history: list[LLMMessage]) -> tuple[int, dict[str, int]]:
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

    This provides a more accurate estimate than a simple ``chars // 4`` heuristic,
    accounting for structured vs unstructured content.
    """
    total = 0
    breakdown: dict[str, int] = {"TEXT": 0, "tool_calls": 0, "system": 0}
    for msg in history:
        role = msg.get("role", "")
        content_raw = msg.get("content")
        text = content_raw if isinstance(content_raw, str) else ""
        tool_calls_raw = msg.get("tool_calls")
        tool_calls: list[ToolCallDict] = cast(
            "list[ToolCallDict]", tool_calls_raw if tool_calls_raw is not None else []
        )

        if role == "system" and text:
            total += estimate_tokens_for_text(text, "system", RATIO_SYSTEM, breakdown)
        elif role == "assistant" and tool_calls:
            total += estimate_tokens_for_assistant_with_tool_calls(
                text, tool_calls, breakdown
            )
        elif text:
            total += estimate_tokens_for_text(text, "text", RATIO_TEXT, breakdown)
    return total, breakdown


def x_estimate_tokens__mutmut_6(history: list[LLMMessage]) -> tuple[int, dict[str, int]]:
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

    This provides a more accurate estimate than a simple ``chars // 4`` heuristic,
    accounting for structured vs unstructured content.
    """
    total = 0
    breakdown: dict[str, int] = {"text": 1, "tool_calls": 0, "system": 0}
    for msg in history:
        role = msg.get("role", "")
        content_raw = msg.get("content")
        text = content_raw if isinstance(content_raw, str) else ""
        tool_calls_raw = msg.get("tool_calls")
        tool_calls: list[ToolCallDict] = cast(
            "list[ToolCallDict]", tool_calls_raw if tool_calls_raw is not None else []
        )

        if role == "system" and text:
            total += estimate_tokens_for_text(text, "system", RATIO_SYSTEM, breakdown)
        elif role == "assistant" and tool_calls:
            total += estimate_tokens_for_assistant_with_tool_calls(
                text, tool_calls, breakdown
            )
        elif text:
            total += estimate_tokens_for_text(text, "text", RATIO_TEXT, breakdown)
    return total, breakdown


def x_estimate_tokens__mutmut_7(history: list[LLMMessage]) -> tuple[int, dict[str, int]]:
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

    This provides a more accurate estimate than a simple ``chars // 4`` heuristic,
    accounting for structured vs unstructured content.
    """
    total = 0
    breakdown: dict[str, int] = {"text": 0, "XXtool_callsXX": 0, "system": 0}
    for msg in history:
        role = msg.get("role", "")
        content_raw = msg.get("content")
        text = content_raw if isinstance(content_raw, str) else ""
        tool_calls_raw = msg.get("tool_calls")
        tool_calls: list[ToolCallDict] = cast(
            "list[ToolCallDict]", tool_calls_raw if tool_calls_raw is not None else []
        )

        if role == "system" and text:
            total += estimate_tokens_for_text(text, "system", RATIO_SYSTEM, breakdown)
        elif role == "assistant" and tool_calls:
            total += estimate_tokens_for_assistant_with_tool_calls(
                text, tool_calls, breakdown
            )
        elif text:
            total += estimate_tokens_for_text(text, "text", RATIO_TEXT, breakdown)
    return total, breakdown


def x_estimate_tokens__mutmut_8(history: list[LLMMessage]) -> tuple[int, dict[str, int]]:
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

    This provides a more accurate estimate than a simple ``chars // 4`` heuristic,
    accounting for structured vs unstructured content.
    """
    total = 0
    breakdown: dict[str, int] = {"text": 0, "TOOL_CALLS": 0, "system": 0}
    for msg in history:
        role = msg.get("role", "")
        content_raw = msg.get("content")
        text = content_raw if isinstance(content_raw, str) else ""
        tool_calls_raw = msg.get("tool_calls")
        tool_calls: list[ToolCallDict] = cast(
            "list[ToolCallDict]", tool_calls_raw if tool_calls_raw is not None else []
        )

        if role == "system" and text:
            total += estimate_tokens_for_text(text, "system", RATIO_SYSTEM, breakdown)
        elif role == "assistant" and tool_calls:
            total += estimate_tokens_for_assistant_with_tool_calls(
                text, tool_calls, breakdown
            )
        elif text:
            total += estimate_tokens_for_text(text, "text", RATIO_TEXT, breakdown)
    return total, breakdown


def x_estimate_tokens__mutmut_9(history: list[LLMMessage]) -> tuple[int, dict[str, int]]:
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

    This provides a more accurate estimate than a simple ``chars // 4`` heuristic,
    accounting for structured vs unstructured content.
    """
    total = 0
    breakdown: dict[str, int] = {"text": 0, "tool_calls": 1, "system": 0}
    for msg in history:
        role = msg.get("role", "")
        content_raw = msg.get("content")
        text = content_raw if isinstance(content_raw, str) else ""
        tool_calls_raw = msg.get("tool_calls")
        tool_calls: list[ToolCallDict] = cast(
            "list[ToolCallDict]", tool_calls_raw if tool_calls_raw is not None else []
        )

        if role == "system" and text:
            total += estimate_tokens_for_text(text, "system", RATIO_SYSTEM, breakdown)
        elif role == "assistant" and tool_calls:
            total += estimate_tokens_for_assistant_with_tool_calls(
                text, tool_calls, breakdown
            )
        elif text:
            total += estimate_tokens_for_text(text, "text", RATIO_TEXT, breakdown)
    return total, breakdown


def x_estimate_tokens__mutmut_10(history: list[LLMMessage]) -> tuple[int, dict[str, int]]:
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

    This provides a more accurate estimate than a simple ``chars // 4`` heuristic,
    accounting for structured vs unstructured content.
    """
    total = 0
    breakdown: dict[str, int] = {"text": 0, "tool_calls": 0, "XXsystemXX": 0}
    for msg in history:
        role = msg.get("role", "")
        content_raw = msg.get("content")
        text = content_raw if isinstance(content_raw, str) else ""
        tool_calls_raw = msg.get("tool_calls")
        tool_calls: list[ToolCallDict] = cast(
            "list[ToolCallDict]", tool_calls_raw if tool_calls_raw is not None else []
        )

        if role == "system" and text:
            total += estimate_tokens_for_text(text, "system", RATIO_SYSTEM, breakdown)
        elif role == "assistant" and tool_calls:
            total += estimate_tokens_for_assistant_with_tool_calls(
                text, tool_calls, breakdown
            )
        elif text:
            total += estimate_tokens_for_text(text, "text", RATIO_TEXT, breakdown)
    return total, breakdown


def x_estimate_tokens__mutmut_11(history: list[LLMMessage]) -> tuple[int, dict[str, int]]:
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

    This provides a more accurate estimate than a simple ``chars // 4`` heuristic,
    accounting for structured vs unstructured content.
    """
    total = 0
    breakdown: dict[str, int] = {"text": 0, "tool_calls": 0, "SYSTEM": 0}
    for msg in history:
        role = msg.get("role", "")
        content_raw = msg.get("content")
        text = content_raw if isinstance(content_raw, str) else ""
        tool_calls_raw = msg.get("tool_calls")
        tool_calls: list[ToolCallDict] = cast(
            "list[ToolCallDict]", tool_calls_raw if tool_calls_raw is not None else []
        )

        if role == "system" and text:
            total += estimate_tokens_for_text(text, "system", RATIO_SYSTEM, breakdown)
        elif role == "assistant" and tool_calls:
            total += estimate_tokens_for_assistant_with_tool_calls(
                text, tool_calls, breakdown
            )
        elif text:
            total += estimate_tokens_for_text(text, "text", RATIO_TEXT, breakdown)
    return total, breakdown


def x_estimate_tokens__mutmut_12(history: list[LLMMessage]) -> tuple[int, dict[str, int]]:
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

    This provides a more accurate estimate than a simple ``chars // 4`` heuristic,
    accounting for structured vs unstructured content.
    """
    total = 0
    breakdown: dict[str, int] = {"text": 0, "tool_calls": 0, "system": 1}
    for msg in history:
        role = msg.get("role", "")
        content_raw = msg.get("content")
        text = content_raw if isinstance(content_raw, str) else ""
        tool_calls_raw = msg.get("tool_calls")
        tool_calls: list[ToolCallDict] = cast(
            "list[ToolCallDict]", tool_calls_raw if tool_calls_raw is not None else []
        )

        if role == "system" and text:
            total += estimate_tokens_for_text(text, "system", RATIO_SYSTEM, breakdown)
        elif role == "assistant" and tool_calls:
            total += estimate_tokens_for_assistant_with_tool_calls(
                text, tool_calls, breakdown
            )
        elif text:
            total += estimate_tokens_for_text(text, "text", RATIO_TEXT, breakdown)
    return total, breakdown


def x_estimate_tokens__mutmut_13(history: list[LLMMessage]) -> tuple[int, dict[str, int]]:
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

    This provides a more accurate estimate than a simple ``chars // 4`` heuristic,
    accounting for structured vs unstructured content.
    """
    total = 0
    breakdown: dict[str, int] = {"text": 0, "tool_calls": 0, "system": 0}
    for msg in history:
        role = None
        content_raw = msg.get("content")
        text = content_raw if isinstance(content_raw, str) else ""
        tool_calls_raw = msg.get("tool_calls")
        tool_calls: list[ToolCallDict] = cast(
            "list[ToolCallDict]", tool_calls_raw if tool_calls_raw is not None else []
        )

        if role == "system" and text:
            total += estimate_tokens_for_text(text, "system", RATIO_SYSTEM, breakdown)
        elif role == "assistant" and tool_calls:
            total += estimate_tokens_for_assistant_with_tool_calls(
                text, tool_calls, breakdown
            )
        elif text:
            total += estimate_tokens_for_text(text, "text", RATIO_TEXT, breakdown)
    return total, breakdown


def x_estimate_tokens__mutmut_14(history: list[LLMMessage]) -> tuple[int, dict[str, int]]:
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

    This provides a more accurate estimate than a simple ``chars // 4`` heuristic,
    accounting for structured vs unstructured content.
    """
    total = 0
    breakdown: dict[str, int] = {"text": 0, "tool_calls": 0, "system": 0}
    for msg in history:
        role = msg.get(None, "")
        content_raw = msg.get("content")
        text = content_raw if isinstance(content_raw, str) else ""
        tool_calls_raw = msg.get("tool_calls")
        tool_calls: list[ToolCallDict] = cast(
            "list[ToolCallDict]", tool_calls_raw if tool_calls_raw is not None else []
        )

        if role == "system" and text:
            total += estimate_tokens_for_text(text, "system", RATIO_SYSTEM, breakdown)
        elif role == "assistant" and tool_calls:
            total += estimate_tokens_for_assistant_with_tool_calls(
                text, tool_calls, breakdown
            )
        elif text:
            total += estimate_tokens_for_text(text, "text", RATIO_TEXT, breakdown)
    return total, breakdown


def x_estimate_tokens__mutmut_15(history: list[LLMMessage]) -> tuple[int, dict[str, int]]:
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

    This provides a more accurate estimate than a simple ``chars // 4`` heuristic,
    accounting for structured vs unstructured content.
    """
    total = 0
    breakdown: dict[str, int] = {"text": 0, "tool_calls": 0, "system": 0}
    for msg in history:
        role = msg.get("role", None)
        content_raw = msg.get("content")
        text = content_raw if isinstance(content_raw, str) else ""
        tool_calls_raw = msg.get("tool_calls")
        tool_calls: list[ToolCallDict] = cast(
            "list[ToolCallDict]", tool_calls_raw if tool_calls_raw is not None else []
        )

        if role == "system" and text:
            total += estimate_tokens_for_text(text, "system", RATIO_SYSTEM, breakdown)
        elif role == "assistant" and tool_calls:
            total += estimate_tokens_for_assistant_with_tool_calls(
                text, tool_calls, breakdown
            )
        elif text:
            total += estimate_tokens_for_text(text, "text", RATIO_TEXT, breakdown)
    return total, breakdown


def x_estimate_tokens__mutmut_16(history: list[LLMMessage]) -> tuple[int, dict[str, int]]:
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

    This provides a more accurate estimate than a simple ``chars // 4`` heuristic,
    accounting for structured vs unstructured content.
    """
    total = 0
    breakdown: dict[str, int] = {"text": 0, "tool_calls": 0, "system": 0}
    for msg in history:
        role = msg.get("")
        content_raw = msg.get("content")
        text = content_raw if isinstance(content_raw, str) else ""
        tool_calls_raw = msg.get("tool_calls")
        tool_calls: list[ToolCallDict] = cast(
            "list[ToolCallDict]", tool_calls_raw if tool_calls_raw is not None else []
        )

        if role == "system" and text:
            total += estimate_tokens_for_text(text, "system", RATIO_SYSTEM, breakdown)
        elif role == "assistant" and tool_calls:
            total += estimate_tokens_for_assistant_with_tool_calls(
                text, tool_calls, breakdown
            )
        elif text:
            total += estimate_tokens_for_text(text, "text", RATIO_TEXT, breakdown)
    return total, breakdown


def x_estimate_tokens__mutmut_17(history: list[LLMMessage]) -> tuple[int, dict[str, int]]:
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

    This provides a more accurate estimate than a simple ``chars // 4`` heuristic,
    accounting for structured vs unstructured content.
    """
    total = 0
    breakdown: dict[str, int] = {"text": 0, "tool_calls": 0, "system": 0}
    for msg in history:
        role = msg.get("role", )
        content_raw = msg.get("content")
        text = content_raw if isinstance(content_raw, str) else ""
        tool_calls_raw = msg.get("tool_calls")
        tool_calls: list[ToolCallDict] = cast(
            "list[ToolCallDict]", tool_calls_raw if tool_calls_raw is not None else []
        )

        if role == "system" and text:
            total += estimate_tokens_for_text(text, "system", RATIO_SYSTEM, breakdown)
        elif role == "assistant" and tool_calls:
            total += estimate_tokens_for_assistant_with_tool_calls(
                text, tool_calls, breakdown
            )
        elif text:
            total += estimate_tokens_for_text(text, "text", RATIO_TEXT, breakdown)
    return total, breakdown


def x_estimate_tokens__mutmut_18(history: list[LLMMessage]) -> tuple[int, dict[str, int]]:
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

    This provides a more accurate estimate than a simple ``chars // 4`` heuristic,
    accounting for structured vs unstructured content.
    """
    total = 0
    breakdown: dict[str, int] = {"text": 0, "tool_calls": 0, "system": 0}
    for msg in history:
        role = msg.get("XXroleXX", "")
        content_raw = msg.get("content")
        text = content_raw if isinstance(content_raw, str) else ""
        tool_calls_raw = msg.get("tool_calls")
        tool_calls: list[ToolCallDict] = cast(
            "list[ToolCallDict]", tool_calls_raw if tool_calls_raw is not None else []
        )

        if role == "system" and text:
            total += estimate_tokens_for_text(text, "system", RATIO_SYSTEM, breakdown)
        elif role == "assistant" and tool_calls:
            total += estimate_tokens_for_assistant_with_tool_calls(
                text, tool_calls, breakdown
            )
        elif text:
            total += estimate_tokens_for_text(text, "text", RATIO_TEXT, breakdown)
    return total, breakdown


def x_estimate_tokens__mutmut_19(history: list[LLMMessage]) -> tuple[int, dict[str, int]]:
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

    This provides a more accurate estimate than a simple ``chars // 4`` heuristic,
    accounting for structured vs unstructured content.
    """
    total = 0
    breakdown: dict[str, int] = {"text": 0, "tool_calls": 0, "system": 0}
    for msg in history:
        role = msg.get("ROLE", "")
        content_raw = msg.get("content")
        text = content_raw if isinstance(content_raw, str) else ""
        tool_calls_raw = msg.get("tool_calls")
        tool_calls: list[ToolCallDict] = cast(
            "list[ToolCallDict]", tool_calls_raw if tool_calls_raw is not None else []
        )

        if role == "system" and text:
            total += estimate_tokens_for_text(text, "system", RATIO_SYSTEM, breakdown)
        elif role == "assistant" and tool_calls:
            total += estimate_tokens_for_assistant_with_tool_calls(
                text, tool_calls, breakdown
            )
        elif text:
            total += estimate_tokens_for_text(text, "text", RATIO_TEXT, breakdown)
    return total, breakdown


def x_estimate_tokens__mutmut_20(history: list[LLMMessage]) -> tuple[int, dict[str, int]]:
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

    This provides a more accurate estimate than a simple ``chars // 4`` heuristic,
    accounting for structured vs unstructured content.
    """
    total = 0
    breakdown: dict[str, int] = {"text": 0, "tool_calls": 0, "system": 0}
    for msg in history:
        role = msg.get("role", "XXXX")
        content_raw = msg.get("content")
        text = content_raw if isinstance(content_raw, str) else ""
        tool_calls_raw = msg.get("tool_calls")
        tool_calls: list[ToolCallDict] = cast(
            "list[ToolCallDict]", tool_calls_raw if tool_calls_raw is not None else []
        )

        if role == "system" and text:
            total += estimate_tokens_for_text(text, "system", RATIO_SYSTEM, breakdown)
        elif role == "assistant" and tool_calls:
            total += estimate_tokens_for_assistant_with_tool_calls(
                text, tool_calls, breakdown
            )
        elif text:
            total += estimate_tokens_for_text(text, "text", RATIO_TEXT, breakdown)
    return total, breakdown


def x_estimate_tokens__mutmut_21(history: list[LLMMessage]) -> tuple[int, dict[str, int]]:
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

    This provides a more accurate estimate than a simple ``chars // 4`` heuristic,
    accounting for structured vs unstructured content.
    """
    total = 0
    breakdown: dict[str, int] = {"text": 0, "tool_calls": 0, "system": 0}
    for msg in history:
        role = msg.get("role", "")
        content_raw = None
        text = content_raw if isinstance(content_raw, str) else ""
        tool_calls_raw = msg.get("tool_calls")
        tool_calls: list[ToolCallDict] = cast(
            "list[ToolCallDict]", tool_calls_raw if tool_calls_raw is not None else []
        )

        if role == "system" and text:
            total += estimate_tokens_for_text(text, "system", RATIO_SYSTEM, breakdown)
        elif role == "assistant" and tool_calls:
            total += estimate_tokens_for_assistant_with_tool_calls(
                text, tool_calls, breakdown
            )
        elif text:
            total += estimate_tokens_for_text(text, "text", RATIO_TEXT, breakdown)
    return total, breakdown


def x_estimate_tokens__mutmut_22(history: list[LLMMessage]) -> tuple[int, dict[str, int]]:
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

    This provides a more accurate estimate than a simple ``chars // 4`` heuristic,
    accounting for structured vs unstructured content.
    """
    total = 0
    breakdown: dict[str, int] = {"text": 0, "tool_calls": 0, "system": 0}
    for msg in history:
        role = msg.get("role", "")
        content_raw = msg.get(None)
        text = content_raw if isinstance(content_raw, str) else ""
        tool_calls_raw = msg.get("tool_calls")
        tool_calls: list[ToolCallDict] = cast(
            "list[ToolCallDict]", tool_calls_raw if tool_calls_raw is not None else []
        )

        if role == "system" and text:
            total += estimate_tokens_for_text(text, "system", RATIO_SYSTEM, breakdown)
        elif role == "assistant" and tool_calls:
            total += estimate_tokens_for_assistant_with_tool_calls(
                text, tool_calls, breakdown
            )
        elif text:
            total += estimate_tokens_for_text(text, "text", RATIO_TEXT, breakdown)
    return total, breakdown


def x_estimate_tokens__mutmut_23(history: list[LLMMessage]) -> tuple[int, dict[str, int]]:
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

    This provides a more accurate estimate than a simple ``chars // 4`` heuristic,
    accounting for structured vs unstructured content.
    """
    total = 0
    breakdown: dict[str, int] = {"text": 0, "tool_calls": 0, "system": 0}
    for msg in history:
        role = msg.get("role", "")
        content_raw = msg.get("XXcontentXX")
        text = content_raw if isinstance(content_raw, str) else ""
        tool_calls_raw = msg.get("tool_calls")
        tool_calls: list[ToolCallDict] = cast(
            "list[ToolCallDict]", tool_calls_raw if tool_calls_raw is not None else []
        )

        if role == "system" and text:
            total += estimate_tokens_for_text(text, "system", RATIO_SYSTEM, breakdown)
        elif role == "assistant" and tool_calls:
            total += estimate_tokens_for_assistant_with_tool_calls(
                text, tool_calls, breakdown
            )
        elif text:
            total += estimate_tokens_for_text(text, "text", RATIO_TEXT, breakdown)
    return total, breakdown


def x_estimate_tokens__mutmut_24(history: list[LLMMessage]) -> tuple[int, dict[str, int]]:
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

    This provides a more accurate estimate than a simple ``chars // 4`` heuristic,
    accounting for structured vs unstructured content.
    """
    total = 0
    breakdown: dict[str, int] = {"text": 0, "tool_calls": 0, "system": 0}
    for msg in history:
        role = msg.get("role", "")
        content_raw = msg.get("CONTENT")
        text = content_raw if isinstance(content_raw, str) else ""
        tool_calls_raw = msg.get("tool_calls")
        tool_calls: list[ToolCallDict] = cast(
            "list[ToolCallDict]", tool_calls_raw if tool_calls_raw is not None else []
        )

        if role == "system" and text:
            total += estimate_tokens_for_text(text, "system", RATIO_SYSTEM, breakdown)
        elif role == "assistant" and tool_calls:
            total += estimate_tokens_for_assistant_with_tool_calls(
                text, tool_calls, breakdown
            )
        elif text:
            total += estimate_tokens_for_text(text, "text", RATIO_TEXT, breakdown)
    return total, breakdown


def x_estimate_tokens__mutmut_25(history: list[LLMMessage]) -> tuple[int, dict[str, int]]:
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

    This provides a more accurate estimate than a simple ``chars // 4`` heuristic,
    accounting for structured vs unstructured content.
    """
    total = 0
    breakdown: dict[str, int] = {"text": 0, "tool_calls": 0, "system": 0}
    for msg in history:
        role = msg.get("role", "")
        content_raw = msg.get("content")
        text = None
        tool_calls_raw = msg.get("tool_calls")
        tool_calls: list[ToolCallDict] = cast(
            "list[ToolCallDict]", tool_calls_raw if tool_calls_raw is not None else []
        )

        if role == "system" and text:
            total += estimate_tokens_for_text(text, "system", RATIO_SYSTEM, breakdown)
        elif role == "assistant" and tool_calls:
            total += estimate_tokens_for_assistant_with_tool_calls(
                text, tool_calls, breakdown
            )
        elif text:
            total += estimate_tokens_for_text(text, "text", RATIO_TEXT, breakdown)
    return total, breakdown


def x_estimate_tokens__mutmut_26(history: list[LLMMessage]) -> tuple[int, dict[str, int]]:
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

    This provides a more accurate estimate than a simple ``chars // 4`` heuristic,
    accounting for structured vs unstructured content.
    """
    total = 0
    breakdown: dict[str, int] = {"text": 0, "tool_calls": 0, "system": 0}
    for msg in history:
        role = msg.get("role", "")
        content_raw = msg.get("content")
        text = content_raw if isinstance(content_raw, str) else "XXXX"
        tool_calls_raw = msg.get("tool_calls")
        tool_calls: list[ToolCallDict] = cast(
            "list[ToolCallDict]", tool_calls_raw if tool_calls_raw is not None else []
        )

        if role == "system" and text:
            total += estimate_tokens_for_text(text, "system", RATIO_SYSTEM, breakdown)
        elif role == "assistant" and tool_calls:
            total += estimate_tokens_for_assistant_with_tool_calls(
                text, tool_calls, breakdown
            )
        elif text:
            total += estimate_tokens_for_text(text, "text", RATIO_TEXT, breakdown)
    return total, breakdown


def x_estimate_tokens__mutmut_27(history: list[LLMMessage]) -> tuple[int, dict[str, int]]:
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

    This provides a more accurate estimate than a simple ``chars // 4`` heuristic,
    accounting for structured vs unstructured content.
    """
    total = 0
    breakdown: dict[str, int] = {"text": 0, "tool_calls": 0, "system": 0}
    for msg in history:
        role = msg.get("role", "")
        content_raw = msg.get("content")
        text = content_raw if isinstance(content_raw, str) else ""
        tool_calls_raw = None
        tool_calls: list[ToolCallDict] = cast(
            "list[ToolCallDict]", tool_calls_raw if tool_calls_raw is not None else []
        )

        if role == "system" and text:
            total += estimate_tokens_for_text(text, "system", RATIO_SYSTEM, breakdown)
        elif role == "assistant" and tool_calls:
            total += estimate_tokens_for_assistant_with_tool_calls(
                text, tool_calls, breakdown
            )
        elif text:
            total += estimate_tokens_for_text(text, "text", RATIO_TEXT, breakdown)
    return total, breakdown


def x_estimate_tokens__mutmut_28(history: list[LLMMessage]) -> tuple[int, dict[str, int]]:
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

    This provides a more accurate estimate than a simple ``chars // 4`` heuristic,
    accounting for structured vs unstructured content.
    """
    total = 0
    breakdown: dict[str, int] = {"text": 0, "tool_calls": 0, "system": 0}
    for msg in history:
        role = msg.get("role", "")
        content_raw = msg.get("content")
        text = content_raw if isinstance(content_raw, str) else ""
        tool_calls_raw = msg.get(None)
        tool_calls: list[ToolCallDict] = cast(
            "list[ToolCallDict]", tool_calls_raw if tool_calls_raw is not None else []
        )

        if role == "system" and text:
            total += estimate_tokens_for_text(text, "system", RATIO_SYSTEM, breakdown)
        elif role == "assistant" and tool_calls:
            total += estimate_tokens_for_assistant_with_tool_calls(
                text, tool_calls, breakdown
            )
        elif text:
            total += estimate_tokens_for_text(text, "text", RATIO_TEXT, breakdown)
    return total, breakdown


def x_estimate_tokens__mutmut_29(history: list[LLMMessage]) -> tuple[int, dict[str, int]]:
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

    This provides a more accurate estimate than a simple ``chars // 4`` heuristic,
    accounting for structured vs unstructured content.
    """
    total = 0
    breakdown: dict[str, int] = {"text": 0, "tool_calls": 0, "system": 0}
    for msg in history:
        role = msg.get("role", "")
        content_raw = msg.get("content")
        text = content_raw if isinstance(content_raw, str) else ""
        tool_calls_raw = msg.get("XXtool_callsXX")
        tool_calls: list[ToolCallDict] = cast(
            "list[ToolCallDict]", tool_calls_raw if tool_calls_raw is not None else []
        )

        if role == "system" and text:
            total += estimate_tokens_for_text(text, "system", RATIO_SYSTEM, breakdown)
        elif role == "assistant" and tool_calls:
            total += estimate_tokens_for_assistant_with_tool_calls(
                text, tool_calls, breakdown
            )
        elif text:
            total += estimate_tokens_for_text(text, "text", RATIO_TEXT, breakdown)
    return total, breakdown


def x_estimate_tokens__mutmut_30(history: list[LLMMessage]) -> tuple[int, dict[str, int]]:
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

    This provides a more accurate estimate than a simple ``chars // 4`` heuristic,
    accounting for structured vs unstructured content.
    """
    total = 0
    breakdown: dict[str, int] = {"text": 0, "tool_calls": 0, "system": 0}
    for msg in history:
        role = msg.get("role", "")
        content_raw = msg.get("content")
        text = content_raw if isinstance(content_raw, str) else ""
        tool_calls_raw = msg.get("TOOL_CALLS")
        tool_calls: list[ToolCallDict] = cast(
            "list[ToolCallDict]", tool_calls_raw if tool_calls_raw is not None else []
        )

        if role == "system" and text:
            total += estimate_tokens_for_text(text, "system", RATIO_SYSTEM, breakdown)
        elif role == "assistant" and tool_calls:
            total += estimate_tokens_for_assistant_with_tool_calls(
                text, tool_calls, breakdown
            )
        elif text:
            total += estimate_tokens_for_text(text, "text", RATIO_TEXT, breakdown)
    return total, breakdown


def x_estimate_tokens__mutmut_31(history: list[LLMMessage]) -> tuple[int, dict[str, int]]:
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

    This provides a more accurate estimate than a simple ``chars // 4`` heuristic,
    accounting for structured vs unstructured content.
    """
    total = 0
    breakdown: dict[str, int] = {"text": 0, "tool_calls": 0, "system": 0}
    for msg in history:
        role = msg.get("role", "")
        content_raw = msg.get("content")
        text = content_raw if isinstance(content_raw, str) else ""
        tool_calls_raw = msg.get("tool_calls")
        tool_calls: list[ToolCallDict] = None

        if role == "system" and text:
            total += estimate_tokens_for_text(text, "system", RATIO_SYSTEM, breakdown)
        elif role == "assistant" and tool_calls:
            total += estimate_tokens_for_assistant_with_tool_calls(
                text, tool_calls, breakdown
            )
        elif text:
            total += estimate_tokens_for_text(text, "text", RATIO_TEXT, breakdown)
    return total, breakdown


def x_estimate_tokens__mutmut_32(history: list[LLMMessage]) -> tuple[int, dict[str, int]]:
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

    This provides a more accurate estimate than a simple ``chars // 4`` heuristic,
    accounting for structured vs unstructured content.
    """
    total = 0
    breakdown: dict[str, int] = {"text": 0, "tool_calls": 0, "system": 0}
    for msg in history:
        role = msg.get("role", "")
        content_raw = msg.get("content")
        text = content_raw if isinstance(content_raw, str) else ""
        tool_calls_raw = msg.get("tool_calls")
        tool_calls: list[ToolCallDict] = cast(
            None, tool_calls_raw if tool_calls_raw is not None else []
        )

        if role == "system" and text:
            total += estimate_tokens_for_text(text, "system", RATIO_SYSTEM, breakdown)
        elif role == "assistant" and tool_calls:
            total += estimate_tokens_for_assistant_with_tool_calls(
                text, tool_calls, breakdown
            )
        elif text:
            total += estimate_tokens_for_text(text, "text", RATIO_TEXT, breakdown)
    return total, breakdown


def x_estimate_tokens__mutmut_33(history: list[LLMMessage]) -> tuple[int, dict[str, int]]:
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

    This provides a more accurate estimate than a simple ``chars // 4`` heuristic,
    accounting for structured vs unstructured content.
    """
    total = 0
    breakdown: dict[str, int] = {"text": 0, "tool_calls": 0, "system": 0}
    for msg in history:
        role = msg.get("role", "")
        content_raw = msg.get("content")
        text = content_raw if isinstance(content_raw, str) else ""
        tool_calls_raw = msg.get("tool_calls")
        tool_calls: list[ToolCallDict] = cast(
            "list[ToolCallDict]", None
        )

        if role == "system" and text:
            total += estimate_tokens_for_text(text, "system", RATIO_SYSTEM, breakdown)
        elif role == "assistant" and tool_calls:
            total += estimate_tokens_for_assistant_with_tool_calls(
                text, tool_calls, breakdown
            )
        elif text:
            total += estimate_tokens_for_text(text, "text", RATIO_TEXT, breakdown)
    return total, breakdown


def x_estimate_tokens__mutmut_34(history: list[LLMMessage]) -> tuple[int, dict[str, int]]:
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

    This provides a more accurate estimate than a simple ``chars // 4`` heuristic,
    accounting for structured vs unstructured content.
    """
    total = 0
    breakdown: dict[str, int] = {"text": 0, "tool_calls": 0, "system": 0}
    for msg in history:
        role = msg.get("role", "")
        content_raw = msg.get("content")
        text = content_raw if isinstance(content_raw, str) else ""
        tool_calls_raw = msg.get("tool_calls")
        tool_calls: list[ToolCallDict] = cast(
            tool_calls_raw if tool_calls_raw is not None else []
        )

        if role == "system" and text:
            total += estimate_tokens_for_text(text, "system", RATIO_SYSTEM, breakdown)
        elif role == "assistant" and tool_calls:
            total += estimate_tokens_for_assistant_with_tool_calls(
                text, tool_calls, breakdown
            )
        elif text:
            total += estimate_tokens_for_text(text, "text", RATIO_TEXT, breakdown)
    return total, breakdown


def x_estimate_tokens__mutmut_35(history: list[LLMMessage]) -> tuple[int, dict[str, int]]:
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

    This provides a more accurate estimate than a simple ``chars // 4`` heuristic,
    accounting for structured vs unstructured content.
    """
    total = 0
    breakdown: dict[str, int] = {"text": 0, "tool_calls": 0, "system": 0}
    for msg in history:
        role = msg.get("role", "")
        content_raw = msg.get("content")
        text = content_raw if isinstance(content_raw, str) else ""
        tool_calls_raw = msg.get("tool_calls")
        tool_calls: list[ToolCallDict] = cast(
            "list[ToolCallDict]", )

        if role == "system" and text:
            total += estimate_tokens_for_text(text, "system", RATIO_SYSTEM, breakdown)
        elif role == "assistant" and tool_calls:
            total += estimate_tokens_for_assistant_with_tool_calls(
                text, tool_calls, breakdown
            )
        elif text:
            total += estimate_tokens_for_text(text, "text", RATIO_TEXT, breakdown)
    return total, breakdown


def x_estimate_tokens__mutmut_36(history: list[LLMMessage]) -> tuple[int, dict[str, int]]:
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

    This provides a more accurate estimate than a simple ``chars // 4`` heuristic,
    accounting for structured vs unstructured content.
    """
    total = 0
    breakdown: dict[str, int] = {"text": 0, "tool_calls": 0, "system": 0}
    for msg in history:
        role = msg.get("role", "")
        content_raw = msg.get("content")
        text = content_raw if isinstance(content_raw, str) else ""
        tool_calls_raw = msg.get("tool_calls")
        tool_calls: list[ToolCallDict] = cast(
            "XXlist[ToolCallDict]XX", tool_calls_raw if tool_calls_raw is not None else []
        )

        if role == "system" and text:
            total += estimate_tokens_for_text(text, "system", RATIO_SYSTEM, breakdown)
        elif role == "assistant" and tool_calls:
            total += estimate_tokens_for_assistant_with_tool_calls(
                text, tool_calls, breakdown
            )
        elif text:
            total += estimate_tokens_for_text(text, "text", RATIO_TEXT, breakdown)
    return total, breakdown


def x_estimate_tokens__mutmut_37(history: list[LLMMessage]) -> tuple[int, dict[str, int]]:
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

    This provides a more accurate estimate than a simple ``chars // 4`` heuristic,
    accounting for structured vs unstructured content.
    """
    total = 0
    breakdown: dict[str, int] = {"text": 0, "tool_calls": 0, "system": 0}
    for msg in history:
        role = msg.get("role", "")
        content_raw = msg.get("content")
        text = content_raw if isinstance(content_raw, str) else ""
        tool_calls_raw = msg.get("tool_calls")
        tool_calls: list[ToolCallDict] = cast(
            "list[toolcalldict]", tool_calls_raw if tool_calls_raw is not None else []
        )

        if role == "system" and text:
            total += estimate_tokens_for_text(text, "system", RATIO_SYSTEM, breakdown)
        elif role == "assistant" and tool_calls:
            total += estimate_tokens_for_assistant_with_tool_calls(
                text, tool_calls, breakdown
            )
        elif text:
            total += estimate_tokens_for_text(text, "text", RATIO_TEXT, breakdown)
    return total, breakdown


def x_estimate_tokens__mutmut_38(history: list[LLMMessage]) -> tuple[int, dict[str, int]]:
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

    This provides a more accurate estimate than a simple ``chars // 4`` heuristic,
    accounting for structured vs unstructured content.
    """
    total = 0
    breakdown: dict[str, int] = {"text": 0, "tool_calls": 0, "system": 0}
    for msg in history:
        role = msg.get("role", "")
        content_raw = msg.get("content")
        text = content_raw if isinstance(content_raw, str) else ""
        tool_calls_raw = msg.get("tool_calls")
        tool_calls: list[ToolCallDict] = cast(
            "LIST[TOOLCALLDICT]", tool_calls_raw if tool_calls_raw is not None else []
        )

        if role == "system" and text:
            total += estimate_tokens_for_text(text, "system", RATIO_SYSTEM, breakdown)
        elif role == "assistant" and tool_calls:
            total += estimate_tokens_for_assistant_with_tool_calls(
                text, tool_calls, breakdown
            )
        elif text:
            total += estimate_tokens_for_text(text, "text", RATIO_TEXT, breakdown)
    return total, breakdown


def x_estimate_tokens__mutmut_39(history: list[LLMMessage]) -> tuple[int, dict[str, int]]:
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

    This provides a more accurate estimate than a simple ``chars // 4`` heuristic,
    accounting for structured vs unstructured content.
    """
    total = 0
    breakdown: dict[str, int] = {"text": 0, "tool_calls": 0, "system": 0}
    for msg in history:
        role = msg.get("role", "")
        content_raw = msg.get("content")
        text = content_raw if isinstance(content_raw, str) else ""
        tool_calls_raw = msg.get("tool_calls")
        tool_calls: list[ToolCallDict] = cast(
            "list[ToolCallDict]", tool_calls_raw if tool_calls_raw is None else []
        )

        if role == "system" and text:
            total += estimate_tokens_for_text(text, "system", RATIO_SYSTEM, breakdown)
        elif role == "assistant" and tool_calls:
            total += estimate_tokens_for_assistant_with_tool_calls(
                text, tool_calls, breakdown
            )
        elif text:
            total += estimate_tokens_for_text(text, "text", RATIO_TEXT, breakdown)
    return total, breakdown


def x_estimate_tokens__mutmut_40(history: list[LLMMessage]) -> tuple[int, dict[str, int]]:
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

    This provides a more accurate estimate than a simple ``chars // 4`` heuristic,
    accounting for structured vs unstructured content.
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

        if role == "system" or text:
            total += estimate_tokens_for_text(text, "system", RATIO_SYSTEM, breakdown)
        elif role == "assistant" and tool_calls:
            total += estimate_tokens_for_assistant_with_tool_calls(
                text, tool_calls, breakdown
            )
        elif text:
            total += estimate_tokens_for_text(text, "text", RATIO_TEXT, breakdown)
    return total, breakdown


def x_estimate_tokens__mutmut_41(history: list[LLMMessage]) -> tuple[int, dict[str, int]]:
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

    This provides a more accurate estimate than a simple ``chars // 4`` heuristic,
    accounting for structured vs unstructured content.
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

        if role != "system" and text:
            total += estimate_tokens_for_text(text, "system", RATIO_SYSTEM, breakdown)
        elif role == "assistant" and tool_calls:
            total += estimate_tokens_for_assistant_with_tool_calls(
                text, tool_calls, breakdown
            )
        elif text:
            total += estimate_tokens_for_text(text, "text", RATIO_TEXT, breakdown)
    return total, breakdown


def x_estimate_tokens__mutmut_42(history: list[LLMMessage]) -> tuple[int, dict[str, int]]:
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

    This provides a more accurate estimate than a simple ``chars // 4`` heuristic,
    accounting for structured vs unstructured content.
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

        if role == "XXsystemXX" and text:
            total += estimate_tokens_for_text(text, "system", RATIO_SYSTEM, breakdown)
        elif role == "assistant" and tool_calls:
            total += estimate_tokens_for_assistant_with_tool_calls(
                text, tool_calls, breakdown
            )
        elif text:
            total += estimate_tokens_for_text(text, "text", RATIO_TEXT, breakdown)
    return total, breakdown


def x_estimate_tokens__mutmut_43(history: list[LLMMessage]) -> tuple[int, dict[str, int]]:
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

    This provides a more accurate estimate than a simple ``chars // 4`` heuristic,
    accounting for structured vs unstructured content.
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

        if role == "SYSTEM" and text:
            total += estimate_tokens_for_text(text, "system", RATIO_SYSTEM, breakdown)
        elif role == "assistant" and tool_calls:
            total += estimate_tokens_for_assistant_with_tool_calls(
                text, tool_calls, breakdown
            )
        elif text:
            total += estimate_tokens_for_text(text, "text", RATIO_TEXT, breakdown)
    return total, breakdown


def x_estimate_tokens__mutmut_44(history: list[LLMMessage]) -> tuple[int, dict[str, int]]:
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

    This provides a more accurate estimate than a simple ``chars // 4`` heuristic,
    accounting for structured vs unstructured content.
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

        if role == "system" and text:
            total = estimate_tokens_for_text(text, "system", RATIO_SYSTEM, breakdown)
        elif role == "assistant" and tool_calls:
            total += estimate_tokens_for_assistant_with_tool_calls(
                text, tool_calls, breakdown
            )
        elif text:
            total += estimate_tokens_for_text(text, "text", RATIO_TEXT, breakdown)
    return total, breakdown


def x_estimate_tokens__mutmut_45(history: list[LLMMessage]) -> tuple[int, dict[str, int]]:
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

    This provides a more accurate estimate than a simple ``chars // 4`` heuristic,
    accounting for structured vs unstructured content.
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

        if role == "system" and text:
            total -= estimate_tokens_for_text(text, "system", RATIO_SYSTEM, breakdown)
        elif role == "assistant" and tool_calls:
            total += estimate_tokens_for_assistant_with_tool_calls(
                text, tool_calls, breakdown
            )
        elif text:
            total += estimate_tokens_for_text(text, "text", RATIO_TEXT, breakdown)
    return total, breakdown


def x_estimate_tokens__mutmut_46(history: list[LLMMessage]) -> tuple[int, dict[str, int]]:
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

    This provides a more accurate estimate than a simple ``chars // 4`` heuristic,
    accounting for structured vs unstructured content.
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

        if role == "system" and text:
            total += estimate_tokens_for_text(None, "system", RATIO_SYSTEM, breakdown)
        elif role == "assistant" and tool_calls:
            total += estimate_tokens_for_assistant_with_tool_calls(
                text, tool_calls, breakdown
            )
        elif text:
            total += estimate_tokens_for_text(text, "text", RATIO_TEXT, breakdown)
    return total, breakdown


def x_estimate_tokens__mutmut_47(history: list[LLMMessage]) -> tuple[int, dict[str, int]]:
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

    This provides a more accurate estimate than a simple ``chars // 4`` heuristic,
    accounting for structured vs unstructured content.
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

        if role == "system" and text:
            total += estimate_tokens_for_text(text, None, RATIO_SYSTEM, breakdown)
        elif role == "assistant" and tool_calls:
            total += estimate_tokens_for_assistant_with_tool_calls(
                text, tool_calls, breakdown
            )
        elif text:
            total += estimate_tokens_for_text(text, "text", RATIO_TEXT, breakdown)
    return total, breakdown


def x_estimate_tokens__mutmut_48(history: list[LLMMessage]) -> tuple[int, dict[str, int]]:
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

    This provides a more accurate estimate than a simple ``chars // 4`` heuristic,
    accounting for structured vs unstructured content.
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

        if role == "system" and text:
            total += estimate_tokens_for_text(text, "system", None, breakdown)
        elif role == "assistant" and tool_calls:
            total += estimate_tokens_for_assistant_with_tool_calls(
                text, tool_calls, breakdown
            )
        elif text:
            total += estimate_tokens_for_text(text, "text", RATIO_TEXT, breakdown)
    return total, breakdown


def x_estimate_tokens__mutmut_49(history: list[LLMMessage]) -> tuple[int, dict[str, int]]:
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

    This provides a more accurate estimate than a simple ``chars // 4`` heuristic,
    accounting for structured vs unstructured content.
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

        if role == "system" and text:
            total += estimate_tokens_for_text(text, "system", RATIO_SYSTEM, None)
        elif role == "assistant" and tool_calls:
            total += estimate_tokens_for_assistant_with_tool_calls(
                text, tool_calls, breakdown
            )
        elif text:
            total += estimate_tokens_for_text(text, "text", RATIO_TEXT, breakdown)
    return total, breakdown


def x_estimate_tokens__mutmut_50(history: list[LLMMessage]) -> tuple[int, dict[str, int]]:
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

    This provides a more accurate estimate than a simple ``chars // 4`` heuristic,
    accounting for structured vs unstructured content.
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

        if role == "system" and text:
            total += estimate_tokens_for_text("system", RATIO_SYSTEM, breakdown)
        elif role == "assistant" and tool_calls:
            total += estimate_tokens_for_assistant_with_tool_calls(
                text, tool_calls, breakdown
            )
        elif text:
            total += estimate_tokens_for_text(text, "text", RATIO_TEXT, breakdown)
    return total, breakdown


def x_estimate_tokens__mutmut_51(history: list[LLMMessage]) -> tuple[int, dict[str, int]]:
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

    This provides a more accurate estimate than a simple ``chars // 4`` heuristic,
    accounting for structured vs unstructured content.
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

        if role == "system" and text:
            total += estimate_tokens_for_text(text, RATIO_SYSTEM, breakdown)
        elif role == "assistant" and tool_calls:
            total += estimate_tokens_for_assistant_with_tool_calls(
                text, tool_calls, breakdown
            )
        elif text:
            total += estimate_tokens_for_text(text, "text", RATIO_TEXT, breakdown)
    return total, breakdown


def x_estimate_tokens__mutmut_52(history: list[LLMMessage]) -> tuple[int, dict[str, int]]:
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

    This provides a more accurate estimate than a simple ``chars // 4`` heuristic,
    accounting for structured vs unstructured content.
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

        if role == "system" and text:
            total += estimate_tokens_for_text(text, "system", breakdown)
        elif role == "assistant" and tool_calls:
            total += estimate_tokens_for_assistant_with_tool_calls(
                text, tool_calls, breakdown
            )
        elif text:
            total += estimate_tokens_for_text(text, "text", RATIO_TEXT, breakdown)
    return total, breakdown


def x_estimate_tokens__mutmut_53(history: list[LLMMessage]) -> tuple[int, dict[str, int]]:
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

    This provides a more accurate estimate than a simple ``chars // 4`` heuristic,
    accounting for structured vs unstructured content.
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

        if role == "system" and text:
            total += estimate_tokens_for_text(text, "system", RATIO_SYSTEM, )
        elif role == "assistant" and tool_calls:
            total += estimate_tokens_for_assistant_with_tool_calls(
                text, tool_calls, breakdown
            )
        elif text:
            total += estimate_tokens_for_text(text, "text", RATIO_TEXT, breakdown)
    return total, breakdown


def x_estimate_tokens__mutmut_54(history: list[LLMMessage]) -> tuple[int, dict[str, int]]:
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

    This provides a more accurate estimate than a simple ``chars // 4`` heuristic,
    accounting for structured vs unstructured content.
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

        if role == "system" and text:
            total += estimate_tokens_for_text(text, "XXsystemXX", RATIO_SYSTEM, breakdown)
        elif role == "assistant" and tool_calls:
            total += estimate_tokens_for_assistant_with_tool_calls(
                text, tool_calls, breakdown
            )
        elif text:
            total += estimate_tokens_for_text(text, "text", RATIO_TEXT, breakdown)
    return total, breakdown


def x_estimate_tokens__mutmut_55(history: list[LLMMessage]) -> tuple[int, dict[str, int]]:
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

    This provides a more accurate estimate than a simple ``chars // 4`` heuristic,
    accounting for structured vs unstructured content.
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

        if role == "system" and text:
            total += estimate_tokens_for_text(text, "SYSTEM", RATIO_SYSTEM, breakdown)
        elif role == "assistant" and tool_calls:
            total += estimate_tokens_for_assistant_with_tool_calls(
                text, tool_calls, breakdown
            )
        elif text:
            total += estimate_tokens_for_text(text, "text", RATIO_TEXT, breakdown)
    return total, breakdown


def x_estimate_tokens__mutmut_56(history: list[LLMMessage]) -> tuple[int, dict[str, int]]:
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

    This provides a more accurate estimate than a simple ``chars // 4`` heuristic,
    accounting for structured vs unstructured content.
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

        if role == "system" and text:
            total += estimate_tokens_for_text(text, "system", RATIO_SYSTEM, breakdown)
        elif role == "assistant" or tool_calls:
            total += estimate_tokens_for_assistant_with_tool_calls(
                text, tool_calls, breakdown
            )
        elif text:
            total += estimate_tokens_for_text(text, "text", RATIO_TEXT, breakdown)
    return total, breakdown


def x_estimate_tokens__mutmut_57(history: list[LLMMessage]) -> tuple[int, dict[str, int]]:
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

    This provides a more accurate estimate than a simple ``chars // 4`` heuristic,
    accounting for structured vs unstructured content.
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

        if role == "system" and text:
            total += estimate_tokens_for_text(text, "system", RATIO_SYSTEM, breakdown)
        elif role != "assistant" and tool_calls:
            total += estimate_tokens_for_assistant_with_tool_calls(
                text, tool_calls, breakdown
            )
        elif text:
            total += estimate_tokens_for_text(text, "text", RATIO_TEXT, breakdown)
    return total, breakdown


def x_estimate_tokens__mutmut_58(history: list[LLMMessage]) -> tuple[int, dict[str, int]]:
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

    This provides a more accurate estimate than a simple ``chars // 4`` heuristic,
    accounting for structured vs unstructured content.
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

        if role == "system" and text:
            total += estimate_tokens_for_text(text, "system", RATIO_SYSTEM, breakdown)
        elif role == "XXassistantXX" and tool_calls:
            total += estimate_tokens_for_assistant_with_tool_calls(
                text, tool_calls, breakdown
            )
        elif text:
            total += estimate_tokens_for_text(text, "text", RATIO_TEXT, breakdown)
    return total, breakdown


def x_estimate_tokens__mutmut_59(history: list[LLMMessage]) -> tuple[int, dict[str, int]]:
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

    This provides a more accurate estimate than a simple ``chars // 4`` heuristic,
    accounting for structured vs unstructured content.
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

        if role == "system" and text:
            total += estimate_tokens_for_text(text, "system", RATIO_SYSTEM, breakdown)
        elif role == "ASSISTANT" and tool_calls:
            total += estimate_tokens_for_assistant_with_tool_calls(
                text, tool_calls, breakdown
            )
        elif text:
            total += estimate_tokens_for_text(text, "text", RATIO_TEXT, breakdown)
    return total, breakdown


def x_estimate_tokens__mutmut_60(history: list[LLMMessage]) -> tuple[int, dict[str, int]]:
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

    This provides a more accurate estimate than a simple ``chars // 4`` heuristic,
    accounting for structured vs unstructured content.
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

        if role == "system" and text:
            total += estimate_tokens_for_text(text, "system", RATIO_SYSTEM, breakdown)
        elif role == "assistant" and tool_calls:
            total = estimate_tokens_for_assistant_with_tool_calls(
                text, tool_calls, breakdown
            )
        elif text:
            total += estimate_tokens_for_text(text, "text", RATIO_TEXT, breakdown)
    return total, breakdown


def x_estimate_tokens__mutmut_61(history: list[LLMMessage]) -> tuple[int, dict[str, int]]:
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

    This provides a more accurate estimate than a simple ``chars // 4`` heuristic,
    accounting for structured vs unstructured content.
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

        if role == "system" and text:
            total += estimate_tokens_for_text(text, "system", RATIO_SYSTEM, breakdown)
        elif role == "assistant" and tool_calls:
            total -= estimate_tokens_for_assistant_with_tool_calls(
                text, tool_calls, breakdown
            )
        elif text:
            total += estimate_tokens_for_text(text, "text", RATIO_TEXT, breakdown)
    return total, breakdown


def x_estimate_tokens__mutmut_62(history: list[LLMMessage]) -> tuple[int, dict[str, int]]:
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

    This provides a more accurate estimate than a simple ``chars // 4`` heuristic,
    accounting for structured vs unstructured content.
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

        if role == "system" and text:
            total += estimate_tokens_for_text(text, "system", RATIO_SYSTEM, breakdown)
        elif role == "assistant" and tool_calls:
            total += estimate_tokens_for_assistant_with_tool_calls(
                None, tool_calls, breakdown
            )
        elif text:
            total += estimate_tokens_for_text(text, "text", RATIO_TEXT, breakdown)
    return total, breakdown


def x_estimate_tokens__mutmut_63(history: list[LLMMessage]) -> tuple[int, dict[str, int]]:
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

    This provides a more accurate estimate than a simple ``chars // 4`` heuristic,
    accounting for structured vs unstructured content.
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

        if role == "system" and text:
            total += estimate_tokens_for_text(text, "system", RATIO_SYSTEM, breakdown)
        elif role == "assistant" and tool_calls:
            total += estimate_tokens_for_assistant_with_tool_calls(
                text, None, breakdown
            )
        elif text:
            total += estimate_tokens_for_text(text, "text", RATIO_TEXT, breakdown)
    return total, breakdown


def x_estimate_tokens__mutmut_64(history: list[LLMMessage]) -> tuple[int, dict[str, int]]:
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

    This provides a more accurate estimate than a simple ``chars // 4`` heuristic,
    accounting for structured vs unstructured content.
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

        if role == "system" and text:
            total += estimate_tokens_for_text(text, "system", RATIO_SYSTEM, breakdown)
        elif role == "assistant" and tool_calls:
            total += estimate_tokens_for_assistant_with_tool_calls(
                text, tool_calls, None
            )
        elif text:
            total += estimate_tokens_for_text(text, "text", RATIO_TEXT, breakdown)
    return total, breakdown


def x_estimate_tokens__mutmut_65(history: list[LLMMessage]) -> tuple[int, dict[str, int]]:
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

    This provides a more accurate estimate than a simple ``chars // 4`` heuristic,
    accounting for structured vs unstructured content.
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

        if role == "system" and text:
            total += estimate_tokens_for_text(text, "system", RATIO_SYSTEM, breakdown)
        elif role == "assistant" and tool_calls:
            total += estimate_tokens_for_assistant_with_tool_calls(
                tool_calls, breakdown
            )
        elif text:
            total += estimate_tokens_for_text(text, "text", RATIO_TEXT, breakdown)
    return total, breakdown


def x_estimate_tokens__mutmut_66(history: list[LLMMessage]) -> tuple[int, dict[str, int]]:
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

    This provides a more accurate estimate than a simple ``chars // 4`` heuristic,
    accounting for structured vs unstructured content.
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

        if role == "system" and text:
            total += estimate_tokens_for_text(text, "system", RATIO_SYSTEM, breakdown)
        elif role == "assistant" and tool_calls:
            total += estimate_tokens_for_assistant_with_tool_calls(
                text, breakdown
            )
        elif text:
            total += estimate_tokens_for_text(text, "text", RATIO_TEXT, breakdown)
    return total, breakdown


def x_estimate_tokens__mutmut_67(history: list[LLMMessage]) -> tuple[int, dict[str, int]]:
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

    This provides a more accurate estimate than a simple ``chars // 4`` heuristic,
    accounting for structured vs unstructured content.
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

        if role == "system" and text:
            total += estimate_tokens_for_text(text, "system", RATIO_SYSTEM, breakdown)
        elif role == "assistant" and tool_calls:
            total += estimate_tokens_for_assistant_with_tool_calls(
                text, tool_calls, )
        elif text:
            total += estimate_tokens_for_text(text, "text", RATIO_TEXT, breakdown)
    return total, breakdown


def x_estimate_tokens__mutmut_68(history: list[LLMMessage]) -> tuple[int, dict[str, int]]:
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

    This provides a more accurate estimate than a simple ``chars // 4`` heuristic,
    accounting for structured vs unstructured content.
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

        if role == "system" and text:
            total += estimate_tokens_for_text(text, "system", RATIO_SYSTEM, breakdown)
        elif role == "assistant" and tool_calls:
            total += estimate_tokens_for_assistant_with_tool_calls(
                text, tool_calls, breakdown
            )
        elif text:
            total = estimate_tokens_for_text(text, "text", RATIO_TEXT, breakdown)
    return total, breakdown


def x_estimate_tokens__mutmut_69(history: list[LLMMessage]) -> tuple[int, dict[str, int]]:
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

    This provides a more accurate estimate than a simple ``chars // 4`` heuristic,
    accounting for structured vs unstructured content.
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

        if role == "system" and text:
            total += estimate_tokens_for_text(text, "system", RATIO_SYSTEM, breakdown)
        elif role == "assistant" and tool_calls:
            total += estimate_tokens_for_assistant_with_tool_calls(
                text, tool_calls, breakdown
            )
        elif text:
            total -= estimate_tokens_for_text(text, "text", RATIO_TEXT, breakdown)
    return total, breakdown


def x_estimate_tokens__mutmut_70(history: list[LLMMessage]) -> tuple[int, dict[str, int]]:
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

    This provides a more accurate estimate than a simple ``chars // 4`` heuristic,
    accounting for structured vs unstructured content.
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

        if role == "system" and text:
            total += estimate_tokens_for_text(text, "system", RATIO_SYSTEM, breakdown)
        elif role == "assistant" and tool_calls:
            total += estimate_tokens_for_assistant_with_tool_calls(
                text, tool_calls, breakdown
            )
        elif text:
            total += estimate_tokens_for_text(None, "text", RATIO_TEXT, breakdown)
    return total, breakdown


def x_estimate_tokens__mutmut_71(history: list[LLMMessage]) -> tuple[int, dict[str, int]]:
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

    This provides a more accurate estimate than a simple ``chars // 4`` heuristic,
    accounting for structured vs unstructured content.
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

        if role == "system" and text:
            total += estimate_tokens_for_text(text, "system", RATIO_SYSTEM, breakdown)
        elif role == "assistant" and tool_calls:
            total += estimate_tokens_for_assistant_with_tool_calls(
                text, tool_calls, breakdown
            )
        elif text:
            total += estimate_tokens_for_text(text, None, RATIO_TEXT, breakdown)
    return total, breakdown


def x_estimate_tokens__mutmut_72(history: list[LLMMessage]) -> tuple[int, dict[str, int]]:
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

    This provides a more accurate estimate than a simple ``chars // 4`` heuristic,
    accounting for structured vs unstructured content.
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

        if role == "system" and text:
            total += estimate_tokens_for_text(text, "system", RATIO_SYSTEM, breakdown)
        elif role == "assistant" and tool_calls:
            total += estimate_tokens_for_assistant_with_tool_calls(
                text, tool_calls, breakdown
            )
        elif text:
            total += estimate_tokens_for_text(text, "text", None, breakdown)
    return total, breakdown


def x_estimate_tokens__mutmut_73(history: list[LLMMessage]) -> tuple[int, dict[str, int]]:
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

    This provides a more accurate estimate than a simple ``chars // 4`` heuristic,
    accounting for structured vs unstructured content.
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

        if role == "system" and text:
            total += estimate_tokens_for_text(text, "system", RATIO_SYSTEM, breakdown)
        elif role == "assistant" and tool_calls:
            total += estimate_tokens_for_assistant_with_tool_calls(
                text, tool_calls, breakdown
            )
        elif text:
            total += estimate_tokens_for_text(text, "text", RATIO_TEXT, None)
    return total, breakdown


def x_estimate_tokens__mutmut_74(history: list[LLMMessage]) -> tuple[int, dict[str, int]]:
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

    This provides a more accurate estimate than a simple ``chars // 4`` heuristic,
    accounting for structured vs unstructured content.
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

        if role == "system" and text:
            total += estimate_tokens_for_text(text, "system", RATIO_SYSTEM, breakdown)
        elif role == "assistant" and tool_calls:
            total += estimate_tokens_for_assistant_with_tool_calls(
                text, tool_calls, breakdown
            )
        elif text:
            total += estimate_tokens_for_text("text", RATIO_TEXT, breakdown)
    return total, breakdown


def x_estimate_tokens__mutmut_75(history: list[LLMMessage]) -> tuple[int, dict[str, int]]:
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

    This provides a more accurate estimate than a simple ``chars // 4`` heuristic,
    accounting for structured vs unstructured content.
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

        if role == "system" and text:
            total += estimate_tokens_for_text(text, "system", RATIO_SYSTEM, breakdown)
        elif role == "assistant" and tool_calls:
            total += estimate_tokens_for_assistant_with_tool_calls(
                text, tool_calls, breakdown
            )
        elif text:
            total += estimate_tokens_for_text(text, RATIO_TEXT, breakdown)
    return total, breakdown


def x_estimate_tokens__mutmut_76(history: list[LLMMessage]) -> tuple[int, dict[str, int]]:
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

    This provides a more accurate estimate than a simple ``chars // 4`` heuristic,
    accounting for structured vs unstructured content.
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

        if role == "system" and text:
            total += estimate_tokens_for_text(text, "system", RATIO_SYSTEM, breakdown)
        elif role == "assistant" and tool_calls:
            total += estimate_tokens_for_assistant_with_tool_calls(
                text, tool_calls, breakdown
            )
        elif text:
            total += estimate_tokens_for_text(text, "text", breakdown)
    return total, breakdown


def x_estimate_tokens__mutmut_77(history: list[LLMMessage]) -> tuple[int, dict[str, int]]:
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

    This provides a more accurate estimate than a simple ``chars // 4`` heuristic,
    accounting for structured vs unstructured content.
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

        if role == "system" and text:
            total += estimate_tokens_for_text(text, "system", RATIO_SYSTEM, breakdown)
        elif role == "assistant" and tool_calls:
            total += estimate_tokens_for_assistant_with_tool_calls(
                text, tool_calls, breakdown
            )
        elif text:
            total += estimate_tokens_for_text(text, "text", RATIO_TEXT, )
    return total, breakdown


def x_estimate_tokens__mutmut_78(history: list[LLMMessage]) -> tuple[int, dict[str, int]]:
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

    This provides a more accurate estimate than a simple ``chars // 4`` heuristic,
    accounting for structured vs unstructured content.
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

        if role == "system" and text:
            total += estimate_tokens_for_text(text, "system", RATIO_SYSTEM, breakdown)
        elif role == "assistant" and tool_calls:
            total += estimate_tokens_for_assistant_with_tool_calls(
                text, tool_calls, breakdown
            )
        elif text:
            total += estimate_tokens_for_text(text, "XXtextXX", RATIO_TEXT, breakdown)
    return total, breakdown


def x_estimate_tokens__mutmut_79(history: list[LLMMessage]) -> tuple[int, dict[str, int]]:
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

    This provides a more accurate estimate than a simple ``chars // 4`` heuristic,
    accounting for structured vs unstructured content.
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

        if role == "system" and text:
            total += estimate_tokens_for_text(text, "system", RATIO_SYSTEM, breakdown)
        elif role == "assistant" and tool_calls:
            total += estimate_tokens_for_assistant_with_tool_calls(
                text, tool_calls, breakdown
            )
        elif text:
            total += estimate_tokens_for_text(text, "TEXT", RATIO_TEXT, breakdown)
    return total, breakdown

mutants_x_estimate_tokens__mutmut['_mutmut_orig'] = x_estimate_tokens__mutmut_orig # type: ignore # mutmut generated
mutants_x_estimate_tokens__mutmut['x_estimate_tokens__mutmut_1'] = x_estimate_tokens__mutmut_1 # type: ignore # mutmut generated
mutants_x_estimate_tokens__mutmut['x_estimate_tokens__mutmut_2'] = x_estimate_tokens__mutmut_2 # type: ignore # mutmut generated
mutants_x_estimate_tokens__mutmut['x_estimate_tokens__mutmut_3'] = x_estimate_tokens__mutmut_3 # type: ignore # mutmut generated
mutants_x_estimate_tokens__mutmut['x_estimate_tokens__mutmut_4'] = x_estimate_tokens__mutmut_4 # type: ignore # mutmut generated
mutants_x_estimate_tokens__mutmut['x_estimate_tokens__mutmut_5'] = x_estimate_tokens__mutmut_5 # type: ignore # mutmut generated
mutants_x_estimate_tokens__mutmut['x_estimate_tokens__mutmut_6'] = x_estimate_tokens__mutmut_6 # type: ignore # mutmut generated
mutants_x_estimate_tokens__mutmut['x_estimate_tokens__mutmut_7'] = x_estimate_tokens__mutmut_7 # type: ignore # mutmut generated
mutants_x_estimate_tokens__mutmut['x_estimate_tokens__mutmut_8'] = x_estimate_tokens__mutmut_8 # type: ignore # mutmut generated
mutants_x_estimate_tokens__mutmut['x_estimate_tokens__mutmut_9'] = x_estimate_tokens__mutmut_9 # type: ignore # mutmut generated
mutants_x_estimate_tokens__mutmut['x_estimate_tokens__mutmut_10'] = x_estimate_tokens__mutmut_10 # type: ignore # mutmut generated
mutants_x_estimate_tokens__mutmut['x_estimate_tokens__mutmut_11'] = x_estimate_tokens__mutmut_11 # type: ignore # mutmut generated
mutants_x_estimate_tokens__mutmut['x_estimate_tokens__mutmut_12'] = x_estimate_tokens__mutmut_12 # type: ignore # mutmut generated
mutants_x_estimate_tokens__mutmut['x_estimate_tokens__mutmut_13'] = x_estimate_tokens__mutmut_13 # type: ignore # mutmut generated
mutants_x_estimate_tokens__mutmut['x_estimate_tokens__mutmut_14'] = x_estimate_tokens__mutmut_14 # type: ignore # mutmut generated
mutants_x_estimate_tokens__mutmut['x_estimate_tokens__mutmut_15'] = x_estimate_tokens__mutmut_15 # type: ignore # mutmut generated
mutants_x_estimate_tokens__mutmut['x_estimate_tokens__mutmut_16'] = x_estimate_tokens__mutmut_16 # type: ignore # mutmut generated
mutants_x_estimate_tokens__mutmut['x_estimate_tokens__mutmut_17'] = x_estimate_tokens__mutmut_17 # type: ignore # mutmut generated
mutants_x_estimate_tokens__mutmut['x_estimate_tokens__mutmut_18'] = x_estimate_tokens__mutmut_18 # type: ignore # mutmut generated
mutants_x_estimate_tokens__mutmut['x_estimate_tokens__mutmut_19'] = x_estimate_tokens__mutmut_19 # type: ignore # mutmut generated
mutants_x_estimate_tokens__mutmut['x_estimate_tokens__mutmut_20'] = x_estimate_tokens__mutmut_20 # type: ignore # mutmut generated
mutants_x_estimate_tokens__mutmut['x_estimate_tokens__mutmut_21'] = x_estimate_tokens__mutmut_21 # type: ignore # mutmut generated
mutants_x_estimate_tokens__mutmut['x_estimate_tokens__mutmut_22'] = x_estimate_tokens__mutmut_22 # type: ignore # mutmut generated
mutants_x_estimate_tokens__mutmut['x_estimate_tokens__mutmut_23'] = x_estimate_tokens__mutmut_23 # type: ignore # mutmut generated
mutants_x_estimate_tokens__mutmut['x_estimate_tokens__mutmut_24'] = x_estimate_tokens__mutmut_24 # type: ignore # mutmut generated
mutants_x_estimate_tokens__mutmut['x_estimate_tokens__mutmut_25'] = x_estimate_tokens__mutmut_25 # type: ignore # mutmut generated
mutants_x_estimate_tokens__mutmut['x_estimate_tokens__mutmut_26'] = x_estimate_tokens__mutmut_26 # type: ignore # mutmut generated
mutants_x_estimate_tokens__mutmut['x_estimate_tokens__mutmut_27'] = x_estimate_tokens__mutmut_27 # type: ignore # mutmut generated
mutants_x_estimate_tokens__mutmut['x_estimate_tokens__mutmut_28'] = x_estimate_tokens__mutmut_28 # type: ignore # mutmut generated
mutants_x_estimate_tokens__mutmut['x_estimate_tokens__mutmut_29'] = x_estimate_tokens__mutmut_29 # type: ignore # mutmut generated
mutants_x_estimate_tokens__mutmut['x_estimate_tokens__mutmut_30'] = x_estimate_tokens__mutmut_30 # type: ignore # mutmut generated
mutants_x_estimate_tokens__mutmut['x_estimate_tokens__mutmut_31'] = x_estimate_tokens__mutmut_31 # type: ignore # mutmut generated
mutants_x_estimate_tokens__mutmut['x_estimate_tokens__mutmut_32'] = x_estimate_tokens__mutmut_32 # type: ignore # mutmut generated
mutants_x_estimate_tokens__mutmut['x_estimate_tokens__mutmut_33'] = x_estimate_tokens__mutmut_33 # type: ignore # mutmut generated
mutants_x_estimate_tokens__mutmut['x_estimate_tokens__mutmut_34'] = x_estimate_tokens__mutmut_34 # type: ignore # mutmut generated
mutants_x_estimate_tokens__mutmut['x_estimate_tokens__mutmut_35'] = x_estimate_tokens__mutmut_35 # type: ignore # mutmut generated
mutants_x_estimate_tokens__mutmut['x_estimate_tokens__mutmut_36'] = x_estimate_tokens__mutmut_36 # type: ignore # mutmut generated
mutants_x_estimate_tokens__mutmut['x_estimate_tokens__mutmut_37'] = x_estimate_tokens__mutmut_37 # type: ignore # mutmut generated
mutants_x_estimate_tokens__mutmut['x_estimate_tokens__mutmut_38'] = x_estimate_tokens__mutmut_38 # type: ignore # mutmut generated
mutants_x_estimate_tokens__mutmut['x_estimate_tokens__mutmut_39'] = x_estimate_tokens__mutmut_39 # type: ignore # mutmut generated
mutants_x_estimate_tokens__mutmut['x_estimate_tokens__mutmut_40'] = x_estimate_tokens__mutmut_40 # type: ignore # mutmut generated
mutants_x_estimate_tokens__mutmut['x_estimate_tokens__mutmut_41'] = x_estimate_tokens__mutmut_41 # type: ignore # mutmut generated
mutants_x_estimate_tokens__mutmut['x_estimate_tokens__mutmut_42'] = x_estimate_tokens__mutmut_42 # type: ignore # mutmut generated
mutants_x_estimate_tokens__mutmut['x_estimate_tokens__mutmut_43'] = x_estimate_tokens__mutmut_43 # type: ignore # mutmut generated
mutants_x_estimate_tokens__mutmut['x_estimate_tokens__mutmut_44'] = x_estimate_tokens__mutmut_44 # type: ignore # mutmut generated
mutants_x_estimate_tokens__mutmut['x_estimate_tokens__mutmut_45'] = x_estimate_tokens__mutmut_45 # type: ignore # mutmut generated
mutants_x_estimate_tokens__mutmut['x_estimate_tokens__mutmut_46'] = x_estimate_tokens__mutmut_46 # type: ignore # mutmut generated
mutants_x_estimate_tokens__mutmut['x_estimate_tokens__mutmut_47'] = x_estimate_tokens__mutmut_47 # type: ignore # mutmut generated
mutants_x_estimate_tokens__mutmut['x_estimate_tokens__mutmut_48'] = x_estimate_tokens__mutmut_48 # type: ignore # mutmut generated
mutants_x_estimate_tokens__mutmut['x_estimate_tokens__mutmut_49'] = x_estimate_tokens__mutmut_49 # type: ignore # mutmut generated
mutants_x_estimate_tokens__mutmut['x_estimate_tokens__mutmut_50'] = x_estimate_tokens__mutmut_50 # type: ignore # mutmut generated
mutants_x_estimate_tokens__mutmut['x_estimate_tokens__mutmut_51'] = x_estimate_tokens__mutmut_51 # type: ignore # mutmut generated
mutants_x_estimate_tokens__mutmut['x_estimate_tokens__mutmut_52'] = x_estimate_tokens__mutmut_52 # type: ignore # mutmut generated
mutants_x_estimate_tokens__mutmut['x_estimate_tokens__mutmut_53'] = x_estimate_tokens__mutmut_53 # type: ignore # mutmut generated
mutants_x_estimate_tokens__mutmut['x_estimate_tokens__mutmut_54'] = x_estimate_tokens__mutmut_54 # type: ignore # mutmut generated
mutants_x_estimate_tokens__mutmut['x_estimate_tokens__mutmut_55'] = x_estimate_tokens__mutmut_55 # type: ignore # mutmut generated
mutants_x_estimate_tokens__mutmut['x_estimate_tokens__mutmut_56'] = x_estimate_tokens__mutmut_56 # type: ignore # mutmut generated
mutants_x_estimate_tokens__mutmut['x_estimate_tokens__mutmut_57'] = x_estimate_tokens__mutmut_57 # type: ignore # mutmut generated
mutants_x_estimate_tokens__mutmut['x_estimate_tokens__mutmut_58'] = x_estimate_tokens__mutmut_58 # type: ignore # mutmut generated
mutants_x_estimate_tokens__mutmut['x_estimate_tokens__mutmut_59'] = x_estimate_tokens__mutmut_59 # type: ignore # mutmut generated
mutants_x_estimate_tokens__mutmut['x_estimate_tokens__mutmut_60'] = x_estimate_tokens__mutmut_60 # type: ignore # mutmut generated
mutants_x_estimate_tokens__mutmut['x_estimate_tokens__mutmut_61'] = x_estimate_tokens__mutmut_61 # type: ignore # mutmut generated
mutants_x_estimate_tokens__mutmut['x_estimate_tokens__mutmut_62'] = x_estimate_tokens__mutmut_62 # type: ignore # mutmut generated
mutants_x_estimate_tokens__mutmut['x_estimate_tokens__mutmut_63'] = x_estimate_tokens__mutmut_63 # type: ignore # mutmut generated
mutants_x_estimate_tokens__mutmut['x_estimate_tokens__mutmut_64'] = x_estimate_tokens__mutmut_64 # type: ignore # mutmut generated
mutants_x_estimate_tokens__mutmut['x_estimate_tokens__mutmut_65'] = x_estimate_tokens__mutmut_65 # type: ignore # mutmut generated
mutants_x_estimate_tokens__mutmut['x_estimate_tokens__mutmut_66'] = x_estimate_tokens__mutmut_66 # type: ignore # mutmut generated
mutants_x_estimate_tokens__mutmut['x_estimate_tokens__mutmut_67'] = x_estimate_tokens__mutmut_67 # type: ignore # mutmut generated
mutants_x_estimate_tokens__mutmut['x_estimate_tokens__mutmut_68'] = x_estimate_tokens__mutmut_68 # type: ignore # mutmut generated
mutants_x_estimate_tokens__mutmut['x_estimate_tokens__mutmut_69'] = x_estimate_tokens__mutmut_69 # type: ignore # mutmut generated
mutants_x_estimate_tokens__mutmut['x_estimate_tokens__mutmut_70'] = x_estimate_tokens__mutmut_70 # type: ignore # mutmut generated
mutants_x_estimate_tokens__mutmut['x_estimate_tokens__mutmut_71'] = x_estimate_tokens__mutmut_71 # type: ignore # mutmut generated
mutants_x_estimate_tokens__mutmut['x_estimate_tokens__mutmut_72'] = x_estimate_tokens__mutmut_72 # type: ignore # mutmut generated
mutants_x_estimate_tokens__mutmut['x_estimate_tokens__mutmut_73'] = x_estimate_tokens__mutmut_73 # type: ignore # mutmut generated
mutants_x_estimate_tokens__mutmut['x_estimate_tokens__mutmut_74'] = x_estimate_tokens__mutmut_74 # type: ignore # mutmut generated
mutants_x_estimate_tokens__mutmut['x_estimate_tokens__mutmut_75'] = x_estimate_tokens__mutmut_75 # type: ignore # mutmut generated
mutants_x_estimate_tokens__mutmut['x_estimate_tokens__mutmut_76'] = x_estimate_tokens__mutmut_76 # type: ignore # mutmut generated
mutants_x_estimate_tokens__mutmut['x_estimate_tokens__mutmut_77'] = x_estimate_tokens__mutmut_77 # type: ignore # mutmut generated
mutants_x_estimate_tokens__mutmut['x_estimate_tokens__mutmut_78'] = x_estimate_tokens__mutmut_78 # type: ignore # mutmut generated
mutants_x_estimate_tokens__mutmut['x_estimate_tokens__mutmut_79'] = x_estimate_tokens__mutmut_79 # type: ignore # mutmut generated
