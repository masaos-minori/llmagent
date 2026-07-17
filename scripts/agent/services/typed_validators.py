"""typed_validators.py

Typed boundary extraction helpers for config reload operations.

Each *_get helper validates a type and raises ConfigReloadValidationError on mismatch.
Each *_apply helper calls the corresponding _get and invokes setter if value is not None.
Non-empty variants skip setter when value is None or empty collection.
"""

from __future__ import annotations

from typing import Any

# Import here to avoid circular import at module level
from agent.services.exceptions import ConfigReloadValidationError


def _get_int(d: dict[str, Any], key: str) -> int | None:
    """Validate and extract an integer value from a config dict."""
    v = d.get(key)
    if v is None:
        return None
    if not isinstance(v, int) or isinstance(v, bool):
        raise ConfigReloadValidationError(
            f"config key {key!r} must be int, got {type(v).__name__}"
        )
    return v


def _get_float(d: dict[str, Any], key: str) -> float | None:
    """Validate and extract a float value from a config dict."""
    v = d.get(key)
    if v is None:
        return None
    if not isinstance(v, (int, float)) or isinstance(v, bool):
        raise ConfigReloadValidationError(
            f"config key {key!r} must be float, got {type(v).__name__}"
        )
    return float(v)


def _get_bool(d: dict[str, Any], key: str) -> bool | None:
    """Validate and extract a boolean value from a config dict."""
    v = d.get(key)
    if v is None:
        return None
    if not isinstance(v, bool):
        raise ConfigReloadValidationError(
            f"config key {key!r} must be bool, got {type(v).__name__}"
        )
    return v


def _get_str(d: dict[str, Any], key: str) -> str | None:
    """Validate and extract a string value from a config dict."""
    v = d.get(key)
    if v is None:
        return None
    if not isinstance(v, str):
        raise ConfigReloadValidationError(
            f"config key {key!r} must be str, got {type(v).__name__}"
        )
    return v


def _get_list(d: dict[str, Any], key: str) -> list[Any] | None:
    """Validate and extract a list value from a config dict."""
    v = d.get(key)
    if v is None:
        return None
    if not isinstance(v, list):
        raise ConfigReloadValidationError(
            f"config key {key!r} must be list, got {type(v).__name__}"
        )
    return v


def _get_dict(d: dict[str, Any], key: str) -> dict[str, Any] | None:
    """Validate and extract a dict value from a config dict."""
    v = d.get(key)
    if v is None:
        return None
    if not isinstance(v, dict):
        raise ConfigReloadValidationError(
            f"config key {key!r} must be dict, got {type(v).__name__}"
        )
    return v


def _apply_int(d: dict[str, Any], key: str, setter: Any) -> None:
    """Apply an integer value via setter if present in config dict."""
    if (v := _get_int(d, key)) is not None:
        setter(v)


def _apply_float(d: dict[str, Any], key: str, setter: Any) -> None:
    """Apply a float value via setter if present in config dict."""
    if (v := _get_float(d, key)) is not None:
        setter(v)


def _apply_bool(d: dict[str, Any], key: str, setter: Any) -> None:
    """Apply a boolean value via setter if present in config dict."""
    if (v := _get_bool(d, key)) is not None:
        setter(v)


def _apply_list(d: dict[str, Any], key: str, setter: Any) -> None:
    """Apply a list value via setter if present in config dict."""
    if (v := _get_list(d, key)) is not None:
        setter(v)


def _apply_str(d: dict[str, Any], key: str, setter: Any) -> None:
    """Apply a string value via setter if present in config dict."""
    if (v := _get_str(d, key)) is not None:
        setter(v)


def _apply_list_nonempty(d: dict[str, Any], key: str, setter: Any) -> None:
    """Apply a non-empty list value via setter if present in config dict."""
    if (v := _get_list(d, key)) is not None and v:
        setter(v)


def _apply_str_nonempty(d: dict[str, Any], key: str, setter: Any) -> None:
    """Apply a non-empty string value via setter if present in config dict."""
    if (v := _get_str(d, key)) is not None and v:
        setter(v)


def _apply_dict_nonempty(d: dict[str, Any], key: str, setter: Any) -> None:
    """Apply a non-empty dict value via setter if present in config dict."""
    if (v := _get_dict(d, key)) is not None and v:
        setter(v)
