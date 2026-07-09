#!/usr/bin/env python3
"""rag/llm_prompts.py
LLM prompt constants, exception types, DTOs, and helper functions for the RAG pipeline.

Provides:
  MqeParseError        — MQE JSON parse failure
  RagExpansionError    — MQE expansion HTTP/parse failure
  RagRerankError       — Cross-encoder rerank HTTP/parse failure
  MqeParseResult       — internal DTO from MQE JSON parsing
  _MQE_TEMPERATURE     — MQE temperature constant
  _MQE_MAX_TOKENS      — MQE max tokens constant
  _RERANK_TEMPERATURE  — rerank temperature constant
  _RERANK_MAX_TOKENS   — rerank max tokens constant
  _SUMMARIZE_*         — summarization constants
  _REFINER_*           — context refiner constants
  _DEFAULT_RERANK_SCORE — default score when LLM omits a candidate
  _mqe_prompt          — build MQE rephrasing prompt
  _parse_mqe_response  — extract/validate JSON array from LLM output
  _extract_chat_content — extract content text from chat completion response
  _build_rerank_prompt  — build Cross-Encoder scoring prompt
  _apply_rerank_scores  — parse LLM score output and return top_k candidates

Import from here:  from rag.llm_prompts import RagLLM, RagExpansionError, ...
"""

from __future__ import annotations

import logging
import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import NotRequired, TypedDict, cast

import orjson
from rag.types import (
    RagHit,  # noqa: F401 — imported for use in this module
    RankedHit,
)

logger = logging.getLogger(__name__)


class _ChatCompletionChoice(TypedDict):
    """Typed dict for a single choice in a chat completion response."""

    message: NotRequired[dict[str, object]]


class _ChatCompletionResponse(TypedDict):
    """Typed dict for an OpenAI-compatible chat completion response."""

    choices: list[_ChatCompletionChoice]


# ─────────────────────────────────────────────────────────────────────────────
# Exception types
# ─────────────────────────────────────────────────────────────────────────────


class MqeParseError(ValueError):
    """Raised when the MQE LLM response cannot be parsed as a valid query list."""


class RagExpansionError(RuntimeError):
    """Raised when MQE query expansion fails (HTTP, parse, or connection error)."""


class RagRerankError(RuntimeError):
    """Raised when cross-encoder reranking fails (HTTP, parse, or connection error)."""


# ─────────────────────────────────────────────────────────────────────────────
# LLM call parameters
# ─────────────────────────────────────────────────────────────────────────────

# Higher temperature (0.6) encourages lexical diversity across paraphrases.
_MQE_TEMPERATURE: float = 0.6
_MQE_MAX_TOKENS: int = 300

# temperature=0 for deterministic relevance scores to reduce variance.
_RERANK_TEMPERATURE: float = 0.0
_RERANK_MAX_TOKENS: int = 256

_SUMMARIZE_TEMPERATURE: float = 0.2
_SUMMARIZE_MAX_TOKENS: int = 256

# Maximum characters of tool result text sent to the summarization LLM.
_SUMMARIZE_INPUT_MAX_CHARS: int = 8000

_SUMMARIZE_PROMPT_TEMPLATE: str = (
    "Summarize the following tool execution result in 3-5 sentences,"
    " preserving all key facts, values, and important details.\n"
    "Tool: {tool_name}\n"
    "Args: {args_str}\n\n"
    "Result:\n{text_preview}\n"
)

# Low temperature for precise, fact-preserving extraction.
_REFINER_TEMPERATURE: float = 0.1
_REFINER_MAX_TOKENS: int = 512

_REFINER_PROMPT_TEMPLATE: str = (
    "Extract and summarize only the key facts and information relevant to the question"
    " from the reference documents below."
    " Be concise \u2014 preserve specific values, numbers, and technical details."
    " Omit irrelevant content. Group related information naturally.\n\n"
    "Question: {query}\n\n"
    "Reference documents:\n{items_text}\n"
)

# Default relevance score assigned when LLM omits a candidate in rerank output
_DEFAULT_RERANK_SCORE = 5.0


# ─────────────────────────────────────────────────────────────────────────────
# Internal DTOs
# ─────────────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class MqeParseResult:
    """Internal typed result from MQE JSON parsing."""

    queries: list[str]  # original_query included as first element


# ─────────────────────────────────────────────────────────────────────────────
# Internal prompt helpers
# ─────────────────────────────────────────────────────────────────────────────


def _mqe_prompt(query: str, context: str, cfg: Mapping[str, object]) -> str:
    """Build the MQE rephrasing prompt, prepending conversation context when given.

    context holds recent user utterances; it is search-only and is never sent
    directly to the final LLM answer prompt.
    """
    template = cfg.get("mqe_prompt_template", "")
    if not isinstance(template, str):
        raise TypeError(
            f"mqe_prompt_template must be str, got {type(template).__name__}"
        )
    n_queries = cfg.get("mqe_n_queries", 3)
    if not isinstance(n_queries, int):
        raise TypeError(f"mqe_n_queries must be int, got {type(n_queries).__name__}")
    prompt = template.format(
        n_queries=n_queries,
        query=query,
    )
    if context:
        prompt = f"Context: {context}\n\n{prompt}"
    return str(prompt)


def _parse_mqe_response(raw: str, original_query: str) -> MqeParseResult:
    """Extract and validate a JSON array of paraphrases from raw LLM output.

    Raises MqeParseError when the response cannot be parsed as a string list.
    """
    m = re.search(r"\[.*\]", raw, re.DOTALL)
    if not m:
        raise MqeParseError(f"MQE response contains no JSON array: {raw!r}")
    try:
        expanded = orjson.loads(m.group())
    except orjson.JSONDecodeError as e:
        raise MqeParseError(f"MQE response JSON is malformed: {e}") from e
    if not isinstance(expanded, list):
        raise MqeParseError(
            f"MQE response JSON is not a list: {type(expanded).__name__}"
        )
    valid = [q for q in expanded if isinstance(q, str) and q.strip()]
    logger.info("MQE: %s queries expanded from original", len(valid))
    return MqeParseResult(queries=[original_query] + valid)


def _extract_chat_content(data: _ChatCompletionResponse) -> str:
    """Extract content text from an OpenAI-compatible chat completion response.

    Raises ValueError if the response is malformed or missing expected fields.
    """
    choices = data.get("choices")
    if not isinstance(choices, list) or not choices:
        raise ValueError("Unexpected LLM response: missing or empty 'choices'")
    first = choices[0]
    if not isinstance(first, dict):
        raise ValueError("Unexpected LLM response: choices[0] is not a dict")
    message = first.get("message")
    if not isinstance(message, dict):
        raise ValueError("Unexpected LLM response: choices[0].message is not a dict")
    content = message.get("content")
    if not isinstance(content, str):
        raise ValueError(
            f"Unexpected LLM response: content is not a str, got {type(content).__name__}"
        )
    return content.strip()


def _build_rerank_prompt(
    query: str, candidates: list[RagHit], cfg: Mapping[str, object]
) -> str:
    """Build the Cross-Encoder scoring prompt from the configured template."""
    items_text = ""
    for i, chunk in enumerate(candidates, start=1):
        preview = chunk.content[:300].replace("\n", " ")
        items_text += f"\n{i}. {preview}"
    template = cfg.get("rerank_prompt_template", "")
    if not isinstance(template, str):
        raise TypeError(
            f"rerank_prompt_template must be str, got {type(template).__name__}"
        )
    return str(
        template.format(query=query, items_text=items_text),
    )


def _apply_rerank_scores(
    raw: str,
    candidates: list[RagHit],
    top_k: int,
) -> list[RagHit] | None:
    """Parse LLM score output and return top_k candidates sorted by score.

    Returns None on parse failure so the caller can fall back to RRF order.
    """
    m = re.search(r"\{.*\}", raw, re.DOTALL)
    if not m:
        return None
    try:
        score_map: dict[str, int | float] = orjson.loads(m.group())
    except orjson.JSONDecodeError:
        logger.warning("Rerank score JSON is malformed")
        return None
    scored = []
    for i, chunk in enumerate(candidates, start=1):
        score_val = score_map.get(str(i), _DEFAULT_RERANK_SCORE)
        try:
            score = float(score_val)
        except (ValueError, TypeError):
            logger.warning(
                "Rerank: non-numeric score %r for candidate %s, using default",
                score_val,
                i,
            )
            score = _DEFAULT_RERANK_SCORE
        scored.append(
            RankedHit(
                chunk_id=chunk.chunk_id,
                content=chunk.content,
                url=chunk.url,
                title=chunk.title,
                distance=chunk.distance,
                bm25_score=chunk.bm25_score,
                rrf_score=getattr(chunk, "rrf_score", 0.0),
                rerank_score=score,
            )
        )
    scored.sort(key=lambda x: cast(float, x.rerank_score or 0.0), reverse=True)
    logger.info("Cross-Encoder rerank: top_k=%s selected", top_k)
    return cast("list[RagHit]", scored[:top_k])


__all__ = [
    "MqeParseError",
    "RagExpansionError",
    "RagRerankError",
    "MqeParseResult",
    "_MQE_TEMPERATURE",
    "_MQE_MAX_TOKENS",
    "_RERANK_TEMPERATURE",
    "_RERANK_MAX_TOKENS",
    "_SUMMARIZE_TEMPERATURE",
    "_SUMMARIZE_MAX_TOKENS",
    "_SUMMARIZE_INPUT_MAX_CHARS",
    "_SUMMARIZE_PROMPT_TEMPLATE",
    "_REFINER_TEMPERATURE",
    "_REFINER_MAX_TOKENS",
    "_REFINER_PROMPT_TEMPLATE",
    "_DEFAULT_RERANK_SCORE",
    "_mqe_prompt",
    "_parse_mqe_response",
    "_extract_chat_content",
    "_build_rerank_prompt",
    "_apply_rerank_scores",
]
