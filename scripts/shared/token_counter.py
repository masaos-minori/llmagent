"""shared/token_counter.py
Accurate token counting via llamacpp /tokenize endpoint.

Priority:
  1. LLM usage.prompt_tokens (passed as last_input_tokens)
  2. POST /tokenize endpoint   (llamacpp standard API)
  3. chars // 4               (fallback)
"""

import logging
from typing import Any

import httpx
import orjson

from shared.types import LLMMessage

logger = logging.getLogger(__name__)


class _WarnOnce:
    """Module-level warn-once helper that suppresses repeated messages per session."""

    def __init__(self) -> None:
        self._warned: bool = False

    def log(self, msg: str, *args: Any) -> None:
        if not self._warned:
            logger.warning(msg, *args)
            self._warned = True


_warned_unavailable = _WarnOnce()


def _estimate_chars(history: list[LLMMessage]) -> int:
    """Count total characters across all messages (content + serialised tool_calls)."""
    return sum(
        len(str(msg.get("content") or ""))
        + sum(len(orjson.dumps(tc)) for tc in msg.get("tool_calls") or [])
        for msg in history
    )


def _serialise_for_tokenize(history: list[LLMMessage]) -> str:
    """Flatten history to a single string for the /tokenize endpoint."""
    parts: list[str] = []
    for msg in history:
        role = msg.get("role", "")
        content = str(msg.get("content") or "")
        if content:
            parts.append(f"{role}: {content}")
        for tc in msg.get("tool_calls") or []:
            parts.append(orjson.dumps(tc).decode())
    return "\n".join(parts)


async def get_token_count(
    history: list[LLMMessage],
    tokenize_url: str,
    http: httpx.AsyncClient,
    timeout: float = 3.0,
) -> tuple[int, bool]:
    """Return (token_count, is_exact) for the given history."""
    if not tokenize_url:
        return _estimate_chars(history) // 4, False

    text = _serialise_for_tokenize(history)
    try:
        resp = await http.post(
            tokenize_url,
            content=orjson.dumps({"content": text}),
            headers={"Content-Type": "application/json"},
            timeout=timeout,
        )
        resp.raise_for_status()
        data = resp.json()
        n_tokens = data.get("n_tokens") or len(data.get("tokens") or [])
        if n_tokens > 0:
            _warned_unavailable._warned = False
            return n_tokens, True
        logger.warning("token_counter: /tokenize returned n_tokens=0, falling back")
    except Exception as exc:
        _warned_unavailable.log(
            "token_counter: /tokenize unavailable (%s), using chars/4 fallback",
            exc,
        )

    return _estimate_chars(history) // 4, False
