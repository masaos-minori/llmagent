#!/usr/bin/env python3
"""scripts/shared/config_utils.py — Typed config value accessors.

Provides helpers for reading typed values from raw config dicts
(e.g. loaded from TOML or JSON) with built-in type validation.

Usage:
    from shared.config_utils import get_str

    auth_token = get_str(config, "auth_token", default="")
"""

from __future__ import annotations

from typing import Any


def get_str(d: dict[str, Any], key: str, default: str = "") -> str:
    """Return d[key] as str, or default if absent/None; raises ValueError on wrong type."""
    v = d.get(key)
    if v is None:
        return default
    if not isinstance(v, str):
        raise ValueError(f"Config key {key!r} must be str, got {type(v).__name__}")
    return v


def get_typed(
    d: dict[str, Any],
    key: str,
    expected_type: type,
    type_label: str,
    default: Any | None = None,
) -> Any:
    """Return ``d[key]``, raising ``ValueError`` if it is not an instance of ``expected_type``.

    ``type_label`` must already include its article, e.g. ``"a list"`` or ``"an integer"``.

    Returns ``default`` when the key is absent or its value is ``None``.
    """
    value = d.get(key)
    if value is None:
        return default
    if not isinstance(value, expected_type):
        raise ValueError(
            f"'{key}' must be {type_label}, got {type(value).__name__}: {value!r}"
        )
    return value
