#!/usr/bin/env python3
"""
llm_client.py
LLM communication layer with robust SSE streaming.

Key components:
  LLMTransportError  — structured exception covering all LLM transport failure modes
  RobustSSEParser    — incremental UTF-8 decoder + heartbeat tracking + malformed retry
  LLMClient          — HTTP retry, payload construction, reconnect-aware SSE streaming
"""

import asyncio
import codecs
import logging
import time
from collections.abc import AsyncIterator, Callable
from typing import Literal, cast

import httpx
import orjson

from shared.types import LLMMessage

logger = logging.getLogger(__name__)

# ── Exception ─────────────────────────────────────────────────────────────────

LLMErrorKind = Literal[
    "HTTP_STATUS_RETRYABLE",
    "HTTP_STATUS_FATAL",
    "CONNECT_ERROR",
    "READ_TIMEOUT",
    "HEARTBEAT_TIMEOUT",
    "MALFORMED_SSE_FRAME",
    "UTF8_PARTIAL_DECODE_ERROR",
    "PREMATURE_EOF",
    "UNKNOWN_STREAM_ERROR",
]


class LLMTransportError(Exception):
    """Structured exception for all LLM HTTP/SSE transport failures.

    partial_text: content accumulated before failure (non-empty = partial completion).
    retryable: whether the caller should attempt reconnect.
    """

    def __init__(
        self,
        kind: LLMErrorKind,
        phase: Literal["pre_stream", "in_stream"],
        url: str,
        status_code: int | None = None,
        retryable: bool = False,
        partial_text: str = "",
        detail: str = "",
    ) -> None:
        super().__init__(f"{kind} phase={phase} retryable={retryable}")
        self.kind: LLMErrorKind = kind
        self.phase: Literal["pre_stream", "in_stream"] = phase
        self.url = url
        self.status_code = status_code
        self.retryable = retryable
        self.partial_text = partial_text
        self.detail = detail


# ── SSE Parser ────────────────────────────────────────────────────────────────


class RobustSSEParser:
    """Stateful SSE parser over a raw byte stream.

    Handles partial UTF-8 sequences via codecs incremental decoder.
    Tracks heartbeat (last-event timestamp) for inactivity detection.
    Counts malformed JSON frames; raises after budget is exhausted.
    One instance per connection — create a new instance on reconnect.
    """

    def __init__(self, malformed_retry: int, heartbeat_timeout: float) -> None:
        self._decoder = codecs.getincrementaldecoder("utf-8")("replace")
        self._buf = ""
        self._malformed_retry = malformed_retry
        self._heartbeat_timeout = heartbeat_timeout
        self._last_event_at: float = time.monotonic()
        self._malformed_count: int = 0
        # Accumulated per-feed parse error count; caller resets after reading
        self.stat_parse_errors: int = 0

    def feed(self, raw: bytes) -> tuple[list[str], bool]:
        """Decode raw bytes and extract complete SSE data payloads.

        Returns (payloads, is_done).
        payloads: list of JSON payload strings (stripped of "data: " prefix).
        is_done: True when [DONE] sentinel was received.
        Raises LLMTransportError(MALFORMED_SSE_FRAME) after malformed budget exhausted.
        """
        text = self._decoder.decode(raw, final=False)
        self._buf += text
        payloads: list[str] = []
        is_done = False
        while "\n" in self._buf:
            line, self._buf = self._buf.split("\n", 1)
            line = line.rstrip("\r")
            result = self._parse_line(line)
            if result is None:
                continue
            payload, done = result
            if done:
                is_done = True
                break
            if payload is not None:
                payloads.append(payload)
        return payloads, is_done

    def _parse_line(self, line: str) -> tuple[str | None, bool] | None:
        """Parse one SSE text line.

        Returns None to skip (blank/comment/unknown field).
        Returns (None, True) for [DONE].
        Returns (payload_str, False) for valid data lines.
        Raises LLMTransportError when malformed budget is exceeded.
        """
        if not line:
            # Blank line (SSE event boundary) acts as keepalive
            self._last_event_at = time.monotonic()
            return None
        if line.startswith(":"):
            # SSE comment line = keepalive
            self._last_event_at = time.monotonic()
            return None
        if not line.startswith("data:"):
            # Unknown SSE field (event:, id:, retry:) — ignore
            return None
        payload = line[5:].lstrip(" ")  # handle "data:" and "data: "
        if payload.strip() == "[DONE]":
            self._last_event_at = time.monotonic()
            return None, True
        try:
            orjson.loads(payload)
        except (orjson.JSONDecodeError, ValueError):
            self._malformed_count += 1
            self.stat_parse_errors += 1
            if self._malformed_count > self._malformed_retry:
                raise LLMTransportError(
                    kind="MALFORMED_SSE_FRAME",
                    phase="in_stream",
                    url="",
                    retryable=False,
                    detail=f"malformed SSE frame (count={self._malformed_count})",
                )
            return None  # within retry budget: skip this frame
        self._last_event_at = time.monotonic()
        return payload, False

    def check_heartbeat(self, url: str) -> None:
        """Raise HEARTBEAT_TIMEOUT when stream has been idle longer than timeout."""
        if self._heartbeat_timeout <= 0:
            return
        elapsed = time.monotonic() - self._last_event_at
        if elapsed > self._heartbeat_timeout:
            raise LLMTransportError(
                kind="HEARTBEAT_TIMEOUT",
                phase="in_stream",
                url=url,
                retryable=True,
                detail=f"no SSE event for {elapsed:.1f}s",
            )


# ── LLM Client ────────────────────────────────────────────────────────────────


async def _anext_or_done(aiter: AsyncIterator[bytes]) -> tuple[bytes, bool]:
    """Await one item from an async bytes iterator.

    Returns (item, False) on success, (b"", True) on StopAsyncIteration.
    This helper prevents StopAsyncIteration from propagating through
    asyncio.wait_for(), which would convert it to RuntimeError (PEP 479).
    """
    try:
        item = await aiter.__anext__()
        return item, False
    except StopAsyncIteration:
        return b"", True


class LLMClient:
    """LLM HTTP client with exponential-backoff retry and robust SSE streaming.

    Stateful statistics (stat_*) accumulate for the lifetime of the instance.
    Temperature and max_tokens are set at construction and apply to every call.
    """

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

    # ── Retry logic ───────────────────────────────────────────────────────────

    async def request_with_retry(self, url: str, payload: dict) -> httpx.Response:
        """POST to an LLM endpoint with exponential backoff retry.

        Retries on HTTP 503 (overloaded) / 429 (rate-limited) and connection
        errors up to _max_retries times.
        Delays: _retry_base_delay × 2^attempt (1s, 2s, 4s for max_retries=3).
        Raises the last exception when all retries are exhausted.
        """
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
                    f"LLM request failed"
                    f" (attempt {attempt + 1}/{self._max_retries}):"
                    f" {last_exc}, retrying in {delay:.1f}s"
                )
                await asyncio.sleep(delay)
            else:
                logger.error(
                    f"LLM request failed after {self._max_retries} attempts: {last_exc}"
                )
        assert (
            last_exc is not None
        )  # loop ran and all attempts raised; max_retries >= 1 required
        raise last_exc

    # ── Payload construction ──────────────────────────────────────────────────

    def build_payload(
        self,
        history: list[LLMMessage],
        tool_defs: list[dict],
        stream: bool = False,
    ) -> dict:
        """Build the request payload for a chat completion request."""
        payload: dict = {
            "messages": history,
            "tools": tool_defs,
            "tool_choice": "auto",
            "temperature": self._temperature,
            "max_tokens": self._max_tokens,
        }
        if stream:
            payload["stream"] = True
        return payload

    def _emit_usage(self, data: dict) -> None:
        """Fire on_usage callback when both token counts are present in data."""
        if self._on_usage is None:
            return
        usage = data.get("usage", {})
        pt = usage.get("prompt_tokens")
        ct = usage.get("completion_tokens")
        if pt is not None and ct is not None:
            self._on_usage(int(pt), int(ct))

    # ── Non-streaming call ────────────────────────────────────────────────────

    async def call(
        self, url: str, history: list[LLMMessage], tool_defs: list[dict]
    ) -> dict:
        """Send conversation history to LLM and return the raw response JSON."""
        resp = await self.request_with_retry(
            url, self.build_payload(history, tool_defs)
        )
        data = dict(resp.json())
        self._emit_usage(data)
        return data

    # ── SSE streaming helpers ─────────────────────────────────────────────────

    @staticmethod
    def _merge_tool_call_delta(tool_calls_map: dict[int, dict], tc_delta: dict) -> None:
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
            tc["id"] = tc_delta["id"]
        fn = tc_delta.get("function", {})
        tc["function"]["name"] += fn.get("name", "")
        tc["function"]["arguments"] += fn.get("arguments", "")

    @staticmethod
    def _build_stream_response(
        content_parts: list[str],
        tool_calls_map: dict[int, dict],
        finish_reason: str | None,
    ) -> dict:
        """Assemble the final response dict from streamed content and tool_call deltas."""
        content = "".join(content_parts)
        tool_calls = (
            [tool_calls_map[i] for i in sorted(tool_calls_map)]
            if tool_calls_map
            else None
        )
        message: dict = {"role": "assistant", "content": content}
        if tool_calls:
            message["tool_calls"] = tool_calls
        return {"choices": [{"message": message, "finish_reason": finish_reason}]}

    def _process_sse_chunk(
        self,
        chunk: dict,
        content_parts: list[str],
        tool_calls_map: dict[int, dict],
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
        """Await the next raw chunk from the byte stream with heartbeat timeout.

        Returns (chunk, exhausted); exhausted=True signals stream end.
        Raises LLMTransportError(HEARTBEAT_TIMEOUT) when no bytes arrive within
        sse_heartbeat_timeout seconds.
        """
        timeout = (
            self._sse_heartbeat_timeout if self._sse_heartbeat_timeout > 0 else None
        )
        try:
            if timeout is not None:
                return await asyncio.wait_for(
                    _anext_or_done(byte_iter), timeout=timeout
                )
            return await _anext_or_done(byte_iter)
        except TimeoutError:
            raise LLMTransportError(
                kind="HEARTBEAT_TIMEOUT",
                phase="in_stream",
                url=url,
                retryable=self._llm_stream_retry_on_heartbeat_timeout,
                detail=f"no bytes for {self._sse_heartbeat_timeout:.1f}s",
            )

    # ── Single-connection SSE attempt ─────────────────────────────────────────

    async def _stream_once(
        self,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict],
        content_parts: list[str],
        tool_calls_map: dict[int, dict],
    ) -> str | None:
        """Execute one SSE connection attempt; return finish_reason on success.

        Appends tokens to content_parts and tool_call deltas to tool_calls_map
        in-place so the caller can inspect partial state on failure.
        Raises LLMTransportError on any connection or stream-level failure.
        """
        parser = RobustSSEParser(
            malformed_retry=self._sse_malformed_retry,
            heartbeat_timeout=self._sse_heartbeat_timeout,
        )
        payload = self.build_payload(history, tool_defs, stream=True)
        finish_reason: str | None = None

        try:
            async with self._http.stream("POST", url, json=payload) as resp:
                try:
                    resp.raise_for_status()
                except httpx.HTTPStatusError as e:
                    code = e.response.status_code
                    retryable = code in (429, 503)
                    raise LLMTransportError(
                        kind="HTTP_STATUS_RETRYABLE"
                        if retryable
                        else "HTTP_STATUS_FATAL",
                        phase="pre_stream",
                        url=url,
                        status_code=code,
                        retryable=retryable,
                    ) from e

                byte_iter = resp.aiter_bytes().__aiter__()
                while True:
                    raw_chunk, exhausted = await self._read_next_chunk(byte_iter, url)
                    if exhausted:
                        break

                    payloads, is_done = parser.feed(raw_chunk)
                    if parser.stat_parse_errors:
                        self.stat_parse_errors += parser.stat_parse_errors
                        parser.stat_parse_errors = 0

                    for raw_payload in payloads:
                        try:
                            chunk = orjson.loads(raw_payload)
                        except (orjson.JSONDecodeError, ValueError):
                            continue
                        reason = self._process_sse_chunk(
                            chunk, content_parts, tool_calls_map
                        )
                        if reason:
                            finish_reason = reason
                        self._emit_usage(chunk)

                    if is_done:
                        break

        except httpx.ConnectError as e:
            raise LLMTransportError(
                kind="CONNECT_ERROR",
                phase="pre_stream",
                url=url,
                retryable=True,
                detail=str(e),
            ) from e
        except httpx.ReadTimeout as e:
            raise LLMTransportError(
                kind="READ_TIMEOUT",
                phase="in_stream",
                url=url,
                retryable=True,
                detail=str(e),
            ) from e
        except LLMTransportError:
            raise
        except Exception as e:
            raise LLMTransportError(
                kind="UNKNOWN_STREAM_ERROR",
                phase="in_stream",
                url=url,
                retryable=False,
                detail=str(e),
            ) from e

        return finish_reason

    # ── Streaming call with reconnect ─────────────────────────────────────────

    async def stream(
        self, url: str, history: list[LLMMessage], tool_defs: list[dict]
    ) -> dict:
        """Stream a chat completion via SSE with reconnect on retryable errors.

        On retryable errors with no partial output: reconnect up to sse_reconnect_max.
        On partial output or non-retryable errors: raise LLMTransportError with
        partial_text set so the caller can apply mark_incomplete policy.
        Returns a response dict in the same shape as call().
        """
        content_parts: list[str] = []
        tool_calls_map: dict[int, dict] = {}
        finish_reason: str | None = None

        for attempt in range(self._sse_reconnect_max + 1):
            try:
                finish_reason = await self._stream_once(
                    url, history, tool_defs, content_parts, tool_calls_map
                )
                break  # success
            except LLMTransportError as e:
                has_partial = bool(content_parts) or bool(tool_calls_map)
                # Override retryable based on per-kind config flags
                effective_retryable = e.retryable
                if e.kind == "HEARTBEAT_TIMEOUT":
                    effective_retryable = self._llm_stream_retry_on_heartbeat_timeout
                    self.stat_heartbeat_timeouts += 1
                elif e.kind == "MALFORMED_SSE_FRAME":
                    effective_retryable = self._llm_stream_retry_on_malformed_chunk

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
                    f"SSE error (attempt {attempt + 1}/{self._sse_reconnect_max + 1}):"
                    f" {e.kind}, reconnecting in {delay:.1f}s"
                )
                await asyncio.sleep(delay)
                # Clear accumulated state before reconnect
                content_parts.clear()
                tool_calls_map.clear()

        if content_parts and self._on_token:
            self._on_token("\n")
        return self._build_stream_response(content_parts, tool_calls_map, finish_reason)

    # ── Response parsing ──────────────────────────────────────────────────────

    @staticmethod
    def extract_message(
        response: dict,
    ) -> tuple[LLMMessage, str | None]:
        """Validate and extract (message, finish_reason) from an LLM response dict.

        Raises ValueError when the response is missing expected fields.
        """
        choices = response.get("choices")
        if not choices or not isinstance(choices, list):
            raise ValueError("Unexpected LLM response: missing 'choices' field")
        choice = choices[0]
        message = choice.get("message")
        if not isinstance(message, dict):
            raise ValueError("Unexpected LLM response: missing 'message' field")
        finish_reason: str | None = choice.get("finish_reason")
        return cast(LLMMessage, message), finish_reason
