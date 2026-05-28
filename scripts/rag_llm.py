#!/usr/bin/env python3
"""
rag_llm.py
LLM-based RAG operations: embedding, MQE query expansion, cross-encoder reranking,
tool summarization, and context refining.

Extracted from agent_rag.py.  Contains:
  - RagLLM class — encapsulates all LLM calls for the RAG pipeline
  - get_embedding  — convert text to a float embedding vector
  - summarize_tool_result — shorten long tool output for LLM context
"""

import logging
import re

import httpx
import orjson
from config_loader import ConfigLoader
from rag_types import LLMMessage, RagHit

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Config (common.json + agent.json — same files as agent_rag._get_cfg)
# ─────────────────────────────────────────────────────────────────────────────

_cfg: dict | None = None


def _get_cfg() -> dict:
    """Load config on first call; cached for the module lifetime."""
    global _cfg
    if _cfg is None:
        try:
            _cfg = ConfigLoader().load("common.json", "agent.json")
        except Exception as e:
            logger.warning(f"Config load failed: {e}")
            _cfg = {}
    return _cfg


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
# Internal prompt helpers
# ─────────────────────────────────────────────────────────────────────────────


def _mqe_prompt(query: str, context: str = "") -> str:
    """Build the MQE rephrasing prompt, prepending conversation context when given.

    context holds recent user utterances; it is search-only and is never sent
    directly to the final LLM answer prompt.
    """
    cfg = _get_cfg()
    prompt = cfg.get("mqe_prompt_template", "").format(
        n_queries=cfg.get("mqe_n_queries", 3), query=query
    )
    if context:
        prompt = f"Context: {context}\n\n{prompt}"
    return str(prompt)


def _parse_mqe_response(raw: str, original_query: str) -> list[str]:
    """Extract and validate a JSON array of paraphrases from raw LLM output."""
    m = re.search(r"\[.*\]", raw, re.DOTALL)
    if not m:
        return [original_query]
    try:
        expanded = orjson.loads(m.group())
    except orjson.JSONDecodeError:
        logger.warning("MQE response JSON is malformed, fallback to original query")
        return [original_query]
    if not isinstance(expanded, list):
        return [original_query]
    valid = [q for q in expanded if isinstance(q, str) and q.strip()]
    logger.info(f"MQE: {len(valid)} queries expanded from original")
    return [original_query] + valid


def _extract_chat_content(data: dict) -> str:
    """Extract content text from an OpenAI-compatible chat completion response.

    Raises ValueError if the response is malformed or missing expected fields.
    """
    choices = data.get("choices")
    if not choices or not isinstance(choices, list):
        raise ValueError("Unexpected LLM response: missing 'choices' field")
    content = choices[0].get("message", {}).get("content")
    if content is None:
        raise ValueError("Unexpected LLM response: missing 'content' field")
    return str(content).strip()


def _build_rerank_prompt(query: str, candidates: list[RagHit]) -> str:
    """Build the Cross-Encoder scoring prompt from the configured template."""
    items_text = ""
    for i, chunk in enumerate(candidates, start=1):
        preview = chunk["content"][:300].replace("\n", " ")
        items_text += f"\n{i}. {preview}"
    return str(
        _get_cfg()
        .get("rerank_prompt_template", "")
        .format(query=query, items_text=items_text)
    )


def _apply_rerank_scores(
    raw: str, candidates: list[RagHit], top_k: int
) -> list[RagHit] | None:
    """Parse LLM score output and return top_k candidates sorted by score.

    Returns None on parse failure so the caller can fall back to RRF order.
    """
    from typing import cast  # noqa: PLC0415

    m = re.search(r"\{.*\}", raw, re.DOTALL)
    if not m:
        return None
    try:
        score_map: dict = orjson.loads(m.group())
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
                f"Rerank: non-numeric score {score_val!r}"
                f" for candidate {i}, using default"
            )
            score = _DEFAULT_RERANK_SCORE
        scored.append({**chunk, "rerank_score": score})
    scored.sort(key=lambda x: cast(float, x["rerank_score"]), reverse=True)
    logger.info(f"Cross-Encoder rerank: top_k={top_k} selected")
    return cast(list[RagHit], scored[:top_k])


# ─────────────────────────────────────────────────────────────────────────────
# RagLLM class
# ─────────────────────────────────────────────────────────────────────────────


class RagLLM:
    """LLM-based query expansion (MQE) and cross-encoder reranking."""

    def __init__(self, client: httpx.AsyncClient, llm_url: str) -> None:
        self._client = client
        self._llm_url = llm_url

    async def _call_llm(
        self, messages: list[LLMMessage], temperature: float, max_tokens: int
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
        return _extract_chat_content(resp.json())

    async def expand_queries(self, query: str, context: str = "") -> list[str]:
        """
        Expand the original query to multiple paraphrases using LLM.
        context: recent user utterances injected into the MQE prompt to help
        the LLM disambiguate pronouns and abbreviations in multi-turn conversations.
        Returns [original_query] on any failure as fallback.
        """
        try:
            raw = await self._call_llm(
                [{"role": "user", "content": _mqe_prompt(query, context)}],
                _MQE_TEMPERATURE,
                _MQE_MAX_TOKENS,
            )
            return _parse_mqe_response(raw, query)
        except httpx.HTTPStatusError as e:
            logger.warning(
                f"MQE failed (HTTP {e.response.status_code}),"
                f" fallback to original query: {e}"
            )
        except httpx.RequestError as e:
            logger.warning(
                f"MQE failed (connection error), fallback to original query: {e}"
            )
        except orjson.JSONDecodeError as e:
            logger.warning(
                f"MQE failed (JSON parse error), fallback to original query: {e}"
            )
        except Exception:
            logger.exception(
                "MQE failed (unexpected error), fallback to original query"
            )
        return [query]

    async def cross_encoder_rerank(
        self,
        query: str,
        candidates: list[RagHit],
        top_k: int,
        rag_min_score: float = 0.0,
    ) -> list[RagHit]:
        """
        Use LLM as a Cross-Encoder to re-evaluate query-chunk relevance.
        Batch-scores N candidates in a single LLM call to reduce latency.
        Drops chunks whose rerank_score < rag_min_score before returning.
        Falls back to RRF score order on LLM call failure.
        """
        if not candidates:
            return []
        try:
            raw = await self._call_llm(
                [{"role": "user", "content": _build_rerank_prompt(query, candidates)}],
                _RERANK_TEMPERATURE,
                _RERANK_MAX_TOKENS,
            )
            result = _apply_rerank_scores(raw, candidates, top_k)
            if result is not None:
                # Remove low-relevance chunks below the configured minimum score
                if rag_min_score > 0.0:
                    result = [
                        c for c in result if c.get("rerank_score", 0.0) >= rag_min_score
                    ]
                    logger.info(
                        f"Rerank score filter: {len(result)} chunks remain"
                        f" (min_score={rag_min_score})"
                    )
                return result
        except httpx.HTTPStatusError as e:
            logger.warning(
                f"Cross-Encoder rerank failed (HTTP {e.response.status_code}),"
                f" fallback to RRF order: {e}"
            )
        except httpx.RequestError as e:
            logger.warning(
                "Cross-Encoder rerank failed (connection error),"
                f" fallback to RRF order: {e}"
            )
        except orjson.JSONDecodeError as e:
            logger.warning(
                "Cross-Encoder rerank failed (JSON parse error),"
                f" fallback to RRF order: {e}"
            )
        except Exception:
            logger.exception(
                "Cross-Encoder rerank failed (unexpected error), fallback to RRF order"
            )
        return candidates[:top_k]

    async def summarize_tool_result(self, text: str, tool_name: str, args: dict) -> str:
        """Summarize a long tool result to reduce LLM context consumption.

        Sends up to _SUMMARIZE_INPUT_MAX_CHARS of the result to the LLM and
        returns a 3-5 sentence summary preserving key facts. Falls back to the
        original text on any error so the caller can use truncation as fallback.
        """
        text_preview = text[:_SUMMARIZE_INPUT_MAX_CHARS]
        args_str = orjson.dumps(args).decode()[:200]
        prompt = _SUMMARIZE_PROMPT_TEMPLATE.format(
            tool_name=tool_name,
            args_str=args_str,
            text_preview=text_preview,
        )
        try:
            return await self._call_llm(
                [{"role": "user", "content": prompt}],
                _SUMMARIZE_TEMPERATURE,
                _SUMMARIZE_MAX_TOKENS,
            )
        except Exception as e:
            logger.warning(f"Tool summarization failed for {tool_name!r}: {e}")
            return text

    async def refine_context(
        self,
        chunks: list[RagHit],
        query: str,
        max_tokens: int,
        per_chunk_chars: int,
        timeout: float,
    ) -> str:
        """Compress RAG chunks into query-relevant key points via a single LLM call.

        Truncates each chunk to per_chunk_chars before prompting to prevent token
        explosion on long chunks. Raises on LLM error so callers can fall back to
        original chunk formatting.
        """
        items = []
        for i, c in enumerate(chunks, 1):
            title = c.get("title") or c.get("url", "")
            text = c["content"][:per_chunk_chars]
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
        return _extract_chat_content(resp.json())


# ─────────────────────────────────────────────────────────────────────────────
# Module-level functions (externally imported)
# ─────────────────────────────────────────────────────────────────────────────


async def get_embedding(text: str, client: httpx.AsyncClient) -> list[float]:
    """
    Convert text to a 384-dimensional float embedding vector.
    E5 model requires "query: " prefix for query input.
    (Ingestion uses "passage: " prefix)
    """
    resp = await client.post(
        _get_cfg().get("embed_url", ""), json={"content": f"query: {text}"}
    )
    resp.raise_for_status()
    embedding = resp.json().get("embedding")
    if not isinstance(embedding, list) or not embedding:
        raise ValueError("missing or empty 'embedding' field in embed response")
    return embedding


async def summarize_tool_result(
    text: str, tool_name: str, args: dict, client: httpx.AsyncClient
) -> str:
    """Tool result summarization. Delegates to RagLLM."""
    return await RagLLM(client, _get_cfg().get("llm_url", "")).summarize_tool_result(
        text, tool_name, args
    )
