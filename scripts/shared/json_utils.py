#!/usr/bin/env python3
"""shared/json_utils.py
String-producing JSON serialization helpers.

orjson.dumps() returns bytes; this module provides convenience functions
that return str directly, reducing the chance of bytes/string mistakes.

All functions use orjson for speed and deterministic output (sort_keys=True by default).
"""

from __future__ import annotations

import orjson


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
