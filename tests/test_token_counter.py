"""
tests/test_token_counter.py
Unit tests for shared/token_counter.py.

httpx.AsyncClient is mocked so no real HTTP calls are made.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import httpx
import orjson
import pytest
from shared import token_counter as tc_module
from shared.token_counter import (
    _estimate_chars,
    _serialise_for_tokenize,
    get_token_count,
)
from shared.types import LLMMessage


def _reset_warned() -> None:
    """Reset module-level warn-once flag between tests."""
    tc_module._warned_unavailable = False


def _history(*pairs: tuple[str, str]) -> list[LLMMessage]:
    return [{"role": r, "content": c} for r, c in pairs]


def _make_http(*, status: int = 200, body: dict | None = None) -> httpx.AsyncClient:
    """Build a mock AsyncClient that returns the given status/body."""
    mock = AsyncMock(spec=httpx.AsyncClient)
    response = MagicMock()
    response.status_code = status
    response.json.return_value = body or {}
    if status >= 400:
        response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "error", request=MagicMock(), response=response
        )
    else:
        response.raise_for_status.return_value = None
    mock.post.return_value = response
    return mock


# ── _estimate_chars ────────────────────────────────────────────────────────────


def test_estimate_chars_empty() -> None:
    assert _estimate_chars([]) == 0


def test_estimate_chars_counts_content() -> None:
    msgs: list[LLMMessage] = [{"role": "user", "content": "hello"}]
    assert _estimate_chars(msgs) == 5


def test_estimate_chars_counts_tool_calls() -> None:
    tc = {"id": "c1", "function": {"name": "f", "arguments": "{}"}}
    msgs: list[LLMMessage] = [
        {"role": "assistant", "content": None, "tool_calls": [tc]}
    ]
    expected = len(orjson.dumps(tc))
    assert _estimate_chars(msgs) == expected


# ── _serialise_for_tokenize ────────────────────────────────────────────────────


def test_serialise_includes_role_prefix() -> None:
    msgs = _history(("user", "hello"))
    result = _serialise_for_tokenize(msgs)
    assert result == "user: hello"


def test_serialise_skips_empty_content() -> None:
    tc = {"id": "c1", "function": {"name": "f", "arguments": "{}"}}
    msgs: list[LLMMessage] = [
        {"role": "assistant", "content": None, "tool_calls": [tc]}
    ]
    result = _serialise_for_tokenize(msgs)
    assert "assistant:" not in result
    assert orjson.dumps(tc).decode() in result


# ── get_token_count — tokenize_url="" (disabled) ───────────────────────────────


@pytest.mark.asyncio
async def test_empty_url_returns_fallback() -> None:
    _reset_warned()
    http = AsyncMock(spec=httpx.AsyncClient)
    msgs = _history(("user", "1234"))  # 4 chars → 1 token
    count, is_exact = await get_token_count(msgs, "", http, timeout=1.0)
    assert count == 1
    assert is_exact is False
    http.post.assert_not_called()


# ── get_token_count — normal response ─────────────────────────────────────────


@pytest.mark.asyncio
async def test_successful_tokenize_n_tokens() -> None:
    _reset_warned()
    http = _make_http(body={"n_tokens": 42, "tokens": list(range(42))})
    msgs = _history(("user", "test"))
    count, is_exact = await get_token_count(msgs, "http://host/tokenize", http)
    assert count == 42
    assert is_exact is True


@pytest.mark.asyncio
async def test_successful_tokenize_tokens_list_fallback() -> None:
    """When n_tokens is absent, len(tokens) is used."""
    _reset_warned()
    http = _make_http(body={"tokens": [1, 2, 3]})
    msgs = _history(("user", "abc"))
    count, is_exact = await get_token_count(msgs, "http://host/tokenize", http)
    assert count == 3
    assert is_exact is True


# ── get_token_count — error handling ─────────────────────────────────────────


@pytest.mark.asyncio
async def test_http_error_falls_back_to_chars4() -> None:
    _reset_warned()
    http = _make_http(status=503)
    msgs = _history(("user", "abcd"))  # 4 chars → 1 token
    count, is_exact = await get_token_count(msgs, "http://host/tokenize", http)
    assert count == 1
    assert is_exact is False


@pytest.mark.asyncio
async def test_timeout_falls_back_to_chars4() -> None:
    _reset_warned()
    http = AsyncMock(spec=httpx.AsyncClient)
    http.post.side_effect = httpx.TimeoutException("timed out")
    msgs = _history(("user", "abcd"))
    count, is_exact = await get_token_count(msgs, "http://host/tokenize", http)
    assert count == 1
    assert is_exact is False


@pytest.mark.asyncio
async def test_n_tokens_zero_falls_back() -> None:
    """n_tokens=0 with empty tokens list should fall back."""
    _reset_warned()
    http = _make_http(body={"n_tokens": 0, "tokens": []})
    msgs = _history(("user", "abcd"))
    count, is_exact = await get_token_count(msgs, "http://host/tokenize", http)
    assert count == 1
    assert is_exact is False


# ── get_token_count — warn-once behaviour ─────────────────────────────────────


@pytest.mark.asyncio
async def test_warn_only_once_on_repeated_failure(
    caplog: pytest.LogCaptureFixture,
) -> None:
    _reset_warned()
    http = AsyncMock(spec=httpx.AsyncClient)
    http.post.side_effect = httpx.ConnectError("refused")
    msgs = _history(("user", "x" * 8))
    import logging

    with caplog.at_level(logging.WARNING, logger="shared.token_counter"):
        await get_token_count(msgs, "http://host/tokenize", http)
        await get_token_count(msgs, "http://host/tokenize", http)
    warnings = [r for r in caplog.records if "unavailable" in r.message]
    assert len(warnings) == 1
