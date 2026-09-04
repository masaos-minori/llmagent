#!/usr/bin/env python3
"""scripts/shared/config_utils.py — Typed config value accessors.

Provides helpers for reading typed values from raw config dicts
(e.g. loaded from TOML or JSON) with built-in type validation.

Usage:
    from shared.config_utils import get_str

    auth_token = get_str(config, "auth_token", default="")
"""

from __future__ import annotations

import os
import re
from typing import Any

_ENV_REF_RE = re.compile(r"^\$\{ENV:([A-Za-z_][A-Za-z0-9_]*)\}$")


def resolve_env_ref(value: str) -> str:
    """Resolve a "${ENV:VAR_NAME}" config value to its environment variable.

    Returns `value` unchanged if it does not match the "${ENV:VAR_NAME}"
    pattern. Raises ValueError if the referenced environment variable is
    unset.
    """
    match = _ENV_REF_RE.match(value)
    if match is None:
        return value
    var_name = match.group(1)
    resolved = os.environ.get(var_name)
    if resolved is None:
        raise ValueError(
            f"Config value references environment variable {var_name!r}, "
            "which is not set."
        )
    return resolved


def get_str(d: dict[str, Any], key: str, default: str = "") -> str:
    """Return d[key] as str (resolving "${ENV:VAR_NAME}" references), or
    default if absent/None; raises ValueError on wrong type or an unset
    referenced environment variable."""
    v = d.get(key)
    if v is None:
        return default
    if not isinstance(v, str):
        raise ValueError(f"Config key {key!r} must be str, got {type(v).__name__}")
    return resolve_env_ref(v)


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
