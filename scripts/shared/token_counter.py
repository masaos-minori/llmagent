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

This is more accurate than the legacy ``chars // 4`` heuristic, especially for
multilingual text and structured tool payloads.  The count is marked
``is_exact=False`` to distinguish it from LLM-provided or /tokenize-derived
counts.
"""

import logging
from typing import Any

import httpx
import orjson

from shared.json_utils import dumps as _json_dumps
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

    def reset(self) -> None:
        """Reset the warn-once flag after a successful call."""
        self._warned = False


def _estimate_chars(history: list[LLMMessage]) -> int:
    """Count total characters across all messages (content + serialised tool_calls)."""
    total = 0
    for msg in history:
        content = msg.get("content")
        total += len(content) if isinstance(content, str) else 0
        total += sum(len(orjson.dumps(tc)) for tc in msg.get("tool_calls") or [])
    return total


# Character-to-token ratios by content category.
# Values tuned for typical English text and JSON-structured tool calls.
_RATIO_TEXT: float = 4.0
_RATIO_TOOL_CALL: float = 2.5
_RATIO_SYSTEM: float = 3.5


def _estimate_tokens(history: list[LLMMessage]) -> tuple[int, dict[str, int]]:
    """Estimate token count using category-aware character-to-token ratios.

    Returns ``(total_tokens, breakdown)`` where *breakdown* maps category names
    to estimated token counts.  Categories:

    - ``"text"`` — natural language content (user messages, assistant text, tool results)
    - ``"tool_calls"`` — serialised JSON from assistant tool_calls
    - ``"system"`` — system prompt content

    Ratios:

    ======  =====  ============================================
    Category   Ratio  Rationale
    ======  =====  ============================================
    text       4.0    English natural language ~4 chars/token
    tool_calls 2.5    JSON is verbose (braces, quotes, keywords)
    system     3.5    Mixed format: instructions + code snippets
    ======  =====  ============================================

    This replaces the legacy ``chars // 4`` fallback with a more accurate estimate
    that accounts for structured vs unstructured content.
    """
    total = 0
    breakdown: dict[str, int] = {"text": 0, "tool_calls": 0, "system": 0}
    for msg in history:
        role = msg.get("role", "")
        content_raw = msg.get("content")
        text = content_raw if isinstance(content_raw, str) else ""
        tool_calls = msg.get("tool_calls") or []

        if role == "system":
            if text:
                n = int(len(text) / _RATIO_SYSTEM)
                breakdown["system"] += n
                total += n
        elif role == "assistant" and tool_calls:
            # Assistant with tool calls: content (text ratio) + serialised tool_calls
            if text:
                n = int(len(text) / _RATIO_TEXT)
                breakdown["text"] += n
                total += n
            for tc in tool_calls:
                n = int(len(orjson.dumps(tc)) / _RATIO_TOOL_CALL)
                breakdown["tool_calls"] += n
                total += n
        else:
            # user, tool, assistant (text-only)
            if text:
                n = int(len(text) / _RATIO_TEXT)
                breakdown["text"] += n
                total += n
    return total, breakdown


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
        return _estimate_tokens(history)[0], False

    text = _serialise_for_tokenize(history)
    try:
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
            n_tokens = n_tokens_raw
        elif isinstance(tokens_raw, list):
            n_tokens = len(tokens_raw)
        else:
            n_tokens = 0
        if n_tokens > 0:
            if warn_once is not None:
                warn_once.reset()
            return n_tokens, True
        logger.warning("token_counter: /tokenize returned n_tokens=0, falling back")
    except (TimeoutError, httpx.HTTPStatusError, httpx.RequestError, ValueError) as exc:
        if warn_once is not None:
            warn_once.log(
                "token_counter: /tokenize unavailable (%s), using category-aware estimate",
                exc,
            )
        else:
            logger.warning(
                "token_counter: /tokenize unavailable (%s), using category-aware estimate",
                exc,
            )

    return _estimate_tokens(history)[0], False
