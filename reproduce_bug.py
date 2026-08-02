import asyncio
from unittest.mock import AsyncMock, MagicMock

import httpx
import orjson
from agent.history import HistoryManager


async def main():
    mock_http = AsyncMock(spec=httpx.AsyncClient)
    # Simulate empty response
    mock_resp = MagicMock()
    mock_resp.content = orjson.dumps({"choices": []})
    mock_resp.raise_for_status = MagicMock()
    mock_http.post.return_value = mock_resp

    # Case: Under char_limit, but over token_limit
    mgr = HistoryManager(
        http=mock_http,
        llm_url="http://localhost:8002/v1/chat/completions",
        char_limit=1000,
        compress_turns=1,
        compress_temperature=0.1,
        compress_max_tokens=200,
        token_limit=5,
    )

    # Small history
    h = [{"role": "user", "content": "hi"}, {"role": "assistant", "content": "hello"}]

    print(f"Char limit: {mgr._char_limit}")
    print(f"Count chars: {mgr.count_chars(h)}")
    print(f"Over char limit: {mgr._is_over_char_limit(h)}")

    result, cr = await mgr.compress(h)
    print(f"Result: {result}")
    print(f"CR Error: {cr.error}")
    print(f"CR Is Fallback: {cr.is_fallback}")


if __name__ == "__main__":
    asyncio.run(main())
