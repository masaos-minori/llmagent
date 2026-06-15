#!/usr/bin/env python3
"""rag_llm.py
LLM-based RAG operations: embedding, MQE query expansion, cross-encoder reranking,
tool summarization, and context refining.

Extracted from agent_rag.py.  Contains:
  - RagLLM class — encapsulates all LLM calls for the RAG pipeline
  - get_embedding  — convert text to a float embedding vector
  - summarize_tool_result — shorten long tool output for LLM context
"""

import logging
import re
from dataclasses import dataclass
from typing import Any, cast

import httpx
import orjson
from shared.config_loader import ConfigLoader
from shared.types import LLMMessage

from rag.types import MergedHit, RankedHit, RawHit

RagHit = RawHit | MergedHit | RankedHit

logger = logging.getLogger(__name__)


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
    " Be concise — preserve specific values, numbers, and technical details."
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


def _mqe_prompt(query: str, context: str, cfg: dict[str, Any]) -> str:
    """Build the MQE rephrasing prompt, prepending conversation context when given.

    context holds recent user utterances; it is search-only and is never sent
    directly to the final LLM answer prompt.
    """
    prompt = cfg.get("mqe_prompt_template", "").format(
        n_queries=cfg.get("mqe_n_queries", 3),
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


def _extract_chat_content(data: dict[str, Any]) -> str:
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
    query: str, candidates: list[RagHit], cfg: dict[str, Any]
) -> str:
    """Build the Cross-Encoder scoring prompt from the configured template."""
    items_text = ""
    for i, chunk in enumerate(candidates, start=1):
        preview = chunk.content[:300].replace("\n", " ")
        items_text += f"\n{i}. {preview}"
    return str(
        cfg.get("rerank_prompt_template", "").format(
            query=query, items_text=items_text
        ),
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
        score_map: dict[str, Any] = orjson.loads(m.group())
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


# ─────────────────────────────────────────────────────────────────────────────
# RagLLM class
# ─────────────────────────────────────────────────────────────────────────────


class RagLLM:
    """LLM-based query expansion (MQE) and cross-encoder reranking."""

    def __init__(
        self,
        client: httpx.AsyncClient,
        llm_url: str,
        cfg: dict[str, Any] | None = None,
    ) -> None:
        self._client = client
        self._llm_url = llm_url
        self._cfg: dict[str, Any] = cfg if cfg is not None else {}

    async def _call_llm(
        self,
        messages: list[LLMMessage],
        temperature: float,
        max_tokens: int,
    ) -> str:
        """Call the chat LLM endpoint and return the response content string."""
        resp = await self._client.post(
            self._llm_url,
            json={
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
        )
        resp.raise_for_status()
        return _extract_chat_content(orjson.loads(resp.content))

    async def expand_queries(self, query: str, context: str = "") -> list[str]:
        """Expand query to MQE paraphrases via LLM.

        Raises RagExpansionError on HTTP failure, connection error, or parse failure.
        """
        try:
            raw = await self._call_llm(
                [{"role": "user", "content": _mqe_prompt(query, context, self._cfg)}],
                _MQE_TEMPERATURE,
                _MQE_MAX_TOKENS,
            )
            result = _parse_mqe_response(raw, query)
            return result.queries
        except (
            httpx.HTTPStatusError,
            httpx.RequestError,
            orjson.JSONDecodeError,
            MqeParseError,
        ) as e:
            raise RagExpansionError(f"MQE expansion failed: {e}") from e

    async def cross_encoder_rerank(
        self,
        query: str,
        candidates: list[RagHit],
        top_k: int,
        rag_min_score: float = 0.0,
    ) -> list[RagHit]:
        """Re-rank candidates with a single batch LLM call; drops below rag_min_score.

        Raises RagRerankError on HTTP failure, connection error, or parse failure.
        """
        if not candidates:
            return []
        try:
            raw = await self._call_llm(
                [
                    {
                        "role": "user",
                        "content": _build_rerank_prompt(query, candidates, self._cfg),
                    }
                ],
                _RERANK_TEMPERATURE,
                _RERANK_MAX_TOKENS,
            )
        except (httpx.HTTPStatusError, httpx.RequestError, orjson.JSONDecodeError) as e:
            raise RagRerankError(f"Cross-encoder rerank LLM call failed: {e}") from e
        result = _apply_rerank_scores(raw, candidates, top_k)
        if result is None:
            raise RagRerankError("Cross-encoder rerank: score parse returned no result")
        if rag_min_score > 0.0:
            result = [
                c
                for c in result
                if cast(float, getattr(c, "rerank_score", None) or 0.0) >= rag_min_score
            ]
            logger.info(
                "Rerank score filter: %s chunks remain (min_score=%s)",
                len(result),
                rag_min_score,
            )
        return result

    async def summarize_tool_result(
        self,
        text: str,
        tool_name: str,
        args: dict[str, Any],
    ) -> str:
        """Summarize a long tool result via LLM (3-5 sentences).

        Raises on any HTTP or parse failure — callers decide how to handle.
        """
        text_preview = text[:_SUMMARIZE_INPUT_MAX_CHARS]
        args_str = orjson.dumps(args).decode()[:200]
        prompt = _SUMMARIZE_PROMPT_TEMPLATE.format(
            tool_name=tool_name,
            args_str=args_str,
            text_preview=text_preview,
        )
        return await self._call_llm(
            [{"role": "user", "content": prompt}],
            _SUMMARIZE_TEMPERATURE,
            _SUMMARIZE_MAX_TOKENS,
        )

    async def refine_context(
        self,
        chunks: list[RagHit],
        query: str,
        max_tokens: int,
        per_chunk_chars: int,
        timeout: float,
    ) -> str:
        """Compress chunks to query-relevant key points via a single LLM call; raises on error so callers can fall back."""
        items = []
        for i, c in enumerate(chunks, 1):
            title = c.title if c.title else c.url
            text = c.content[:per_chunk_chars]
            items.append(f"[{i}] {title}\n{text}")
        items_text = "\n\n".join(items)
        prompt = _REFINER_PROMPT_TEMPLATE.format(query=query, items_text=items_text)
        resp = await self._client.post(
            self._llm_url,
            json={
                "messages": [{"role": "user", "content": prompt}],
                "temperature": _REFINER_TEMPERATURE,
                "max_tokens": max_tokens,
            },
            timeout=timeout,
        )
        resp.raise_for_status()
        return _extract_chat_content(orjson.loads(resp.content))


# ─────────────────────────────────────────────────────────────────────────────
# Module-level functions (externally imported)
# ─────────────────────────────────────────────────────────────────────────────


async def get_embedding(
    text: str, client: httpx.AsyncClient, embed_url: str
) -> list[float]:
    """Convert text to a 384-dimensional float embedding vector.
    E5 model requires "query: " prefix for query input.
    (Ingestion uses "passage: " prefix)
    """
    resp = await client.post(
        embed_url,
        json={"content": f"query: {text}"},
    )
    resp.raise_for_status()
    embedding = orjson.loads(resp.content).get("embedding")
    if not isinstance(embedding, list) or not embedding:
        raise ValueError("missing or empty 'embedding' field in embed response")
    return embedding


async def summarize_tool_result(
    text: str,
    tool_name: str,
    args: dict[str, Any],
    client: httpx.AsyncClient,
    llm_url: str | None = None,
) -> str:
    """Tool result summarization. Delegates to RagLLM.

    llm_url: if None, reads from common.toml/agent.toml at call time.
    Raises on config load failure or LLM call failure.
    """
    if llm_url is None:
        cfg = ConfigLoader().load("common.toml", "agent.toml")
        llm_url = cfg.get("llm_url", "")
    return await RagLLM(client, llm_url).summarize_tool_result(text, tool_name, args)
