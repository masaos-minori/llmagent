"""
tests/test_regression_history_compress_reload.py
Regression tests: compression result consistency.

Locks down: summary_added=True when LLM succeeds;
is_fallback=True and valid (non-empty) history when LLM fails.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import httpx
import orjson
from agent.history import HistoryManager
from shared.types import LLMMessage


def _make_manager(
    *,
    char_limit: int = 1,
    compress_turns: int = 2,
    http: httpx.AsyncClient | None = None,
) -> HistoryManager:
    return HistoryManager(
        http=http or AsyncMock(spec=httpx.AsyncClient),
        llm_url="http://localhost:8002/v1/chat/completions",
        char_limit=char_limit,
        compress_turns=compress_turns,
        compress_temperature=0.1,
        compress_max_tokens=200,
        protect_turns=0,
    )


def _over_limit_history() -> list[LLMMessage]:
    return [{"role": r, "content": "x" * 20} for r in ("user", "assistant") * 5]


class TestCompressResultOnSuccess:
    async def test_compress_summary_added_true_when_llm_succeeds(self) -> None:
        """compress() returns summary_added=True when LLM provides a summary."""
        mock_http = AsyncMock(spec=httpx.AsyncClient)
        mock_resp = MagicMock()
        mock_resp.content = orjson.dumps(
            {"choices": [{"message": {"content": "Compressed summary."}}]}
        )
        mock_resp.raise_for_status = MagicMock()
        mock_http.post.return_value = mock_resp

        mgr = _make_manager(http=mock_http)
        history = _over_limit_history()
        new_history, result = await mgr.compress(history)

        assert result.summary_added is True
        assert result.is_fallback is False
        assert any(m["role"] == "system" for m in new_history)

    async def test_compress_result_has_nonzero_compressed_count(self) -> None:
        """compress() reports compressed_count > 0 when turns were summarised."""
        mock_http = AsyncMock(spec=httpx.AsyncClient)
        mock_resp = MagicMock()
        mock_resp.content = orjson.dumps(
            {"choices": [{"message": {"content": "Summary."}}]}
        )
        mock_resp.raise_for_status = MagicMock()
        mock_http.post.return_value = mock_resp

        mgr = _make_manager(http=mock_http)
        history = _over_limit_history()
        _, result = await mgr.compress(history)

        assert result.compressed_count > 0


class TestCompressResultOnLlmFailure:
    async def test_fallback_is_flagged_when_llm_raises(self) -> None:
        """compress() sets is_fallback=True when LLM call raises."""
        mock_http = AsyncMock(spec=httpx.AsyncClient)
        mock_http.post.side_effect = httpx.RequestError("connection refused")

        mgr = _make_manager(http=mock_http)
        history = _over_limit_history()
        new_history, result = await mgr.compress(history)

        assert result.is_fallback is True
        assert result.summary_added is False

    async def test_fallback_history_shorter_or_equal(self) -> None:
        """After fallback truncation the returned history is not longer than the original."""
        mock_http = AsyncMock(spec=httpx.AsyncClient)
        mock_http.post.side_effect = httpx.RequestError("connection refused")

        mgr = _make_manager(http=mock_http)
        history = _over_limit_history()
        new_history, result = await mgr.compress(history)

        assert result.is_fallback is True
        assert len(new_history) <= len(history)

    async def test_no_compression_noop_returns_unchanged_history(self) -> None:
        """compress() returns history unchanged and noop CompressResult when under limit."""
        mgr = _make_manager(char_limit=100_000)
        history: list[LLMMessage] = [
            {"role": "user", "content": "hi"},
            {"role": "assistant", "content": "hello"},
        ]
        new_history, result = await mgr.compress(history)

        assert result.compressed_count == 0
        assert result.summary_added is False
        assert result.is_fallback is False
        assert new_history is history
