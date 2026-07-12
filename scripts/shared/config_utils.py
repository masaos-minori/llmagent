#!/usr/bin/env python3
"""shared/config_utils.py — Typed config value accessors.

Provides helpers for reading typed values from raw config dicts
(e.g. loaded from TOML or JSON) with built-in type validation.

Usage:
    from shared.config_utils import get_str

    auth_token = get_str(config, "auth_token", default="")
"""

from __future__ import annotations


def get_str(d: dict[str, object], key: str, default: str = "") -> str:
    """Return d[key] as str, or default if absent/None; raises ValueError on wrong type."""
    v = d.get(key)
    if v is None:
        return default
    if not isinstance(v, str):
        raise ValueError(f"Config key {key!r} must be str, got {type(v).__name__}")
    return v
