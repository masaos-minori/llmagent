"""shared/llm_client.py
LLM communication layer with robust SSE streaming.

Backward-compatible re-exports (also available from sub-modules):
  shared.llm_exceptions → LLMErrorKind, LLMTransportError
  shared.sse_parser     → RobustSSEParser, _anext_or_done

Key components:
  LLMClient — HTTP retry, payload construction, reconnect-aware SSE streaming
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator, Callable
from typing import Any

import httpx
import orjson

from shared.llm_exceptions import LLMErrorKind, LLMTransportError
from shared.llm_types import LLMResponse, LLMUsage
from shared.sse_parser import RobustSSEParser, _anext_or_done
from shared.types import AccumulatedToolCall, LLMMessage, ToolCallDelta

# Re-exports for backward compatibility

# Re-exports for backward compatibility
__all__ = [
    "LLMClient",
    "LLMTransportError",
    "LLMErrorKind",
    "RobustSSEParser",
    "_anext_or_done",
]

logger = logging.getLogger(__name__)


class LLMClient:
    """LLM HTTP client with exponential-backoff retry and robust SSE streaming; stat_* counters accumulate for the instance lifetime."""

    def __init__(
        self,
        http: httpx.AsyncClient,
        max_retries: int,
        retry_base_delay: float,
        temperature: float,
        max_tokens: int,
        on_token: Callable[[str], None] | None = None,
        on_usage: Callable[[int, int], None] | None = None,
        sse_heartbeat_timeout: float = 30.0,
        sse_malformed_retry: int = 2,
        sse_reconnect_max: int = 1,
        llm_stream_retry_on_heartbeat_timeout: bool = True,
        llm_stream_retry_on_malformed_chunk: bool = False,
    ) -> None:
        self._http = http
        self._max_retries = max_retries
        self._retry_base_delay = retry_base_delay
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._on_token = on_token
        # Called with (prompt_tokens, completion_tokens) when usage data is available.
        self._on_usage = on_usage
        self._sse_heartbeat_timeout = sse_heartbeat_timeout
        self._sse_malformed_retry = sse_malformed_retry
        self._sse_reconnect_max = sse_reconnect_max
        self._llm_stream_retry_on_heartbeat_timeout = (
            llm_stream_retry_on_heartbeat_timeout
        )
        self._llm_stream_retry_on_malformed_chunk = llm_stream_retry_on_malformed_chunk
        # Cumulative session statistics
        self.stat_retries: int = 0
        self.stat_reconnects: int = 0
        self.stat_heartbeat_timeouts: int = 0
        self.stat_partial_completions: int = 0
        self.stat_parse_errors: int = 0

    _HOT_CONFIG_FIELDS: tuple[tuple[str, str], ...] = (
        ("_temperature", "temperature"),
        ("_max_tokens", "max_tokens"),
        ("_max_retries", "max_retries"),
        ("_retry_base_delay", "retry_base_delay"),
        ("_sse_heartbeat_timeout", "sse_heartbeat_timeout"),
        ("_sse_malformed_retry", "sse_malformed_retry"),
        ("_sse_reconnect_max", "sse_reconnect_max"),
        ("_llm_stream_retry_on_heartbeat_timeout", "stream_retry_on_heartbeat_timeout"),
        ("_llm_stream_retry_on_malformed_chunk", "stream_retry_on_malformed_chunk"),
    )

    @classmethod
    def _apply_one(cls, instance: object, field: str, kwarg: str, value: Any) -> None:
        setattr(instance, field, value)

    def apply_config(
        self,
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
        max_retries: int | None = None,
        retry_base_delay: float | None = None,
        sse_heartbeat_timeout: float | None = None,
        sse_malformed_retry: int | None = None,
        sse_reconnect_max: int | None = None,
        stream_retry_on_heartbeat_timeout: bool | None = None,
        stream_retry_on_malformed_chunk: bool | None = None,
    ) -> None:
        """Update hot-reloadable configuration fields without recreating the instance."""
        args = dict(
            temperature=temperature,
            max_tokens=max_tokens,
            max_retries=max_retries,
            retry_base_delay=retry_base_delay,
            sse_heartbeat_timeout=sse_heartbeat_timeout,
            sse_malformed_retry=sse_malformed_retry,
            sse_reconnect_max=sse_reconnect_max,
            stream_retry_on_heartbeat_timeout=stream_retry_on_heartbeat_timeout,
            stream_retry_on_malformed_chunk=stream_retry_on_malformed_chunk,
        )
        for attr, kwarg in self._HOT_CONFIG_FIELDS:
            if (value := args.get(kwarg)) is not None:
                self._apply_one(self, attr, kwarg, value)

    # ── Retry logic ───────────────────────────────────────────────────────────

    async def request_with_retry(
        self,
        url: str,
        payload: dict[str, Any],
    ) -> httpx.Response:
        """POST to an LLM endpoint with exponential backoff retry; retries on 503/429 and connection errors; raises last exception when all attempts exhausted."""
        last_exc: Exception | None = None
        for attempt in range(self._max_retries):
            try:
                resp = await self._http.post(url, json=payload)
                resp.raise_for_status()
                return resp
            except httpx.HTTPStatusError as e:
                # Re-raise immediately for non-transient HTTP errors
                if e.response.status_code not in (429, 503):
                    raise
                last_exc = e
            except httpx.RequestError as e:
                # Connection resets and other network errors are transient
                last_exc = e
            if attempt < self._max_retries - 1:
                self.stat_retries += 1
                delay = self._retry_base_delay * (2**attempt)
                logger.warning(
                    "LLM request failed (attempt %d/%d): %s, retrying in %.1fs",
                    attempt + 1,
                    self._max_retries,
                    last_exc,
                    delay,
                )
                await asyncio.sleep(delay)
            else:
                logger.error(
                    "LLM request failed after %d attempts: %s",
                    self._max_retries,
                    last_exc,
                )
        if last_exc is None:
            # Unreachable: loop always sets last_exc or returns; max_retries >= 1 required
            raise RuntimeError("request_with_retry: max_retries must be >= 1")
        raise last_exc

    # ── Payload construction ──────────────────────────────────────────────────

    def build_payload(
        self,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
        stream: bool = False,
    ) -> dict[str, Any]:
        """Build the request payload for a chat completion request."""
        payload: dict[str, Any] = {
            "messages": history,
            "tools": tool_defs,
            "tool_choice": "auto",
            "temperature": self._temperature,
            "max_tokens": self._max_tokens,
        }
        if stream:
            payload["stream"] = True
        return payload

    def _parse_usage(self, data: dict[str, Any]) -> LLMUsage | None:
        """Extract token usage from response data; fire on_usage callback; return LLMUsage or None."""
        usage_raw = data.get("usage")
        if not isinstance(usage_raw, dict):
            return None
        pt = usage_raw.get("prompt_tokens")
        ct = usage_raw.get("completion_tokens")
        if not isinstance(pt, int) or not isinstance(ct, int):
            return None
        if self._on_usage is not None:
            self._on_usage(pt, ct)
        return LLMUsage(prompt_tokens=pt, completion_tokens=ct)

    def _parse_response(self, raw: dict[str, Any]) -> LLMResponse:
        """Validate and parse raw LLM JSON into LLMResponse DTO; raises ValueError on schema mismatch."""
        choices = raw.get("choices")
        if not isinstance(choices, list) or not choices:
            raise ValueError("Unexpected LLM response: missing or empty 'choices'")
        choice = choices[0]
        if not isinstance(choice, dict):
            raise ValueError("Unexpected LLM response: choices[0] is not a dict")
        message_raw = choice.get("message")
        if not isinstance(message_raw, dict):
            raise ValueError("Unexpected LLM response: 'message' is not a dict")
        finish_reason = choice.get("finish_reason")
        if finish_reason is not None and not isinstance(finish_reason, str):
            finish_reason = None
        usage = self._parse_usage(raw)
        return LLMResponse(
            message=message_raw,  # type: ignore[typeddict-item] — validated as dict above
            finish_reason=finish_reason,
            usage=usage,
        )

    # ── Non-streaming call ────────────────────────────────────────────────────

    async def call(
        self,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
    ) -> LLMResponse:
        """Send conversation history to LLM and return a typed LLMResponse."""
        resp = await self.request_with_retry(
            url,
            self.build_payload(history, tool_defs),
        )
        raw = orjson.loads(resp.content)
        if not isinstance(raw, dict):
            raise ValueError(f"LLM response is not a JSON object: {type(raw).__name__}")
        return self._parse_response(raw)

    # ── SSE streaming helpers ─────────────────────────────────────────────────

    @staticmethod
    def _merge_tool_call_delta(
        tool_calls_map: dict[int, AccumulatedToolCall],
        tc_delta: ToolCallDelta,
    ) -> None:
        """Accumulate one streaming tool_call delta into the index-keyed map."""
        idx = tc_delta.get("index", 0)
        if idx not in tool_calls_map:
            tool_calls_map[idx] = {
                "id": "",
                "type": "function",
                "function": {"name": "", "arguments": ""},
            }
        tc = tool_calls_map[idx]
        if tc_delta.get("id"):
            tc["id"] = tc_delta["id"]  # type: ignore[typeddict-item]
        fn = tc_delta.get("function")
        if fn is not None:
            tc["function"]["name"] += fn.get("name", "")
            tc["function"]["arguments"] += fn.get("arguments", "")

    @staticmethod
    def _build_stream_response(
        content_parts: list[str],
        tool_calls_map: dict[int, AccumulatedToolCall],
        finish_reason: str | None,
    ) -> dict[str, Any]:
        """Assemble the final response dict from streamed content and tool_call deltas."""
        content = "".join(content_parts)
        tool_calls = (
            [tool_calls_map[i] for i in sorted(tool_calls_map)]
            if tool_calls_map
            else None
        )
        message: dict[str, Any] = {"role": "assistant", "content": content}
        if tool_calls:
            message["tool_calls"] = tool_calls
        return {"choices": [{"message": message, "finish_reason": finish_reason}]}

    def _process_sse_chunk(
        self,
        chunk: dict[str, Any],
        content_parts: list[str],
        tool_calls_map: dict[int, AccumulatedToolCall],
    ) -> str | None:
        """Process one parsed SSE chunk delta; return finish_reason or None."""
        choices = chunk.get("choices")
        if not choices:
            return None
        choice = choices[0]
        delta = choice.get("delta", {})
        finish_reason: str | None = choice.get("finish_reason") or None
        token = delta.get("content") or ""
        if token:
            content_parts.append(token)
            if self._on_token:
                self._on_token(token)
        for tc_delta in delta.get("tool_calls", []):
            self._merge_tool_call_delta(tool_calls_map, tc_delta)
        return finish_reason

    # ── SSE byte reading ──────────────────────────────────────────────────────

    async def _read_next_chunk(
        self,
        byte_iter: AsyncIterator[bytes],
        url: str,
    ) -> tuple[bytes, bool]:
        """Await the next raw chunk with heartbeat timeout; returns (chunk, exhausted); raises HEARTBEAT_TIMEOUT when no bytes arrive within sse_heartbeat_timeout."""
        try:
            coro = _anext_or_done(byte_iter)
            if self._sse_heartbeat_timeout > 0:
                return await asyncio.wait_for(coro, timeout=self._sse_heartbeat_timeout)
            return await coro
        except TimeoutError:
            raise LLMTransportError(
                kind="HEARTBEAT_TIMEOUT",
                phase="in_stream",
                url=url,
                retryable=self._llm_stream_retry_on_heartbeat_timeout,
                detail=f"no bytes for {self._sse_heartbeat_timeout:.1f}s",
            )

    # ── Single-connection SSE attempt ─────────────────────────────────────────

    def _raise_http_status_error(self, e: httpx.HTTPStatusError, url: str) -> None:
        """Convert an httpx HTTP status error into LLMTransportError and raise it."""
        code = e.response.status_code
        retryable = code in (429, 503)
        raise LLMTransportError(
            kind="HTTP_STATUS_RETRYABLE" if retryable else "HTTP_STATUS_FATAL",
            phase="pre_stream",
            url=url,
            status_code=code,
            retryable=retryable,
        ) from e

    def _process_sse_payloads(
        self,
        payloads: list[str],
        content_parts: list[str],
        tool_calls_map: dict[int, AccumulatedToolCall],
    ) -> str | None:
        """Parse and process a list of raw SSE payloads; return last finish_reason seen."""
        finish_reason: str | None = None
        for raw_payload in payloads:
            try:
                chunk = orjson.loads(raw_payload)
            except (orjson.JSONDecodeError, ValueError):
                continue
            reason = self._process_sse_chunk(chunk, content_parts, tool_calls_map)
            if reason:
                finish_reason = reason
            self._parse_usage(chunk)
        return finish_reason

    def _translate_stream_error(self, e: Exception, url: str) -> LLMTransportError:
        """Translate a stream-level exception into LLMTransportError.

        HTTP status errors are handled separately in _raise_http_status_error.
        """
        if isinstance(e, httpx.ConnectError):
            return LLMTransportError(
                kind="CONNECT_ERROR",
                phase="pre_stream",
                url=url,
                retryable=True,
                detail=str(e),
            )
        if isinstance(e, httpx.ReadTimeout):
            return LLMTransportError(
                kind="READ_TIMEOUT",
                phase="in_stream",
                url=url,
                retryable=True,
                detail=str(e),
            )
        return LLMTransportError(
            kind="UNKNOWN_STREAM_ERROR",
            phase="in_stream",
            url=url,
            retryable=False,
            detail=str(e),
        )

    async def _stream_once(
        self,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
        content_parts: list[str],
        tool_calls_map: dict[int, AccumulatedToolCall],
    ) -> str | None:
        """Execute one SSE connection attempt; appends tokens/tool_calls in-place; returns finish_reason on success; raises LLMTransportError on any failure."""
        parser = RobustSSEParser(
            malformed_retry=self._sse_malformed_retry,
            heartbeat_timeout=self._sse_heartbeat_timeout,
        )
        payload = self.build_payload(history, tool_defs, stream=True)
        finish_reason: str | None = None

        try:
            async with self._http.stream("POST", url, json=payload) as resp:
                await self._handle_status(resp, url)

                byte_iter = resp.aiter_bytes().__aiter__()
                while True:
                    raw_chunk, exhausted = await self._read_next_chunk(byte_iter, url)
                    if exhausted:
                        break

                    payloads, is_done = parser.feed(raw_chunk)
                    self._accumulate_parse_errors(parser)

                    reason = self._process_sse_payloads(
                        payloads, content_parts, tool_calls_map
                    )
                    if reason:
                        finish_reason = reason

                    if is_done:
                        break

        except LLMTransportError:
            raise
        except (
            TimeoutError,
            httpx.ConnectError,
            httpx.ReadTimeout,
            httpx.RemoteProtocolError,
        ) as e:
            raise self._translate_stream_error(e, url) from e

        return finish_reason

    async def _handle_status(self, resp: httpx.Response, url: str) -> None:
        """Raise on HTTP errors."""
        try:
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            self._raise_http_status_error(e, url)

    def _accumulate_parse_errors(self, parser: RobustSSEParser) -> None:
        """Add parse errors to instance stats and reset the parser's counter."""
        if parser.stat_parse_errors:
            self.stat_parse_errors += parser.stat_parse_errors
            parser.stat_parse_errors = 0

    # ── Streaming call with reconnect ─────────────────────────────────────────

    def _resolve_retryable(self, e: LLMTransportError) -> bool:
        """Return effective retryable flag; increments stat_heartbeat_timeouts when e.kind == 'HEARTBEAT_TIMEOUT'."""
        if e.kind == "HEARTBEAT_TIMEOUT":
            self.stat_heartbeat_timeouts += 1
            return self._llm_stream_retry_on_heartbeat_timeout
        if e.kind == "MALFORMED_SSE_FRAME":
            return self._llm_stream_retry_on_malformed_chunk
        return e.retryable

    async def stream(
        self,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
    ) -> LLMResponse:
        """Stream a chat completion via SSE; returns LLMResponse; raises LLMTransportError with partial_text on failure."""
        content_parts: list[str] = []
        tool_calls_map: dict[int, AccumulatedToolCall] = {}
        finish_reason: str | None = None

        for attempt in range(self._sse_reconnect_max + 1):
            try:
                finish_reason = await self._stream_once(
                    url,
                    history,
                    tool_defs,
                    content_parts,
                    tool_calls_map,
                )
                break  # success
            except LLMTransportError as e:
                has_partial = bool(content_parts) or bool(tool_calls_map)
                effective_retryable = self._resolve_retryable(e)
                if has_partial or not effective_retryable:
                    # Partial output or non-retryable: mark_incomplete
                    e.partial_text = "".join(content_parts)
                    raise
                if attempt >= self._sse_reconnect_max:
                    e.partial_text = "".join(content_parts)
                    raise
                self.stat_reconnects += 1
                delay = self._retry_base_delay * (2**attempt)
                logger.warning(
                    "SSE error (attempt %d/%d): %s, reconnecting in %.1fs",
                    attempt + 1,
                    self._sse_reconnect_max + 1,
                    e.kind,
                    delay,
                )
                await asyncio.sleep(delay)
                # Clear accumulated state before reconnect
                content_parts.clear()
                tool_calls_map.clear()

        if content_parts and self._on_token:
            self._on_token("\n")
        raw = self._build_stream_response(content_parts, tool_calls_map, finish_reason)
        return self._parse_response(raw)
