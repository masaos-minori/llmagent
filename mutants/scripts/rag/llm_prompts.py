#!/usr/bin/env python3
"""scripts/rag/llm_prompts.py

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
   _build_rerank_prompt  — build Cross-Encoder scoring prompt
  _apply_rerank_scores  — parse LLM score output and return top_k candidates

Import from here:  from rag.llm_prompts import RagExpansionError, RagRerankError, ...
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import cast

import orjson
from shared.types import (
    RagConfig,
    RagHit,
    RankedHit,
)

logger = logging.getLogger(__name__)


from mutmut.mutation.trampoline import wrap_in_trampoline as _mutmut_mutated, MutantDict


# ──────────────────────────────────────────────────────────────────────────────
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
mutants_x__mqe_prompt__mutmut: MutantDict = {}  # type: ignore


# ─────────────────────────────────────────────────────────────────────────────
# Internal prompt helpers
# ─────────────────────────────────────────────────────────────────────────────


@_mutmut_mutated(mutants_x__mqe_prompt__mutmut)
def _mqe_prompt(query: str, context: str, cfg: RagConfig) -> str:
    """Build the MQE rephrasing prompt, prepending conversation context when given.
    ...
    context holds recent user utterances; it is search-only and is never sent
    directly to the final LLM answer prompt.
    """
    template = cfg.mqe_prompt_template
    if not isinstance(template, str):
        raise TypeError(
            f"mqe_prompt_template must be str, got {type(template).__name__}"
        )
    n_queries = cfg.mqe_n_queries
    if not isinstance(n_queries, int):
        raise TypeError(f"mqe_n_queries must be int, got {type(n_queries).__name__}")
    prompt = template.format(
        n_queries=n_queries,
        query=query,
    )
    if context:
        prompt = f"Context: {context}\n\n{prompt}"
    return str(prompt)


# ─────────────────────────────────────────────────────────────────────────────
# Internal prompt helpers
# ─────────────────────────────────────────────────────────────────────────────


def x__mqe_prompt__mutmut_orig(query: str, context: str, cfg: RagConfig) -> str:
    """Build the MQE rephrasing prompt, prepending conversation context when given.
    ...
    context holds recent user utterances; it is search-only and is never sent
    directly to the final LLM answer prompt.
    """
    template = cfg.mqe_prompt_template
    if not isinstance(template, str):
        raise TypeError(
            f"mqe_prompt_template must be str, got {type(template).__name__}"
        )
    n_queries = cfg.mqe_n_queries
    if not isinstance(n_queries, int):
        raise TypeError(f"mqe_n_queries must be int, got {type(n_queries).__name__}")
    prompt = template.format(
        n_queries=n_queries,
        query=query,
    )
    if context:
        prompt = f"Context: {context}\n\n{prompt}"
    return str(prompt)


# ─────────────────────────────────────────────────────────────────────────────
# Internal prompt helpers
# ─────────────────────────────────────────────────────────────────────────────


def x__mqe_prompt__mutmut_1(query: str, context: str, cfg: RagConfig) -> str:
    """Build the MQE rephrasing prompt, prepending conversation context when given.
    ...
    context holds recent user utterances; it is search-only and is never sent
    directly to the final LLM answer prompt.
    """
    template = None
    if not isinstance(template, str):
        raise TypeError(
            f"mqe_prompt_template must be str, got {type(template).__name__}"
        )
    n_queries = cfg.mqe_n_queries
    if not isinstance(n_queries, int):
        raise TypeError(f"mqe_n_queries must be int, got {type(n_queries).__name__}")
    prompt = template.format(
        n_queries=n_queries,
        query=query,
    )
    if context:
        prompt = f"Context: {context}\n\n{prompt}"
    return str(prompt)


# ─────────────────────────────────────────────────────────────────────────────
# Internal prompt helpers
# ─────────────────────────────────────────────────────────────────────────────


def x__mqe_prompt__mutmut_2(query: str, context: str, cfg: RagConfig) -> str:
    """Build the MQE rephrasing prompt, prepending conversation context when given.
    ...
    context holds recent user utterances; it is search-only and is never sent
    directly to the final LLM answer prompt.
    """
    template = cfg.mqe_prompt_template
    if isinstance(template, str):
        raise TypeError(
            f"mqe_prompt_template must be str, got {type(template).__name__}"
        )
    n_queries = cfg.mqe_n_queries
    if not isinstance(n_queries, int):
        raise TypeError(f"mqe_n_queries must be int, got {type(n_queries).__name__}")
    prompt = template.format(
        n_queries=n_queries,
        query=query,
    )
    if context:
        prompt = f"Context: {context}\n\n{prompt}"
    return str(prompt)


# ─────────────────────────────────────────────────────────────────────────────
# Internal prompt helpers
# ─────────────────────────────────────────────────────────────────────────────


def x__mqe_prompt__mutmut_3(query: str, context: str, cfg: RagConfig) -> str:
    """Build the MQE rephrasing prompt, prepending conversation context when given.
    ...
    context holds recent user utterances; it is search-only and is never sent
    directly to the final LLM answer prompt.
    """
    template = cfg.mqe_prompt_template
    if not isinstance(template, str):
        raise TypeError(
            None
        )
    n_queries = cfg.mqe_n_queries
    if not isinstance(n_queries, int):
        raise TypeError(f"mqe_n_queries must be int, got {type(n_queries).__name__}")
    prompt = template.format(
        n_queries=n_queries,
        query=query,
    )
    if context:
        prompt = f"Context: {context}\n\n{prompt}"
    return str(prompt)


# ─────────────────────────────────────────────────────────────────────────────
# Internal prompt helpers
# ─────────────────────────────────────────────────────────────────────────────


def x__mqe_prompt__mutmut_4(query: str, context: str, cfg: RagConfig) -> str:
    """Build the MQE rephrasing prompt, prepending conversation context when given.
    ...
    context holds recent user utterances; it is search-only and is never sent
    directly to the final LLM answer prompt.
    """
    template = cfg.mqe_prompt_template
    if not isinstance(template, str):
        raise TypeError(
            f"mqe_prompt_template must be str, got {type(None).__name__}"
        )
    n_queries = cfg.mqe_n_queries
    if not isinstance(n_queries, int):
        raise TypeError(f"mqe_n_queries must be int, got {type(n_queries).__name__}")
    prompt = template.format(
        n_queries=n_queries,
        query=query,
    )
    if context:
        prompt = f"Context: {context}\n\n{prompt}"
    return str(prompt)


# ─────────────────────────────────────────────────────────────────────────────
# Internal prompt helpers
# ─────────────────────────────────────────────────────────────────────────────


def x__mqe_prompt__mutmut_5(query: str, context: str, cfg: RagConfig) -> str:
    """Build the MQE rephrasing prompt, prepending conversation context when given.
    ...
    context holds recent user utterances; it is search-only and is never sent
    directly to the final LLM answer prompt.
    """
    template = cfg.mqe_prompt_template
    if not isinstance(template, str):
        raise TypeError(
            f"mqe_prompt_template must be str, got {type(template).__name__}"
        )
    n_queries = None
    if not isinstance(n_queries, int):
        raise TypeError(f"mqe_n_queries must be int, got {type(n_queries).__name__}")
    prompt = template.format(
        n_queries=n_queries,
        query=query,
    )
    if context:
        prompt = f"Context: {context}\n\n{prompt}"
    return str(prompt)


# ─────────────────────────────────────────────────────────────────────────────
# Internal prompt helpers
# ─────────────────────────────────────────────────────────────────────────────


def x__mqe_prompt__mutmut_6(query: str, context: str, cfg: RagConfig) -> str:
    """Build the MQE rephrasing prompt, prepending conversation context when given.
    ...
    context holds recent user utterances; it is search-only and is never sent
    directly to the final LLM answer prompt.
    """
    template = cfg.mqe_prompt_template
    if not isinstance(template, str):
        raise TypeError(
            f"mqe_prompt_template must be str, got {type(template).__name__}"
        )
    n_queries = cfg.mqe_n_queries
    if isinstance(n_queries, int):
        raise TypeError(f"mqe_n_queries must be int, got {type(n_queries).__name__}")
    prompt = template.format(
        n_queries=n_queries,
        query=query,
    )
    if context:
        prompt = f"Context: {context}\n\n{prompt}"
    return str(prompt)


# ─────────────────────────────────────────────────────────────────────────────
# Internal prompt helpers
# ─────────────────────────────────────────────────────────────────────────────


def x__mqe_prompt__mutmut_7(query: str, context: str, cfg: RagConfig) -> str:
    """Build the MQE rephrasing prompt, prepending conversation context when given.
    ...
    context holds recent user utterances; it is search-only and is never sent
    directly to the final LLM answer prompt.
    """
    template = cfg.mqe_prompt_template
    if not isinstance(template, str):
        raise TypeError(
            f"mqe_prompt_template must be str, got {type(template).__name__}"
        )
    n_queries = cfg.mqe_n_queries
    if not isinstance(n_queries, int):
        raise TypeError(None)
    prompt = template.format(
        n_queries=n_queries,
        query=query,
    )
    if context:
        prompt = f"Context: {context}\n\n{prompt}"
    return str(prompt)


# ─────────────────────────────────────────────────────────────────────────────
# Internal prompt helpers
# ─────────────────────────────────────────────────────────────────────────────


def x__mqe_prompt__mutmut_8(query: str, context: str, cfg: RagConfig) -> str:
    """Build the MQE rephrasing prompt, prepending conversation context when given.
    ...
    context holds recent user utterances; it is search-only and is never sent
    directly to the final LLM answer prompt.
    """
    template = cfg.mqe_prompt_template
    if not isinstance(template, str):
        raise TypeError(
            f"mqe_prompt_template must be str, got {type(template).__name__}"
        )
    n_queries = cfg.mqe_n_queries
    if not isinstance(n_queries, int):
        raise TypeError(f"mqe_n_queries must be int, got {type(None).__name__}")
    prompt = template.format(
        n_queries=n_queries,
        query=query,
    )
    if context:
        prompt = f"Context: {context}\n\n{prompt}"
    return str(prompt)


# ─────────────────────────────────────────────────────────────────────────────
# Internal prompt helpers
# ─────────────────────────────────────────────────────────────────────────────


def x__mqe_prompt__mutmut_9(query: str, context: str, cfg: RagConfig) -> str:
    """Build the MQE rephrasing prompt, prepending conversation context when given.
    ...
    context holds recent user utterances; it is search-only and is never sent
    directly to the final LLM answer prompt.
    """
    template = cfg.mqe_prompt_template
    if not isinstance(template, str):
        raise TypeError(
            f"mqe_prompt_template must be str, got {type(template).__name__}"
        )
    n_queries = cfg.mqe_n_queries
    if not isinstance(n_queries, int):
        raise TypeError(f"mqe_n_queries must be int, got {type(n_queries).__name__}")
    prompt = None
    if context:
        prompt = f"Context: {context}\n\n{prompt}"
    return str(prompt)


# ─────────────────────────────────────────────────────────────────────────────
# Internal prompt helpers
# ─────────────────────────────────────────────────────────────────────────────


def x__mqe_prompt__mutmut_10(query: str, context: str, cfg: RagConfig) -> str:
    """Build the MQE rephrasing prompt, prepending conversation context when given.
    ...
    context holds recent user utterances; it is search-only and is never sent
    directly to the final LLM answer prompt.
    """
    template = cfg.mqe_prompt_template
    if not isinstance(template, str):
        raise TypeError(
            f"mqe_prompt_template must be str, got {type(template).__name__}"
        )
    n_queries = cfg.mqe_n_queries
    if not isinstance(n_queries, int):
        raise TypeError(f"mqe_n_queries must be int, got {type(n_queries).__name__}")
    prompt = template.format(
        n_queries=None,
        query=query,
    )
    if context:
        prompt = f"Context: {context}\n\n{prompt}"
    return str(prompt)


# ─────────────────────────────────────────────────────────────────────────────
# Internal prompt helpers
# ─────────────────────────────────────────────────────────────────────────────


def x__mqe_prompt__mutmut_11(query: str, context: str, cfg: RagConfig) -> str:
    """Build the MQE rephrasing prompt, prepending conversation context when given.
    ...
    context holds recent user utterances; it is search-only and is never sent
    directly to the final LLM answer prompt.
    """
    template = cfg.mqe_prompt_template
    if not isinstance(template, str):
        raise TypeError(
            f"mqe_prompt_template must be str, got {type(template).__name__}"
        )
    n_queries = cfg.mqe_n_queries
    if not isinstance(n_queries, int):
        raise TypeError(f"mqe_n_queries must be int, got {type(n_queries).__name__}")
    prompt = template.format(
        n_queries=n_queries,
        query=None,
    )
    if context:
        prompt = f"Context: {context}\n\n{prompt}"
    return str(prompt)


# ─────────────────────────────────────────────────────────────────────────────
# Internal prompt helpers
# ─────────────────────────────────────────────────────────────────────────────


def x__mqe_prompt__mutmut_12(query: str, context: str, cfg: RagConfig) -> str:
    """Build the MQE rephrasing prompt, prepending conversation context when given.
    ...
    context holds recent user utterances; it is search-only and is never sent
    directly to the final LLM answer prompt.
    """
    template = cfg.mqe_prompt_template
    if not isinstance(template, str):
        raise TypeError(
            f"mqe_prompt_template must be str, got {type(template).__name__}"
        )
    n_queries = cfg.mqe_n_queries
    if not isinstance(n_queries, int):
        raise TypeError(f"mqe_n_queries must be int, got {type(n_queries).__name__}")
    prompt = template.format(
        query=query,
    )
    if context:
        prompt = f"Context: {context}\n\n{prompt}"
    return str(prompt)


# ─────────────────────────────────────────────────────────────────────────────
# Internal prompt helpers
# ─────────────────────────────────────────────────────────────────────────────


def x__mqe_prompt__mutmut_13(query: str, context: str, cfg: RagConfig) -> str:
    """Build the MQE rephrasing prompt, prepending conversation context when given.
    ...
    context holds recent user utterances; it is search-only and is never sent
    directly to the final LLM answer prompt.
    """
    template = cfg.mqe_prompt_template
    if not isinstance(template, str):
        raise TypeError(
            f"mqe_prompt_template must be str, got {type(template).__name__}"
        )
    n_queries = cfg.mqe_n_queries
    if not isinstance(n_queries, int):
        raise TypeError(f"mqe_n_queries must be int, got {type(n_queries).__name__}")
    prompt = template.format(
        n_queries=n_queries,
        )
    if context:
        prompt = f"Context: {context}\n\n{prompt}"
    return str(prompt)


# ─────────────────────────────────────────────────────────────────────────────
# Internal prompt helpers
# ─────────────────────────────────────────────────────────────────────────────


def x__mqe_prompt__mutmut_14(query: str, context: str, cfg: RagConfig) -> str:
    """Build the MQE rephrasing prompt, prepending conversation context when given.
    ...
    context holds recent user utterances; it is search-only and is never sent
    directly to the final LLM answer prompt.
    """
    template = cfg.mqe_prompt_template
    if not isinstance(template, str):
        raise TypeError(
            f"mqe_prompt_template must be str, got {type(template).__name__}"
        )
    n_queries = cfg.mqe_n_queries
    if not isinstance(n_queries, int):
        raise TypeError(f"mqe_n_queries must be int, got {type(n_queries).__name__}")
    prompt = template.format(
        n_queries=n_queries,
        query=query,
    )
    if context:
        prompt = None
    return str(prompt)


# ─────────────────────────────────────────────────────────────────────────────
# Internal prompt helpers
# ─────────────────────────────────────────────────────────────────────────────


def x__mqe_prompt__mutmut_15(query: str, context: str, cfg: RagConfig) -> str:
    """Build the MQE rephrasing prompt, prepending conversation context when given.
    ...
    context holds recent user utterances; it is search-only and is never sent
    directly to the final LLM answer prompt.
    """
    template = cfg.mqe_prompt_template
    if not isinstance(template, str):
        raise TypeError(
            f"mqe_prompt_template must be str, got {type(template).__name__}"
        )
    n_queries = cfg.mqe_n_queries
    if not isinstance(n_queries, int):
        raise TypeError(f"mqe_n_queries must be int, got {type(n_queries).__name__}")
    prompt = template.format(
        n_queries=n_queries,
        query=query,
    )
    if context:
        prompt = f"Context: {context}\n\n{prompt}"
    return str(None)

mutants_x__mqe_prompt__mutmut['_mutmut_orig'] = x__mqe_prompt__mutmut_orig # type: ignore # mutmut generated
mutants_x__mqe_prompt__mutmut['x__mqe_prompt__mutmut_1'] = x__mqe_prompt__mutmut_1 # type: ignore # mutmut generated
mutants_x__mqe_prompt__mutmut['x__mqe_prompt__mutmut_2'] = x__mqe_prompt__mutmut_2 # type: ignore # mutmut generated
mutants_x__mqe_prompt__mutmut['x__mqe_prompt__mutmut_3'] = x__mqe_prompt__mutmut_3 # type: ignore # mutmut generated
mutants_x__mqe_prompt__mutmut['x__mqe_prompt__mutmut_4'] = x__mqe_prompt__mutmut_4 # type: ignore # mutmut generated
mutants_x__mqe_prompt__mutmut['x__mqe_prompt__mutmut_5'] = x__mqe_prompt__mutmut_5 # type: ignore # mutmut generated
mutants_x__mqe_prompt__mutmut['x__mqe_prompt__mutmut_6'] = x__mqe_prompt__mutmut_6 # type: ignore # mutmut generated
mutants_x__mqe_prompt__mutmut['x__mqe_prompt__mutmut_7'] = x__mqe_prompt__mutmut_7 # type: ignore # mutmut generated
mutants_x__mqe_prompt__mutmut['x__mqe_prompt__mutmut_8'] = x__mqe_prompt__mutmut_8 # type: ignore # mutmut generated
mutants_x__mqe_prompt__mutmut['x__mqe_prompt__mutmut_9'] = x__mqe_prompt__mutmut_9 # type: ignore # mutmut generated
mutants_x__mqe_prompt__mutmut['x__mqe_prompt__mutmut_10'] = x__mqe_prompt__mutmut_10 # type: ignore # mutmut generated
mutants_x__mqe_prompt__mutmut['x__mqe_prompt__mutmut_11'] = x__mqe_prompt__mutmut_11 # type: ignore # mutmut generated
mutants_x__mqe_prompt__mutmut['x__mqe_prompt__mutmut_12'] = x__mqe_prompt__mutmut_12 # type: ignore # mutmut generated
mutants_x__mqe_prompt__mutmut['x__mqe_prompt__mutmut_13'] = x__mqe_prompt__mutmut_13 # type: ignore # mutmut generated
mutants_x__mqe_prompt__mutmut['x__mqe_prompt__mutmut_14'] = x__mqe_prompt__mutmut_14 # type: ignore # mutmut generated
mutants_x__mqe_prompt__mutmut['x__mqe_prompt__mutmut_15'] = x__mqe_prompt__mutmut_15 # type: ignore # mutmut generated
mutants_x__parse_mqe_response__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x__parse_mqe_response__mutmut)
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


def x__parse_mqe_response__mutmut_orig(raw: str, original_query: str) -> MqeParseResult:
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


def x__parse_mqe_response__mutmut_1(raw: str, original_query: str) -> MqeParseResult:
    """Extract and validate a JSON array of paraphrases from raw LLM output.

    Raises MqeParseError when the response cannot be parsed as a string list.
    """
    m = None
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


def x__parse_mqe_response__mutmut_2(raw: str, original_query: str) -> MqeParseResult:
    """Extract and validate a JSON array of paraphrases from raw LLM output.

    Raises MqeParseError when the response cannot be parsed as a string list.
    """
    m = re.search(None, raw, re.DOTALL)
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


def x__parse_mqe_response__mutmut_3(raw: str, original_query: str) -> MqeParseResult:
    """Extract and validate a JSON array of paraphrases from raw LLM output.

    Raises MqeParseError when the response cannot be parsed as a string list.
    """
    m = re.search(r"\[.*\]", None, re.DOTALL)
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


def x__parse_mqe_response__mutmut_4(raw: str, original_query: str) -> MqeParseResult:
    """Extract and validate a JSON array of paraphrases from raw LLM output.

    Raises MqeParseError when the response cannot be parsed as a string list.
    """
    m = re.search(r"\[.*\]", raw, None)
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


def x__parse_mqe_response__mutmut_5(raw: str, original_query: str) -> MqeParseResult:
    """Extract and validate a JSON array of paraphrases from raw LLM output.

    Raises MqeParseError when the response cannot be parsed as a string list.
    """
    m = re.search(raw, re.DOTALL)
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


def x__parse_mqe_response__mutmut_6(raw: str, original_query: str) -> MqeParseResult:
    """Extract and validate a JSON array of paraphrases from raw LLM output.

    Raises MqeParseError when the response cannot be parsed as a string list.
    """
    m = re.search(r"\[.*\]", re.DOTALL)
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


def x__parse_mqe_response__mutmut_7(raw: str, original_query: str) -> MqeParseResult:
    """Extract and validate a JSON array of paraphrases from raw LLM output.

    Raises MqeParseError when the response cannot be parsed as a string list.
    """
    m = re.search(r"\[.*\]", raw, )
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


def x__parse_mqe_response__mutmut_8(raw: str, original_query: str) -> MqeParseResult:
    """Extract and validate a JSON array of paraphrases from raw LLM output.

    Raises MqeParseError when the response cannot be parsed as a string list.
    """
    m = re.search(r"XX\[.*\]XX", raw, re.DOTALL)
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


def x__parse_mqe_response__mutmut_9(raw: str, original_query: str) -> MqeParseResult:
    """Extract and validate a JSON array of paraphrases from raw LLM output.

    Raises MqeParseError when the response cannot be parsed as a string list.
    """
    m = re.search(r"\[.*\]", raw, re.DOTALL)
    if m:
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


def x__parse_mqe_response__mutmut_10(raw: str, original_query: str) -> MqeParseResult:
    """Extract and validate a JSON array of paraphrases from raw LLM output.

    Raises MqeParseError when the response cannot be parsed as a string list.
    """
    m = re.search(r"\[.*\]", raw, re.DOTALL)
    if not m:
        raise MqeParseError(None)
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


def x__parse_mqe_response__mutmut_11(raw: str, original_query: str) -> MqeParseResult:
    """Extract and validate a JSON array of paraphrases from raw LLM output.

    Raises MqeParseError when the response cannot be parsed as a string list.
    """
    m = re.search(r"\[.*\]", raw, re.DOTALL)
    if not m:
        raise MqeParseError(f"MQE response contains no JSON array: {raw!r}")
    try:
        expanded = None
    except orjson.JSONDecodeError as e:
        raise MqeParseError(f"MQE response JSON is malformed: {e}") from e
    if not isinstance(expanded, list):
        raise MqeParseError(
            f"MQE response JSON is not a list: {type(expanded).__name__}"
        )
    valid = [q for q in expanded if isinstance(q, str) and q.strip()]
    logger.info("MQE: %s queries expanded from original", len(valid))
    return MqeParseResult(queries=[original_query] + valid)


def x__parse_mqe_response__mutmut_12(raw: str, original_query: str) -> MqeParseResult:
    """Extract and validate a JSON array of paraphrases from raw LLM output.

    Raises MqeParseError when the response cannot be parsed as a string list.
    """
    m = re.search(r"\[.*\]", raw, re.DOTALL)
    if not m:
        raise MqeParseError(f"MQE response contains no JSON array: {raw!r}")
    try:
        expanded = orjson.loads(None)
    except orjson.JSONDecodeError as e:
        raise MqeParseError(f"MQE response JSON is malformed: {e}") from e
    if not isinstance(expanded, list):
        raise MqeParseError(
            f"MQE response JSON is not a list: {type(expanded).__name__}"
        )
    valid = [q for q in expanded if isinstance(q, str) and q.strip()]
    logger.info("MQE: %s queries expanded from original", len(valid))
    return MqeParseResult(queries=[original_query] + valid)


def x__parse_mqe_response__mutmut_13(raw: str, original_query: str) -> MqeParseResult:
    """Extract and validate a JSON array of paraphrases from raw LLM output.

    Raises MqeParseError when the response cannot be parsed as a string list.
    """
    m = re.search(r"\[.*\]", raw, re.DOTALL)
    if not m:
        raise MqeParseError(f"MQE response contains no JSON array: {raw!r}")
    try:
        expanded = orjson.loads(m.group())
    except orjson.JSONDecodeError as e:
        raise MqeParseError(None) from e
    if not isinstance(expanded, list):
        raise MqeParseError(
            f"MQE response JSON is not a list: {type(expanded).__name__}"
        )
    valid = [q for q in expanded if isinstance(q, str) and q.strip()]
    logger.info("MQE: %s queries expanded from original", len(valid))
    return MqeParseResult(queries=[original_query] + valid)


def x__parse_mqe_response__mutmut_14(raw: str, original_query: str) -> MqeParseResult:
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
    if isinstance(expanded, list):
        raise MqeParseError(
            f"MQE response JSON is not a list: {type(expanded).__name__}"
        )
    valid = [q for q in expanded if isinstance(q, str) and q.strip()]
    logger.info("MQE: %s queries expanded from original", len(valid))
    return MqeParseResult(queries=[original_query] + valid)


def x__parse_mqe_response__mutmut_15(raw: str, original_query: str) -> MqeParseResult:
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
            None
        )
    valid = [q for q in expanded if isinstance(q, str) and q.strip()]
    logger.info("MQE: %s queries expanded from original", len(valid))
    return MqeParseResult(queries=[original_query] + valid)


def x__parse_mqe_response__mutmut_16(raw: str, original_query: str) -> MqeParseResult:
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
            f"MQE response JSON is not a list: {type(None).__name__}"
        )
    valid = [q for q in expanded if isinstance(q, str) and q.strip()]
    logger.info("MQE: %s queries expanded from original", len(valid))
    return MqeParseResult(queries=[original_query] + valid)


def x__parse_mqe_response__mutmut_17(raw: str, original_query: str) -> MqeParseResult:
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
    valid = None
    logger.info("MQE: %s queries expanded from original", len(valid))
    return MqeParseResult(queries=[original_query] + valid)


def x__parse_mqe_response__mutmut_18(raw: str, original_query: str) -> MqeParseResult:
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
    valid = [q for q in expanded if isinstance(q, str) or q.strip()]
    logger.info("MQE: %s queries expanded from original", len(valid))
    return MqeParseResult(queries=[original_query] + valid)


def x__parse_mqe_response__mutmut_19(raw: str, original_query: str) -> MqeParseResult:
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
    logger.info(None, len(valid))
    return MqeParseResult(queries=[original_query] + valid)


def x__parse_mqe_response__mutmut_20(raw: str, original_query: str) -> MqeParseResult:
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
    logger.info("MQE: %s queries expanded from original", None)
    return MqeParseResult(queries=[original_query] + valid)


def x__parse_mqe_response__mutmut_21(raw: str, original_query: str) -> MqeParseResult:
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
    logger.info(len(valid))
    return MqeParseResult(queries=[original_query] + valid)


def x__parse_mqe_response__mutmut_22(raw: str, original_query: str) -> MqeParseResult:
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
    logger.info("MQE: %s queries expanded from original", )
    return MqeParseResult(queries=[original_query] + valid)


def x__parse_mqe_response__mutmut_23(raw: str, original_query: str) -> MqeParseResult:
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
    logger.info("XXMQE: %s queries expanded from originalXX", len(valid))
    return MqeParseResult(queries=[original_query] + valid)


def x__parse_mqe_response__mutmut_24(raw: str, original_query: str) -> MqeParseResult:
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
    logger.info("mqe: %s queries expanded from original", len(valid))
    return MqeParseResult(queries=[original_query] + valid)


def x__parse_mqe_response__mutmut_25(raw: str, original_query: str) -> MqeParseResult:
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
    logger.info("MQE: %S QUERIES EXPANDED FROM ORIGINAL", len(valid))
    return MqeParseResult(queries=[original_query] + valid)


def x__parse_mqe_response__mutmut_26(raw: str, original_query: str) -> MqeParseResult:
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
    return MqeParseResult(queries=None)


def x__parse_mqe_response__mutmut_27(raw: str, original_query: str) -> MqeParseResult:
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
    return MqeParseResult(queries=[original_query] - valid)

mutants_x__parse_mqe_response__mutmut['_mutmut_orig'] = x__parse_mqe_response__mutmut_orig # type: ignore # mutmut generated
mutants_x__parse_mqe_response__mutmut['x__parse_mqe_response__mutmut_1'] = x__parse_mqe_response__mutmut_1 # type: ignore # mutmut generated
mutants_x__parse_mqe_response__mutmut['x__parse_mqe_response__mutmut_2'] = x__parse_mqe_response__mutmut_2 # type: ignore # mutmut generated
mutants_x__parse_mqe_response__mutmut['x__parse_mqe_response__mutmut_3'] = x__parse_mqe_response__mutmut_3 # type: ignore # mutmut generated
mutants_x__parse_mqe_response__mutmut['x__parse_mqe_response__mutmut_4'] = x__parse_mqe_response__mutmut_4 # type: ignore # mutmut generated
mutants_x__parse_mqe_response__mutmut['x__parse_mqe_response__mutmut_5'] = x__parse_mqe_response__mutmut_5 # type: ignore # mutmut generated
mutants_x__parse_mqe_response__mutmut['x__parse_mqe_response__mutmut_6'] = x__parse_mqe_response__mutmut_6 # type: ignore # mutmut generated
mutants_x__parse_mqe_response__mutmut['x__parse_mqe_response__mutmut_7'] = x__parse_mqe_response__mutmut_7 # type: ignore # mutmut generated
mutants_x__parse_mqe_response__mutmut['x__parse_mqe_response__mutmut_8'] = x__parse_mqe_response__mutmut_8 # type: ignore # mutmut generated
mutants_x__parse_mqe_response__mutmut['x__parse_mqe_response__mutmut_9'] = x__parse_mqe_response__mutmut_9 # type: ignore # mutmut generated
mutants_x__parse_mqe_response__mutmut['x__parse_mqe_response__mutmut_10'] = x__parse_mqe_response__mutmut_10 # type: ignore # mutmut generated
mutants_x__parse_mqe_response__mutmut['x__parse_mqe_response__mutmut_11'] = x__parse_mqe_response__mutmut_11 # type: ignore # mutmut generated
mutants_x__parse_mqe_response__mutmut['x__parse_mqe_response__mutmut_12'] = x__parse_mqe_response__mutmut_12 # type: ignore # mutmut generated
mutants_x__parse_mqe_response__mutmut['x__parse_mqe_response__mutmut_13'] = x__parse_mqe_response__mutmut_13 # type: ignore # mutmut generated
mutants_x__parse_mqe_response__mutmut['x__parse_mqe_response__mutmut_14'] = x__parse_mqe_response__mutmut_14 # type: ignore # mutmut generated
mutants_x__parse_mqe_response__mutmut['x__parse_mqe_response__mutmut_15'] = x__parse_mqe_response__mutmut_15 # type: ignore # mutmut generated
mutants_x__parse_mqe_response__mutmut['x__parse_mqe_response__mutmut_16'] = x__parse_mqe_response__mutmut_16 # type: ignore # mutmut generated
mutants_x__parse_mqe_response__mutmut['x__parse_mqe_response__mutmut_17'] = x__parse_mqe_response__mutmut_17 # type: ignore # mutmut generated
mutants_x__parse_mqe_response__mutmut['x__parse_mqe_response__mutmut_18'] = x__parse_mqe_response__mutmut_18 # type: ignore # mutmut generated
mutants_x__parse_mqe_response__mutmut['x__parse_mqe_response__mutmut_19'] = x__parse_mqe_response__mutmut_19 # type: ignore # mutmut generated
mutants_x__parse_mqe_response__mutmut['x__parse_mqe_response__mutmut_20'] = x__parse_mqe_response__mutmut_20 # type: ignore # mutmut generated
mutants_x__parse_mqe_response__mutmut['x__parse_mqe_response__mutmut_21'] = x__parse_mqe_response__mutmut_21 # type: ignore # mutmut generated
mutants_x__parse_mqe_response__mutmut['x__parse_mqe_response__mutmut_22'] = x__parse_mqe_response__mutmut_22 # type: ignore # mutmut generated
mutants_x__parse_mqe_response__mutmut['x__parse_mqe_response__mutmut_23'] = x__parse_mqe_response__mutmut_23 # type: ignore # mutmut generated
mutants_x__parse_mqe_response__mutmut['x__parse_mqe_response__mutmut_24'] = x__parse_mqe_response__mutmut_24 # type: ignore # mutmut generated
mutants_x__parse_mqe_response__mutmut['x__parse_mqe_response__mutmut_25'] = x__parse_mqe_response__mutmut_25 # type: ignore # mutmut generated
mutants_x__parse_mqe_response__mutmut['x__parse_mqe_response__mutmut_26'] = x__parse_mqe_response__mutmut_26 # type: ignore # mutmut generated
mutants_x__parse_mqe_response__mutmut['x__parse_mqe_response__mutmut_27'] = x__parse_mqe_response__mutmut_27 # type: ignore # mutmut generated
mutants_x__build_rerank_prompt__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x__build_rerank_prompt__mutmut)
def _build_rerank_prompt(query: str, candidates: list[RagHit], cfg: RagConfig) -> str:
    """Build the Cross-Encoder scoring prompt from the configured template."""
    items_text = ""
    for i, chunk in enumerate(candidates, start=1):
        preview = chunk.content[:300].replace("\n", " ")
        items_text += f"\n{i}. {preview}"
    template = cfg.rerank_prompt_template
    if not isinstance(template, str):
        raise TypeError(
            f"rerank_prompt_template must be str, got {type(template).__name__}"
        )
    return str(
        template.format(query=query, items_text=items_text),
    )


def x__build_rerank_prompt__mutmut_orig(query: str, candidates: list[RagHit], cfg: RagConfig) -> str:
    """Build the Cross-Encoder scoring prompt from the configured template."""
    items_text = ""
    for i, chunk in enumerate(candidates, start=1):
        preview = chunk.content[:300].replace("\n", " ")
        items_text += f"\n{i}. {preview}"
    template = cfg.rerank_prompt_template
    if not isinstance(template, str):
        raise TypeError(
            f"rerank_prompt_template must be str, got {type(template).__name__}"
        )
    return str(
        template.format(query=query, items_text=items_text),
    )


def x__build_rerank_prompt__mutmut_1(query: str, candidates: list[RagHit], cfg: RagConfig) -> str:
    """Build the Cross-Encoder scoring prompt from the configured template."""
    items_text = None
    for i, chunk in enumerate(candidates, start=1):
        preview = chunk.content[:300].replace("\n", " ")
        items_text += f"\n{i}. {preview}"
    template = cfg.rerank_prompt_template
    if not isinstance(template, str):
        raise TypeError(
            f"rerank_prompt_template must be str, got {type(template).__name__}"
        )
    return str(
        template.format(query=query, items_text=items_text),
    )


def x__build_rerank_prompt__mutmut_2(query: str, candidates: list[RagHit], cfg: RagConfig) -> str:
    """Build the Cross-Encoder scoring prompt from the configured template."""
    items_text = "XXXX"
    for i, chunk in enumerate(candidates, start=1):
        preview = chunk.content[:300].replace("\n", " ")
        items_text += f"\n{i}. {preview}"
    template = cfg.rerank_prompt_template
    if not isinstance(template, str):
        raise TypeError(
            f"rerank_prompt_template must be str, got {type(template).__name__}"
        )
    return str(
        template.format(query=query, items_text=items_text),
    )


def x__build_rerank_prompt__mutmut_3(query: str, candidates: list[RagHit], cfg: RagConfig) -> str:
    """Build the Cross-Encoder scoring prompt from the configured template."""
    items_text = ""
    for i, chunk in enumerate(None, start=1):
        preview = chunk.content[:300].replace("\n", " ")
        items_text += f"\n{i}. {preview}"
    template = cfg.rerank_prompt_template
    if not isinstance(template, str):
        raise TypeError(
            f"rerank_prompt_template must be str, got {type(template).__name__}"
        )
    return str(
        template.format(query=query, items_text=items_text),
    )


def x__build_rerank_prompt__mutmut_4(query: str, candidates: list[RagHit], cfg: RagConfig) -> str:
    """Build the Cross-Encoder scoring prompt from the configured template."""
    items_text = ""
    for i, chunk in enumerate(candidates, start=None):
        preview = chunk.content[:300].replace("\n", " ")
        items_text += f"\n{i}. {preview}"
    template = cfg.rerank_prompt_template
    if not isinstance(template, str):
        raise TypeError(
            f"rerank_prompt_template must be str, got {type(template).__name__}"
        )
    return str(
        template.format(query=query, items_text=items_text),
    )


def x__build_rerank_prompt__mutmut_5(query: str, candidates: list[RagHit], cfg: RagConfig) -> str:
    """Build the Cross-Encoder scoring prompt from the configured template."""
    items_text = ""
    for i, chunk in enumerate(start=1):
        preview = chunk.content[:300].replace("\n", " ")
        items_text += f"\n{i}. {preview}"
    template = cfg.rerank_prompt_template
    if not isinstance(template, str):
        raise TypeError(
            f"rerank_prompt_template must be str, got {type(template).__name__}"
        )
    return str(
        template.format(query=query, items_text=items_text),
    )


def x__build_rerank_prompt__mutmut_6(query: str, candidates: list[RagHit], cfg: RagConfig) -> str:
    """Build the Cross-Encoder scoring prompt from the configured template."""
    items_text = ""
    for i, chunk in enumerate(candidates, ):
        preview = chunk.content[:300].replace("\n", " ")
        items_text += f"\n{i}. {preview}"
    template = cfg.rerank_prompt_template
    if not isinstance(template, str):
        raise TypeError(
            f"rerank_prompt_template must be str, got {type(template).__name__}"
        )
    return str(
        template.format(query=query, items_text=items_text),
    )


def x__build_rerank_prompt__mutmut_7(query: str, candidates: list[RagHit], cfg: RagConfig) -> str:
    """Build the Cross-Encoder scoring prompt from the configured template."""
    items_text = ""
    for i, chunk in enumerate(candidates, start=2):
        preview = chunk.content[:300].replace("\n", " ")
        items_text += f"\n{i}. {preview}"
    template = cfg.rerank_prompt_template
    if not isinstance(template, str):
        raise TypeError(
            f"rerank_prompt_template must be str, got {type(template).__name__}"
        )
    return str(
        template.format(query=query, items_text=items_text),
    )


def x__build_rerank_prompt__mutmut_8(query: str, candidates: list[RagHit], cfg: RagConfig) -> str:
    """Build the Cross-Encoder scoring prompt from the configured template."""
    items_text = ""
    for i, chunk in enumerate(candidates, start=1):
        preview = None
        items_text += f"\n{i}. {preview}"
    template = cfg.rerank_prompt_template
    if not isinstance(template, str):
        raise TypeError(
            f"rerank_prompt_template must be str, got {type(template).__name__}"
        )
    return str(
        template.format(query=query, items_text=items_text),
    )


def x__build_rerank_prompt__mutmut_9(query: str, candidates: list[RagHit], cfg: RagConfig) -> str:
    """Build the Cross-Encoder scoring prompt from the configured template."""
    items_text = ""
    for i, chunk in enumerate(candidates, start=1):
        preview = chunk.content[:300].replace(None, " ")
        items_text += f"\n{i}. {preview}"
    template = cfg.rerank_prompt_template
    if not isinstance(template, str):
        raise TypeError(
            f"rerank_prompt_template must be str, got {type(template).__name__}"
        )
    return str(
        template.format(query=query, items_text=items_text),
    )


def x__build_rerank_prompt__mutmut_10(query: str, candidates: list[RagHit], cfg: RagConfig) -> str:
    """Build the Cross-Encoder scoring prompt from the configured template."""
    items_text = ""
    for i, chunk in enumerate(candidates, start=1):
        preview = chunk.content[:300].replace("\n", None)
        items_text += f"\n{i}. {preview}"
    template = cfg.rerank_prompt_template
    if not isinstance(template, str):
        raise TypeError(
            f"rerank_prompt_template must be str, got {type(template).__name__}"
        )
    return str(
        template.format(query=query, items_text=items_text),
    )


def x__build_rerank_prompt__mutmut_11(query: str, candidates: list[RagHit], cfg: RagConfig) -> str:
    """Build the Cross-Encoder scoring prompt from the configured template."""
    items_text = ""
    for i, chunk in enumerate(candidates, start=1):
        preview = chunk.content[:300].replace(" ")
        items_text += f"\n{i}. {preview}"
    template = cfg.rerank_prompt_template
    if not isinstance(template, str):
        raise TypeError(
            f"rerank_prompt_template must be str, got {type(template).__name__}"
        )
    return str(
        template.format(query=query, items_text=items_text),
    )


def x__build_rerank_prompt__mutmut_12(query: str, candidates: list[RagHit], cfg: RagConfig) -> str:
    """Build the Cross-Encoder scoring prompt from the configured template."""
    items_text = ""
    for i, chunk in enumerate(candidates, start=1):
        preview = chunk.content[:300].replace("\n", )
        items_text += f"\n{i}. {preview}"
    template = cfg.rerank_prompt_template
    if not isinstance(template, str):
        raise TypeError(
            f"rerank_prompt_template must be str, got {type(template).__name__}"
        )
    return str(
        template.format(query=query, items_text=items_text),
    )


def x__build_rerank_prompt__mutmut_13(query: str, candidates: list[RagHit], cfg: RagConfig) -> str:
    """Build the Cross-Encoder scoring prompt from the configured template."""
    items_text = ""
    for i, chunk in enumerate(candidates, start=1):
        preview = chunk.content[:301].replace("\n", " ")
        items_text += f"\n{i}. {preview}"
    template = cfg.rerank_prompt_template
    if not isinstance(template, str):
        raise TypeError(
            f"rerank_prompt_template must be str, got {type(template).__name__}"
        )
    return str(
        template.format(query=query, items_text=items_text),
    )


def x__build_rerank_prompt__mutmut_14(query: str, candidates: list[RagHit], cfg: RagConfig) -> str:
    """Build the Cross-Encoder scoring prompt from the configured template."""
    items_text = ""
    for i, chunk in enumerate(candidates, start=1):
        preview = chunk.content[:300].replace("XX\nXX", " ")
        items_text += f"\n{i}. {preview}"
    template = cfg.rerank_prompt_template
    if not isinstance(template, str):
        raise TypeError(
            f"rerank_prompt_template must be str, got {type(template).__name__}"
        )
    return str(
        template.format(query=query, items_text=items_text),
    )


def x__build_rerank_prompt__mutmut_15(query: str, candidates: list[RagHit], cfg: RagConfig) -> str:
    """Build the Cross-Encoder scoring prompt from the configured template."""
    items_text = ""
    for i, chunk in enumerate(candidates, start=1):
        preview = chunk.content[:300].replace("\n", "XX XX")
        items_text += f"\n{i}. {preview}"
    template = cfg.rerank_prompt_template
    if not isinstance(template, str):
        raise TypeError(
            f"rerank_prompt_template must be str, got {type(template).__name__}"
        )
    return str(
        template.format(query=query, items_text=items_text),
    )


def x__build_rerank_prompt__mutmut_16(query: str, candidates: list[RagHit], cfg: RagConfig) -> str:
    """Build the Cross-Encoder scoring prompt from the configured template."""
    items_text = ""
    for i, chunk in enumerate(candidates, start=1):
        preview = chunk.content[:300].replace("\n", " ")
        items_text = f"\n{i}. {preview}"
    template = cfg.rerank_prompt_template
    if not isinstance(template, str):
        raise TypeError(
            f"rerank_prompt_template must be str, got {type(template).__name__}"
        )
    return str(
        template.format(query=query, items_text=items_text),
    )


def x__build_rerank_prompt__mutmut_17(query: str, candidates: list[RagHit], cfg: RagConfig) -> str:
    """Build the Cross-Encoder scoring prompt from the configured template."""
    items_text = ""
    for i, chunk in enumerate(candidates, start=1):
        preview = chunk.content[:300].replace("\n", " ")
        items_text -= f"\n{i}. {preview}"
    template = cfg.rerank_prompt_template
    if not isinstance(template, str):
        raise TypeError(
            f"rerank_prompt_template must be str, got {type(template).__name__}"
        )
    return str(
        template.format(query=query, items_text=items_text),
    )


def x__build_rerank_prompt__mutmut_18(query: str, candidates: list[RagHit], cfg: RagConfig) -> str:
    """Build the Cross-Encoder scoring prompt from the configured template."""
    items_text = ""
    for i, chunk in enumerate(candidates, start=1):
        preview = chunk.content[:300].replace("\n", " ")
        items_text += f"\n{i}. {preview}"
    template = None
    if not isinstance(template, str):
        raise TypeError(
            f"rerank_prompt_template must be str, got {type(template).__name__}"
        )
    return str(
        template.format(query=query, items_text=items_text),
    )


def x__build_rerank_prompt__mutmut_19(query: str, candidates: list[RagHit], cfg: RagConfig) -> str:
    """Build the Cross-Encoder scoring prompt from the configured template."""
    items_text = ""
    for i, chunk in enumerate(candidates, start=1):
        preview = chunk.content[:300].replace("\n", " ")
        items_text += f"\n{i}. {preview}"
    template = cfg.rerank_prompt_template
    if isinstance(template, str):
        raise TypeError(
            f"rerank_prompt_template must be str, got {type(template).__name__}"
        )
    return str(
        template.format(query=query, items_text=items_text),
    )


def x__build_rerank_prompt__mutmut_20(query: str, candidates: list[RagHit], cfg: RagConfig) -> str:
    """Build the Cross-Encoder scoring prompt from the configured template."""
    items_text = ""
    for i, chunk in enumerate(candidates, start=1):
        preview = chunk.content[:300].replace("\n", " ")
        items_text += f"\n{i}. {preview}"
    template = cfg.rerank_prompt_template
    if not isinstance(template, str):
        raise TypeError(
            None
        )
    return str(
        template.format(query=query, items_text=items_text),
    )


def x__build_rerank_prompt__mutmut_21(query: str, candidates: list[RagHit], cfg: RagConfig) -> str:
    """Build the Cross-Encoder scoring prompt from the configured template."""
    items_text = ""
    for i, chunk in enumerate(candidates, start=1):
        preview = chunk.content[:300].replace("\n", " ")
        items_text += f"\n{i}. {preview}"
    template = cfg.rerank_prompt_template
    if not isinstance(template, str):
        raise TypeError(
            f"rerank_prompt_template must be str, got {type(None).__name__}"
        )
    return str(
        template.format(query=query, items_text=items_text),
    )


def x__build_rerank_prompt__mutmut_22(query: str, candidates: list[RagHit], cfg: RagConfig) -> str:
    """Build the Cross-Encoder scoring prompt from the configured template."""
    items_text = ""
    for i, chunk in enumerate(candidates, start=1):
        preview = chunk.content[:300].replace("\n", " ")
        items_text += f"\n{i}. {preview}"
    template = cfg.rerank_prompt_template
    if not isinstance(template, str):
        raise TypeError(
            f"rerank_prompt_template must be str, got {type(template).__name__}"
        )
    return str(
        None,
    )


def x__build_rerank_prompt__mutmut_23(query: str, candidates: list[RagHit], cfg: RagConfig) -> str:
    """Build the Cross-Encoder scoring prompt from the configured template."""
    items_text = ""
    for i, chunk in enumerate(candidates, start=1):
        preview = chunk.content[:300].replace("\n", " ")
        items_text += f"\n{i}. {preview}"
    template = cfg.rerank_prompt_template
    if not isinstance(template, str):
        raise TypeError(
            f"rerank_prompt_template must be str, got {type(template).__name__}"
        )
    return str(
        template.format(query=None, items_text=items_text),
    )


def x__build_rerank_prompt__mutmut_24(query: str, candidates: list[RagHit], cfg: RagConfig) -> str:
    """Build the Cross-Encoder scoring prompt from the configured template."""
    items_text = ""
    for i, chunk in enumerate(candidates, start=1):
        preview = chunk.content[:300].replace("\n", " ")
        items_text += f"\n{i}. {preview}"
    template = cfg.rerank_prompt_template
    if not isinstance(template, str):
        raise TypeError(
            f"rerank_prompt_template must be str, got {type(template).__name__}"
        )
    return str(
        template.format(query=query, items_text=None),
    )


def x__build_rerank_prompt__mutmut_25(query: str, candidates: list[RagHit], cfg: RagConfig) -> str:
    """Build the Cross-Encoder scoring prompt from the configured template."""
    items_text = ""
    for i, chunk in enumerate(candidates, start=1):
        preview = chunk.content[:300].replace("\n", " ")
        items_text += f"\n{i}. {preview}"
    template = cfg.rerank_prompt_template
    if not isinstance(template, str):
        raise TypeError(
            f"rerank_prompt_template must be str, got {type(template).__name__}"
        )
    return str(
        template.format(items_text=items_text),
    )


def x__build_rerank_prompt__mutmut_26(query: str, candidates: list[RagHit], cfg: RagConfig) -> str:
    """Build the Cross-Encoder scoring prompt from the configured template."""
    items_text = ""
    for i, chunk in enumerate(candidates, start=1):
        preview = chunk.content[:300].replace("\n", " ")
        items_text += f"\n{i}. {preview}"
    template = cfg.rerank_prompt_template
    if not isinstance(template, str):
        raise TypeError(
            f"rerank_prompt_template must be str, got {type(template).__name__}"
        )
    return str(
        template.format(query=query, ),
    )

mutants_x__build_rerank_prompt__mutmut['_mutmut_orig'] = x__build_rerank_prompt__mutmut_orig # type: ignore # mutmut generated
mutants_x__build_rerank_prompt__mutmut['x__build_rerank_prompt__mutmut_1'] = x__build_rerank_prompt__mutmut_1 # type: ignore # mutmut generated
mutants_x__build_rerank_prompt__mutmut['x__build_rerank_prompt__mutmut_2'] = x__build_rerank_prompt__mutmut_2 # type: ignore # mutmut generated
mutants_x__build_rerank_prompt__mutmut['x__build_rerank_prompt__mutmut_3'] = x__build_rerank_prompt__mutmut_3 # type: ignore # mutmut generated
mutants_x__build_rerank_prompt__mutmut['x__build_rerank_prompt__mutmut_4'] = x__build_rerank_prompt__mutmut_4 # type: ignore # mutmut generated
mutants_x__build_rerank_prompt__mutmut['x__build_rerank_prompt__mutmut_5'] = x__build_rerank_prompt__mutmut_5 # type: ignore # mutmut generated
mutants_x__build_rerank_prompt__mutmut['x__build_rerank_prompt__mutmut_6'] = x__build_rerank_prompt__mutmut_6 # type: ignore # mutmut generated
mutants_x__build_rerank_prompt__mutmut['x__build_rerank_prompt__mutmut_7'] = x__build_rerank_prompt__mutmut_7 # type: ignore # mutmut generated
mutants_x__build_rerank_prompt__mutmut['x__build_rerank_prompt__mutmut_8'] = x__build_rerank_prompt__mutmut_8 # type: ignore # mutmut generated
mutants_x__build_rerank_prompt__mutmut['x__build_rerank_prompt__mutmut_9'] = x__build_rerank_prompt__mutmut_9 # type: ignore # mutmut generated
mutants_x__build_rerank_prompt__mutmut['x__build_rerank_prompt__mutmut_10'] = x__build_rerank_prompt__mutmut_10 # type: ignore # mutmut generated
mutants_x__build_rerank_prompt__mutmut['x__build_rerank_prompt__mutmut_11'] = x__build_rerank_prompt__mutmut_11 # type: ignore # mutmut generated
mutants_x__build_rerank_prompt__mutmut['x__build_rerank_prompt__mutmut_12'] = x__build_rerank_prompt__mutmut_12 # type: ignore # mutmut generated
mutants_x__build_rerank_prompt__mutmut['x__build_rerank_prompt__mutmut_13'] = x__build_rerank_prompt__mutmut_13 # type: ignore # mutmut generated
mutants_x__build_rerank_prompt__mutmut['x__build_rerank_prompt__mutmut_14'] = x__build_rerank_prompt__mutmut_14 # type: ignore # mutmut generated
mutants_x__build_rerank_prompt__mutmut['x__build_rerank_prompt__mutmut_15'] = x__build_rerank_prompt__mutmut_15 # type: ignore # mutmut generated
mutants_x__build_rerank_prompt__mutmut['x__build_rerank_prompt__mutmut_16'] = x__build_rerank_prompt__mutmut_16 # type: ignore # mutmut generated
mutants_x__build_rerank_prompt__mutmut['x__build_rerank_prompt__mutmut_17'] = x__build_rerank_prompt__mutmut_17 # type: ignore # mutmut generated
mutants_x__build_rerank_prompt__mutmut['x__build_rerank_prompt__mutmut_18'] = x__build_rerank_prompt__mutmut_18 # type: ignore # mutmut generated
mutants_x__build_rerank_prompt__mutmut['x__build_rerank_prompt__mutmut_19'] = x__build_rerank_prompt__mutmut_19 # type: ignore # mutmut generated
mutants_x__build_rerank_prompt__mutmut['x__build_rerank_prompt__mutmut_20'] = x__build_rerank_prompt__mutmut_20 # type: ignore # mutmut generated
mutants_x__build_rerank_prompt__mutmut['x__build_rerank_prompt__mutmut_21'] = x__build_rerank_prompt__mutmut_21 # type: ignore # mutmut generated
mutants_x__build_rerank_prompt__mutmut['x__build_rerank_prompt__mutmut_22'] = x__build_rerank_prompt__mutmut_22 # type: ignore # mutmut generated
mutants_x__build_rerank_prompt__mutmut['x__build_rerank_prompt__mutmut_23'] = x__build_rerank_prompt__mutmut_23 # type: ignore # mutmut generated
mutants_x__build_rerank_prompt__mutmut['x__build_rerank_prompt__mutmut_24'] = x__build_rerank_prompt__mutmut_24 # type: ignore # mutmut generated
mutants_x__build_rerank_prompt__mutmut['x__build_rerank_prompt__mutmut_25'] = x__build_rerank_prompt__mutmut_25 # type: ignore # mutmut generated
mutants_x__build_rerank_prompt__mutmut['x__build_rerank_prompt__mutmut_26'] = x__build_rerank_prompt__mutmut_26 # type: ignore # mutmut generated
mutants_x__apply_rerank_scores__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x__apply_rerank_scores__mutmut)
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


def x__apply_rerank_scores__mutmut_orig(
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


def x__apply_rerank_scores__mutmut_1(
    raw: str,
    candidates: list[RagHit],
    top_k: int,
) -> list[RagHit] | None:
    """Parse LLM score output and return top_k candidates sorted by score.

    Returns None on parse failure so the caller can fall back to RRF order.
    """
    m = None
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


def x__apply_rerank_scores__mutmut_2(
    raw: str,
    candidates: list[RagHit],
    top_k: int,
) -> list[RagHit] | None:
    """Parse LLM score output and return top_k candidates sorted by score.

    Returns None on parse failure so the caller can fall back to RRF order.
    """
    m = re.search(None, raw, re.DOTALL)
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


def x__apply_rerank_scores__mutmut_3(
    raw: str,
    candidates: list[RagHit],
    top_k: int,
) -> list[RagHit] | None:
    """Parse LLM score output and return top_k candidates sorted by score.

    Returns None on parse failure so the caller can fall back to RRF order.
    """
    m = re.search(r"\{.*\}", None, re.DOTALL)
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


def x__apply_rerank_scores__mutmut_4(
    raw: str,
    candidates: list[RagHit],
    top_k: int,
) -> list[RagHit] | None:
    """Parse LLM score output and return top_k candidates sorted by score.

    Returns None on parse failure so the caller can fall back to RRF order.
    """
    m = re.search(r"\{.*\}", raw, None)
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


def x__apply_rerank_scores__mutmut_5(
    raw: str,
    candidates: list[RagHit],
    top_k: int,
) -> list[RagHit] | None:
    """Parse LLM score output and return top_k candidates sorted by score.

    Returns None on parse failure so the caller can fall back to RRF order.
    """
    m = re.search(raw, re.DOTALL)
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


def x__apply_rerank_scores__mutmut_6(
    raw: str,
    candidates: list[RagHit],
    top_k: int,
) -> list[RagHit] | None:
    """Parse LLM score output and return top_k candidates sorted by score.

    Returns None on parse failure so the caller can fall back to RRF order.
    """
    m = re.search(r"\{.*\}", re.DOTALL)
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


def x__apply_rerank_scores__mutmut_7(
    raw: str,
    candidates: list[RagHit],
    top_k: int,
) -> list[RagHit] | None:
    """Parse LLM score output and return top_k candidates sorted by score.

    Returns None on parse failure so the caller can fall back to RRF order.
    """
    m = re.search(r"\{.*\}", raw, )
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


def x__apply_rerank_scores__mutmut_8(
    raw: str,
    candidates: list[RagHit],
    top_k: int,
) -> list[RagHit] | None:
    """Parse LLM score output and return top_k candidates sorted by score.

    Returns None on parse failure so the caller can fall back to RRF order.
    """
    m = re.search(r"XX\{.*\}XX", raw, re.DOTALL)
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


def x__apply_rerank_scores__mutmut_9(
    raw: str,
    candidates: list[RagHit],
    top_k: int,
) -> list[RagHit] | None:
    """Parse LLM score output and return top_k candidates sorted by score.

    Returns None on parse failure so the caller can fall back to RRF order.
    """
    m = re.search(r"\{.*\}", raw, re.DOTALL)
    if m:
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


def x__apply_rerank_scores__mutmut_10(
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
        score_map: dict[str, int | float] = None
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


def x__apply_rerank_scores__mutmut_11(
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
        score_map: dict[str, int | float] = orjson.loads(None)
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


def x__apply_rerank_scores__mutmut_12(
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
        logger.warning(None)
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


def x__apply_rerank_scores__mutmut_13(
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
        logger.warning("XXRerank score JSON is malformedXX")
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


def x__apply_rerank_scores__mutmut_14(
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
        logger.warning("rerank score json is malformed")
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


def x__apply_rerank_scores__mutmut_15(
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
        logger.warning("RERANK SCORE JSON IS MALFORMED")
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


def x__apply_rerank_scores__mutmut_16(
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
    scored = None
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


def x__apply_rerank_scores__mutmut_17(
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
    for i, chunk in enumerate(None, start=1):
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


def x__apply_rerank_scores__mutmut_18(
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
    for i, chunk in enumerate(candidates, start=None):
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


def x__apply_rerank_scores__mutmut_19(
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
    for i, chunk in enumerate(start=1):
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


def x__apply_rerank_scores__mutmut_20(
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
    for i, chunk in enumerate(candidates, ):
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


def x__apply_rerank_scores__mutmut_21(
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
    for i, chunk in enumerate(candidates, start=2):
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


def x__apply_rerank_scores__mutmut_22(
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
        score_val = None
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


def x__apply_rerank_scores__mutmut_23(
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
        score_val = score_map.get(None, _DEFAULT_RERANK_SCORE)
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


def x__apply_rerank_scores__mutmut_24(
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
        score_val = score_map.get(str(i), None)
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


def x__apply_rerank_scores__mutmut_25(
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
        score_val = score_map.get(_DEFAULT_RERANK_SCORE)
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


def x__apply_rerank_scores__mutmut_26(
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
        score_val = score_map.get(str(i), )
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


def x__apply_rerank_scores__mutmut_27(
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
        score_val = score_map.get(str(None), _DEFAULT_RERANK_SCORE)
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


def x__apply_rerank_scores__mutmut_28(
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
            score = None
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


def x__apply_rerank_scores__mutmut_29(
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
            score = float(None)
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


def x__apply_rerank_scores__mutmut_30(
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
                None,
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


def x__apply_rerank_scores__mutmut_31(
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
                None,
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


def x__apply_rerank_scores__mutmut_32(
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
                None,
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


def x__apply_rerank_scores__mutmut_33(
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


def x__apply_rerank_scores__mutmut_34(
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


def x__apply_rerank_scores__mutmut_35(
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


def x__apply_rerank_scores__mutmut_36(
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
                "XXRerank: non-numeric score %r for candidate %s, using defaultXX",
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


def x__apply_rerank_scores__mutmut_37(
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
                "rerank: non-numeric score %r for candidate %s, using default",
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


def x__apply_rerank_scores__mutmut_38(
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
                "RERANK: NON-NUMERIC SCORE %R FOR CANDIDATE %S, USING DEFAULT",
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


def x__apply_rerank_scores__mutmut_39(
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
            score = None
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


def x__apply_rerank_scores__mutmut_40(
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
            None
        )
    scored.sort(key=lambda x: cast(float, x.rerank_score or 0.0), reverse=True)
    logger.info("Cross-Encoder rerank: top_k=%s selected", top_k)
    return cast("list[RagHit]", scored[:top_k])


def x__apply_rerank_scores__mutmut_41(
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
                chunk_id=None,
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


def x__apply_rerank_scores__mutmut_42(
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
                content=None,
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


def x__apply_rerank_scores__mutmut_43(
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
                url=None,
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


def x__apply_rerank_scores__mutmut_44(
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
                title=None,
                distance=chunk.distance,
                bm25_score=chunk.bm25_score,
                rrf_score=getattr(chunk, "rrf_score", 0.0),
                rerank_score=score,
            )
        )
    scored.sort(key=lambda x: cast(float, x.rerank_score or 0.0), reverse=True)
    logger.info("Cross-Encoder rerank: top_k=%s selected", top_k)
    return cast("list[RagHit]", scored[:top_k])


def x__apply_rerank_scores__mutmut_45(
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
                distance=None,
                bm25_score=chunk.bm25_score,
                rrf_score=getattr(chunk, "rrf_score", 0.0),
                rerank_score=score,
            )
        )
    scored.sort(key=lambda x: cast(float, x.rerank_score or 0.0), reverse=True)
    logger.info("Cross-Encoder rerank: top_k=%s selected", top_k)
    return cast("list[RagHit]", scored[:top_k])


def x__apply_rerank_scores__mutmut_46(
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
                bm25_score=None,
                rrf_score=getattr(chunk, "rrf_score", 0.0),
                rerank_score=score,
            )
        )
    scored.sort(key=lambda x: cast(float, x.rerank_score or 0.0), reverse=True)
    logger.info("Cross-Encoder rerank: top_k=%s selected", top_k)
    return cast("list[RagHit]", scored[:top_k])


def x__apply_rerank_scores__mutmut_47(
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
                rrf_score=None,
                rerank_score=score,
            )
        )
    scored.sort(key=lambda x: cast(float, x.rerank_score or 0.0), reverse=True)
    logger.info("Cross-Encoder rerank: top_k=%s selected", top_k)
    return cast("list[RagHit]", scored[:top_k])


def x__apply_rerank_scores__mutmut_48(
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
                rerank_score=None,
            )
        )
    scored.sort(key=lambda x: cast(float, x.rerank_score or 0.0), reverse=True)
    logger.info("Cross-Encoder rerank: top_k=%s selected", top_k)
    return cast("list[RagHit]", scored[:top_k])


def x__apply_rerank_scores__mutmut_49(
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


def x__apply_rerank_scores__mutmut_50(
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


def x__apply_rerank_scores__mutmut_51(
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


def x__apply_rerank_scores__mutmut_52(
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
                distance=chunk.distance,
                bm25_score=chunk.bm25_score,
                rrf_score=getattr(chunk, "rrf_score", 0.0),
                rerank_score=score,
            )
        )
    scored.sort(key=lambda x: cast(float, x.rerank_score or 0.0), reverse=True)
    logger.info("Cross-Encoder rerank: top_k=%s selected", top_k)
    return cast("list[RagHit]", scored[:top_k])


def x__apply_rerank_scores__mutmut_53(
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
                bm25_score=chunk.bm25_score,
                rrf_score=getattr(chunk, "rrf_score", 0.0),
                rerank_score=score,
            )
        )
    scored.sort(key=lambda x: cast(float, x.rerank_score or 0.0), reverse=True)
    logger.info("Cross-Encoder rerank: top_k=%s selected", top_k)
    return cast("list[RagHit]", scored[:top_k])


def x__apply_rerank_scores__mutmut_54(
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
                rrf_score=getattr(chunk, "rrf_score", 0.0),
                rerank_score=score,
            )
        )
    scored.sort(key=lambda x: cast(float, x.rerank_score or 0.0), reverse=True)
    logger.info("Cross-Encoder rerank: top_k=%s selected", top_k)
    return cast("list[RagHit]", scored[:top_k])


def x__apply_rerank_scores__mutmut_55(
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
                rerank_score=score,
            )
        )
    scored.sort(key=lambda x: cast(float, x.rerank_score or 0.0), reverse=True)
    logger.info("Cross-Encoder rerank: top_k=%s selected", top_k)
    return cast("list[RagHit]", scored[:top_k])


def x__apply_rerank_scores__mutmut_56(
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
                )
        )
    scored.sort(key=lambda x: cast(float, x.rerank_score or 0.0), reverse=True)
    logger.info("Cross-Encoder rerank: top_k=%s selected", top_k)
    return cast("list[RagHit]", scored[:top_k])


def x__apply_rerank_scores__mutmut_57(
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
                rrf_score=getattr(None, "rrf_score", 0.0),
                rerank_score=score,
            )
        )
    scored.sort(key=lambda x: cast(float, x.rerank_score or 0.0), reverse=True)
    logger.info("Cross-Encoder rerank: top_k=%s selected", top_k)
    return cast("list[RagHit]", scored[:top_k])


def x__apply_rerank_scores__mutmut_58(
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
                rrf_score=getattr(chunk, None, 0.0),
                rerank_score=score,
            )
        )
    scored.sort(key=lambda x: cast(float, x.rerank_score or 0.0), reverse=True)
    logger.info("Cross-Encoder rerank: top_k=%s selected", top_k)
    return cast("list[RagHit]", scored[:top_k])


def x__apply_rerank_scores__mutmut_59(
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
                rrf_score=getattr(chunk, "rrf_score", None),
                rerank_score=score,
            )
        )
    scored.sort(key=lambda x: cast(float, x.rerank_score or 0.0), reverse=True)
    logger.info("Cross-Encoder rerank: top_k=%s selected", top_k)
    return cast("list[RagHit]", scored[:top_k])


def x__apply_rerank_scores__mutmut_60(
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
                rrf_score=getattr("rrf_score", 0.0),
                rerank_score=score,
            )
        )
    scored.sort(key=lambda x: cast(float, x.rerank_score or 0.0), reverse=True)
    logger.info("Cross-Encoder rerank: top_k=%s selected", top_k)
    return cast("list[RagHit]", scored[:top_k])


def x__apply_rerank_scores__mutmut_61(
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
                rrf_score=getattr(chunk, 0.0),
                rerank_score=score,
            )
        )
    scored.sort(key=lambda x: cast(float, x.rerank_score or 0.0), reverse=True)
    logger.info("Cross-Encoder rerank: top_k=%s selected", top_k)
    return cast("list[RagHit]", scored[:top_k])


def x__apply_rerank_scores__mutmut_62(
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
                rrf_score=getattr(chunk, "rrf_score", ),
                rerank_score=score,
            )
        )
    scored.sort(key=lambda x: cast(float, x.rerank_score or 0.0), reverse=True)
    logger.info("Cross-Encoder rerank: top_k=%s selected", top_k)
    return cast("list[RagHit]", scored[:top_k])


def x__apply_rerank_scores__mutmut_63(
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
                rrf_score=getattr(chunk, "XXrrf_scoreXX", 0.0),
                rerank_score=score,
            )
        )
    scored.sort(key=lambda x: cast(float, x.rerank_score or 0.0), reverse=True)
    logger.info("Cross-Encoder rerank: top_k=%s selected", top_k)
    return cast("list[RagHit]", scored[:top_k])


def x__apply_rerank_scores__mutmut_64(
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
                rrf_score=getattr(chunk, "RRF_SCORE", 0.0),
                rerank_score=score,
            )
        )
    scored.sort(key=lambda x: cast(float, x.rerank_score or 0.0), reverse=True)
    logger.info("Cross-Encoder rerank: top_k=%s selected", top_k)
    return cast("list[RagHit]", scored[:top_k])


def x__apply_rerank_scores__mutmut_65(
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
                rrf_score=getattr(chunk, "rrf_score", 1.0),
                rerank_score=score,
            )
        )
    scored.sort(key=lambda x: cast(float, x.rerank_score or 0.0), reverse=True)
    logger.info("Cross-Encoder rerank: top_k=%s selected", top_k)
    return cast("list[RagHit]", scored[:top_k])


def x__apply_rerank_scores__mutmut_66(
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
    scored.sort(key=None, reverse=True)
    logger.info("Cross-Encoder rerank: top_k=%s selected", top_k)
    return cast("list[RagHit]", scored[:top_k])


def x__apply_rerank_scores__mutmut_67(
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
    scored.sort(key=lambda x: cast(float, x.rerank_score or 0.0), reverse=None)
    logger.info("Cross-Encoder rerank: top_k=%s selected", top_k)
    return cast("list[RagHit]", scored[:top_k])


def x__apply_rerank_scores__mutmut_68(
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
    scored.sort(reverse=True)
    logger.info("Cross-Encoder rerank: top_k=%s selected", top_k)
    return cast("list[RagHit]", scored[:top_k])


def x__apply_rerank_scores__mutmut_69(
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
    scored.sort(key=lambda x: cast(float, x.rerank_score or 0.0), )
    logger.info("Cross-Encoder rerank: top_k=%s selected", top_k)
    return cast("list[RagHit]", scored[:top_k])


def x__apply_rerank_scores__mutmut_70(
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
    scored.sort(key=lambda x: None, reverse=True)
    logger.info("Cross-Encoder rerank: top_k=%s selected", top_k)
    return cast("list[RagHit]", scored[:top_k])


def x__apply_rerank_scores__mutmut_71(
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
    scored.sort(key=lambda x: cast(None, x.rerank_score or 0.0), reverse=True)
    logger.info("Cross-Encoder rerank: top_k=%s selected", top_k)
    return cast("list[RagHit]", scored[:top_k])


def x__apply_rerank_scores__mutmut_72(
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
    scored.sort(key=lambda x: cast(float, None), reverse=True)
    logger.info("Cross-Encoder rerank: top_k=%s selected", top_k)
    return cast("list[RagHit]", scored[:top_k])


def x__apply_rerank_scores__mutmut_73(
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
    scored.sort(key=lambda x: cast(x.rerank_score or 0.0), reverse=True)
    logger.info("Cross-Encoder rerank: top_k=%s selected", top_k)
    return cast("list[RagHit]", scored[:top_k])


def x__apply_rerank_scores__mutmut_74(
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
    scored.sort(key=lambda x: cast(float, ), reverse=True)
    logger.info("Cross-Encoder rerank: top_k=%s selected", top_k)
    return cast("list[RagHit]", scored[:top_k])


def x__apply_rerank_scores__mutmut_75(
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
    scored.sort(key=lambda x: cast(float, x.rerank_score and 0.0), reverse=True)
    logger.info("Cross-Encoder rerank: top_k=%s selected", top_k)
    return cast("list[RagHit]", scored[:top_k])


def x__apply_rerank_scores__mutmut_76(
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
    scored.sort(key=lambda x: cast(float, x.rerank_score or 1.0), reverse=True)
    logger.info("Cross-Encoder rerank: top_k=%s selected", top_k)
    return cast("list[RagHit]", scored[:top_k])


def x__apply_rerank_scores__mutmut_77(
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
    scored.sort(key=lambda x: cast(float, x.rerank_score or 0.0), reverse=False)
    logger.info("Cross-Encoder rerank: top_k=%s selected", top_k)
    return cast("list[RagHit]", scored[:top_k])


def x__apply_rerank_scores__mutmut_78(
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
    logger.info(None, top_k)
    return cast("list[RagHit]", scored[:top_k])


def x__apply_rerank_scores__mutmut_79(
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
    logger.info("Cross-Encoder rerank: top_k=%s selected", None)
    return cast("list[RagHit]", scored[:top_k])


def x__apply_rerank_scores__mutmut_80(
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
    logger.info(top_k)
    return cast("list[RagHit]", scored[:top_k])


def x__apply_rerank_scores__mutmut_81(
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
    logger.info("Cross-Encoder rerank: top_k=%s selected", )
    return cast("list[RagHit]", scored[:top_k])


def x__apply_rerank_scores__mutmut_82(
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
    logger.info("XXCross-Encoder rerank: top_k=%s selectedXX", top_k)
    return cast("list[RagHit]", scored[:top_k])


def x__apply_rerank_scores__mutmut_83(
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
    logger.info("cross-encoder rerank: top_k=%s selected", top_k)
    return cast("list[RagHit]", scored[:top_k])


def x__apply_rerank_scores__mutmut_84(
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
    logger.info("CROSS-ENCODER RERANK: TOP_K=%S SELECTED", top_k)
    return cast("list[RagHit]", scored[:top_k])


def x__apply_rerank_scores__mutmut_85(
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
    return cast(None, scored[:top_k])


def x__apply_rerank_scores__mutmut_86(
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
    return cast("list[RagHit]", None)


def x__apply_rerank_scores__mutmut_87(
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
    return cast(scored[:top_k])


def x__apply_rerank_scores__mutmut_88(
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
    return cast("list[RagHit]", )


def x__apply_rerank_scores__mutmut_89(
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
    return cast("XXlist[RagHit]XX", scored[:top_k])


def x__apply_rerank_scores__mutmut_90(
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
    return cast("list[raghit]", scored[:top_k])


def x__apply_rerank_scores__mutmut_91(
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
    return cast("LIST[RAGHIT]", scored[:top_k])

mutants_x__apply_rerank_scores__mutmut['_mutmut_orig'] = x__apply_rerank_scores__mutmut_orig # type: ignore # mutmut generated
mutants_x__apply_rerank_scores__mutmut['x__apply_rerank_scores__mutmut_1'] = x__apply_rerank_scores__mutmut_1 # type: ignore # mutmut generated
mutants_x__apply_rerank_scores__mutmut['x__apply_rerank_scores__mutmut_2'] = x__apply_rerank_scores__mutmut_2 # type: ignore # mutmut generated
mutants_x__apply_rerank_scores__mutmut['x__apply_rerank_scores__mutmut_3'] = x__apply_rerank_scores__mutmut_3 # type: ignore # mutmut generated
mutants_x__apply_rerank_scores__mutmut['x__apply_rerank_scores__mutmut_4'] = x__apply_rerank_scores__mutmut_4 # type: ignore # mutmut generated
mutants_x__apply_rerank_scores__mutmut['x__apply_rerank_scores__mutmut_5'] = x__apply_rerank_scores__mutmut_5 # type: ignore # mutmut generated
mutants_x__apply_rerank_scores__mutmut['x__apply_rerank_scores__mutmut_6'] = x__apply_rerank_scores__mutmut_6 # type: ignore # mutmut generated
mutants_x__apply_rerank_scores__mutmut['x__apply_rerank_scores__mutmut_7'] = x__apply_rerank_scores__mutmut_7 # type: ignore # mutmut generated
mutants_x__apply_rerank_scores__mutmut['x__apply_rerank_scores__mutmut_8'] = x__apply_rerank_scores__mutmut_8 # type: ignore # mutmut generated
mutants_x__apply_rerank_scores__mutmut['x__apply_rerank_scores__mutmut_9'] = x__apply_rerank_scores__mutmut_9 # type: ignore # mutmut generated
mutants_x__apply_rerank_scores__mutmut['x__apply_rerank_scores__mutmut_10'] = x__apply_rerank_scores__mutmut_10 # type: ignore # mutmut generated
mutants_x__apply_rerank_scores__mutmut['x__apply_rerank_scores__mutmut_11'] = x__apply_rerank_scores__mutmut_11 # type: ignore # mutmut generated
mutants_x__apply_rerank_scores__mutmut['x__apply_rerank_scores__mutmut_12'] = x__apply_rerank_scores__mutmut_12 # type: ignore # mutmut generated
mutants_x__apply_rerank_scores__mutmut['x__apply_rerank_scores__mutmut_13'] = x__apply_rerank_scores__mutmut_13 # type: ignore # mutmut generated
mutants_x__apply_rerank_scores__mutmut['x__apply_rerank_scores__mutmut_14'] = x__apply_rerank_scores__mutmut_14 # type: ignore # mutmut generated
mutants_x__apply_rerank_scores__mutmut['x__apply_rerank_scores__mutmut_15'] = x__apply_rerank_scores__mutmut_15 # type: ignore # mutmut generated
mutants_x__apply_rerank_scores__mutmut['x__apply_rerank_scores__mutmut_16'] = x__apply_rerank_scores__mutmut_16 # type: ignore # mutmut generated
mutants_x__apply_rerank_scores__mutmut['x__apply_rerank_scores__mutmut_17'] = x__apply_rerank_scores__mutmut_17 # type: ignore # mutmut generated
mutants_x__apply_rerank_scores__mutmut['x__apply_rerank_scores__mutmut_18'] = x__apply_rerank_scores__mutmut_18 # type: ignore # mutmut generated
mutants_x__apply_rerank_scores__mutmut['x__apply_rerank_scores__mutmut_19'] = x__apply_rerank_scores__mutmut_19 # type: ignore # mutmut generated
mutants_x__apply_rerank_scores__mutmut['x__apply_rerank_scores__mutmut_20'] = x__apply_rerank_scores__mutmut_20 # type: ignore # mutmut generated
mutants_x__apply_rerank_scores__mutmut['x__apply_rerank_scores__mutmut_21'] = x__apply_rerank_scores__mutmut_21 # type: ignore # mutmut generated
mutants_x__apply_rerank_scores__mutmut['x__apply_rerank_scores__mutmut_22'] = x__apply_rerank_scores__mutmut_22 # type: ignore # mutmut generated
mutants_x__apply_rerank_scores__mutmut['x__apply_rerank_scores__mutmut_23'] = x__apply_rerank_scores__mutmut_23 # type: ignore # mutmut generated
mutants_x__apply_rerank_scores__mutmut['x__apply_rerank_scores__mutmut_24'] = x__apply_rerank_scores__mutmut_24 # type: ignore # mutmut generated
mutants_x__apply_rerank_scores__mutmut['x__apply_rerank_scores__mutmut_25'] = x__apply_rerank_scores__mutmut_25 # type: ignore # mutmut generated
mutants_x__apply_rerank_scores__mutmut['x__apply_rerank_scores__mutmut_26'] = x__apply_rerank_scores__mutmut_26 # type: ignore # mutmut generated
mutants_x__apply_rerank_scores__mutmut['x__apply_rerank_scores__mutmut_27'] = x__apply_rerank_scores__mutmut_27 # type: ignore # mutmut generated
mutants_x__apply_rerank_scores__mutmut['x__apply_rerank_scores__mutmut_28'] = x__apply_rerank_scores__mutmut_28 # type: ignore # mutmut generated
mutants_x__apply_rerank_scores__mutmut['x__apply_rerank_scores__mutmut_29'] = x__apply_rerank_scores__mutmut_29 # type: ignore # mutmut generated
mutants_x__apply_rerank_scores__mutmut['x__apply_rerank_scores__mutmut_30'] = x__apply_rerank_scores__mutmut_30 # type: ignore # mutmut generated
mutants_x__apply_rerank_scores__mutmut['x__apply_rerank_scores__mutmut_31'] = x__apply_rerank_scores__mutmut_31 # type: ignore # mutmut generated
mutants_x__apply_rerank_scores__mutmut['x__apply_rerank_scores__mutmut_32'] = x__apply_rerank_scores__mutmut_32 # type: ignore # mutmut generated
mutants_x__apply_rerank_scores__mutmut['x__apply_rerank_scores__mutmut_33'] = x__apply_rerank_scores__mutmut_33 # type: ignore # mutmut generated
mutants_x__apply_rerank_scores__mutmut['x__apply_rerank_scores__mutmut_34'] = x__apply_rerank_scores__mutmut_34 # type: ignore # mutmut generated
mutants_x__apply_rerank_scores__mutmut['x__apply_rerank_scores__mutmut_35'] = x__apply_rerank_scores__mutmut_35 # type: ignore # mutmut generated
mutants_x__apply_rerank_scores__mutmut['x__apply_rerank_scores__mutmut_36'] = x__apply_rerank_scores__mutmut_36 # type: ignore # mutmut generated
mutants_x__apply_rerank_scores__mutmut['x__apply_rerank_scores__mutmut_37'] = x__apply_rerank_scores__mutmut_37 # type: ignore # mutmut generated
mutants_x__apply_rerank_scores__mutmut['x__apply_rerank_scores__mutmut_38'] = x__apply_rerank_scores__mutmut_38 # type: ignore # mutmut generated
mutants_x__apply_rerank_scores__mutmut['x__apply_rerank_scores__mutmut_39'] = x__apply_rerank_scores__mutmut_39 # type: ignore # mutmut generated
mutants_x__apply_rerank_scores__mutmut['x__apply_rerank_scores__mutmut_40'] = x__apply_rerank_scores__mutmut_40 # type: ignore # mutmut generated
mutants_x__apply_rerank_scores__mutmut['x__apply_rerank_scores__mutmut_41'] = x__apply_rerank_scores__mutmut_41 # type: ignore # mutmut generated
mutants_x__apply_rerank_scores__mutmut['x__apply_rerank_scores__mutmut_42'] = x__apply_rerank_scores__mutmut_42 # type: ignore # mutmut generated
mutants_x__apply_rerank_scores__mutmut['x__apply_rerank_scores__mutmut_43'] = x__apply_rerank_scores__mutmut_43 # type: ignore # mutmut generated
mutants_x__apply_rerank_scores__mutmut['x__apply_rerank_scores__mutmut_44'] = x__apply_rerank_scores__mutmut_44 # type: ignore # mutmut generated
mutants_x__apply_rerank_scores__mutmut['x__apply_rerank_scores__mutmut_45'] = x__apply_rerank_scores__mutmut_45 # type: ignore # mutmut generated
mutants_x__apply_rerank_scores__mutmut['x__apply_rerank_scores__mutmut_46'] = x__apply_rerank_scores__mutmut_46 # type: ignore # mutmut generated
mutants_x__apply_rerank_scores__mutmut['x__apply_rerank_scores__mutmut_47'] = x__apply_rerank_scores__mutmut_47 # type: ignore # mutmut generated
mutants_x__apply_rerank_scores__mutmut['x__apply_rerank_scores__mutmut_48'] = x__apply_rerank_scores__mutmut_48 # type: ignore # mutmut generated
mutants_x__apply_rerank_scores__mutmut['x__apply_rerank_scores__mutmut_49'] = x__apply_rerank_scores__mutmut_49 # type: ignore # mutmut generated
mutants_x__apply_rerank_scores__mutmut['x__apply_rerank_scores__mutmut_50'] = x__apply_rerank_scores__mutmut_50 # type: ignore # mutmut generated
mutants_x__apply_rerank_scores__mutmut['x__apply_rerank_scores__mutmut_51'] = x__apply_rerank_scores__mutmut_51 # type: ignore # mutmut generated
mutants_x__apply_rerank_scores__mutmut['x__apply_rerank_scores__mutmut_52'] = x__apply_rerank_scores__mutmut_52 # type: ignore # mutmut generated
mutants_x__apply_rerank_scores__mutmut['x__apply_rerank_scores__mutmut_53'] = x__apply_rerank_scores__mutmut_53 # type: ignore # mutmut generated
mutants_x__apply_rerank_scores__mutmut['x__apply_rerank_scores__mutmut_54'] = x__apply_rerank_scores__mutmut_54 # type: ignore # mutmut generated
mutants_x__apply_rerank_scores__mutmut['x__apply_rerank_scores__mutmut_55'] = x__apply_rerank_scores__mutmut_55 # type: ignore # mutmut generated
mutants_x__apply_rerank_scores__mutmut['x__apply_rerank_scores__mutmut_56'] = x__apply_rerank_scores__mutmut_56 # type: ignore # mutmut generated
mutants_x__apply_rerank_scores__mutmut['x__apply_rerank_scores__mutmut_57'] = x__apply_rerank_scores__mutmut_57 # type: ignore # mutmut generated
mutants_x__apply_rerank_scores__mutmut['x__apply_rerank_scores__mutmut_58'] = x__apply_rerank_scores__mutmut_58 # type: ignore # mutmut generated
mutants_x__apply_rerank_scores__mutmut['x__apply_rerank_scores__mutmut_59'] = x__apply_rerank_scores__mutmut_59 # type: ignore # mutmut generated
mutants_x__apply_rerank_scores__mutmut['x__apply_rerank_scores__mutmut_60'] = x__apply_rerank_scores__mutmut_60 # type: ignore # mutmut generated
mutants_x__apply_rerank_scores__mutmut['x__apply_rerank_scores__mutmut_61'] = x__apply_rerank_scores__mutmut_61 # type: ignore # mutmut generated
mutants_x__apply_rerank_scores__mutmut['x__apply_rerank_scores__mutmut_62'] = x__apply_rerank_scores__mutmut_62 # type: ignore # mutmut generated
mutants_x__apply_rerank_scores__mutmut['x__apply_rerank_scores__mutmut_63'] = x__apply_rerank_scores__mutmut_63 # type: ignore # mutmut generated
mutants_x__apply_rerank_scores__mutmut['x__apply_rerank_scores__mutmut_64'] = x__apply_rerank_scores__mutmut_64 # type: ignore # mutmut generated
mutants_x__apply_rerank_scores__mutmut['x__apply_rerank_scores__mutmut_65'] = x__apply_rerank_scores__mutmut_65 # type: ignore # mutmut generated
mutants_x__apply_rerank_scores__mutmut['x__apply_rerank_scores__mutmut_66'] = x__apply_rerank_scores__mutmut_66 # type: ignore # mutmut generated
mutants_x__apply_rerank_scores__mutmut['x__apply_rerank_scores__mutmut_67'] = x__apply_rerank_scores__mutmut_67 # type: ignore # mutmut generated
mutants_x__apply_rerank_scores__mutmut['x__apply_rerank_scores__mutmut_68'] = x__apply_rerank_scores__mutmut_68 # type: ignore # mutmut generated
mutants_x__apply_rerank_scores__mutmut['x__apply_rerank_scores__mutmut_69'] = x__apply_rerank_scores__mutmut_69 # type: ignore # mutmut generated
mutants_x__apply_rerank_scores__mutmut['x__apply_rerank_scores__mutmut_70'] = x__apply_rerank_scores__mutmut_70 # type: ignore # mutmut generated
mutants_x__apply_rerank_scores__mutmut['x__apply_rerank_scores__mutmut_71'] = x__apply_rerank_scores__mutmut_71 # type: ignore # mutmut generated
mutants_x__apply_rerank_scores__mutmut['x__apply_rerank_scores__mutmut_72'] = x__apply_rerank_scores__mutmut_72 # type: ignore # mutmut generated
mutants_x__apply_rerank_scores__mutmut['x__apply_rerank_scores__mutmut_73'] = x__apply_rerank_scores__mutmut_73 # type: ignore # mutmut generated
mutants_x__apply_rerank_scores__mutmut['x__apply_rerank_scores__mutmut_74'] = x__apply_rerank_scores__mutmut_74 # type: ignore # mutmut generated
mutants_x__apply_rerank_scores__mutmut['x__apply_rerank_scores__mutmut_75'] = x__apply_rerank_scores__mutmut_75 # type: ignore # mutmut generated
mutants_x__apply_rerank_scores__mutmut['x__apply_rerank_scores__mutmut_76'] = x__apply_rerank_scores__mutmut_76 # type: ignore # mutmut generated
mutants_x__apply_rerank_scores__mutmut['x__apply_rerank_scores__mutmut_77'] = x__apply_rerank_scores__mutmut_77 # type: ignore # mutmut generated
mutants_x__apply_rerank_scores__mutmut['x__apply_rerank_scores__mutmut_78'] = x__apply_rerank_scores__mutmut_78 # type: ignore # mutmut generated
mutants_x__apply_rerank_scores__mutmut['x__apply_rerank_scores__mutmut_79'] = x__apply_rerank_scores__mutmut_79 # type: ignore # mutmut generated
mutants_x__apply_rerank_scores__mutmut['x__apply_rerank_scores__mutmut_80'] = x__apply_rerank_scores__mutmut_80 # type: ignore # mutmut generated
mutants_x__apply_rerank_scores__mutmut['x__apply_rerank_scores__mutmut_81'] = x__apply_rerank_scores__mutmut_81 # type: ignore # mutmut generated
mutants_x__apply_rerank_scores__mutmut['x__apply_rerank_scores__mutmut_82'] = x__apply_rerank_scores__mutmut_82 # type: ignore # mutmut generated
mutants_x__apply_rerank_scores__mutmut['x__apply_rerank_scores__mutmut_83'] = x__apply_rerank_scores__mutmut_83 # type: ignore # mutmut generated
mutants_x__apply_rerank_scores__mutmut['x__apply_rerank_scores__mutmut_84'] = x__apply_rerank_scores__mutmut_84 # type: ignore # mutmut generated
mutants_x__apply_rerank_scores__mutmut['x__apply_rerank_scores__mutmut_85'] = x__apply_rerank_scores__mutmut_85 # type: ignore # mutmut generated
mutants_x__apply_rerank_scores__mutmut['x__apply_rerank_scores__mutmut_86'] = x__apply_rerank_scores__mutmut_86 # type: ignore # mutmut generated
mutants_x__apply_rerank_scores__mutmut['x__apply_rerank_scores__mutmut_87'] = x__apply_rerank_scores__mutmut_87 # type: ignore # mutmut generated
mutants_x__apply_rerank_scores__mutmut['x__apply_rerank_scores__mutmut_88'] = x__apply_rerank_scores__mutmut_88 # type: ignore # mutmut generated
mutants_x__apply_rerank_scores__mutmut['x__apply_rerank_scores__mutmut_89'] = x__apply_rerank_scores__mutmut_89 # type: ignore # mutmut generated
mutants_x__apply_rerank_scores__mutmut['x__apply_rerank_scores__mutmut_90'] = x__apply_rerank_scores__mutmut_90 # type: ignore # mutmut generated
mutants_x__apply_rerank_scores__mutmut['x__apply_rerank_scores__mutmut_91'] = x__apply_rerank_scores__mutmut_91 # type: ignore # mutmut generated


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
    "_build_rerank_prompt",
    "_apply_rerank_scores",
]
