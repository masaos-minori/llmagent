"""shared/token_counter.py
Accurate token counting via llamacpp /tokenize endpoint.

Priority:
  1. LLM usage.prompt_tokens (passed as last_input_tokens)
  2. POST /tokenize endpoint   (llamacpp standard API)
  3. chars // 4               (fallback)
"""

import logging

import httpx
import orjson

from shared.types import LLMMessage

logger = logging.getLogger(__name__)

# Warn once per session when /tokenize is unavailable, then fall back silently.
_warned_unavailable: bool = False


def _estimate_chars(history: list[LLMMessage]) -> int:
    """Count total characters across all messages (content + serialised tool_calls)."""
    total = 0
    for msg in history:
        total += len(str(msg.get("content") or ""))
        for tc in msg.get("tool_calls") or []:
            total += len(orjson.dumps(tc))
    return total


def _serialise_for_tokenize(history: list[LLMMessage]) -> str:
    """Flatten history to a single string for the /tokenize endpoint.

    Concatenates role-prefixed content lines; tool_calls are rendered as JSON.
    This mirrors what the LLM would receive, giving a close approximation.
    """
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
    """Return (token_count, is_exact) for the given history.

    is_exact=True  when /tokenize was called successfully.
    is_exact=False when falling back to chars // 4.

    Falls back silently to chars // 4 when:
      - tokenize_url is empty
      - HTTP request fails or times out
      - Response format is unexpected
    """
    global _warned_unavailable  # noqa: PLW0603 — module-level warn-once flag

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
            _warned_unavailable = False
            return n_tokens, True
        logger.warning("token_counter: /tokenize returned n_tokens=0, falling back")
    except Exception as exc:
        if not _warned_unavailable:
            logger.warning(
                "token_counter: /tokenize unavailable (%s), using chars/4 fallback",
                exc,
            )
            _warned_unavailable = True

    return _estimate_chars(history) // 4, False
