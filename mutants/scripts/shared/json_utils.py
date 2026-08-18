#!/usr/bin/env python3
"""scripts/shared/json_utils.py

String-producing JSON serialization helpers.

orjson.dumps() returns bytes; this module provides convenience functions
that return str directly, reducing the chance of bytes/string mistakes.

All functions use orjson for speed and deterministic output (sort_keys=True by default).
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

import orjson

if TYPE_CHECKING:
    from httpx import Response


from mutmut.mutation.trampoline import wrap_in_trampoline as _mutmut_mutated, MutantDict
mutants_x_dumps__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x_dumps__mutmut)
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


def x_dumps__mutmut_orig(obj: object, option: int | None = orjson.OPT_SORT_KEYS) -> str:
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


def x_dumps__mutmut_1(obj: object, option: int | None = orjson.OPT_SORT_KEYS) -> str:
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
    return orjson.dumps(None, option=option).decode()


def x_dumps__mutmut_2(obj: object, option: int | None = orjson.OPT_SORT_KEYS) -> str:
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
    return orjson.dumps(obj, option=None).decode()


def x_dumps__mutmut_3(obj: object, option: int | None = orjson.OPT_SORT_KEYS) -> str:
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
    return orjson.dumps(option=option).decode()


def x_dumps__mutmut_4(obj: object, option: int | None = orjson.OPT_SORT_KEYS) -> str:
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
    return orjson.dumps(obj, ).decode()

mutants_x_dumps__mutmut['_mutmut_orig'] = x_dumps__mutmut_orig # type: ignore # mutmut generated
mutants_x_dumps__mutmut['x_dumps__mutmut_1'] = x_dumps__mutmut_1 # type: ignore # mutmut generated
mutants_x_dumps__mutmut['x_dumps__mutmut_2'] = x_dumps__mutmut_2 # type: ignore # mutmut generated
mutants_x_dumps__mutmut['x_dumps__mutmut_3'] = x_dumps__mutmut_3 # type: ignore # mutmut generated
mutants_x_dumps__mutmut['x_dumps__mutmut_4'] = x_dumps__mutmut_4 # type: ignore # mutmut generated
mutants_x_now_iso__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x_now_iso__mutmut)
def now_iso() -> str:
    """Return current time as ISO 8601 string: YYYY-MM-DDTHH:MM:SSZ.

    Wrapper around datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ") that
    centralizes the format so it cannot drift across the codebase.
    """
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def x_now_iso__mutmut_orig() -> str:
    """Return current time as ISO 8601 string: YYYY-MM-DDTHH:MM:SSZ.

    Wrapper around datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ") that
    centralizes the format so it cannot drift across the codebase.
    """
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def x_now_iso__mutmut_1() -> str:
    """Return current time as ISO 8601 string: YYYY-MM-DDTHH:MM:SSZ.

    Wrapper around datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ") that
    centralizes the format so it cannot drift across the codebase.
    """
    return datetime.now(UTC).strftime(None)


def x_now_iso__mutmut_2() -> str:
    """Return current time as ISO 8601 string: YYYY-MM-DDTHH:MM:SSZ.

    Wrapper around datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ") that
    centralizes the format so it cannot drift across the codebase.
    """
    return datetime.now(None).strftime("%Y-%m-%dT%H:%M:%SZ")


def x_now_iso__mutmut_3() -> str:
    """Return current time as ISO 8601 string: YYYY-MM-DDTHH:MM:SSZ.

    Wrapper around datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ") that
    centralizes the format so it cannot drift across the codebase.
    """
    return datetime.now(UTC).strftime("XX%Y-%m-%dT%H:%M:%SZXX")


def x_now_iso__mutmut_4() -> str:
    """Return current time as ISO 8601 string: YYYY-MM-DDTHH:MM:SSZ.

    Wrapper around datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ") that
    centralizes the format so it cannot drift across the codebase.
    """
    return datetime.now(UTC).strftime("%y-%m-%dt%h:%m:%sz")


def x_now_iso__mutmut_5() -> str:
    """Return current time as ISO 8601 string: YYYY-MM-DDTHH:MM:SSZ.

    Wrapper around datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ") that
    centralizes the format so it cannot drift across the codebase.
    """
    return datetime.now(UTC).strftime("%Y-%M-%DT%H:%M:%SZ")

mutants_x_now_iso__mutmut['_mutmut_orig'] = x_now_iso__mutmut_orig # type: ignore # mutmut generated
mutants_x_now_iso__mutmut['x_now_iso__mutmut_1'] = x_now_iso__mutmut_1 # type: ignore # mutmut generated
mutants_x_now_iso__mutmut['x_now_iso__mutmut_2'] = x_now_iso__mutmut_2 # type: ignore # mutmut generated
mutants_x_now_iso__mutmut['x_now_iso__mutmut_3'] = x_now_iso__mutmut_3 # type: ignore # mutmut generated
mutants_x_now_iso__mutmut['x_now_iso__mutmut_4'] = x_now_iso__mutmut_4 # type: ignore # mutmut generated
mutants_x_now_iso__mutmut['x_now_iso__mutmut_5'] = x_now_iso__mutmut_5 # type: ignore # mutmut generated
mutants_x_now_iso_raw__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x_now_iso_raw__mutmut)
def now_iso_raw() -> str:
    """Return current time as ISO 8601 string via datetime.isoformat().

    Wrapper around datetime.now(UTC).isoformat() that centralizes the call
    so it cannot drift across the codebase. Produces output like
    '2026-07-13T12:00:00+00:00'.
    """
    return datetime.now(UTC).isoformat()


def x_now_iso_raw__mutmut_orig() -> str:
    """Return current time as ISO 8601 string via datetime.isoformat().

    Wrapper around datetime.now(UTC).isoformat() that centralizes the call
    so it cannot drift across the codebase. Produces output like
    '2026-07-13T12:00:00+00:00'.
    """
    return datetime.now(UTC).isoformat()


def x_now_iso_raw__mutmut_1() -> str:
    """Return current time as ISO 8601 string via datetime.isoformat().

    Wrapper around datetime.now(UTC).isoformat() that centralizes the call
    so it cannot drift across the codebase. Produces output like
    '2026-07-13T12:00:00+00:00'.
    """
    return datetime.now(None).isoformat()

mutants_x_now_iso_raw__mutmut['_mutmut_orig'] = x_now_iso_raw__mutmut_orig # type: ignore # mutmut generated
mutants_x_now_iso_raw__mutmut['x_now_iso_raw__mutmut_1'] = x_now_iso_raw__mutmut_1 # type: ignore # mutmut generated


def serialized_length(obj: object) -> int:
    """Return the byte length of obj when serialized to JSON.

    Wrapper around ``len(orjson.dumps(obj))`` that centralizes the serialization
    so it cannot drift across the codebase.
    """
    return len(orjson.dumps(obj))
mutants_x_tool_call_serialized_length__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x_tool_call_serialized_length__mutmut)
def tool_call_serialized_length(tool_call: object) -> int:
    """Return the byte length of a tool call dict when serialized to JSON.

    Delegates to :func:`serialized_length`, which centralizes the
    serialization so it cannot drift across the codebase.
    """
    return serialized_length(tool_call)


def x_tool_call_serialized_length__mutmut_orig(tool_call: object) -> int:
    """Return the byte length of a tool call dict when serialized to JSON.

    Delegates to :func:`serialized_length`, which centralizes the
    serialization so it cannot drift across the codebase.
    """
    return serialized_length(tool_call)


def x_tool_call_serialized_length__mutmut_1(tool_call: object) -> int:
    """Return the byte length of a tool call dict when serialized to JSON.

    Delegates to :func:`serialized_length`, which centralizes the
    serialization so it cannot drift across the codebase.
    """
    return serialized_length(None)

mutants_x_tool_call_serialized_length__mutmut['_mutmut_orig'] = x_tool_call_serialized_length__mutmut_orig # type: ignore # mutmut generated
mutants_x_tool_call_serialized_length__mutmut['x_tool_call_serialized_length__mutmut_1'] = x_tool_call_serialized_length__mutmut_1 # type: ignore # mutmut generated
mutants_x_parse_http_json__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x_parse_http_json__mutmut)
def parse_http_json(resp: Response) -> dict[str, Any]:
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


def x_parse_http_json__mutmut_orig(resp: Response) -> dict[str, Any]:
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


def x_parse_http_json__mutmut_1(resp: Response) -> dict[str, Any]:
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
        data = None
    except orjson.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON dict, got {type(data).__name__}: {data!r}")
    return data


def x_parse_http_json__mutmut_2(resp: Response) -> dict[str, Any]:
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
        data = orjson.loads(None)
    except orjson.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON dict, got {type(data).__name__}: {data!r}")
    return data


def x_parse_http_json__mutmut_3(resp: Response) -> dict[str, Any]:
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
        raise ValueError(None) from exc
    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON dict, got {type(data).__name__}: {data!r}")
    return data


def x_parse_http_json__mutmut_4(resp: Response) -> dict[str, Any]:
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
    if isinstance(data, dict):
        raise ValueError(f"Expected JSON dict, got {type(data).__name__}: {data!r}")
    return data


def x_parse_http_json__mutmut_5(resp: Response) -> dict[str, Any]:
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
        raise ValueError(None)
    return data


def x_parse_http_json__mutmut_6(resp: Response) -> dict[str, Any]:
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
        raise ValueError(f"Expected JSON dict, got {type(None).__name__}: {data!r}")
    return data

mutants_x_parse_http_json__mutmut['_mutmut_orig'] = x_parse_http_json__mutmut_orig # type: ignore # mutmut generated
mutants_x_parse_http_json__mutmut['x_parse_http_json__mutmut_1'] = x_parse_http_json__mutmut_1 # type: ignore # mutmut generated
mutants_x_parse_http_json__mutmut['x_parse_http_json__mutmut_2'] = x_parse_http_json__mutmut_2 # type: ignore # mutmut generated
mutants_x_parse_http_json__mutmut['x_parse_http_json__mutmut_3'] = x_parse_http_json__mutmut_3 # type: ignore # mutmut generated
mutants_x_parse_http_json__mutmut['x_parse_http_json__mutmut_4'] = x_parse_http_json__mutmut_4 # type: ignore # mutmut generated
mutants_x_parse_http_json__mutmut['x_parse_http_json__mutmut_5'] = x_parse_http_json__mutmut_5 # type: ignore # mutmut generated
mutants_x_parse_http_json__mutmut['x_parse_http_json__mutmut_6'] = x_parse_http_json__mutmut_6 # type: ignore # mutmut generated
mutants_x_extract_llm_content__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x_extract_llm_content__mutmut)
def extract_llm_content(data: dict[str, Any]) -> str:
    """Extract and validate content text from an OpenAI-compatible chat completion response.

    Validates the nested structure: choices → choices[0] → message → content.

    Empty string content is valid input — the function returns ``""`` (stripped empty
    string), not ``None``. Callers should check for empty content if they consider it
    an error condition.

    Args:
        data: Raw LLM response dict.

    Returns:
        Stripped content string. May be empty if the API returned empty content.

    Raises:
        ValueError: If the response is malformed, missing expected fields, or
            ``content`` is not a string type (e.g., null).
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


def x_extract_llm_content__mutmut_orig(data: dict[str, Any]) -> str:
    """Extract and validate content text from an OpenAI-compatible chat completion response.

    Validates the nested structure: choices → choices[0] → message → content.

    Empty string content is valid input — the function returns ``""`` (stripped empty
    string), not ``None``. Callers should check for empty content if they consider it
    an error condition.

    Args:
        data: Raw LLM response dict.

    Returns:
        Stripped content string. May be empty if the API returned empty content.

    Raises:
        ValueError: If the response is malformed, missing expected fields, or
            ``content`` is not a string type (e.g., null).
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


def x_extract_llm_content__mutmut_1(data: dict[str, Any]) -> str:
    """Extract and validate content text from an OpenAI-compatible chat completion response.

    Validates the nested structure: choices → choices[0] → message → content.

    Empty string content is valid input — the function returns ``""`` (stripped empty
    string), not ``None``. Callers should check for empty content if they consider it
    an error condition.

    Args:
        data: Raw LLM response dict.

    Returns:
        Stripped content string. May be empty if the API returned empty content.

    Raises:
        ValueError: If the response is malformed, missing expected fields, or
            ``content`` is not a string type (e.g., null).
    """
    choices = None
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


def x_extract_llm_content__mutmut_2(data: dict[str, Any]) -> str:
    """Extract and validate content text from an OpenAI-compatible chat completion response.

    Validates the nested structure: choices → choices[0] → message → content.

    Empty string content is valid input — the function returns ``""`` (stripped empty
    string), not ``None``. Callers should check for empty content if they consider it
    an error condition.

    Args:
        data: Raw LLM response dict.

    Returns:
        Stripped content string. May be empty if the API returned empty content.

    Raises:
        ValueError: If the response is malformed, missing expected fields, or
            ``content`` is not a string type (e.g., null).
    """
    choices = data.get(None)
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


def x_extract_llm_content__mutmut_3(data: dict[str, Any]) -> str:
    """Extract and validate content text from an OpenAI-compatible chat completion response.

    Validates the nested structure: choices → choices[0] → message → content.

    Empty string content is valid input — the function returns ``""`` (stripped empty
    string), not ``None``. Callers should check for empty content if they consider it
    an error condition.

    Args:
        data: Raw LLM response dict.

    Returns:
        Stripped content string. May be empty if the API returned empty content.

    Raises:
        ValueError: If the response is malformed, missing expected fields, or
            ``content`` is not a string type (e.g., null).
    """
    choices = data.get("XXchoicesXX")
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


def x_extract_llm_content__mutmut_4(data: dict[str, Any]) -> str:
    """Extract and validate content text from an OpenAI-compatible chat completion response.

    Validates the nested structure: choices → choices[0] → message → content.

    Empty string content is valid input — the function returns ``""`` (stripped empty
    string), not ``None``. Callers should check for empty content if they consider it
    an error condition.

    Args:
        data: Raw LLM response dict.

    Returns:
        Stripped content string. May be empty if the API returned empty content.

    Raises:
        ValueError: If the response is malformed, missing expected fields, or
            ``content`` is not a string type (e.g., null).
    """
    choices = data.get("CHOICES")
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


def x_extract_llm_content__mutmut_5(data: dict[str, Any]) -> str:
    """Extract and validate content text from an OpenAI-compatible chat completion response.

    Validates the nested structure: choices → choices[0] → message → content.

    Empty string content is valid input — the function returns ``""`` (stripped empty
    string), not ``None``. Callers should check for empty content if they consider it
    an error condition.

    Args:
        data: Raw LLM response dict.

    Returns:
        Stripped content string. May be empty if the API returned empty content.

    Raises:
        ValueError: If the response is malformed, missing expected fields, or
            ``content`` is not a string type (e.g., null).
    """
    choices = data.get("choices")
    if not isinstance(choices, list) and not choices:
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


def x_extract_llm_content__mutmut_6(data: dict[str, Any]) -> str:
    """Extract and validate content text from an OpenAI-compatible chat completion response.

    Validates the nested structure: choices → choices[0] → message → content.

    Empty string content is valid input — the function returns ``""`` (stripped empty
    string), not ``None``. Callers should check for empty content if they consider it
    an error condition.

    Args:
        data: Raw LLM response dict.

    Returns:
        Stripped content string. May be empty if the API returned empty content.

    Raises:
        ValueError: If the response is malformed, missing expected fields, or
            ``content`` is not a string type (e.g., null).
    """
    choices = data.get("choices")
    if isinstance(choices, list) or not choices:
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


def x_extract_llm_content__mutmut_7(data: dict[str, Any]) -> str:
    """Extract and validate content text from an OpenAI-compatible chat completion response.

    Validates the nested structure: choices → choices[0] → message → content.

    Empty string content is valid input — the function returns ``""`` (stripped empty
    string), not ``None``. Callers should check for empty content if they consider it
    an error condition.

    Args:
        data: Raw LLM response dict.

    Returns:
        Stripped content string. May be empty if the API returned empty content.

    Raises:
        ValueError: If the response is malformed, missing expected fields, or
            ``content`` is not a string type (e.g., null).
    """
    choices = data.get("choices")
    if not isinstance(choices, list) or choices:
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


def x_extract_llm_content__mutmut_8(data: dict[str, Any]) -> str:
    """Extract and validate content text from an OpenAI-compatible chat completion response.

    Validates the nested structure: choices → choices[0] → message → content.

    Empty string content is valid input — the function returns ``""`` (stripped empty
    string), not ``None``. Callers should check for empty content if they consider it
    an error condition.

    Args:
        data: Raw LLM response dict.

    Returns:
        Stripped content string. May be empty if the API returned empty content.

    Raises:
        ValueError: If the response is malformed, missing expected fields, or
            ``content`` is not a string type (e.g., null).
    """
    choices = data.get("choices")
    if not isinstance(choices, list) or not choices:
        raise ValueError(None)
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


def x_extract_llm_content__mutmut_9(data: dict[str, Any]) -> str:
    """Extract and validate content text from an OpenAI-compatible chat completion response.

    Validates the nested structure: choices → choices[0] → message → content.

    Empty string content is valid input — the function returns ``""`` (stripped empty
    string), not ``None``. Callers should check for empty content if they consider it
    an error condition.

    Args:
        data: Raw LLM response dict.

    Returns:
        Stripped content string. May be empty if the API returned empty content.

    Raises:
        ValueError: If the response is malformed, missing expected fields, or
            ``content`` is not a string type (e.g., null).
    """
    choices = data.get("choices")
    if not isinstance(choices, list) or not choices:
        raise ValueError("XXMissing or empty 'choices' in LLM responseXX")
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


def x_extract_llm_content__mutmut_10(data: dict[str, Any]) -> str:
    """Extract and validate content text from an OpenAI-compatible chat completion response.

    Validates the nested structure: choices → choices[0] → message → content.

    Empty string content is valid input — the function returns ``""`` (stripped empty
    string), not ``None``. Callers should check for empty content if they consider it
    an error condition.

    Args:
        data: Raw LLM response dict.

    Returns:
        Stripped content string. May be empty if the API returned empty content.

    Raises:
        ValueError: If the response is malformed, missing expected fields, or
            ``content`` is not a string type (e.g., null).
    """
    choices = data.get("choices")
    if not isinstance(choices, list) or not choices:
        raise ValueError("missing or empty 'choices' in llm response")
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


def x_extract_llm_content__mutmut_11(data: dict[str, Any]) -> str:
    """Extract and validate content text from an OpenAI-compatible chat completion response.

    Validates the nested structure: choices → choices[0] → message → content.

    Empty string content is valid input — the function returns ``""`` (stripped empty
    string), not ``None``. Callers should check for empty content if they consider it
    an error condition.

    Args:
        data: Raw LLM response dict.

    Returns:
        Stripped content string. May be empty if the API returned empty content.

    Raises:
        ValueError: If the response is malformed, missing expected fields, or
            ``content`` is not a string type (e.g., null).
    """
    choices = data.get("choices")
    if not isinstance(choices, list) or not choices:
        raise ValueError("MISSING OR EMPTY 'CHOICES' IN LLM RESPONSE")
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


def x_extract_llm_content__mutmut_12(data: dict[str, Any]) -> str:
    """Extract and validate content text from an OpenAI-compatible chat completion response.

    Validates the nested structure: choices → choices[0] → message → content.

    Empty string content is valid input — the function returns ``""`` (stripped empty
    string), not ``None``. Callers should check for empty content if they consider it
    an error condition.

    Args:
        data: Raw LLM response dict.

    Returns:
        Stripped content string. May be empty if the API returned empty content.

    Raises:
        ValueError: If the response is malformed, missing expected fields, or
            ``content`` is not a string type (e.g., null).
    """
    choices = data.get("choices")
    if not isinstance(choices, list) or not choices:
        raise ValueError("Missing or empty 'choices' in LLM response")
    first = None
    if not isinstance(first, dict):
        raise ValueError("choices[0] is not a dict")
    message = first.get("message")
    if not isinstance(message, dict):
        raise ValueError("choices[0].message is not a dict")
    content = message.get("content")
    if not isinstance(content, str):
        raise ValueError(f"content is not a str, got {type(content).__name__}")
    return content.strip()


def x_extract_llm_content__mutmut_13(data: dict[str, Any]) -> str:
    """Extract and validate content text from an OpenAI-compatible chat completion response.

    Validates the nested structure: choices → choices[0] → message → content.

    Empty string content is valid input — the function returns ``""`` (stripped empty
    string), not ``None``. Callers should check for empty content if they consider it
    an error condition.

    Args:
        data: Raw LLM response dict.

    Returns:
        Stripped content string. May be empty if the API returned empty content.

    Raises:
        ValueError: If the response is malformed, missing expected fields, or
            ``content`` is not a string type (e.g., null).
    """
    choices = data.get("choices")
    if not isinstance(choices, list) or not choices:
        raise ValueError("Missing or empty 'choices' in LLM response")
    first = choices[1]
    if not isinstance(first, dict):
        raise ValueError("choices[0] is not a dict")
    message = first.get("message")
    if not isinstance(message, dict):
        raise ValueError("choices[0].message is not a dict")
    content = message.get("content")
    if not isinstance(content, str):
        raise ValueError(f"content is not a str, got {type(content).__name__}")
    return content.strip()


def x_extract_llm_content__mutmut_14(data: dict[str, Any]) -> str:
    """Extract and validate content text from an OpenAI-compatible chat completion response.

    Validates the nested structure: choices → choices[0] → message → content.

    Empty string content is valid input — the function returns ``""`` (stripped empty
    string), not ``None``. Callers should check for empty content if they consider it
    an error condition.

    Args:
        data: Raw LLM response dict.

    Returns:
        Stripped content string. May be empty if the API returned empty content.

    Raises:
        ValueError: If the response is malformed, missing expected fields, or
            ``content`` is not a string type (e.g., null).
    """
    choices = data.get("choices")
    if not isinstance(choices, list) or not choices:
        raise ValueError("Missing or empty 'choices' in LLM response")
    first = choices[0]
    if isinstance(first, dict):
        raise ValueError("choices[0] is not a dict")
    message = first.get("message")
    if not isinstance(message, dict):
        raise ValueError("choices[0].message is not a dict")
    content = message.get("content")
    if not isinstance(content, str):
        raise ValueError(f"content is not a str, got {type(content).__name__}")
    return content.strip()


def x_extract_llm_content__mutmut_15(data: dict[str, Any]) -> str:
    """Extract and validate content text from an OpenAI-compatible chat completion response.

    Validates the nested structure: choices → choices[0] → message → content.

    Empty string content is valid input — the function returns ``""`` (stripped empty
    string), not ``None``. Callers should check for empty content if they consider it
    an error condition.

    Args:
        data: Raw LLM response dict.

    Returns:
        Stripped content string. May be empty if the API returned empty content.

    Raises:
        ValueError: If the response is malformed, missing expected fields, or
            ``content`` is not a string type (e.g., null).
    """
    choices = data.get("choices")
    if not isinstance(choices, list) or not choices:
        raise ValueError("Missing or empty 'choices' in LLM response")
    first = choices[0]
    if not isinstance(first, dict):
        raise ValueError(None)
    message = first.get("message")
    if not isinstance(message, dict):
        raise ValueError("choices[0].message is not a dict")
    content = message.get("content")
    if not isinstance(content, str):
        raise ValueError(f"content is not a str, got {type(content).__name__}")
    return content.strip()


def x_extract_llm_content__mutmut_16(data: dict[str, Any]) -> str:
    """Extract and validate content text from an OpenAI-compatible chat completion response.

    Validates the nested structure: choices → choices[0] → message → content.

    Empty string content is valid input — the function returns ``""`` (stripped empty
    string), not ``None``. Callers should check for empty content if they consider it
    an error condition.

    Args:
        data: Raw LLM response dict.

    Returns:
        Stripped content string. May be empty if the API returned empty content.

    Raises:
        ValueError: If the response is malformed, missing expected fields, or
            ``content`` is not a string type (e.g., null).
    """
    choices = data.get("choices")
    if not isinstance(choices, list) or not choices:
        raise ValueError("Missing or empty 'choices' in LLM response")
    first = choices[0]
    if not isinstance(first, dict):
        raise ValueError("XXchoices[0] is not a dictXX")
    message = first.get("message")
    if not isinstance(message, dict):
        raise ValueError("choices[0].message is not a dict")
    content = message.get("content")
    if not isinstance(content, str):
        raise ValueError(f"content is not a str, got {type(content).__name__}")
    return content.strip()


def x_extract_llm_content__mutmut_17(data: dict[str, Any]) -> str:
    """Extract and validate content text from an OpenAI-compatible chat completion response.

    Validates the nested structure: choices → choices[0] → message → content.

    Empty string content is valid input — the function returns ``""`` (stripped empty
    string), not ``None``. Callers should check for empty content if they consider it
    an error condition.

    Args:
        data: Raw LLM response dict.

    Returns:
        Stripped content string. May be empty if the API returned empty content.

    Raises:
        ValueError: If the response is malformed, missing expected fields, or
            ``content`` is not a string type (e.g., null).
    """
    choices = data.get("choices")
    if not isinstance(choices, list) or not choices:
        raise ValueError("Missing or empty 'choices' in LLM response")
    first = choices[0]
    if not isinstance(first, dict):
        raise ValueError("CHOICES[0] IS NOT A DICT")
    message = first.get("message")
    if not isinstance(message, dict):
        raise ValueError("choices[0].message is not a dict")
    content = message.get("content")
    if not isinstance(content, str):
        raise ValueError(f"content is not a str, got {type(content).__name__}")
    return content.strip()


def x_extract_llm_content__mutmut_18(data: dict[str, Any]) -> str:
    """Extract and validate content text from an OpenAI-compatible chat completion response.

    Validates the nested structure: choices → choices[0] → message → content.

    Empty string content is valid input — the function returns ``""`` (stripped empty
    string), not ``None``. Callers should check for empty content if they consider it
    an error condition.

    Args:
        data: Raw LLM response dict.

    Returns:
        Stripped content string. May be empty if the API returned empty content.

    Raises:
        ValueError: If the response is malformed, missing expected fields, or
            ``content`` is not a string type (e.g., null).
    """
    choices = data.get("choices")
    if not isinstance(choices, list) or not choices:
        raise ValueError("Missing or empty 'choices' in LLM response")
    first = choices[0]
    if not isinstance(first, dict):
        raise ValueError("choices[0] is not a dict")
    message = None
    if not isinstance(message, dict):
        raise ValueError("choices[0].message is not a dict")
    content = message.get("content")
    if not isinstance(content, str):
        raise ValueError(f"content is not a str, got {type(content).__name__}")
    return content.strip()


def x_extract_llm_content__mutmut_19(data: dict[str, Any]) -> str:
    """Extract and validate content text from an OpenAI-compatible chat completion response.

    Validates the nested structure: choices → choices[0] → message → content.

    Empty string content is valid input — the function returns ``""`` (stripped empty
    string), not ``None``. Callers should check for empty content if they consider it
    an error condition.

    Args:
        data: Raw LLM response dict.

    Returns:
        Stripped content string. May be empty if the API returned empty content.

    Raises:
        ValueError: If the response is malformed, missing expected fields, or
            ``content`` is not a string type (e.g., null).
    """
    choices = data.get("choices")
    if not isinstance(choices, list) or not choices:
        raise ValueError("Missing or empty 'choices' in LLM response")
    first = choices[0]
    if not isinstance(first, dict):
        raise ValueError("choices[0] is not a dict")
    message = first.get(None)
    if not isinstance(message, dict):
        raise ValueError("choices[0].message is not a dict")
    content = message.get("content")
    if not isinstance(content, str):
        raise ValueError(f"content is not a str, got {type(content).__name__}")
    return content.strip()


def x_extract_llm_content__mutmut_20(data: dict[str, Any]) -> str:
    """Extract and validate content text from an OpenAI-compatible chat completion response.

    Validates the nested structure: choices → choices[0] → message → content.

    Empty string content is valid input — the function returns ``""`` (stripped empty
    string), not ``None``. Callers should check for empty content if they consider it
    an error condition.

    Args:
        data: Raw LLM response dict.

    Returns:
        Stripped content string. May be empty if the API returned empty content.

    Raises:
        ValueError: If the response is malformed, missing expected fields, or
            ``content`` is not a string type (e.g., null).
    """
    choices = data.get("choices")
    if not isinstance(choices, list) or not choices:
        raise ValueError("Missing or empty 'choices' in LLM response")
    first = choices[0]
    if not isinstance(first, dict):
        raise ValueError("choices[0] is not a dict")
    message = first.get("XXmessageXX")
    if not isinstance(message, dict):
        raise ValueError("choices[0].message is not a dict")
    content = message.get("content")
    if not isinstance(content, str):
        raise ValueError(f"content is not a str, got {type(content).__name__}")
    return content.strip()


def x_extract_llm_content__mutmut_21(data: dict[str, Any]) -> str:
    """Extract and validate content text from an OpenAI-compatible chat completion response.

    Validates the nested structure: choices → choices[0] → message → content.

    Empty string content is valid input — the function returns ``""`` (stripped empty
    string), not ``None``. Callers should check for empty content if they consider it
    an error condition.

    Args:
        data: Raw LLM response dict.

    Returns:
        Stripped content string. May be empty if the API returned empty content.

    Raises:
        ValueError: If the response is malformed, missing expected fields, or
            ``content`` is not a string type (e.g., null).
    """
    choices = data.get("choices")
    if not isinstance(choices, list) or not choices:
        raise ValueError("Missing or empty 'choices' in LLM response")
    first = choices[0]
    if not isinstance(first, dict):
        raise ValueError("choices[0] is not a dict")
    message = first.get("MESSAGE")
    if not isinstance(message, dict):
        raise ValueError("choices[0].message is not a dict")
    content = message.get("content")
    if not isinstance(content, str):
        raise ValueError(f"content is not a str, got {type(content).__name__}")
    return content.strip()


def x_extract_llm_content__mutmut_22(data: dict[str, Any]) -> str:
    """Extract and validate content text from an OpenAI-compatible chat completion response.

    Validates the nested structure: choices → choices[0] → message → content.

    Empty string content is valid input — the function returns ``""`` (stripped empty
    string), not ``None``. Callers should check for empty content if they consider it
    an error condition.

    Args:
        data: Raw LLM response dict.

    Returns:
        Stripped content string. May be empty if the API returned empty content.

    Raises:
        ValueError: If the response is malformed, missing expected fields, or
            ``content`` is not a string type (e.g., null).
    """
    choices = data.get("choices")
    if not isinstance(choices, list) or not choices:
        raise ValueError("Missing or empty 'choices' in LLM response")
    first = choices[0]
    if not isinstance(first, dict):
        raise ValueError("choices[0] is not a dict")
    message = first.get("message")
    if isinstance(message, dict):
        raise ValueError("choices[0].message is not a dict")
    content = message.get("content")
    if not isinstance(content, str):
        raise ValueError(f"content is not a str, got {type(content).__name__}")
    return content.strip()


def x_extract_llm_content__mutmut_23(data: dict[str, Any]) -> str:
    """Extract and validate content text from an OpenAI-compatible chat completion response.

    Validates the nested structure: choices → choices[0] → message → content.

    Empty string content is valid input — the function returns ``""`` (stripped empty
    string), not ``None``. Callers should check for empty content if they consider it
    an error condition.

    Args:
        data: Raw LLM response dict.

    Returns:
        Stripped content string. May be empty if the API returned empty content.

    Raises:
        ValueError: If the response is malformed, missing expected fields, or
            ``content`` is not a string type (e.g., null).
    """
    choices = data.get("choices")
    if not isinstance(choices, list) or not choices:
        raise ValueError("Missing or empty 'choices' in LLM response")
    first = choices[0]
    if not isinstance(first, dict):
        raise ValueError("choices[0] is not a dict")
    message = first.get("message")
    if not isinstance(message, dict):
        raise ValueError(None)
    content = message.get("content")
    if not isinstance(content, str):
        raise ValueError(f"content is not a str, got {type(content).__name__}")
    return content.strip()


def x_extract_llm_content__mutmut_24(data: dict[str, Any]) -> str:
    """Extract and validate content text from an OpenAI-compatible chat completion response.

    Validates the nested structure: choices → choices[0] → message → content.

    Empty string content is valid input — the function returns ``""`` (stripped empty
    string), not ``None``. Callers should check for empty content if they consider it
    an error condition.

    Args:
        data: Raw LLM response dict.

    Returns:
        Stripped content string. May be empty if the API returned empty content.

    Raises:
        ValueError: If the response is malformed, missing expected fields, or
            ``content`` is not a string type (e.g., null).
    """
    choices = data.get("choices")
    if not isinstance(choices, list) or not choices:
        raise ValueError("Missing or empty 'choices' in LLM response")
    first = choices[0]
    if not isinstance(first, dict):
        raise ValueError("choices[0] is not a dict")
    message = first.get("message")
    if not isinstance(message, dict):
        raise ValueError("XXchoices[0].message is not a dictXX")
    content = message.get("content")
    if not isinstance(content, str):
        raise ValueError(f"content is not a str, got {type(content).__name__}")
    return content.strip()


def x_extract_llm_content__mutmut_25(data: dict[str, Any]) -> str:
    """Extract and validate content text from an OpenAI-compatible chat completion response.

    Validates the nested structure: choices → choices[0] → message → content.

    Empty string content is valid input — the function returns ``""`` (stripped empty
    string), not ``None``. Callers should check for empty content if they consider it
    an error condition.

    Args:
        data: Raw LLM response dict.

    Returns:
        Stripped content string. May be empty if the API returned empty content.

    Raises:
        ValueError: If the response is malformed, missing expected fields, or
            ``content`` is not a string type (e.g., null).
    """
    choices = data.get("choices")
    if not isinstance(choices, list) or not choices:
        raise ValueError("Missing or empty 'choices' in LLM response")
    first = choices[0]
    if not isinstance(first, dict):
        raise ValueError("choices[0] is not a dict")
    message = first.get("message")
    if not isinstance(message, dict):
        raise ValueError("CHOICES[0].MESSAGE IS NOT A DICT")
    content = message.get("content")
    if not isinstance(content, str):
        raise ValueError(f"content is not a str, got {type(content).__name__}")
    return content.strip()


def x_extract_llm_content__mutmut_26(data: dict[str, Any]) -> str:
    """Extract and validate content text from an OpenAI-compatible chat completion response.

    Validates the nested structure: choices → choices[0] → message → content.

    Empty string content is valid input — the function returns ``""`` (stripped empty
    string), not ``None``. Callers should check for empty content if they consider it
    an error condition.

    Args:
        data: Raw LLM response dict.

    Returns:
        Stripped content string. May be empty if the API returned empty content.

    Raises:
        ValueError: If the response is malformed, missing expected fields, or
            ``content`` is not a string type (e.g., null).
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
    content = None
    if not isinstance(content, str):
        raise ValueError(f"content is not a str, got {type(content).__name__}")
    return content.strip()


def x_extract_llm_content__mutmut_27(data: dict[str, Any]) -> str:
    """Extract and validate content text from an OpenAI-compatible chat completion response.

    Validates the nested structure: choices → choices[0] → message → content.

    Empty string content is valid input — the function returns ``""`` (stripped empty
    string), not ``None``. Callers should check for empty content if they consider it
    an error condition.

    Args:
        data: Raw LLM response dict.

    Returns:
        Stripped content string. May be empty if the API returned empty content.

    Raises:
        ValueError: If the response is malformed, missing expected fields, or
            ``content`` is not a string type (e.g., null).
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
    content = message.get(None)
    if not isinstance(content, str):
        raise ValueError(f"content is not a str, got {type(content).__name__}")
    return content.strip()


def x_extract_llm_content__mutmut_28(data: dict[str, Any]) -> str:
    """Extract and validate content text from an OpenAI-compatible chat completion response.

    Validates the nested structure: choices → choices[0] → message → content.

    Empty string content is valid input — the function returns ``""`` (stripped empty
    string), not ``None``. Callers should check for empty content if they consider it
    an error condition.

    Args:
        data: Raw LLM response dict.

    Returns:
        Stripped content string. May be empty if the API returned empty content.

    Raises:
        ValueError: If the response is malformed, missing expected fields, or
            ``content`` is not a string type (e.g., null).
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
    content = message.get("XXcontentXX")
    if not isinstance(content, str):
        raise ValueError(f"content is not a str, got {type(content).__name__}")
    return content.strip()


def x_extract_llm_content__mutmut_29(data: dict[str, Any]) -> str:
    """Extract and validate content text from an OpenAI-compatible chat completion response.

    Validates the nested structure: choices → choices[0] → message → content.

    Empty string content is valid input — the function returns ``""`` (stripped empty
    string), not ``None``. Callers should check for empty content if they consider it
    an error condition.

    Args:
        data: Raw LLM response dict.

    Returns:
        Stripped content string. May be empty if the API returned empty content.

    Raises:
        ValueError: If the response is malformed, missing expected fields, or
            ``content`` is not a string type (e.g., null).
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
    content = message.get("CONTENT")
    if not isinstance(content, str):
        raise ValueError(f"content is not a str, got {type(content).__name__}")
    return content.strip()


def x_extract_llm_content__mutmut_30(data: dict[str, Any]) -> str:
    """Extract and validate content text from an OpenAI-compatible chat completion response.

    Validates the nested structure: choices → choices[0] → message → content.

    Empty string content is valid input — the function returns ``""`` (stripped empty
    string), not ``None``. Callers should check for empty content if they consider it
    an error condition.

    Args:
        data: Raw LLM response dict.

    Returns:
        Stripped content string. May be empty if the API returned empty content.

    Raises:
        ValueError: If the response is malformed, missing expected fields, or
            ``content`` is not a string type (e.g., null).
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
    if isinstance(content, str):
        raise ValueError(f"content is not a str, got {type(content).__name__}")
    return content.strip()


def x_extract_llm_content__mutmut_31(data: dict[str, Any]) -> str:
    """Extract and validate content text from an OpenAI-compatible chat completion response.

    Validates the nested structure: choices → choices[0] → message → content.

    Empty string content is valid input — the function returns ``""`` (stripped empty
    string), not ``None``. Callers should check for empty content if they consider it
    an error condition.

    Args:
        data: Raw LLM response dict.

    Returns:
        Stripped content string. May be empty if the API returned empty content.

    Raises:
        ValueError: If the response is malformed, missing expected fields, or
            ``content`` is not a string type (e.g., null).
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
        raise ValueError(None)
    return content.strip()


def x_extract_llm_content__mutmut_32(data: dict[str, Any]) -> str:
    """Extract and validate content text from an OpenAI-compatible chat completion response.

    Validates the nested structure: choices → choices[0] → message → content.

    Empty string content is valid input — the function returns ``""`` (stripped empty
    string), not ``None``. Callers should check for empty content if they consider it
    an error condition.

    Args:
        data: Raw LLM response dict.

    Returns:
        Stripped content string. May be empty if the API returned empty content.

    Raises:
        ValueError: If the response is malformed, missing expected fields, or
            ``content`` is not a string type (e.g., null).
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
        raise ValueError(f"content is not a str, got {type(None).__name__}")
    return content.strip()

mutants_x_extract_llm_content__mutmut['_mutmut_orig'] = x_extract_llm_content__mutmut_orig # type: ignore # mutmut generated
mutants_x_extract_llm_content__mutmut['x_extract_llm_content__mutmut_1'] = x_extract_llm_content__mutmut_1 # type: ignore # mutmut generated
mutants_x_extract_llm_content__mutmut['x_extract_llm_content__mutmut_2'] = x_extract_llm_content__mutmut_2 # type: ignore # mutmut generated
mutants_x_extract_llm_content__mutmut['x_extract_llm_content__mutmut_3'] = x_extract_llm_content__mutmut_3 # type: ignore # mutmut generated
mutants_x_extract_llm_content__mutmut['x_extract_llm_content__mutmut_4'] = x_extract_llm_content__mutmut_4 # type: ignore # mutmut generated
mutants_x_extract_llm_content__mutmut['x_extract_llm_content__mutmut_5'] = x_extract_llm_content__mutmut_5 # type: ignore # mutmut generated
mutants_x_extract_llm_content__mutmut['x_extract_llm_content__mutmut_6'] = x_extract_llm_content__mutmut_6 # type: ignore # mutmut generated
mutants_x_extract_llm_content__mutmut['x_extract_llm_content__mutmut_7'] = x_extract_llm_content__mutmut_7 # type: ignore # mutmut generated
mutants_x_extract_llm_content__mutmut['x_extract_llm_content__mutmut_8'] = x_extract_llm_content__mutmut_8 # type: ignore # mutmut generated
mutants_x_extract_llm_content__mutmut['x_extract_llm_content__mutmut_9'] = x_extract_llm_content__mutmut_9 # type: ignore # mutmut generated
mutants_x_extract_llm_content__mutmut['x_extract_llm_content__mutmut_10'] = x_extract_llm_content__mutmut_10 # type: ignore # mutmut generated
mutants_x_extract_llm_content__mutmut['x_extract_llm_content__mutmut_11'] = x_extract_llm_content__mutmut_11 # type: ignore # mutmut generated
mutants_x_extract_llm_content__mutmut['x_extract_llm_content__mutmut_12'] = x_extract_llm_content__mutmut_12 # type: ignore # mutmut generated
mutants_x_extract_llm_content__mutmut['x_extract_llm_content__mutmut_13'] = x_extract_llm_content__mutmut_13 # type: ignore # mutmut generated
mutants_x_extract_llm_content__mutmut['x_extract_llm_content__mutmut_14'] = x_extract_llm_content__mutmut_14 # type: ignore # mutmut generated
mutants_x_extract_llm_content__mutmut['x_extract_llm_content__mutmut_15'] = x_extract_llm_content__mutmut_15 # type: ignore # mutmut generated
mutants_x_extract_llm_content__mutmut['x_extract_llm_content__mutmut_16'] = x_extract_llm_content__mutmut_16 # type: ignore # mutmut generated
mutants_x_extract_llm_content__mutmut['x_extract_llm_content__mutmut_17'] = x_extract_llm_content__mutmut_17 # type: ignore # mutmut generated
mutants_x_extract_llm_content__mutmut['x_extract_llm_content__mutmut_18'] = x_extract_llm_content__mutmut_18 # type: ignore # mutmut generated
mutants_x_extract_llm_content__mutmut['x_extract_llm_content__mutmut_19'] = x_extract_llm_content__mutmut_19 # type: ignore # mutmut generated
mutants_x_extract_llm_content__mutmut['x_extract_llm_content__mutmut_20'] = x_extract_llm_content__mutmut_20 # type: ignore # mutmut generated
mutants_x_extract_llm_content__mutmut['x_extract_llm_content__mutmut_21'] = x_extract_llm_content__mutmut_21 # type: ignore # mutmut generated
mutants_x_extract_llm_content__mutmut['x_extract_llm_content__mutmut_22'] = x_extract_llm_content__mutmut_22 # type: ignore # mutmut generated
mutants_x_extract_llm_content__mutmut['x_extract_llm_content__mutmut_23'] = x_extract_llm_content__mutmut_23 # type: ignore # mutmut generated
mutants_x_extract_llm_content__mutmut['x_extract_llm_content__mutmut_24'] = x_extract_llm_content__mutmut_24 # type: ignore # mutmut generated
mutants_x_extract_llm_content__mutmut['x_extract_llm_content__mutmut_25'] = x_extract_llm_content__mutmut_25 # type: ignore # mutmut generated
mutants_x_extract_llm_content__mutmut['x_extract_llm_content__mutmut_26'] = x_extract_llm_content__mutmut_26 # type: ignore # mutmut generated
mutants_x_extract_llm_content__mutmut['x_extract_llm_content__mutmut_27'] = x_extract_llm_content__mutmut_27 # type: ignore # mutmut generated
mutants_x_extract_llm_content__mutmut['x_extract_llm_content__mutmut_28'] = x_extract_llm_content__mutmut_28 # type: ignore # mutmut generated
mutants_x_extract_llm_content__mutmut['x_extract_llm_content__mutmut_29'] = x_extract_llm_content__mutmut_29 # type: ignore # mutmut generated
mutants_x_extract_llm_content__mutmut['x_extract_llm_content__mutmut_30'] = x_extract_llm_content__mutmut_30 # type: ignore # mutmut generated
mutants_x_extract_llm_content__mutmut['x_extract_llm_content__mutmut_31'] = x_extract_llm_content__mutmut_31 # type: ignore # mutmut generated
mutants_x_extract_llm_content__mutmut['x_extract_llm_content__mutmut_32'] = x_extract_llm_content__mutmut_32 # type: ignore # mutmut generated
