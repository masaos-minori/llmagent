#!/usr/bin/env python3
"""shared/sse_parser.py
Stateful SSE parser for LLM streaming responses.

Provides:
  RobustSSEParser — incremental UTF-8 decoder + heartbeat tracking + malformed frame budget
  _anext_or_done  — async iterator helper to prevent PEP 479 RuntimeError
"""

from __future__ import annotations

import codecs
import time
from collections.abc import AsyncIterator

import orjson
from shared.llm_exceptions import LLMTransportError


class RobustSSEParser:
    """Stateful SSE parser: incremental UTF-8 decoder + heartbeat tracking + malformed frame budget; one instance per connection."""

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
        """Decode raw bytes and extract complete SSE data payloads; returns (payloads, is_done); raises MALFORMED_SSE_FRAME after malformed budget exhausted."""
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
        """Parse one SSE text line; returns None to skip, (None, True) for [DONE], (payload_str, False) for valid data; raises MALFORMED_SSE_FRAME on budget exhaustion."""
        if self._is_keepalive(line):
            return None
        if not line.startswith("data:"):
            return None
        payload = line[5:].lstrip(" ")
        if payload.strip() == "[DONE]":
            self._last_event_at = time.monotonic()
            return None, True
        if not self._is_valid_json(payload):
            return None
        self._last_event_at = time.monotonic()
        return payload, False

    def _is_keepalive(self, line: str) -> bool:
        """Return True for blank lines and SSE comments (keepalive)."""
        if not line:
            self._last_event_at = time.monotonic()
            return True
        if line.startswith(":"):
            self._last_event_at = time.monotonic()
            return True
        return False

    def _is_valid_json(self, payload: str) -> bool:
        """Validate that payload is valid JSON; track malformed count."""
        try:
            orjson.loads(payload)
            return True
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
            return False

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


async def _anext_or_done(aiter: AsyncIterator[bytes]) -> tuple[bytes, bool]:
    """Await one item from an async bytes iterator; returns (item, False) on success or (b"", True) on StopAsyncIteration; prevents PEP 479 RuntimeError in wait_for."""
    try:
        item = await aiter.__anext__()
        return item, False
    except StopAsyncIteration:
        return b"", True
