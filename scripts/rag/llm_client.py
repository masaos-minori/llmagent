#!/usr/bin/env python3
"""rag/llm_client.py

RagLLM class and module-level LLM functions for the RAG pipeline.

Provides:
  RagLLM              — LLM-based query expansion (MQE) and cross-encoder reranking
  get_embedding       — convert text to a float embedding vector
  summarize_tool_result — shorten long tool output for LLM context

Import from here:  from rag.llm_client import RagLLM, get_embedding, summarize_tool_result
"""

from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any

import httpx
import orjson
from shared.config_loader import ConfigLoader
from shared.json_utils import (
    dumps as _json_dumps,
)
from shared.json_utils import (
    extract_llm_content,
    parse_http_json,
)
from shared.llm_client import build_embed_url, build_llm_url
from shared.types import (
    LLMMessage,
    RagHit,  # noqa: F401 — imported for use in this module
)

from rag.llm_prompts import (
    _MQE_MAX_TOKENS,
    _MQE_TEMPERATURE,
    _REFINER_PROMPT_TEMPLATE,
    _REFINER_TEMPERATURE,
    _RERANK_MAX_TOKENS,
    _RERANK_TEMPERATURE,
    _SUMMARIZE_INPUT_MAX_CHARS,
    _SUMMARIZE_MAX_TOKENS,
    _SUMMARIZE_PROMPT_TEMPLATE,
    _SUMMARIZE_TEMPERATURE,
    MqeParseError,
    RagExpansionError,
    RagRerankError,
    _apply_rerank_scores,
    _build_rerank_prompt,
    _mqe_prompt,
    _parse_mqe_response,
)

logger = logging.getLogger(__name__)

# Module-level cached llm_url; loaded once and reused across calls.
_llm_url_cache: str | None = None
_embed_url_cache: str | None = None


def _get_cached_llm_url() -> str:
    """Return the cached llm_url, loading from config on first call."""
    global _llm_url_cache
    if _llm_url_cache is None:
        try:
            cfg = ConfigLoader().load_all()
            _llm_url_cache = build_llm_url(cfg.get("llm_url", ""))
        except (FileNotFoundError, ValueError):
            _llm_url_cache = ""
    assert _llm_url_cache is not None
    return _llm_url_cache


def _get_cached_embed_url() -> str:
    """Return the cached embed_url, loading from config on first call."""
    global _embed_url_cache
    if _embed_url_cache is None:
        try:
            cfg = ConfigLoader().load_all()
            _embed_url_cache = build_embed_url(cfg.get("embed_url", ""))
        except (FileNotFoundError, ValueError):
            _embed_url_cache = ""
    assert _embed_url_cache is not None
    return _embed_url_cache


# ─────────────────────────────────────────────────────────────────────────────
# RagLLM class
# ─────────────────────────────────────────────────────────────────────────────


class RagLLM:
    """LLM-based query expansion (MQE) and cross-encoder reranking."""

    def __init__(
        self,
        client: httpx.AsyncClient,
        llm_url: str,
        cfg: Mapping[str, object] | None = None,
    ) -> None:
        self._client = client
        self._llm_url = llm_url
        self._cfg: Mapping[str, object] = cfg if cfg is not None else {}

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
        chat_content: str = extract_llm_content(parse_http_json(resp))
        return chat_content

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
            queries: list[str] = result.queries
            return queries
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
        except (httpx.HTTPStatusError, httpx.RequestError, ValueError) as e:
            raise RagRerankError(f"Cross-encoder rerank LLM call failed: {e}") from e
        result = _apply_rerank_scores(raw, candidates, top_k)
        if result is None:
            raise RagRerankError("Cross-encoder rerank: score parse returned no result")
        if rag_min_score > 0.0:
            result = [
                c
                for c in result
                if (getattr(c, "rerank_score", None) or 0.0) >= rag_min_score
            ]
            logger.info(
                "Rerank score filter: %s chunks remain (min_score=%s)",
                len(result),
                rag_min_score,
            )
        reranked: list[Any] = result
        return reranked

    async def summarize_tool_result(
        self,
        text: str,
        tool_name: str,
        args: dict[str, object],
    ) -> str:
        """Summarize a long tool result via LLM (3-5 sentences).

        Raises on any HTTP or parse failure — callers decide how to handle.
        """
        text_preview = text[:_SUMMARIZE_INPUT_MAX_CHARS]
        args_str = _json_dumps(args)[:200]
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
        refined_text: str = extract_llm_content(parse_http_json(resp))
        return refined_text


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
    embedding = parse_http_json(resp).get("embedding")
    if not isinstance(embedding, list) or not embedding:
        raise ValueError("missing or empty 'embedding' field in embed response")
    return embedding


async def summarize_tool_result(
    text: str,
    tool_name: str,
    args: dict[str, object],
    client: httpx.AsyncClient,
    llm_url: str | None = None,
) -> str:
    """Tool result summarization. Delegates to RagLLM.

    llm_url: if None, uses cached config value (loaded once per process).
    Raises on LLM call failure.
    """
    if llm_url is None:
        llm_url = _get_cached_llm_url()
    return await RagLLM(client, llm_url).summarize_tool_result(text, tool_name, args)


__all__ = [
    "RagHit",
    "RagLLM",
    "get_embedding",
    "summarize_tool_result",
]
