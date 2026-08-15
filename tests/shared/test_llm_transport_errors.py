#!/usr/bin/env python3
"""Characterization tests for scripts/shared/llm_transport_errors.py.

Locks the current retryable/kind classification behavior of
LlmTransportErrorHandler before refactoring. Do not change expected
kind/retryable/phase values here without explicit approval — these
values feed retry decisions elsewhere in the codebase.
"""

import httpx
import pytest
from shared.llm_exceptions import LLMTransportError
from shared.llm_transport_errors import LlmTransportErrorHandler

# ── raise_http_status_error ──────────────────────────────────────────────────


class TestRaiseHttpStatusError:
    @pytest.mark.parametrize("status_code", [429, 503])
    def test_retryable_status_codes_raise_retryable_kind(
        self, status_code: int
    ) -> None:
        req = httpx.Request("POST", "http://example.com")
        resp = httpx.Response(status_code, request=req)
        original = httpx.HTTPStatusError("boom", request=req, response=resp)
        with pytest.raises(LLMTransportError) as exc_info:
            LlmTransportErrorHandler.raise_http_status_error(
                original, "http://example.com"
            )
        e = exc_info.value
        assert e.kind == "HTTP_STATUS_RETRYABLE"
        assert e.phase == "pre_stream"
        assert e.url == "http://example.com"
        assert e.status_code == status_code
        assert e.retryable is True
        assert e.__cause__ is original

    @pytest.mark.parametrize("status_code", [400, 404, 500, 502])
    def test_non_retryable_status_codes_raise_fatal_kind(
        self, status_code: int
    ) -> None:
        req = httpx.Request("POST", "http://example.com")
        resp = httpx.Response(status_code, request=req)
        original = httpx.HTTPStatusError("boom", request=req, response=resp)
        with pytest.raises(LLMTransportError) as exc_info:
            LlmTransportErrorHandler.raise_http_status_error(
                original, "http://example.com"
            )
        e = exc_info.value
        assert e.kind == "HTTP_STATUS_FATAL"
        assert e.phase == "pre_stream"
        assert e.status_code == status_code
        assert e.retryable is False
        assert e.__cause__ is original


# ── translate_stream_error ───────────────────────────────────────────────────


class TestTranslateStreamError:
    def test_connect_error_is_retryable_pre_stream(self) -> None:
        original = httpx.ConnectError("refused")
        e = LlmTransportErrorHandler.translate_stream_error(
            original, "http://example.com"
        )
        assert e.kind == "CONNECT_ERROR"
        assert e.phase == "pre_stream"
        assert e.url == "http://example.com"
        assert e.retryable is True
        assert e.detail == str(original)

    def test_read_timeout_is_retryable_in_stream(self) -> None:
        original = httpx.ReadTimeout("timeout")
        e = LlmTransportErrorHandler.translate_stream_error(
            original, "http://example.com"
        )
        assert e.kind == "READ_TIMEOUT"
        assert e.phase == "in_stream"
        assert e.url == "http://example.com"
        assert e.retryable is True
        assert e.detail == str(original)

    def test_unknown_exception_is_not_retryable_in_stream(self) -> None:
        original = ValueError("weird")
        e = LlmTransportErrorHandler.translate_stream_error(
            original, "http://example.com"
        )
        assert e.kind == "UNKNOWN_STREAM_ERROR"
        assert e.phase == "in_stream"
        assert e.url == "http://example.com"
        assert e.retryable is False
        assert e.detail == str(original)
