"""tests/shared/test_llm_client_characterization.py

Characterization tests for scripts/shared/llm_client.py paths not already covered by
tests/agent/test_llm_client.py: build_llm_url/build_embed_url edge cases, the
LLMClient.build_payload wrapper, the non-streaming LLMClient.call() path, and the
request_with_retry exception-propagation branch (stat_retries increment on exhaustion).

These tests exist to lock current behavior before a refactoring pass on
scripts/shared/llm_client.py (see prompts/04_refactor.md). They assert observed
behavior, not intended/ideal behavior.
"""

from __future__ import annotations

import httpx
import pytest
import respx
from shared.llm_client import LLMClient, build_embed_url, build_llm_url

# ── build_llm_url / build_embed_url ───────────────────────────────────────────


class TestBuildLlmUrl:
    def test_empty_base_returns_empty(self) -> None:
        assert build_llm_url("") == ""

    def test_appends_chat_completions_path(self) -> None:
        assert build_llm_url("http://llm:8000") == "http://llm:8000/v1/chat/completions"

    def test_strips_trailing_slash_before_append(self) -> None:
        assert (
            build_llm_url("http://llm:8000/") == "http://llm:8000/v1/chat/completions"
        )


class TestBuildEmbedUrl:
    def test_empty_base_returns_empty(self) -> None:
        assert build_embed_url("") == ""

    def test_appends_embedding_path(self) -> None:
        assert build_embed_url("http://llm:8000") == "http://llm:8000/embedding"

    def test_strips_trailing_slash_before_append(self) -> None:
        assert build_embed_url("http://llm:8000/") == "http://llm:8000/embedding"


# ── LLMClient.build_payload ────────────────────────────────────────────────────


class TestLLMClientBuildPayload:
    def _client(self) -> LLMClient:
        return LLMClient(
            http=httpx.AsyncClient(),
            max_retries=1,
            retry_base_delay=0.0,
            temperature=0.3,
            max_tokens=256,
        )

    def test_build_payload_without_stream(self) -> None:
        client = self._client()
        payload = client.build_payload([{"role": "user", "content": "hi"}], [])
        assert payload["messages"] == [{"role": "user", "content": "hi"}]
        assert payload["tools"] == []
        assert payload["temperature"] == 0.3
        assert payload["max_tokens"] == 256
        assert "stream" not in payload

    def test_build_payload_with_stream_true(self) -> None:
        client = self._client()
        payload = client.build_payload(
            [{"role": "user", "content": "hi"}], [], stream=True
        )
        assert payload["stream"] is True


# ── LLMClient.call (non-streaming) ─────────────────────────────────────────────


class TestLLMClientCall:
    @pytest.mark.asyncio
    async def test_call_returns_parsed_response(self) -> None:
        http = httpx.AsyncClient()
        client = LLMClient(
            http=http,
            max_retries=1,
            retry_base_delay=0.0,
            temperature=0.2,
            max_tokens=128,
        )
        body = {
            "choices": [
                {
                    "message": {"role": "assistant", "content": "hello"},
                    "finish_reason": "stop",
                }
            ]
        }
        with respx.mock:
            respx.post("http://llm/v1/chat").mock(
                return_value=httpx.Response(200, json=body)
            )
            result = await client.call(
                "http://llm/v1/chat", [{"role": "user", "content": "hi"}], []
            )
        assert result.message.get("content") == "hello"
        assert result.finish_reason == "stop"


# ── request_with_retry exception-propagation branch ───────────────────────────


class TestLLMClientRequestWithRetryExhaustion:
    @pytest.mark.asyncio
    async def test_stat_retries_incremented_and_exception_reraised_on_exhaustion(
        self,
    ) -> None:
        http = httpx.AsyncClient()
        client = LLMClient(
            http=http,
            max_retries=1,
            retry_base_delay=0.0,
            temperature=0.2,
            max_tokens=128,
        )
        assert client.stat_retries == 0
        with respx.mock:
            respx.post("http://llm/v1/chat").mock(
                return_value=httpx.Response(429, content=b"rate limited")
            )
            with pytest.raises(httpx.HTTPStatusError):
                await client.request_with_retry("http://llm/v1/chat", {"messages": []})
        assert client.stat_retries == 1
