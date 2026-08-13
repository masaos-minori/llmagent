"""tests/shared/test_llm_retry.py

Characterization tests for scripts/shared/llm_retry.py — locks current retry/backoff
behavior (transient vs non-transient error classification, exponential delay, exhaustion,
logging) before a refactoring pass on scripts/shared/llm_retry.py (see prompts/04_refactor.md).
These tests assert observed behavior, not intended/ideal behavior.
"""

from __future__ import annotations

import logging
from typing import Any
from unittest.mock import patch

import httpx
import pytest
from shared.llm_retry import LlmRetryHandler, _backoff_delay, _is_transient_http_error


class _FakeClient:
    """Minimal async client stand-in exposing only the `post` method LlmRetryHandler uses."""

    def __init__(self, responses: list[httpx.Response | Exception]) -> None:
        self._responses = list(responses)
        self.call_count = 0

    async def post(self, url: str, json: dict[str, Any]) -> httpx.Response:
        self.call_count += 1
        item = self._responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


def _response(status_code: int, url: str = "http://llm/v1/chat") -> httpx.Response:
    req = httpx.Request("POST", url)
    return httpx.Response(status_code, request=req, json={"ok": True})


class TestIsTransientHttpError:
    @pytest.mark.parametrize("status_code", [429, 503])
    def test_transient_codes_return_true(self, status_code: int) -> None:
        try:
            _response(status_code).raise_for_status()
        except httpx.HTTPStatusError as e:
            assert _is_transient_http_error(e) is True
        else:
            pytest.fail("expected HTTPStatusError")

    @pytest.mark.parametrize("status_code", [400, 401, 404, 500, 502])
    def test_non_transient_codes_return_false(self, status_code: int) -> None:
        try:
            _response(status_code).raise_for_status()
        except httpx.HTTPStatusError as e:
            assert _is_transient_http_error(e) is False
        else:
            pytest.fail("expected HTTPStatusError")


class TestBackoffDelay:
    @pytest.mark.parametrize(
        ("base", "attempt", "expected"),
        [
            (1.0, 0, 1.0),
            (1.0, 1, 2.0),
            (1.0, 2, 4.0),
            (2.5, 3, 20.0),
        ],
    )
    def test_exponential_growth(
        self, base: float, attempt: int, expected: float
    ) -> None:
        assert _backoff_delay(base, attempt) == expected


class TestRequestWithRetrySuccess:
    @pytest.mark.asyncio
    async def test_succeeds_on_first_attempt_no_sleep(self) -> None:
        client = _FakeClient([_response(200)])
        with patch("shared.llm_retry.asyncio.sleep") as mock_sleep:
            resp = await LlmRetryHandler.request_with_retry(
                client,  # type: ignore[arg-type]  # fake client — mirrors the httpx.AsyncClient.post surface used
                "http://llm/v1/chat",
                {"messages": []},
                max_retries=3,
                retry_base_delay=1.0,
            )
        assert resp.status_code == 200
        assert client.call_count == 1
        mock_sleep.assert_not_called()


class TestRequestWithRetryTransientRecovery:
    @pytest.mark.asyncio
    async def test_retries_on_503_then_succeeds(self) -> None:
        client = _FakeClient([_response(503), _response(503), _response(200)])
        with patch("shared.llm_retry.asyncio.sleep") as mock_sleep:
            resp = await LlmRetryHandler.request_with_retry(
                client,  # type: ignore[arg-type]  # fake client — mirrors the httpx.AsyncClient.post surface used
                "http://llm/v1/chat",
                {"messages": []},
                max_retries=5,
                retry_base_delay=2.0,
            )
        assert resp.status_code == 200
        assert client.call_count == 3
        # exponential backoff: base * 2**attempt, for attempt 0 then attempt 1
        assert [call.args[0] for call in mock_sleep.call_args_list] == [2.0, 4.0]

    @pytest.mark.asyncio
    async def test_retries_on_429_then_succeeds(self) -> None:
        client = _FakeClient([_response(429), _response(200)])
        with patch("shared.llm_retry.asyncio.sleep") as mock_sleep:
            resp = await LlmRetryHandler.request_with_retry(
                client,  # type: ignore[arg-type]  # fake client — mirrors the httpx.AsyncClient.post surface used
                "http://llm/v1/chat",
                {"messages": []},
                max_retries=3,
                retry_base_delay=0.5,
            )
        assert resp.status_code == 200
        assert client.call_count == 2
        mock_sleep.assert_called_once_with(0.5)

    @pytest.mark.asyncio
    async def test_retries_on_connect_error_then_succeeds(self) -> None:
        client = _FakeClient([httpx.ConnectError("refused"), _response(200)])
        with patch("shared.llm_retry.asyncio.sleep") as mock_sleep:
            resp = await LlmRetryHandler.request_with_retry(
                client,  # type: ignore[arg-type]  # fake client — mirrors the httpx.AsyncClient.post surface used
                "http://llm/v1/chat",
                {"messages": []},
                max_retries=3,
                retry_base_delay=0.25,
            )
        assert resp.status_code == 200
        assert client.call_count == 2
        mock_sleep.assert_called_once_with(0.25)


class TestRequestWithRetryNonTransient:
    @pytest.mark.asyncio
    async def test_non_transient_http_status_raises_immediately(self) -> None:
        client = _FakeClient([_response(400)])
        with patch("shared.llm_retry.asyncio.sleep") as mock_sleep:
            with pytest.raises(httpx.HTTPStatusError) as exc_info:
                await LlmRetryHandler.request_with_retry(
                    client,  # type: ignore[arg-type]  # fake client — mirrors the httpx.AsyncClient.post surface used
                    "http://llm/v1/chat",
                    {"messages": []},
                    max_retries=5,
                    retry_base_delay=1.0,
                )
        assert exc_info.value.response.status_code == 400
        assert client.call_count == 1
        mock_sleep.assert_not_called()


class TestRequestWithRetryExhaustion:
    @pytest.mark.asyncio
    async def test_exhausts_retries_on_503_and_raises_last_http_status_error(
        self,
    ) -> None:
        client = _FakeClient([_response(503), _response(503)])
        with patch("shared.llm_retry.asyncio.sleep") as mock_sleep:
            with pytest.raises(httpx.HTTPStatusError) as exc_info:
                await LlmRetryHandler.request_with_retry(
                    client,  # type: ignore[arg-type]  # fake client — mirrors the httpx.AsyncClient.post surface used
                    "http://llm/v1/chat",
                    {"messages": []},
                    max_retries=2,
                    retry_base_delay=1.0,
                )
        assert exc_info.value.response.status_code == 503
        assert client.call_count == 2
        mock_sleep.assert_called_once_with(1.0)

    @pytest.mark.asyncio
    async def test_exhausts_retries_on_connect_error_and_raises_last_request_error(
        self,
    ) -> None:
        errors: list[httpx.Response | Exception] = [
            httpx.ConnectError("refused"),
            httpx.ConnectError("refused again"),
        ]
        client = _FakeClient(errors)
        with patch("shared.llm_retry.asyncio.sleep"):
            with pytest.raises(httpx.ConnectError, match="refused again"):
                await LlmRetryHandler.request_with_retry(
                    client,  # type: ignore[arg-type]  # fake client — mirrors the httpx.AsyncClient.post surface used
                    "http://llm/v1/chat",
                    {"messages": []},
                    max_retries=2,
                    retry_base_delay=1.0,
                )
        assert client.call_count == 2

    @pytest.mark.asyncio
    async def test_max_retries_zero_raises_runtime_error(self) -> None:
        client = _FakeClient([])
        with patch("shared.llm_retry.asyncio.sleep") as mock_sleep:
            with pytest.raises(RuntimeError, match="max_retries must be >= 1"):
                await LlmRetryHandler.request_with_retry(
                    client,  # type: ignore[arg-type]  # fake client — mirrors the httpx.AsyncClient.post surface used
                    "http://llm/v1/chat",
                    {"messages": []},
                    max_retries=0,
                    retry_base_delay=1.0,
                )
        assert client.call_count == 0
        mock_sleep.assert_not_called()


class TestRequestWithRetryLogging:
    @pytest.mark.asyncio
    async def test_logs_warning_on_each_retry_and_error_on_exhaustion(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        client = _FakeClient([_response(503), _response(503)])
        with caplog.at_level(logging.WARNING, logger="shared.llm_retry"):
            with patch("shared.llm_retry.asyncio.sleep"):
                with pytest.raises(httpx.HTTPStatusError):
                    await LlmRetryHandler.request_with_retry(
                        client,  # type: ignore[arg-type]  # fake client — mirrors the httpx.AsyncClient.post surface used
                        "http://llm/v1/chat",
                        {"messages": []},
                        max_retries=2,
                        retry_base_delay=1.0,
                    )
        warning_msgs = [
            r.message for r in caplog.records if r.levelno == logging.WARNING
        ]
        error_msgs = [r.message for r in caplog.records if r.levelno == logging.ERROR]
        assert any("attempt 1/2" in m for m in warning_msgs)
        assert any("after 2 attempts" in m for m in error_msgs)
