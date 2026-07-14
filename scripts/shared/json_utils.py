#!/usr/bin/env python3
"""shared/json_utils.py

String-producing JSON serialization helpers.

orjson.dumps() returns bytes; this module provides convenience functions
that return str directly, reducing the chance of bytes/string mistakes.

All functions use orjson for speed and deterministic output (sort_keys=True by default).
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

import orjson

if TYPE_CHECKING:
    from httpx import Response


def dumps(obj: object, option: int | None = orjson.OPT_SORT_KEYS) -> str:
    """Serialize obj to a JSON string.

    Wrapper around orjson.dumps().decode() that returns str directly.
    Uses sort_keys=True by default for deterministic output.

    Args:
        obj: Object to serialize.
        option: orjson option flags (default: OPT_SORT_KEYS).

    Returns:
        JSON string representation of obj.

    Example:
        >>> dumps({"key": "value"})
        '{"key":"value"}'
        >>> dumps([1, 2, 3], option=orjson.OPT_INDENT_2)
        '[\\n  1,\\n  2,\\n  3\\n]'
    """
    return orjson.dumps(obj, option=option).decode()


def now_iso() -> str:
    """Return current time as ISO 8601 string: YYYY-MM-DDTHH:MM:SSZ.

    Wrapper around datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ") that
    centralizes the format so it cannot drift across the codebase.
    """
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def now_iso_raw() -> str:
    """Return current time as ISO 8601 string via datetime.isoformat().

    Wrapper around datetime.now(UTC).isoformat() that centralizes the call
    so it cannot drift across the codebase. Produces output like
    '2026-07-13T12:00:00+00:00'.
    """
    return datetime.now(UTC).isoformat()


def tool_call_serialized_length(tool_call: object) -> int:
    """Return the byte length of a tool call dict when serialized to JSON.

    Wrapper around ``len(orjson.dumps(tc))`` that centralizes the serialization
    so it cannot drift across the codebase.
    """
    return len(orjson.dumps(tool_call))


def serialized_length(obj: object) -> int:
    """Return the byte length of obj when serialized to JSON.

    Wrapper around ``len(orjson.dumps(obj))`` that centralizes the serialization
    so it cannot drift across the codebase.
    """
    return len(orjson.dumps(obj))


def parse_http_json(resp: Response) -> dict[str, object]:
    """Parse an HTTP response body as JSON and return a dict.

    Wrapper around ``orjson.loads(resp.content)`` that centralizes the
    deserialization so it cannot drift across the codebase.

    Args:
        resp: An object with a ``content`` attribute (e.g. httpx.Response).

    Returns:
        Parsed JSON dict.

    Raises:
        ValueError: If the parsed value is not a dict or the body is invalid JSON.
    """
    try:
        data = orjson.loads(resp.content)
    except orjson.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON dict, got {type(data).__name__}: {data!r}")
    return data


def extract_llm_content(data: dict[str, object]) -> str:
    """Extract and validate content text from an OpenAI-compatible chat completion response.

    Validates the nested structure: choices → choices[0] → message → content.

    Args:
        data: Raw LLM response dict.

    Returns:
        Stripped content string.

    Raises:
        ValueError: If the response is malformed or missing expected fields.
    """
    choices = data.get("choices")
    if not isinstance(choices, list) or not choices:
        raise ValueError("Missing or empty 'choices' in LLM response")
    first = choices[0]
    if not isinstance(first, dict):
        raise ValueError("choices[0] is not a dict")
    message = first.get("message")
    if not isinstance(message, dict):
        raise ValueError("choices[0].message is not a dict")
    content = message.get("content")
    if not isinstance(content, str):
        raise ValueError(f"content is not a str, got {type(content).__name__}")
    return content.strip()
