import asyncio
from dataclasses import dataclass
from unittest.mock import AsyncMock

import httpx


@dataclass
class LLMMessage:
    role: str
    content: str | None
    tool_calls: list | None = None


@dataclass
class CompressResult:
    compressed_count: int
    protected_count: int
    summary_added: bool
    is_fallback: bool = False
    error: str | None = None


class HistoryCompressionError(RuntimeError):
    pass


class HistorySelectionPolicy:
    def __init__(self, compress_turns, protect_turns):
        self.compress_turns = compress_turns
        self.protect_turns = protect_turns

    def select_turns_to_compress(self, history):
        class Split:
            system_msgs = []
            remaining = history
            to_compress = history

        return Split()


class HistoryManager:
    def __init__(self, http, llm_url, char_limit, compress_turns):
        self._http = http
        self._llm_url = llm_url
        self._char_limit = char_limit
        self._compress_turns = compress_turns
        self._selection_policy = HistorySelectionPolicy(compress_turns, 0)

    def _is_over_char_limit(self, history):
        total = sum(len(str(m.get("content") or "")) for m in history)
        return self._char_limit > 0 and total > self._char_limit

    async def _call_compress_llm(self, text):
        raise HistoryCompressionError("fail")

    async def _get_summary_text(self, history):
        try:
            return await self._call_compress_llm("...")
        except HistoryCompressionError as e:
            print(f"Caught expected error: {e}")
            return None

    async def compress(self, history):
        summary_text = await self._get_summary_text(history)
        if summary_text is None:
            if self._is_over_char_limit(history):
                print("Entering fallback path")
                return history, CompressResult(0, 0, False, True)
            print("Entering error path")
            return history, CompressResult(
                compressed_count=0,
                protected_count=0,
                summary_added=False,
                error="compression returned None",
            )
        return history, CompressResult(0, 0, False)


async def main():
    mock_http = AsyncMock(spec=httpx.AsyncClient)
    mgr = HistoryManager(mock_http, "url", 1000, 1)
    h = [{"role": "user", "content": "hi"}, {"role": "assistant", "content": "hello"}]
    res, cr = await mgr.compress(h)
    print(f"Result: {res}")
    print(f"CR Error: {cr.error}")
    if cr.error == "compression returned None":
        print("SUCCESS: error is set correctly")
    else:
        print(f"FAILURE: error is '{cr.error}'")


asyncio.run(main())
