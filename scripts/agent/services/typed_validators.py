"""typed_validators.py

Typed boundary extraction helpers for config reload operations.

Each *_get helper validates a type and raises ConfigReloadValidationError on mismatch.
Each *_apply helper calls the corresponding _get and invokes setter if value is not None.
Non-empty variants skip setter when value is None or empty collection.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from agent.services.exceptions import ConfigReloadValidationError

# Import here to avoid circular import at module level
from agent.services.exceptions import ConfigReloadValidationError


def _get_int(d: dict[str, Any], key: str) -> int | None:
    v = d.get(key)
    if v is None:
        return None
    if not isinstance(v, int) or isinstance(v, bool):
        raise ConfigReloadValidationError(
            f"config key {key!r} must be int, got {type(v).__name__}"
        )
    return v


def _get_float(d: dict[str, Any], key: str) -> float | None:
    v = d.get(key)
    if v is None:
        return None
    if not isinstance(v, (int, float)) or isinstance(v, bool):
        raise ConfigReloadValidationError(
            f"config key {key!r} must be float, got {type(v).__name__}"
        )
    return float(v)


def _get_bool(d: dict[str, Any], key: str) -> bool | None:
    v = d.get(key)
    if v is None:
        return None
    if not isinstance(v, bool):
        raise ConfigReloadValidationError(
            f"config key {key!r} must be bool, got {type(v).__name__}"
        )
    return v


def _get_str(d: dict[str, Any], key: str) -> str | None:
    v = d.get(key)
    if v is None:
        return None
    if not isinstance(v, str):
        raise ConfigReloadValidationError(
            f"config key {key!r} must be str, got {type(v).__name__}"
        )
    return v


def _get_list(d: dict[str, Any], key: str) -> list[Any] | None:
    v = d.get(key)
    if v is None:
        return None
    if not isinstance(v, list):
        raise ConfigReloadValidationError(
            f"config key {key!r} must be list, got {type(v).__name__}"
        )
    return v


def _get_dict(d: dict[str, Any], key: str) -> dict[str, Any] | None:
    v = d.get(key)
    if v is None:
        return None
    if not isinstance(v, dict):
        raise ConfigReloadValidationError(
            f"config key {key!r} must be dict, got {type(v).__name__}"
        )
    return v


def _apply_int(d: dict[str, Any], key: str, setter: Any) -> None:
    if (v := _get_int(d, key)) is not None:
        setter(v)


def _apply_float(d: dict[str, Any], key: str, setter: Any) -> None:
    if (v := _get_float(d, key)) is not None:
        setter(v)


def _apply_bool(d: dict[str, Any], key: str, setter: Any) -> None:
    if (v := _get_bool(d, key)) is not None:
        setter(v)


def _apply_list(d: dict[str, Any], key: str, setter: Any) -> None:
    if (v := _get_list(d, key)) is not None:
        setter(v)


def _apply_str(d: dict[str, Any], key: str, setter: Any) -> None:
    if (v := _get_str(d, key)) is not None:
        setter(v)


def _apply_list_nonempty(d: dict[str, Any], key: str, setter: Any) -> None:
    if (v := _get_list(d, key)) is not None and v:
        setter(v)


def _apply_str_nonempty(d: dict[str, Any], key: str, setter: Any) -> None:
    if (v := _get_str(d, key)) is not None and v:
        setter(v)


def _apply_dict_nonempty(d: dict[str, Any], key: str, setter: Any) -> None:
    if (v := _get_dict(d, key)) is not None and v:
        setter(v)
