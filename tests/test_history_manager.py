"""
tests/test_history_manager.py
Behavior-lock tests for HistoryManager.

httpx.AsyncClient is mocked so no real HTTP calls are made.
"""

from __future__ import annotations

from collections.abc import Callable
from unittest.mock import AsyncMock, MagicMock

import httpx
import orjson
import pytest
from agent.history import HistoryManager
from rag.types import LLMMessage

# ── Fixtures ──────────────────────────────────────────────────────────────────


def _make_manager(
    *,
    char_limit: int = 1000,
    compress_turns: int = 2,
    on_compress: Callable[[int], None] | None = None,
    http: httpx.AsyncClient | None = None,
    protect_turns: int = 0,
    token_limit: int = 0,
) -> HistoryManager:
    return HistoryManager(
        http=http or AsyncMock(spec=httpx.AsyncClient),
        llm_url="http://localhost:8002/v1/chat/completions",
        char_limit=char_limit,
        compress_turns=compress_turns,
        compress_temperature=0.1,
        compress_max_tokens=200,
        on_compress=on_compress,
        protect_turns=protect_turns,
        token_limit=token_limit,
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
        assert chars == len(orjson.dumps(tc))

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


# ── compress_turns public property ────────────────────────────────────────────


class TestCompressTurnsProperty:
    def test_compress_turns_property_matches_init(self) -> None:
        mgr = _make_manager(compress_turns=3)
        assert mgr.compress_turns == 3

    def test_compress_turns_property_is_readable(self) -> None:
        mgr = _make_manager(compress_turns=2)
        # Ensure the property is accessible (not AttributeError)
        val = mgr.compress_turns
        assert isinstance(val, int)


# ── protect_turns — recent turns are excluded from compression ────────────────


class TestProtectTurns:
    @pytest.mark.asyncio
    async def test_protected_turns_not_compressed(self) -> None:
        """With protect_turns=2, the most-recent 2 turn pairs must survive compression."""
        mock_http = AsyncMock(spec=httpx.AsyncClient)
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "choices": [{"message": {"content": "Summary."}}]
        }
        mock_resp.raise_for_status = MagicMock()
        mock_http.post.return_value = mock_resp

        # 6 turn messages total; compress_turns=2 wants to compress 4 messages,
        # but protect_turns=2 protects the last 4 messages.
        # Result: not enough messages to compress → original history returned.
        mgr = _make_manager(
            char_limit=1, compress_turns=2, http=mock_http, protect_turns=2
        )
        h = _history(
            ("user", "q1"),
            ("assistant", "a1"),
            ("user", "q2"),
            ("assistant", "a2"),
            ("user", "q3"),
            ("assistant", "a3"),
        )
        result = await mgr.compress(h)
        # When protect_turns=2 and compress_turns=2, need at least 8 turn messages;
        # with only 6, _select_turns_to_compress returns None → original returned
        assert result == h

    @pytest.mark.asyncio
    async def test_enough_turns_allows_compression_with_protection(self) -> None:
        """With protect_turns=1 and compress_turns=2, and 7 turn pairs, compression proceeds."""
        mock_http = AsyncMock(spec=httpx.AsyncClient)
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "choices": [{"message": {"content": "Summary."}}]
        }
        mock_resp.raise_for_status = MagicMock()
        mock_http.post.return_value = mock_resp

        # 10 turn messages; compress_turns=2 (4 msgs); protect_turns=1 (2 msgs)
        # Needs at least 6 turn messages → 10 >= 6 → compression proceeds
        mgr = _make_manager(
            char_limit=1, compress_turns=2, http=mock_http, protect_turns=1
        )
        pairs = [("user", "x" * 20), ("assistant", "x" * 20)] * 5
        h = _history(*pairs)
        result = await mgr.compress(h)
        # Summary message should appear; history should be shorter
        roles = [m["role"] for m in result]
        assert "system" in roles
        assert len(result) < len(h)


# ── _classify() ───────────────────────────────────────────────────────────────


class TestClassify:
    def test_tool_role_is_temporary(self) -> None:
        msg: LLMMessage = {"role": "tool", "content": "result"}
        assert HistoryManager._classify(msg) == "temporary"

    def test_system_role_is_factual(self) -> None:
        msg: LLMMessage = {"role": "system", "content": "You are helpful."}
        assert HistoryManager._classify(msg) == "factual"

    def test_assistant_with_tool_calls_is_temporary_reasoning(self) -> None:
        msg: LLMMessage = {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": "x",
                    "type": "function",
                    "function": {"name": "f", "arguments": "{}"},
                }
            ],
        }
        assert HistoryManager._classify(msg) == "temporary_reasoning"

    def test_assistant_without_tool_calls_is_history(self) -> None:
        msg: LLMMessage = {"role": "assistant", "content": "I can help with that."}
        assert HistoryManager._classify(msg) == "history"

    def test_user_role_is_history(self) -> None:
        msg: LLMMessage = {"role": "user", "content": "What is Python?"}
        assert HistoryManager._classify(msg) == "history"


# ── count_tokens() ────────────────────────────────────────────────────────────


class TestCountTokens:
    def test_uses_last_input_tokens_when_provided(self) -> None:
        mgr = _make_manager()
        h = _history(("user", "x" * 100))
        # last_input_tokens takes priority over chars // 4
        assert mgr.count_tokens(h, last_input_tokens=42) == 42

    def test_falls_back_to_chars_div_4(self) -> None:
        mgr = _make_manager()
        h = _history(("user", "x" * 400))
        # chars = 400, estimate = 400 // 4 = 100
        assert mgr.count_tokens(h, last_input_tokens=None) == 100

    def test_empty_history_returns_zero(self) -> None:
        mgr = _make_manager()
        assert mgr.count_tokens([], last_input_tokens=None) == 0


# ── compress() — token_limit trigger ─────────────────────────────────────────


class TestCompressTokenLimit:
    def _over_token_history(self) -> list[LLMMessage]:
        # Each message: 400 chars → ~100 tokens. 5 pairs = 10 msgs × 100 = ~1000 tokens.
        pairs = [(r, "x" * 400) for r, _ in [("user", ""), ("assistant", "")] * 5]
        return _history(*pairs)

    def _mock_http(self) -> AsyncMock:
        mock_http = AsyncMock(spec=httpx.AsyncClient)
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "choices": [{"message": {"content": "Summary."}}]
        }
        mock_resp.raise_for_status = MagicMock()
        mock_http.post.return_value = mock_resp
        return mock_http

    @pytest.mark.asyncio
    async def test_token_limit_triggers_compression(self) -> None:
        # token_limit=10; 10 msgs × 100 tokens each >> 10 → should compress
        mgr = _make_manager(
            char_limit=0, compress_turns=2, http=self._mock_http(), token_limit=10
        )
        h = self._over_token_history()
        result = await mgr.compress(h)
        roles = [m["role"] for m in result]
        assert "system" in roles
        assert len(result) < len(h)

    @pytest.mark.asyncio
    async def test_token_limit_zero_does_not_trigger(self) -> None:
        # token_limit=0 (disabled); char_limit large → no compression
        mgr = _make_manager(
            char_limit=999999, compress_turns=2, http=self._mock_http(), token_limit=0
        )
        h = self._over_token_history()
        result = await mgr.compress(h)
        assert result == h

    @pytest.mark.asyncio
    async def test_char_only_over_limit_triggers_compression(self) -> None:
        # char_limit=1 (over), token_limit=0 (disabled) → char trigger fires
        mgr = _make_manager(
            char_limit=1, compress_turns=2, http=self._mock_http(), token_limit=0
        )
        h = self._over_token_history()
        result = await mgr.compress(h)
        roles = [m["role"] for m in result]
        assert "system" in roles

    @pytest.mark.asyncio
    async def test_token_only_over_limit_triggers_compression(self) -> None:
        # char_limit=0 (disabled), token_limit=10 → token trigger fires
        mgr = _make_manager(
            char_limit=0, compress_turns=2, http=self._mock_http(), token_limit=10
        )
        h = self._over_token_history()
        result = await mgr.compress(h)
        roles = [m["role"] for m in result]
        assert "system" in roles


# ── split is None warning log ─────────────────────────────────────────────────


class TestCompressSkippedWarning:
    @pytest.mark.asyncio
    async def test_warns_when_not_enough_turns_but_over_limit(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """When _select_turns_to_compress returns None and chars > limit, a warning is logged."""
        import logging

        # char_limit=1 ensures we're over the limit
        # compress_turns=2, protect_turns=3 → needs (2+3)*2=10 turn msgs; only 4 available
        mgr = _make_manager(char_limit=1, compress_turns=2, protect_turns=3)
        h = _history(
            ("user", "question 1"),
            ("assistant", "answer 1"),
            ("user", "question 2"),
            ("assistant", "answer 2"),
        )
        with caplog.at_level(logging.WARNING, logger="history_manager"):
            result = await mgr.compress(h)
        # History returned unchanged
        assert result == h
        # Warning logged
        assert any("compression skipped" in r.message.lower() for r in caplog.records)


# ── apply_config / force_compress ────────────────────────────────────────────


class TestApplyConfig:
    def test_apply_config_updates_char_limit(self) -> None:
        mgr = _make_manager(char_limit=1000)
        mgr.apply_config(char_limit=500)
        assert mgr._char_limit == 500

    def test_apply_config_updates_compress_turns(self) -> None:
        mgr = _make_manager(compress_turns=2)
        mgr.apply_config(compress_turns=4)
        assert mgr._compress_turns == 4

    def test_apply_config_updates_token_limit(self) -> None:
        mgr = _make_manager(token_limit=0)
        mgr.apply_config(token_limit=8000)
        assert mgr._token_limit == 8000

    def test_apply_config_updates_tokenize_url(self) -> None:
        mgr = _make_manager()
        mgr.apply_config(tokenize_url="http://localhost/tokenize")
        assert mgr._tokenize_url == "http://localhost/tokenize"

    def test_apply_config_none_args_are_no_op(self) -> None:
        mgr = _make_manager(char_limit=1000, compress_turns=2)
        mgr.apply_config()
        assert mgr._char_limit == 1000
        assert mgr._compress_turns == 2


class TestForceCompress:
    def _mock_http(self) -> httpx.AsyncClient:
        mock = AsyncMock(spec=httpx.AsyncClient)
        resp = MagicMock()
        resp.raise_for_status = MagicMock()
        resp.text = "compressed summary"
        mock.post = AsyncMock(return_value=resp)
        return mock

    @pytest.mark.asyncio
    async def test_force_compress_proceeds_regardless_of_limit(self) -> None:
        # char_limit=99999 normally never triggers compression
        mgr = _make_manager(char_limit=99999, compress_turns=2, http=self._mock_http())
        h = _history(
            ("user", "q1"),
            ("assistant", "a1"),
            ("user", "q2"),
            ("assistant", "a2"),
            ("user", "q3"),
            ("assistant", "a3"),
        )
        result = await mgr.force_compress(h)
        # Should have compressed (fewer messages)
        assert len(result) < len(h)

    @pytest.mark.asyncio
    async def test_force_compress_restores_original_limits(self) -> None:
        mgr = _make_manager(char_limit=5000, token_limit=1000, http=self._mock_http())
        h = _history(
            ("user", "q1"),
            ("assistant", "a1"),
            ("user", "q2"),
            ("assistant", "a2"),
            ("user", "q3"),
            ("assistant", "a3"),
        )
        await mgr.force_compress(h)
        # Limits must be restored after force_compress
        assert mgr._char_limit == 5000
        assert mgr._token_limit == 1000
