#!/usr/bin/env python3
"""scripts/shared/config_field_types.py — Strict config field type primitives.

One implementation of the declared-type rules, shared by the startup config builders
and the reload path so both reject the same wrong-typed value (REQ-001, AC-1). The
module lives in the leaf layer because `.importlinter` contract `shared-is-leaf`
forbids `shared` importing `agent`, and `shared/mcp_config.py` needs the same rules.

Raised errors name the field path and the violated rule and never include the
configured value, which can carry tokens or paths (REQ-011).

Usage:
    from shared.config_field_types import strict_int, strict_str_list
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any, NoReturn


@dataclass(frozen=True)
class FieldRule:
    """Declared type rule for one configuration field.

    Attributes:
        name: Rule identifier reported on the raised error.
        type_label: Wording used in the error text.
        declared_type: Python type the rule accepts, or None for a rule with no type.
    """

    name: str
    type_label: str
    declared_type: type | None = None


RULE_BOOL = FieldRule(name="bool", type_label="bool", declared_type=bool)
RULE_INT = FieldRule(name="int", type_label="int", declared_type=int)
RULE_FLOAT = FieldRule(name="float", type_label="float", declared_type=float)
RULE_STR = FieldRule(name="str", type_label="str", declared_type=str)
RULE_STR_LIST = FieldRule(name="str_list", type_label="list", declared_type=list)
RULE_MAPPING = FieldRule(name="mapping", type_label="dict", declared_type=dict)
RULE_STR_MAPPING = FieldRule(name="str_mapping", type_label="dict", declared_type=dict)
RULE_NON_EMPTY = FieldRule(name="non_empty", type_label="non-empty value")
RULE_UNKNOWN_KEY = FieldRule(name="unknown_key", type_label="unknown key")


class ConfigFieldTypeError(ValueError):
    """A configuration value does not match its declared type rule.

    Attributes:
        field_path: Path of the field that failed: the config key name for an agent
            section field (``llm_max_tokens``), or a dotted path for an MCP server
            field (``mcp_servers.shell.cmd``).
        rule: Name of the violated ``FieldRule``.
    """

    def __init__(self, field_path: str, rule: str, message: str) -> None:
        super().__init__(message)
        self.field_path = field_path
        self.rule = rule


def _reject_type(field_path: str, rule: FieldRule, value: object) -> NoReturn:
    """Raise with the field path, the rule, and the received type name, never the value."""
    raise ConfigFieldTypeError(
        field_path,
        rule.name,
        f"config key {field_path!r} must be {rule.type_label}, "
        f"got {type(value).__name__}",
    )


def _reject_empty(field_path: str) -> NoReturn:
    """Raise the non-empty rule for the field, without echoing the value."""
    raise ConfigFieldTypeError(
        field_path,
        RULE_NON_EMPTY.name,
        f"config key {field_path!r} must not be empty",
    )


def strict_bool(value: object, field_path: str) -> bool:
    """Return ``value`` when it is a ``bool``, else raise ``ConfigFieldTypeError``."""
    if not isinstance(value, bool):
        _reject_type(field_path, RULE_BOOL, value)
    return value


def strict_int(value: object, field_path: str) -> int:
    """Return ``value`` when it is an ``int``.

    ``bool`` is rejected even though it is an ``int`` subclass.
    """
    if isinstance(value, bool) or not isinstance(value, int):
        _reject_type(field_path, RULE_INT, value)
    return value


def strict_float(value: object, field_path: str) -> float:
    """Return ``value`` as a ``float``, widening an ``int``.

    ``bool`` is rejected; a ``str`` is not coerced.
    """
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        _reject_type(field_path, RULE_FLOAT, value)
    return float(value)


def strict_str(value: object, field_path: str, *, allow_empty: bool = False) -> str:
    """Return ``value`` when it is a ``str``.

    An empty or whitespace-only string is rejected unless the caller declares the
    field ``allow_empty``.
    """
    if not isinstance(value, str):
        _reject_type(field_path, RULE_STR, value)
    if value and not value.strip():
        # Whitespace-only is never a meaningful value, whatever allow_empty says.
        _reject_empty(field_path)
    if not value and not allow_empty:
        _reject_empty(field_path)
    return value


def strict_str_list(
    value: object, field_path: str, *, allow_empty: bool = False
) -> list[str]:
    """Return ``value`` when it is a ``list`` of ``str`` items.

    A ``tuple`` or a ``str`` is rejected rather than accepted or split. ``allow_empty``
    governs emptiness at both levels: without it an empty list and an empty or
    whitespace-only item are rejected; with it the caller decides what an empty item
    means, which is what keeps ``approval_shell_safe_prefixes`` skipping its empty
    entries instead of failing startup.
    """
    if not isinstance(value, list):
        _reject_type(field_path, RULE_STR_LIST, value)
    if not value and not allow_empty:
        _reject_empty(field_path)
    for index, item in enumerate(value):
        item_path = f"{field_path}[{index}]"
        if not isinstance(item, str):
            _reject_type(item_path, RULE_STR, item)
        elif not allow_empty and not item.strip():
            _reject_empty(item_path)
    return value


def strict_mapping(
    value: object, field_path: str, *, allow_empty: bool = False
) -> dict[str, Any]:
    """Return ``value`` when it is a ``dict``, without checking the value types.

    Used for a config section whose values are of mixed declared types.
    """
    if not isinstance(value, dict):
        _reject_type(field_path, RULE_MAPPING, value)
    if not value and not allow_empty:
        _reject_empty(field_path)
    return value


def strict_str_mapping(
    value: object, field_path: str, *, allow_empty: bool = False
) -> dict[str, str]:
    """Return ``value`` when it is a ``dict`` with ``str`` keys and ``str`` values.

    A wrong-typed item is rejected by naming its key, not its value.
    """
    if not isinstance(value, dict):
        _reject_type(field_path, RULE_STR_MAPPING, value)
    if not value and not allow_empty:
        _reject_empty(field_path)
    for key, item in value.items():
        item_path = f"{field_path}[{key!r}]"
        if not isinstance(key, str):
            _reject_type(item_path, RULE_STR, key)
        if not isinstance(item, str):
            _reject_type(item_path, RULE_STR, item)
    return value


def apply_field_rule(
    rule: FieldRule,
    value: object,
    field_path: str,
    *,
    allow_empty: bool = False,
) -> Any:
    """Run one declared ``FieldRule`` against one value and return the typed value.

    Lets a caller that stores a declared rule (the config field registry) run it
    before comparing a value against the live one, so a wrong-typed value is rejected
    instead of being skipped as unchanged.
    """
    if rule is RULE_BOOL:
        return strict_bool(value, field_path)
    if rule is RULE_INT:
        return strict_int(value, field_path)
    if rule is RULE_FLOAT:
        return strict_float(value, field_path)
    if rule is RULE_STR:
        return strict_str(value, field_path, allow_empty=allow_empty)
    if rule is RULE_STR_LIST:
        return strict_str_list(value, field_path, allow_empty=allow_empty)
    if rule is RULE_MAPPING:
        return strict_mapping(value, field_path, allow_empty=allow_empty)
    if rule is RULE_STR_MAPPING:
        return strict_str_mapping(value, field_path, allow_empty=allow_empty)
    raise ValueError(f"no strict primitive registered for field rule {rule.name!r}")


def reject_unknown_keys(
    payload: Mapping[str, object], declared_keys: Iterable[str], *, section: str = ""
) -> None:
    """Raise ``ConfigFieldTypeError`` for every key outside the declared key set.

    The error names the key, never its value. ``section`` qualifies the key path when
    the payload belongs to a named config section.
    """
    declared = set(declared_keys)
    for key in payload:
        if key in declared:
            continue
        field_path = f"{section}.{key}" if section else str(key)
        raise ConfigFieldTypeError(
            field_path,
            RULE_UNKNOWN_KEY.name,
            f"unknown config key {key!r}" + (f" in {section}" if section else ""),
        )
