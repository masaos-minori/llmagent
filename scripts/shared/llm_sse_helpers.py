#!/usr/bin/env python3
"""shared/llm_sse_helpers.py — SSE streaming helper methods for LLMClient."""

from collections.abc import Callable
from typing import Any

import orjson

from shared.llm_types import LLMUsage
from shared.sse_parser import RobustSSEParser
from shared.types import AccumulatedToolCall, ToolCallDelta


class LlmSseHelpers:
    """Static methods for SSE streaming helpers used by LLMClient."""

    @staticmethod
    def merge_tool_call_delta(
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
            tc["id"] = tc_delta.get("id", "")
        fn = tc_delta.get("function")
        if fn is not None:
            tc["function"]["name"] += fn.get("name", "")
            tc["function"]["arguments"] += fn.get("arguments", "")

    @staticmethod
    def build_stream_response(
        content_parts: list[str],
        tool_calls_map: dict[int, AccumulatedToolCall],
        finish_reason: str | None,
    ) -> dict[str, object]:
        """Assemble the final response dict from streamed content and tool_call deltas."""
        content = "".join(content_parts)
        tool_calls = (
            [tool_calls_map[i] for i in sorted(tool_calls_map)]
            if tool_calls_map
            else None
        )
        message: dict[str, object] = {"role": "assistant", "content": content}
        if tool_calls:
            message["tool_calls"] = tool_calls
        return {"choices": [{"message": message, "finish_reason": finish_reason}]}

    @staticmethod
    def process_sse_chunk(
        chunk: dict[str, Any],
        content_parts: list[str],
        tool_calls_map: dict[int, AccumulatedToolCall],
        on_token: Callable[[str], None] | None = None,
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
            if on_token is not None:
                on_token(token)
        for tc_delta in delta.get("tool_calls", []):
            LlmSseHelpers.merge_tool_call_delta(tool_calls_map, tc_delta)
        return finish_reason

    @staticmethod
    def process_sse_payloads(
        payloads: list[str],
        content_parts: list[str],
        tool_calls_map: dict[int, AccumulatedToolCall],
        on_token: Callable[[str], None] | None = None,
        on_usage: Callable[[int, int], None] | None = None,
    ) -> str | None:
        """Parse and process a list of raw SSE payloads; return last finish_reason seen."""
        finish_reason: str | None = None
        for raw_payload in payloads:
            try:
                chunk = orjson.loads(raw_payload)
            except (orjson.JSONDecodeError, ValueError):
                continue
            reason = LlmSseHelpers.process_sse_chunk(
                chunk, content_parts, tool_calls_map, on_token
            )
            if reason:
                finish_reason = reason
            LlmSseHelpers.parse_usage(chunk, on_usage)
        return finish_reason

    @staticmethod
    def parse_usage(
        data: dict[str, Any], on_usage: Callable[[int, int], None] | None = None
    ) -> LLMUsage | None:
        """Extract token usage from response data; fire on_usage callback; return LLMUsage or None."""
        usage_raw = data.get("usage")
        if not isinstance(usage_raw, dict):
            return None
        pt = usage_raw.get("prompt_tokens")
        ct = usage_raw.get("completion_tokens")
        if not isinstance(pt, int) or not isinstance(ct, int):
            return None
        if on_usage is not None:
            on_usage(pt, ct)
        return LLMUsage(prompt_tokens=pt, completion_tokens=ct)

    @staticmethod
    def accumulate_parse_errors(
        parser: RobustSSEParser,
        stat_parse_errors: int,
    ) -> int:
        """Add parse errors to instance stats and reset the parser's counter; return updated count."""
        if parser.stat_parse_errors:
            stat_parse_errors += parser.stat_parse_errors
            parser.stat_parse_errors = 0
        return stat_parse_errors
