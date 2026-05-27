"""
tests/test_history_manager.py
Behavior-lock tests for HistoryManager.

httpx.AsyncClient is mocked so no real HTTP calls are made.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
from history_manager import HistoryManager
from rag_types import LLMMessage

# ── Fixtures ──────────────────────────────────────────────────────────────────


def _make_manager(
    *,
    char_limit: int = 1000,
    compress_turns: int = 2,
    on_compress: Callable[[int], None] | None = None,
    http: httpx.AsyncClient | None = None,
) -> HistoryManager:
    return HistoryManager(
        http=http or AsyncMock(spec=httpx.AsyncClient),
        chat_url="http://localhost:8002/v1/chat/completions",
        char_limit=char_limit,
        compress_turns=compress_turns,
        compress_temperature=0.1,
        compress_max_tokens=200,
        on_compress=on_compress,
    )


def _history(*pairs: tuple[str, str]) -> list[LLMMessage]:
    """Build a message list from (role, content) pairs."""
    return [{"role": r, "content": c} for r, c in pairs]


# ── count_chars() ─────────────────────────────────────────────────────────────


class TestCountChars:
    def test_counts_content_length(self) -> None:
        mgr = _make_manager()
        h = _history(("user", "hello"), ("assistant", "world"))
        assert mgr.count_chars(h) == len("hello") + len("world")

    def test_includes_tool_calls_length(self) -> None:
        mgr = _make_manager()
        tc = {
            "id": "x",
            "type": "function",
            "function": {"name": "f", "arguments": "{}"},
        }
        h: list[LLMMessage] = [
            {"role": "assistant", "content": None, "tool_calls": [tc]}
        ]
        chars = mgr.count_chars(h)
        assert chars == len(json.dumps(tc))

    def test_empty_history_returns_zero(self) -> None:
        mgr = _make_manager()
        assert mgr.count_chars([]) == 0

    def test_none_content_counts_as_zero(self) -> None:
        mgr = _make_manager()
        h: list[LLMMessage] = [{"role": "assistant", "content": None}]
        assert mgr.count_chars(h) == 0


# ── compress() — no-op paths ─────────────────────────────────────────────────


class TestCompressNoOp:
    @pytest.mark.asyncio
    async def test_returns_history_unchanged_under_limit(self) -> None:
        mgr = _make_manager(char_limit=10000)
        h = _history(("user", "hi"), ("assistant", "hello"))
        result = await mgr.compress(h)
        assert result == h

    @pytest.mark.asyncio
    async def test_returns_history_unchanged_when_too_few_turns(self) -> None:
        # char_limit=1 forces compression attempt, but only 1 turn (2 msgs)
        # compress_turns=2 → needs 4 turn messages to compress
        mgr = _make_manager(char_limit=1, compress_turns=2)
        h = _history(("user", "q"), ("assistant", "a"))
        result = await mgr.compress(h)
        assert result == h


# ── compress() — LLM call paths ──────────────────────────────────────────────


class TestCompressWithLLM:
    def _over_limit_history(self, limit: int = 10) -> list[LLMMessage]:
        # 5 turn pairs (10 messages), all well above any small char_limit
        pairs = [(r, "x" * 20) for r, _ in [("user", ""), ("assistant", "")] * 5]
        return _history(*pairs)

    @pytest.mark.asyncio
    async def test_calls_compress_llm_when_over_limit(self) -> None:
        mock_http = AsyncMock(spec=httpx.AsyncClient)
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "choices": [{"message": {"content": "Summary."}}]
        }
        mock_resp.raise_for_status = MagicMock()
        mock_http.post.return_value = mock_resp

        mgr = _make_manager(char_limit=1, compress_turns=2, http=mock_http)
        h = self._over_limit_history()
        result = await mgr.compress(h)

        mock_http.post.assert_called_once()
        # Result should contain a summary message
        roles = [m["role"] for m in result]
        assert "system" in roles

    @pytest.mark.asyncio
    async def test_increments_stat_compress_count(self) -> None:
        mock_http = AsyncMock(spec=httpx.AsyncClient)
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "choices": [{"message": {"content": "Summary."}}]
        }
        mock_resp.raise_for_status = MagicMock()
        mock_http.post.return_value = mock_resp

        mgr = _make_manager(char_limit=1, compress_turns=2, http=mock_http)
        h = self._over_limit_history()
        await mgr.compress(h)
        assert mgr.stat_compress_count == 1

    @pytest.mark.asyncio
    async def test_calls_on_compress_callback(self) -> None:
        mock_http = AsyncMock(spec=httpx.AsyncClient)
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "choices": [{"message": {"content": "Summary."}}]
        }
        mock_resp.raise_for_status = MagicMock()
        mock_http.post.return_value = mock_resp

        callback = MagicMock()
        mgr = _make_manager(
            char_limit=1, compress_turns=2, http=mock_http, on_compress=callback
        )
        h = self._over_limit_history()
        await mgr.compress(h)
        callback.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_original_history_on_llm_failure(self) -> None:
        mock_http = AsyncMock(spec=httpx.AsyncClient)
        mock_http.post.side_effect = httpx.RequestError("connection refused")

        mgr = _make_manager(char_limit=1, compress_turns=2, http=mock_http)
        h = self._over_limit_history()
        result = await mgr.compress(h)
        # Fallback: original history returned unchanged
        assert result == h

    @pytest.mark.asyncio
    async def test_returns_original_history_on_empty_llm_response(self) -> None:
        mock_http = AsyncMock(spec=httpx.AsyncClient)
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"choices": []}
        mock_resp.raise_for_status = MagicMock()
        mock_http.post.return_value = mock_resp

        mgr = _make_manager(char_limit=1, compress_turns=2, http=mock_http)
        h = self._over_limit_history()
        result = await mgr.compress(h)
        assert result == h

    @pytest.mark.asyncio
    async def test_preserves_system_messages(self) -> None:
        mock_http = AsyncMock(spec=httpx.AsyncClient)
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "choices": [{"message": {"content": "Summary."}}]
        }
        mock_resp.raise_for_status = MagicMock()
        mock_http.post.return_value = mock_resp

        mgr = _make_manager(char_limit=1, compress_turns=2, http=mock_http)
        system_msg: LLMMessage = {"role": "system", "content": "You are helpful."}
        h = [system_msg] + self._over_limit_history()
        result = await mgr.compress(h)
        assert result[0] == system_msg
