"""scripts/agent/services/typed_validators.py

Typed boundary extraction helpers for config reload operations.

Each *_get helper validates a type and raises ConfigReloadValidationError on mismatch.
The type rules themselves live in scripts/shared/config_field_types.py, so the startup
builders and the reload path run one parser instead of two (REQ-001). The key is passed
to the shared primitive as the field path, so the raised error names the field and never
the value (REQ-011).

Each *_apply helper calls the corresponding _get and invokes setter if value is not None.
Non-empty variants skip setter when value is None or empty collection.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, NoReturn

from shared.config_field_types import (
    ConfigFieldTypeError,
    strict_bool,
    strict_float,
    strict_int,
    strict_mapping,
    strict_str,
    strict_str_list,
)

from agent.services.exceptions import ConfigReloadValidationError


def _raise_required(key: str) -> NoReturn:
    """Raise the required-key error for *key*."""
    raise ConfigReloadValidationError(f"config key {key!r} is required but missing")


def _extract[T](key: str, value: object, rule: Callable[[object, str], T]) -> T:
    """Run one shared primitive and re-raise its error as the reload error type."""
    try:
        return rule(value, key)
    except ConfigFieldTypeError as exc:
        raise ConfigReloadValidationError(str(exc)) from exc


def _str_allowing_empty(value: object, key: str) -> str:
    """Apply the str rule while accepting an empty configured value.

    An empty string is a meaningful configured value for the fields read here
    (`tokenize_url`, `otel_endpoint`, `encryption_key`); `_or_default` turns it into
    the section default at the call site.
    """
    return strict_str(value, key, allow_empty=True)


def _list_allowing_empty(value: object, key: str) -> list[str]:
    """Apply the list-of-str rule while accepting an empty configured list.

    `allowed_tools`, `disabled_tools`, and `approval_github_allowed_repos` are
    configured empty in `config/agent.toml`; whether an empty list is valid for a
    field is the registry's `allow_empty` decision, not this getter's.
    """
    return strict_str_list(value, key, allow_empty=True)


def _mapping_allowing_empty(value: object, key: str) -> dict[str, Any]:
    """Apply the dict rule without checking the value types, accepting an empty dict.

    Used for config sections whose values have mixed declared types
    (`tool_concurrency_limits`, `diagnostics`).
    """
    return strict_mapping(value, key, allow_empty=True)


def _get_int(d: dict[str, object], key: str, *, required: bool = False) -> int | None:
    """Validate and extract an integer value from a config dict.

    Args:
        d: Config dictionary to extract from.
        key: Key to look up in the dictionary.
        required: If True and the key is missing or None, raise
            ConfigReloadValidationError instead of returning None.
    """
    v = d.get(key)
    if v is None:
        if required:
            _raise_required(key)
        return None
    return _extract(key, v, strict_int)


def _get_float(
    d: dict[str, object], key: str, *, required: bool = False
) -> float | None:
    """Validate and extract a float value from a config dict.

    An int is widened to float; a bool or a str is rejected.
    """
    v = d.get(key)
    if v is None:
        if required:
            _raise_required(key)
        return None
    return _extract(key, v, strict_float)


def _get_bool(d: dict[str, object], key: str, *, required: bool = False) -> bool | None:
    """Validate and extract a boolean value from a config dict."""
    v = d.get(key)
    if v is None:
        if required:
            _raise_required(key)
        return None
    return _extract(key, v, strict_bool)


def _get_str(d: dict[str, object], key: str, *, required: bool = False) -> str | None:
    """Validate and extract a string value from a config dict."""
    v = d.get(key)
    if v is None:
        if required:
            _raise_required(key)
        return None
    return _extract(key, v, _str_allowing_empty)


def _get_list(
    d: dict[str, object], key: str, *, required: bool = False
) -> list[Any] | None:
    """Validate and extract a list-of-strings value from a config dict.

    A tuple or a str is rejected; a str is never split into characters.
    """
    v = d.get(key)
    if v is None:
        if required:
            _raise_required(key)
        return None
    return _extract(key, v, _list_allowing_empty)


def _get_dict(
    d: dict[str, object], key: str, *, required: bool = False
) -> dict[str, Any] | None:
    """Validate and extract a dict value from a config dict.

    The value types are not checked here: this getter reads config sections whose
    values have mixed declared types.
    """
    v = d.get(key)
    if v is None:
        if required:
            _raise_required(key)
        return None
    return _extract(key, v, _mapping_allowing_empty)


def _get_list_nonempty(
    d: dict[str, object], key: str, *, required: bool = False
) -> list[Any] | None:
    """Validate and extract a non-empty list value from a config dict.

    Returns None if the key is missing or empty; raises ConfigReloadValidationError
    on type mismatch.
    """
    v = _get_list(d, key, required=required)
    return v if v else None


def _get_str_nonempty(
    d: dict[str, object], key: str, *, required: bool = False
) -> str | None:
    """Validate and extract a non-empty string value from a config dict.

    Returns None if the key is missing or empty; raises ConfigReloadValidationError
    on type mismatch.
    """
    v = _get_str(d, key, required=required)
    return v if v else None


def _get_dict_nonempty(
    d: dict[str, object], key: str, *, required: bool = False
) -> dict[str, Any] | None:
    """Validate and extract a non-empty dict value from a config dict.

    Returns None if the key is missing or empty; raises ConfigReloadValidationError
    on type mismatch.
    """
    v = _get_dict(d, key, required=required)
    return v if v else None


def _apply_int(d: dict[str, object], key: str, setter: Callable[[int], None]) -> None:
    """Apply an integer value via setter if present in config dict."""
    if (v := _get_int(d, key)) is not None:
        setter(v)


def _apply_float(
    d: dict[str, object], key: str, setter: Callable[[float], None]
) -> None:
    """Apply a float value via setter if present in config dict."""
    if (v := _get_float(d, key)) is not None:
        setter(v)


def _apply_bool(d: dict[str, object], key: str, setter: Callable[[bool], None]) -> None:
    """Apply a boolean value via setter if present in config dict."""
    if (v := _get_bool(d, key)) is not None:
        setter(v)


def _apply_list(
    d: dict[str, object], key: str, setter: Callable[[list[Any]], None]
) -> None:
    """Apply a list value via setter if present in config dict."""
    if (v := _get_list(d, key)) is not None:
        setter(v)


def _apply_str(d: dict[str, object], key: str, setter: Callable[[str], None]) -> None:
    """Apply a string value via setter if present in config dict."""
    if (v := _get_str(d, key)) is not None:
        setter(v)


def _apply_list_nonempty(
    d: dict[str, object], key: str, setter: Callable[[list[Any]], None]
) -> None:
    """Apply a non-empty list value via setter if present in config dict."""
    if (v := _get_list_nonempty(d, key)) is not None:
        setter(v)


def _apply_str_nonempty(
    d: dict[str, object], key: str, setter: Callable[[str], None]
) -> None:
    """Apply a non-empty string value via setter if present in config dict."""
    if (v := _get_str_nonempty(d, key)) is not None:
        setter(v)


def _apply_dict_nonempty(
    d: dict[str, object], key: str, setter: Callable[[dict[str, Any]], None]
) -> None:
    """Apply a non-empty dict value via setter if present in config dict."""
    if (v := _get_dict_nonempty(d, key)) is not None:
        setter(v)
