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


from mutmut.mutation.trampoline import wrap_in_trampoline as _mutmut_mutated, MutantDict
mutants_x_get_str__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x_get_str__mutmut)
def get_str(d: dict[str, Any], key: str, default: str = "") -> str:
    """Return d[key] as str, or default if absent/None; raises ValueError on wrong type."""
    v = d.get(key)
    if v is None:
        return default
    if not isinstance(v, str):
        raise ValueError(f"Config key {key!r} must be str, got {type(v).__name__}")
    return v


def x_get_str__mutmut_orig(d: dict[str, Any], key: str, default: str = "") -> str:
    """Return d[key] as str, or default if absent/None; raises ValueError on wrong type."""
    v = d.get(key)
    if v is None:
        return default
    if not isinstance(v, str):
        raise ValueError(f"Config key {key!r} must be str, got {type(v).__name__}")
    return v


def x_get_str__mutmut_1(d: dict[str, Any], key: str, default: str = "XXXX") -> str:
    """Return d[key] as str, or default if absent/None; raises ValueError on wrong type."""
    v = d.get(key)
    if v is None:
        return default
    if not isinstance(v, str):
        raise ValueError(f"Config key {key!r} must be str, got {type(v).__name__}")
    return v


def x_get_str__mutmut_2(d: dict[str, Any], key: str, default: str = "") -> str:
    """Return d[key] as str, or default if absent/None; raises ValueError on wrong type."""
    v = None
    if v is None:
        return default
    if not isinstance(v, str):
        raise ValueError(f"Config key {key!r} must be str, got {type(v).__name__}")
    return v


def x_get_str__mutmut_3(d: dict[str, Any], key: str, default: str = "") -> str:
    """Return d[key] as str, or default if absent/None; raises ValueError on wrong type."""
    v = d.get(None)
    if v is None:
        return default
    if not isinstance(v, str):
        raise ValueError(f"Config key {key!r} must be str, got {type(v).__name__}")
    return v


def x_get_str__mutmut_4(d: dict[str, Any], key: str, default: str = "") -> str:
    """Return d[key] as str, or default if absent/None; raises ValueError on wrong type."""
    v = d.get(key)
    if v is not None:
        return default
    if not isinstance(v, str):
        raise ValueError(f"Config key {key!r} must be str, got {type(v).__name__}")
    return v


def x_get_str__mutmut_5(d: dict[str, Any], key: str, default: str = "") -> str:
    """Return d[key] as str, or default if absent/None; raises ValueError on wrong type."""
    v = d.get(key)
    if v is None:
        return default
    if isinstance(v, str):
        raise ValueError(f"Config key {key!r} must be str, got {type(v).__name__}")
    return v


def x_get_str__mutmut_6(d: dict[str, Any], key: str, default: str = "") -> str:
    """Return d[key] as str, or default if absent/None; raises ValueError on wrong type."""
    v = d.get(key)
    if v is None:
        return default
    if not isinstance(v, str):
        raise ValueError(None)
    return v


def x_get_str__mutmut_7(d: dict[str, Any], key: str, default: str = "") -> str:
    """Return d[key] as str, or default if absent/None; raises ValueError on wrong type."""
    v = d.get(key)
    if v is None:
        return default
    if not isinstance(v, str):
        raise ValueError(f"Config key {key!r} must be str, got {type(None).__name__}")
    return v

mutants_x_get_str__mutmut['_mutmut_orig'] = x_get_str__mutmut_orig # type: ignore # mutmut generated
mutants_x_get_str__mutmut['x_get_str__mutmut_1'] = x_get_str__mutmut_1 # type: ignore # mutmut generated
mutants_x_get_str__mutmut['x_get_str__mutmut_2'] = x_get_str__mutmut_2 # type: ignore # mutmut generated
mutants_x_get_str__mutmut['x_get_str__mutmut_3'] = x_get_str__mutmut_3 # type: ignore # mutmut generated
mutants_x_get_str__mutmut['x_get_str__mutmut_4'] = x_get_str__mutmut_4 # type: ignore # mutmut generated
mutants_x_get_str__mutmut['x_get_str__mutmut_5'] = x_get_str__mutmut_5 # type: ignore # mutmut generated
mutants_x_get_str__mutmut['x_get_str__mutmut_6'] = x_get_str__mutmut_6 # type: ignore # mutmut generated
mutants_x_get_str__mutmut['x_get_str__mutmut_7'] = x_get_str__mutmut_7 # type: ignore # mutmut generated
