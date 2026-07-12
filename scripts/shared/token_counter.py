"""shared/token_counter.py
Accurate token counting via llamacpp /tokenize endpoint.

Priority:
  1. LLM usage.prompt_tokens (passed as last_input_tokens) — exact
  2. POST /tokenize endpoint   (llamacpp standard API)      — exact
  3. Category-aware estimate                               — estimated

When exact token counts are unavailable (sources 1 and 2), the fallback uses
category-aware estimation with different character-to-token ratios per content
type:

  - Natural language text (user/assistant/tool):   4.0 chars/token
  - Structured JSON (assistant tool_calls):        2.5 chars/token
  - System messages (mixed format):                3.5 chars/token

This is more accurate than a simple ``chars // 4`` heuristic, especially for
multilingual text and structured tool payloads.  The count is marked
``is_exact=False`` to distinguish it from LLM-provided or /tokenize-derived
counts.
"""

import logging

import httpx
import orjson
from shared.json_utils import dumps as _json_dumps
from shared.json_utils import tool_call_serialized_length
from shared.token_estimation import estimate_tokens
from shared.types import LLMMessage

logger = logging.getLogger(__name__)


class _WarnOnce:
    """Module-level warn-once helper that suppresses repeated messages per session."""

    def __init__(self) -> None:
        self._warned: bool = False

    def log(self, msg: str, *args: object) -> None:
        if not self._warned:
            logger.warning(msg, *args)
            self._warned = True

    def reset(self) -> None:
        """Reset the warn-once flag after a successful call."""
        self._warned = False


def _estimate_chars(history: list[LLMMessage]) -> int:
    """Count total characters across all messages (content + serialised tool_calls)."""
    total = 0
    for msg in history:
        content = msg.get("content")
        total += len(content) if isinstance(content, str) else 0
        total += sum(
            tool_call_serialized_length(tc) for tc in msg.get("tool_calls") or []
        )
    return total


def _serialise_for_tokenize(history: list[LLMMessage]) -> str:
    """Flatten history to a single string for the /tokenize endpoint."""
    parts: list[str] = []
    for msg in history:
        role = msg.get("role", "")
        content_raw = msg.get("content")
        content = content_raw if isinstance(content_raw, str) else ""
        if content:
            parts.append(f"{role}: {content}")
        for tc in msg.get("tool_calls") or []:
            parts.append(_json_dumps(tc))
    return "\n".join(parts)


async def get_token_count(
    history: list[LLMMessage],
    tokenize_url: str,
    http: httpx.AsyncClient,
    timeout: float = 3.0,
    warn_once: _WarnOnce | None = None,
) -> tuple[int, bool]:
    """Return (token_count, is_exact) for the given history."""
    if not tokenize_url:
        return estimate_tokens(history)[0], False

    text = _serialise_for_tokenize(history)
    try:
        n_tokens = await _fetch_token_count(text, tokenize_url, http, timeout)
        if n_tokens > 0:
            if warn_once is not None:
                warn_once.reset()
            return n_tokens, True
        logger.warning("token_counter: /tokenize returned n_tokens=0, falling back")
    except (TimeoutError, httpx.HTTPStatusError, httpx.RequestError, ValueError) as exc:
        _warn_tokenize_unavailable(exc, warn_once)

    return estimate_tokens(history)[0], False


async def _fetch_token_count(
    text: str,
    tokenize_url: str,
    http: httpx.AsyncClient,
    timeout: float,
) -> int:
    """POST to /tokenize and extract n_tokens from the response."""
    resp = await http.post(
        tokenize_url,
        content=orjson.dumps({"content": text}),
        headers={"Content-Type": "application/json"},
        timeout=timeout,
    )
    resp.raise_for_status()
    data = orjson.loads(resp.content)
    if not isinstance(data, dict):
        raise ValueError(f"/tokenize returned non-dict: {type(data).__name__}")
    n_tokens_raw = data.get("n_tokens")
    tokens_raw = data.get("tokens")
    if isinstance(n_tokens_raw, int) and n_tokens_raw > 0:
        return n_tokens_raw
    if isinstance(tokens_raw, list):
        return len(tokens_raw)
    return 0


def _warn_tokenize_unavailable(
    exc: Exception,
    warn_once: _WarnOnce | None = None,
) -> None:
    """Log a warning when /tokenize is unavailable."""
    msg = "token_counter: /tokenize unavailable (%s), using category-aware estimate"
    if warn_once is not None:
        warn_once.log(msg, exc)
    else:
        logger.warning(msg, exc)
