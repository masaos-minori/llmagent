#!/usr/bin/env python3
"""shared/llm_payload.py — LLM request/response payload construction."""

from collections.abc import Callable
from typing import Any, cast

import orjson

from shared.llm_sse_helpers import LlmSseHelpers
from shared.llm_types import LLMResponse
from shared.types import LLMMessage


class LlmPayloadHandler:
    """Construct LLM request payloads and parse responses."""

    @staticmethod
    def build_payload(
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
        temperature: float,
        max_tokens: int,
        stream: bool = False,
    ) -> dict[str, Any]:
        """Build the request payload for a chat completion request."""
        payload: dict[str, Any] = {
            "messages": history,
            "tools": tool_defs,
            "tool_choice": "auto",
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if stream:
            payload["stream"] = True
        return payload

    @staticmethod
    def parse_response(
        raw: dict[str, Any],
        on_usage: Callable[[int, int], None] | None = None,
    ) -> LLMResponse:
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
        usage = LlmSseHelpers.parse_usage(raw, on_usage)
        return LLMResponse(
            message=cast(LLMMessage, message_raw),
            finish_reason=finish_reason,
            usage=usage,
        )

    @staticmethod
    def parse_non_stream_response(
        content: bytes, on_usage: Callable[[int, int], None] | None = None
    ) -> LLMResponse:
        """Parse a non-streaming LLM response body into LLMResponse."""
        raw = orjson.loads(content)
        if not isinstance(raw, dict):
            raise ValueError(f"LLM response is not a JSON object: {type(raw).__name__}")
        return LlmPayloadHandler.parse_response(raw, on_usage)
