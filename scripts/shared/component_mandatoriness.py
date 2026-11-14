#!/usr/bin/env python3
"""scripts/shared/component_mandatoriness.py — Leaf-safe loader for the MCP
component-mandatoriness registry.

Encodes ADR-004 Decision Group 3 item 13: each MCP server's approved
required/non-required classification lives in one machine-readable registry that
``config/agent.toml`` ``required`` values are validated against at startup. The
criteria themselves remain solely in ADR-004; this module only reads the derived
table.

Data source is ``registry/component_mandatoriness.yaml``; consumers import this
module as ``shared.component_mandatoriness``. Imports stdlib and PyYAML only, so
``shared`` stays a leaf module (import-linter ``shared-is-leaf`` contract).
"""

from __future__ import annotations

import dataclasses
from collections.abc import Mapping
from pathlib import Path
from types import MappingProxyType

import yaml

# Repo root is two levels above ``scripts/shared``: ``scripts/shared`` ->
# ``scripts`` -> repository root. Resolving against ``__file__`` keeps the path
# correct regardless of the caller's working directory (cf. shared.runtime_paths).
_REGISTRY_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_REGISTRY_PATH = _REGISTRY_ROOT / "registry" / "component_mandatoriness.yaml"

# Field vocabulary mirrors registry/component_mandatoriness.yaml entry keys.
_ENTRY_FIELDS = (
    "component_id",
    "classification",
    "failure_category",
    "safety_role",
    "safely_disableable_functions",
    "startup_consequence",
    "observability",
    "owner",
    "authority_adr",
    "rationale",
)

_VALID_CLASSIFICATIONS = ("required", "non_required")


class ComponentMandatorinessError(Exception):
    """Base error for any malformed or inconsistent registry content."""


class UnknownComponentError(ComponentMandatorinessError):
    """Raised when a component id is absent from the registry."""


class ClassificationConflictError(ComponentMandatorinessError):
    """Raised when config disagrees with the approved classification."""


@dataclasses.dataclass(frozen=True)
class ComponentClassification:
    """One server's approved mandatoriness classification (one row of the registry)."""

    component_id: str
    classification: str
    failure_category: str
    safety_role: str
    safely_disableable_functions: frozenset[str]
    startup_consequence: str
    observability: frozenset[str]
    owner: str
    authority_adr: str
    rationale: str


def _coerce_nonempty_str(value: object, field: str, component: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ComponentMandatorinessError(
            f"Registry entry #{component!r}: {field!r} must be a non-empty string"
        )
    return value


def _normalize_entry(raw: object, index: int) -> ComponentClassification:
    if not isinstance(raw, dict):
        raise ComponentMandatorinessError(
            f"Registry entries[{index}] must be a mapping, got {type(raw).__name__}"
        )
    keys = set(raw)
    missing = [field for field in _ENTRY_FIELDS if field not in keys]
    extra = keys - set(_ENTRY_FIELDS)
    if missing:
        raise ComponentMandatorinessError(
            f"Registry entries[{index}] ({raw.get('component_id', '<missing>')!r}) "
            f"missing field(s): {', '.join(missing)}"
        )
    if extra:
        raise ComponentMandatorinessError(
            f"Registry entries[{index}] ({raw.get('component_id', '<missing>')!r}) "
            f"has unknown field(s): {', '.join(sorted(extra))}"
        )

    classification = str(raw["classification"])
    if classification not in _VALID_CLASSIFICATIONS:
        raise ComponentMandatorinessError(
            f"Registry entry {raw['component_id']!r}: classification must be one of "
            f"{_VALID_CLASSIFICATIONS}, got {classification!r}"
        )

    return ComponentClassification(
        component_id=_coerce_nonempty_str(
            raw["component_id"], "component_id", str(index)
        ),
        classification=classification,
        failure_category=_coerce_nonempty_str(
            raw["failure_category"], "failure_category", str(index)
        ),
        safety_role=_coerce_nonempty_str(raw["safety_role"], "safety_role", str(index)),
        safely_disableable_functions=frozenset(
            raw["safely_disableable_functions"] or ()
        ),
        startup_consequence=_coerce_nonempty_str(
            raw["startup_consequence"], "startup_consequence", str(index)
        ),
        observability=frozenset(raw["observability"] or ()),
        owner=_coerce_nonempty_str(raw["owner"], "owner", str(index)),
        authority_adr=_coerce_nonempty_str(
            raw["authority_adr"], "authority_adr", str(index)
        ),
        rationale=_coerce_nonempty_str(raw["rationale"], "rationale", str(index)),
    )


def load_component_mandatoriness(
    path: str | Path | None = None,
) -> Mapping[str, ComponentClassification]:
    """Load and validate the component-mandatoriness registry.

    Raises:
        ComponentMandatorinessError: If the file is missing, unparseable, or
            structurally invalid (bad top-level shape, malformed entry, unknown
            key, invalid classification, or duplicate component id).

    Returns:
        A read-only (frozen) mapping keyed by ``component_id``.
    """
    target = Path(path) if path is not None else DEFAULT_REGISTRY_PATH
    try:
        raw = yaml.safe_load(target.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise ComponentMandatorinessError(
            f"Component-mandatoriness registry not found: {target}. "
            "Undeterminable component mandatoriness (ADR-004 Fail-Fast)."
        ) from None
    except yaml.YAMLError as cause:
        raise ComponentMandatorinessError(
            f"Failed to parse component-mandatoriness registry {target}: {cause}"
        ) from cause

    if not isinstance(raw, dict):
        raise ComponentMandatorinessError(
            f"Component-mandatoriness registry {target}: top level must be a mapping"
        )
    if "version" not in raw or "entries" not in raw:
        raise ComponentMandatorinessError(
            f"Component-mandatoriness registry {target}: top level must define "
            f"'version' and 'entries', got {sorted(raw)}"
        )
    entries_raw = raw["entries"]
    if not isinstance(entries_raw, list):
        raise ComponentMandatorinessError(
            f"Component-mandatoriness registry {target}: 'entries' must be a list"
        )

    map_builder: dict[str, ComponentClassification] = {}
    for index, entry_raw in enumerate(entries_raw):
        entry = _normalize_entry(entry_raw, index)
        if entry.component_id in map_builder:
            raise ComponentMandatorinessError(
                f"Duplicate component_id {entry.component_id!r} in {target}: "
                "a duplicated row is a classification conflict at the source"
            )
        map_builder[entry.component_id] = entry

    return MappingProxyType(map_builder)


def get_classification(
    registry: Mapping[str, ComponentClassification],
    component_id: str,
) -> ComponentClassification:
    """Return the approved classification for ``component_id``.

    Raises:
        UnknownComponentError: If ``component_id`` is absent from the registry.
    """

    classification = registry.get(component_id)
    if classification is None:
        raise UnknownComponentError(
            f"Component {component_id!r} not found in component-mandatoriness "
            f"registry at {DEFAULT_REGISTRY_PATH}; classified servers: "
            f"{sorted(registry)}"
        )
    return classification


def check_required_agreement(
    registry: Mapping[str, ComponentClassification],
    component_id: str,
    config_required: bool,
) -> None:
    """Assert the configured ``required`` agrees with the approved classification.

    Unknown component ids raise :class:`UnknownComponentError`; a registry
    ``required`` server configured as ``required = false`` raises
    :class:`ClassificationConflictError` carrying the approved classification and
    the config value (the fatal startup report names this reason, ADR-004 item 13).

    Raises:
        UnknownComponentError: If ``component_id`` is absent from the registry.
        ClassificationConflictError: If the server is approved ``required`` but
            ``config_required`` is ``False``.
    """

    approved = get_classification(registry, component_id)
    if approved.classification == "required" and not config_required:
        raise ClassificationConflictError(
            f"Component {component_id!r} is classified {approved.classification} in "
            f"{DEFAULT_REGISTRY_PATH} but config sets required={config_required}; "
            "revert the config or reclassify via agent_08_04 (ADR-004 item 13)"
        )
