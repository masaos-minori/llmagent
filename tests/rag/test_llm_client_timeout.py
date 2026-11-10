"""tests/rag/test_llm_client_timeout.py

Regression tests for per-request timeout forwarding at the in-process RAG POST
call sites (rag002).

Prove `RagLLM._call_llm` (driven through `expand_queries`) and `get_embedding`
forward the injected client's configured timeout verbatim at the HTTP boundary:
a non-production value (7.5) proves derivation rather than a copied literal,
and the production value (120.0) pins "no numeric drift".
"""

from __future__ import annotations

import dataclasses
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import httpx
import orjson
import pytest
from rag.exceptions import RagExpansionError
from rag.llm_client import RagLLM, get_embedding
from rag.models_config import RagConfigImpl
from shared.types import RagConfig

# ── Fixtures ──────────────────────────────────────────────────────────────────


def _make_cfg(**overrides: object) -> RagConfig:
    """Create a minimal RagConfigImpl with defaults (models test_augment_refiner)."""
    base = RagConfigImpl(
        llm_url="http://localhost:8000/v1/chat/completions",
        embed_url="http://localhost:8000/v1/embeddings",
        rag_db_path=":memory:",
        sqlite_vec_so="/opt/llm/sqlite-vec/vec0.so",
        sqlite_timeout=5,
        sqlite_busy_timeout_ms=5000,
        embed_retry=3,
        embed_workers=4,
        rag_pipeline_service_url=None,
        mqe_prompt_template="Expand query: {query}",
        mqe_n_queries=3,
        rerank_prompt_template="Rerank results for: {query}",
        use_search=True,
        use_refiner=False,
        use_mqe=False,
        use_rerank=False,
        use_rrf=True,
        rrf_k=60,
        top_k_search=5,
        rag_top_k=3,
        top_k_rerank=10,
        rag_min_score=0.0,
        max_chunks_per_doc=3,
        refiner_max_tokens=256,
        refiner_max_chars_per_chunk=500,
        refiner_timeout=10.0,
    )
    return dataclasses.replace(base, **overrides) if overrides else base


# Response bodies differ per endpoint: chat-completion for expand_queries,
# embedding list for get_embedding.
_CHAT_BODY = orjson.dumps(
    {
        "choices": [
            {
                "message": {
                    "content": '["alt query 1", "alt query 2", "alt query 3"]',
                }
            }
        ]
    }
)
_EMBED_BODY = orjson.dumps({"embedding": [0.1, 0.2]})


def _make_fake_client(timeout: float, body: bytes) -> MagicMock:
    """Fake httpx.AsyncClient exposing .timeout and recording post() call kwargs.

    The stub response carries only what the RAG call sites read: no-op
    raise_for_status() and .content bytes (parse_http_json reads .content).
    """
    client = MagicMock(spec=httpx.AsyncClient)
    client.timeout = timeout
    resp = MagicMock()
    resp.raise_for_status = MagicMock()
    resp.content = body
    client.post = AsyncMock(return_value=resp)
    return client


# ── Tests ─────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_call_llm_forwards_client_timeout() -> None:
    """REQ-001/AC-2: _call_llm (via expand_queries) forwards the client's 7.5 timeout verbatim."""
    client = _make_fake_client(7.5, _CHAT_BODY)
    rag_llm = RagLLM(
        client=client,
        llm_url="http://localhost:8000/v1/chat/completions",
        cfg=_make_cfg(),
    )
    await rag_llm.expand_queries("query")
    recorded: dict[str, Any] = client.post.await_args.kwargs
    assert recorded["timeout"] == 7.5


@pytest.mark.asyncio
async def test_get_embedding_forwards_client_timeout() -> None:
    """REQ-002/AC-2: get_embedding forwards the client's 7.5 timeout verbatim."""
    client = _make_fake_client(7.5, _EMBED_BODY)
    await get_embedding("text", client, "http://localhost:8000/embeddings")
    recorded: dict[str, Any] = client.post.await_args.kwargs
    assert recorded["timeout"] == 7.5


@pytest.mark.asyncio
async def test_forwarded_timeout_matches_production_client_value() -> None:
    """REQ-003/AC-2: at the production client timeout (120.0) both sites forward exactly 120.0."""
    chat_client = _make_fake_client(120.0, _CHAT_BODY)
    rag_llm = RagLLM(
        client=chat_client,
        llm_url="http://localhost:8000/v1/chat/completions",
        cfg=_make_cfg(),
    )
    await rag_llm.expand_queries("query")
    assert chat_client.post.await_args.kwargs["timeout"] == 120.0

    embed_client = _make_fake_client(120.0, _EMBED_BODY)
    await get_embedding("text", embed_client, "http://localhost:8000/embeddings")
    assert embed_client.post.await_args.kwargs["timeout"] == 120.0


# ── get_embedding element validation (ragvec001) ───────────────────────────────

# orjson serializes non-finite floats as null on the way in, so the inf case
# arrives at get_embedding as a non-numeric element; both must be rejected.
_OVER_RANGE_EMBED_BODY = orjson.dumps({"embedding": [0.1, 1e300]})
_INF_EMBED_BODY = orjson.dumps({"embedding": [0.1, float("inf")]})


@pytest.mark.asyncio
async def test_get_embedding_rejects_out_of_float32_range() -> None:
    """REQ-001: a finite-but-out-of-range element raises ValueError naming the index."""
    client = _make_fake_client(7.5, _OVER_RANGE_EMBED_BODY)
    with pytest.raises(ValueError, match="index 1"):
        await get_embedding("text", client, "http://localhost:8000/embeddings")


@pytest.mark.asyncio
async def test_get_embedding_rejects_non_numeric_element() -> None:
    """REQ-001: an element that is not numeric (inf serialized as null) is rejected."""
    client = _make_fake_client(7.5, _INF_EMBED_BODY)
    with pytest.raises(ValueError, match="index 1"):
        await get_embedding("text", client, "http://localhost:8000/embeddings")


@pytest.mark.asyncio
async def test_get_embedding_returns_valid_embedding_unchanged() -> None:
    """REQ-001: a normal-range embedding passes validation and is returned as-is."""
    client = _make_fake_client(7.5, _EMBED_BODY)
    result = await get_embedding("text", client, "http://localhost:8000/embeddings")
    assert result == [0.1, 0.2]


# ── MQE malformed-response conversion (ragrev001) ───────────────────────────────

# One body per REQ-001 shape: content null, empty choices, non-JSON body.
_MALFORMED_BODIES: list[bytes] = [
    orjson.dumps({"choices": [{"message": {"content": None}}]}),
    orjson.dumps({"choices": []}),
    b"not json",
]


def _make_llm(client: MagicMock, cfg: RagConfig) -> RagLLM:
    """Build a RagLLM around a fake client, matching the timeout tests above."""
    return RagLLM(
        client=client,
        llm_url="http://localhost:8000/v1/chat/completions",
        cfg=cfg,
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("body", _MALFORMED_BODIES)
async def test_expand_queries_malformed_response_converts(body: bytes) -> None:
    """REQ-001: every malformed-response shape aborts with RagExpansionError."""
    rag_llm = _make_llm(_make_fake_client(7.5, body), _make_cfg())
    with pytest.raises(RagExpansionError) as exc_info:
        await rag_llm.expand_queries("query")
    assert isinstance(exc_info.value.__cause__, ValueError)


@pytest.mark.asyncio
async def test_expand_queries_prompt_typeerror_propagates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """REQ-002 guard: a TypeError raised while building the prompt is not converted."""

    def _broken_prompt(query: str, context: str, cfg: RagConfig) -> str:
        raise TypeError("prompt construction defect")

    monkeypatch.setattr("rag.llm_client._mqe_prompt", _broken_prompt)
    rag_llm = _make_llm(_make_fake_client(7.5, _CHAT_BODY), _make_cfg())
    with pytest.raises(TypeError, match="prompt construction defect"):
        await rag_llm.expand_queries("query")


@pytest.mark.asyncio
async def test_expand_queries_bad_template_valueerror_propagates() -> None:
    """REQ-002 guard: a format ValueError from a malformed template is not converted."""
    rag_llm = _make_llm(
        _make_fake_client(7.5, _CHAT_BODY),
        _make_cfg(mqe_prompt_template="Expand query: {query"),
    )
    with pytest.raises(ValueError, match="expected .* before end of string"):
        await rag_llm.expand_queries("query")
