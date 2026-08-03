from unittest.mock import AsyncMock, MagicMock

import pytest

from scripts.agent.history import (
    HistoryManager,
)


@pytest.fixture
def mock_http():
    return MagicMock()


@pytest.fixture
def history_manager(mock_http):
    # char_limit=100, compress_turns=1, compress_temperature=0.0, compress_max_tokens=10, tokenize_url=""
    return HistoryManager(
        http=mock_http,
        llm_url="http://localhost:11434/api/chat",
        char_limit=100,
        compress_turns=1,
        compress_temperature=0.0,
        compress_max_tokens=10,
        protect_turns=1,  # n_protect = 2
    )


@pytest.mark.asyncio
async def test_compress_returns_error_on_none_and_under_limit(
    history_manager, mock_http
):
    # Setup: under char limit, but over token limit, and enough turns to compress
    # n_protect = 2, n_compress = 2. Need len(turn_msgs) > 4.
    history = []
    for i in range(5):
        history.append({"role": "user", "content": f"msg {i}"})
        history.append({"role": "assistant", "content": f"resp {i}"})

    history_manager._call_compress_llm = AsyncMock(return_value=None)

    # Ensure we are under char limit but over token limit
    history_manager._char_limit = 1000
    history_manager._token_limit = 1

    result_history, result = await history_manager.compress(history)

    assert result.error == "compression returned None"
    assert result_history == history
    assert result.compressed_count == 0


@pytest.mark.asyncio
async def test_compress_returns_fallback_on_none_and_over_limit(
    history_manager, mock_http
):
    # Setup: over limit, but enough turns to compress
    history = []
    for i in range(5):
        history.append({"role": "user", "content": f"msg {i} " * 20})  # make it long
        history.append({"role": "assistant", "content": f"resp {i} " * 20})

    history_manager._call_compress_llm = AsyncMock(return_value=None)

    # Ensure we are over char limit
    history_manager._char_limit = 10

    result_history, result = await history_manager.compress(history)

    assert result.is_fallback is True
    assert len(result_history) < len(history)
