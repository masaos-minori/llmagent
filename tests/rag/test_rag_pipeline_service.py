"""tests/test_rag_pipeline_service.py
Unit tests for rag/pipeline_service.py — call_rag_service canonical path.
"""

from __future__ import annotations

import httpx
import orjson
import pytest
import respx
from rag.models_data import TwoStageFetchResult
from rag.pipeline_service import call_rag_service

RAG_URL = "http://rag.local"


def _noop_fetch(r: TwoStageFetchResult) -> None:
    pass


# ── Canonical endpoint ────────────────────────────────────────────────────────


class TestCallToolEndpoint:
    @pytest.mark.asyncio
    @respx.mock
    async def test_uses_call_tool_url(self) -> None:
        route = respx.post(f"{RAG_URL}/v1/call_tool").mock(
            return_value=httpx.Response(200, content=orjson.dumps({"result": "ctx"}))
        )
        async with httpx.AsyncClient() as client:
            result, status, _ = await call_rag_service(
                client,
                RAG_URL,
                "query",
                "",
                set_fetch_result=_noop_fetch,
            )
        assert route.called
        assert "/v1/call_tool" in str(route.calls[0].request.url)
        assert result == "ctx"
        assert status == 200

    @pytest.mark.asyncio
    @respx.mock
    async def test_does_not_use_v1_search(self) -> None:
        respx.post(f"{RAG_URL}/v1/call_tool").mock(
            return_value=httpx.Response(200, content=orjson.dumps({"result": "ctx"}))
        )
        async with httpx.AsyncClient() as client:
            result, _, _ = await call_rag_service(
                client,
                RAG_URL,
                "query",
                "",
                set_fetch_result=_noop_fetch,
            )
        assert result == "ctx"

    @pytest.mark.asyncio
    @respx.mock
    async def test_request_body_contains_rag_run_pipeline(self) -> None:
        route = respx.post(f"{RAG_URL}/v1/call_tool").mock(
            return_value=httpx.Response(200, content=orjson.dumps({"result": "ctx"}))
        )
        async with httpx.AsyncClient() as client:
            await call_rag_service(
                client,
                RAG_URL,
                "my query",
                "history",
                set_fetch_result=_noop_fetch,
            )
        body = orjson.loads(route.calls[0].request.content)
        assert body["name"] == "rag_run_pipeline"
        assert body["args"]["query"] == "my query"
        assert "history" in body["args"]["history_context"]

    @pytest.mark.asyncio
    @respx.mock
    async def test_empty_history_context_sends_empty_list(self) -> None:
        route = respx.post(f"{RAG_URL}/v1/call_tool").mock(
            return_value=httpx.Response(200, content=orjson.dumps({"result": ""}))
        )
        async with httpx.AsyncClient() as client:
            await call_rag_service(
                client,
                RAG_URL,
                "q",
                "",
                set_fetch_result=_noop_fetch,
            )
        body = orjson.loads(route.calls[0].request.content)
        assert body["args"]["history_context"] == []


# ── Response parsing ──────────────────────────────────────────────────────────


class TestResponseParsing:
    @pytest.mark.asyncio
    @respx.mock
    async def test_parses_result_field(self) -> None:
        respx.post(f"{RAG_URL}/v1/call_tool").mock(
            return_value=httpx.Response(
                200,
                content=orjson.dumps({"result": "augmented text", "is_error": False}),
            )
        )
        async with httpx.AsyncClient() as client:
            result, status, _ = await call_rag_service(
                client,
                RAG_URL,
                "q",
                "",
                set_fetch_result=_noop_fetch,
            )
        assert result == "augmented text"
        assert status == 200

    @pytest.mark.asyncio
    @respx.mock
    async def test_null_result_returns_empty_string(self) -> None:
        respx.post(f"{RAG_URL}/v1/call_tool").mock(
            return_value=httpx.Response(200, content=orjson.dumps({"result": None}))
        )
        async with httpx.AsyncClient() as client:
            result, status, _ = await call_rag_service(
                client,
                RAG_URL,
                "q",
                "",
                set_fetch_result=_noop_fetch,
            )
        assert result == ""
        assert status == 200

    @pytest.mark.asyncio
    @respx.mock
    async def test_missing_result_returns_empty_string(self) -> None:
        respx.post(f"{RAG_URL}/v1/call_tool").mock(
            return_value=httpx.Response(200, content=orjson.dumps({"is_error": False}))
        )
        async with httpx.AsyncClient() as client:
            result, status, _ = await call_rag_service(
                client,
                RAG_URL,
                "q",
                "",
                set_fetch_result=_noop_fetch,
            )
        assert result == ""

    @pytest.mark.asyncio
    @respx.mock
    async def test_5xx_retries_and_returns_none(self) -> None:
        respx.post(f"{RAG_URL}/v1/call_tool").mock(
            return_value=httpx.Response(503, content=b'{"error": "unavailable"}')
        )
        async with httpx.AsyncClient() as client:
            result, status, _ = await call_rag_service(
                client,
                RAG_URL,
                "q",
                "",
                set_fetch_result=_noop_fetch,
            )
        assert result is None

    @pytest.mark.asyncio
    @respx.mock
    async def test_4xx_returns_none_no_retry(self) -> None:
        route = respx.post(f"{RAG_URL}/v1/call_tool").mock(
            return_value=httpx.Response(400, content=b'{"error": "bad request"}')
        )
        async with httpx.AsyncClient() as client:
            result, status, _ = await call_rag_service(
                client,
                RAG_URL,
                "q",
                "",
                set_fetch_result=_noop_fetch,
            )
        assert result is None
        assert status == 400
        assert route.call_count == 1


# ── Fallback reason callback and status code ───────────────────────────────────


class TestFallbackReasonCallback:
    @pytest.mark.asyncio
    @respx.mock
    async def test_4xx_calls_set_fallback_reason(self) -> None:
        reasons: list[str] = []
        respx.post(f"{RAG_URL}/v1/call_tool").mock(
            return_value=httpx.Response(400, content=b'{"error": "bad request"}')
        )
        async with httpx.AsyncClient() as client:
            result, status, _ = await call_rag_service(
                client,
                RAG_URL,
                "q",
                "",
                set_fetch_result=_noop_fetch,
                set_fallback_reason=reasons.append,
            )
        assert result is None
        assert status == 400
        assert len(reasons) == 1
        assert reasons[0].startswith("http_client_error:")

    @pytest.mark.asyncio
    @respx.mock
    async def test_5xx_exhausted_calls_set_fallback_reason(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from unittest.mock import AsyncMock

        reasons: list[str] = []
        respx.post(f"{RAG_URL}/v1/call_tool").mock(
            return_value=httpx.Response(503, content=b'{"error": "unavailable"}')
        )
        monkeypatch.setattr("asyncio.sleep", AsyncMock())
        async with httpx.AsyncClient() as client:
            result, status, _ = await call_rag_service(
                client,
                RAG_URL,
                "q",
                "",
                set_fetch_result=_noop_fetch,
                set_fallback_reason=reasons.append,
            )
        assert result is None
        assert len(reasons) == 1
        assert reasons[0].startswith("http_max_retries:")

    @pytest.mark.asyncio
    @respx.mock
    async def test_json_parse_error_calls_set_fallback_reason(self) -> None:
        reasons: list[str] = []
        respx.post(f"{RAG_URL}/v1/call_tool").mock(
            return_value=httpx.Response(200, content=b"not-json")
        )
        async with httpx.AsyncClient() as client:
            result, status, _ = await call_rag_service(
                client,
                RAG_URL,
                "q",
                "",
                set_fetch_result=_noop_fetch,
                set_fallback_reason=reasons.append,
            )
        assert result is None
        assert len(reasons) == 1
        assert reasons[0].startswith("http_parse_error:")


class TestReturnedStatusCode:
    @pytest.mark.asyncio
    @respx.mock
    async def test_4xx_returns_status_code(self) -> None:
        respx.post(f"{RAG_URL}/v1/call_tool").mock(
            return_value=httpx.Response(400, content=b'{"error": "bad request"}')
        )
        async with httpx.AsyncClient() as client:
            _, status, _ = await call_rag_service(
                client,
                RAG_URL,
                "q",
                "",
                set_fetch_result=_noop_fetch,
            )
        assert status == 400
