#!/usr/bin/env python3
"""
llm_client.py
LLM communication layer extracted from REPLAgent.
Handles request/retry, payload building, streaming, and response parsing.
"""

import asyncio
import json
import logging
from collections.abc import Callable
from typing import cast

import httpx
from rag_types import LLMMessage

logger = logging.getLogger(__name__)


class LLMClient:
    """Encapsulates all LLM HTTP communication for REPLAgent.

    Handles exponential-backoff retry, payload construction, SSE streaming,
    and response parsing.  Temperature and max_tokens are set at construction
    time and apply to every call unless overridden inside build_payload.
    """

    def __init__(
        self,
        http: httpx.AsyncClient,
        max_retries: int,
        retry_base_delay: float,
        temperature: float,
        max_tokens: int,
        on_token: Callable[[str], None] | None = None,
    ) -> None:
        self._http = http
        self._max_retries = max_retries
        self._retry_base_delay = retry_base_delay
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._on_token = on_token
        # Cumulative count of retry attempts across all requests in this session
        self.stat_retries: int = 0

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
        raise last_exc  # type: ignore[misc]

    # ── Payload construction ──────────────────────────────────────────────────

    def build_payload(
        self,
        history: list[LLMMessage],
        tool_defs: list[dict],
        stream: bool = False,
    ) -> dict:
        """Build the request payload for a chat completion request.

        Takes history as an explicit parameter so the caller controls which
        history slice is sent (e.g. after compression).
        """
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

    # ── Non-streaming call ────────────────────────────────────────────────────

    async def call(
        self, url: str, history: list[LLMMessage], tool_defs: list[dict]
    ) -> dict:
        """Send conversation history to LLM and return the raw response JSON."""
        resp = await self.request_with_retry(
            url, self.build_payload(history, tool_defs)
        )
        return dict(resp.json())

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
        """Assemble the final response dict from streamed content and tool_call
        deltas, matching the shape returned by call()."""
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

    @staticmethod
    def _parse_sse_line(line: str) -> tuple[str | None, bool]:
        """Parse one SSE data line.

        Returns (payload_str, is_done).
        payload_str is None when the line is not a data line or is unparseable.
        is_done is True when the stream signals [DONE].
        """
        if not line.startswith("data: "):
            return None, False
        payload = line[6:]
        if payload.strip() == "[DONE]":
            return None, True
        return payload, False

    def _process_sse_chunk(
        self,
        chunk: dict,
        content_parts: list[str],
        tool_calls_map: dict[int, dict],
    ) -> str | None:
        """Process one parsed SSE chunk delta; return finish_reason or None.

        Appends content tokens to content_parts, prints them inline, and
        accumulates tool_call deltas into tool_calls_map.
        """
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

    # ── Streaming call ────────────────────────────────────────────────────────

    async def stream(
        self, url: str, history: list[LLMMessage], tool_defs: list[dict]
    ) -> dict:
        """Stream a chat completion via SSE and print content tokens as they arrive.

        Assembles tool_calls deltas by index and returns a response dict in the
        same format as call() so the caller can handle both uniformly.
        Falls back to call() on any streaming error.
        """
        content_parts: list[str] = []
        tool_calls_map: dict[int, dict] = {}
        finish_reason: str | None = None
        try:
            async with self._http.stream(
                "POST",
                url,
                json=self.build_payload(history, tool_defs, stream=True),
            ) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    payload, is_done = self._parse_sse_line(line)
                    if is_done:
                        break
                    if payload is None:
                        continue
                    try:
                        chunk = json.loads(payload)
                    except json.JSONDecodeError:
                        continue
                    reason = self._process_sse_chunk(
                        chunk, content_parts, tool_calls_map
                    )
                    if reason:
                        finish_reason = reason
        except Exception as e:
            logger.warning(f"Streaming failed, retrying without stream: {e}")
            return await self.call(url, history, tool_defs)
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
