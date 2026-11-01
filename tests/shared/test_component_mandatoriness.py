"""Loader contract tests for ``shared.component_mandatoriness`` (mcpgate001 row 10).

Covers the Phase 1 contract: the live registry round-trips exactly the ten
approved servers, the returned map is frozen, typed errors fire on unknown /
conflicting / malformed input, and an empty ``entries`` list loads to an empty
map (a missing *file* is fatal at startup, but an empty registry is not).
"""

from __future__ import annotations

import textwrap

import pytest
import yaml
from shared.component_mandatoriness import (
    ClassificationConflictError,
    ComponentClassification,
    ComponentMandatorinessError,
    UnknownComponentError,
    check_required_agreement,
    get_classification,
    load_component_mandatoriness,
)

# The ten servers shipped in registry/component_mandatoriness.yaml (AC-2 inventory).
LIVE_IDS = frozenset(
    {
        "cicd",
        "file_delete",
        "file_read",
        "file_write",
        "git",
        "github",
        "mdq",
        "rag_pipeline",
        "shell",
        "web_search",
    }
)

# Every REQ-002 field that must be a non-empty string on each live entry.
_NONEMPTY_FIELDS = (
    "component_id",
    "classification",
    "failure_category",
    "safety_role",
    "startup_consequence",
    "owner",
    "authority_adr",
    "rationale",
)


def _valid_entry(component_id: str = "shell", **overrides: object) -> dict:
    """A structurally complete registry entry; overrides replace one field."""

    entry: dict = {
        "component_id": component_id,
        "classification": "required",
        "failure_category": "safety-integrity",
        "safety_role": "Baseline safety role.",
        "safely_disableable_functions": [],
        "startup_consequence": "abort_startup",
        "observability": ["ServiceWarning"],
        "owner": "agent-architecture-owner",
        "authority_adr": "ADR-004",
        "rationale": "Baseline rationale text.",
    }
    entry.update(overrides)
    return entry


def _write(tmp_path, entries: list[dict]) -> str:
    path = tmp_path / "component_mandatoriness.yaml"
    path.write_text(
        yaml.safe_dump({"version": 1, "entries": entries}),
        encoding="utf-8",
    )
    return str(path)


def test_live_registry_round_trips_ten_approved_entries() -> None:
    registry = load_component_mandatoriness()

    assert set(registry) == LIVE_IDS
    for component_id, classification in registry.items():
        assert isinstance(classification, ComponentClassification)
        assert classification.classification == "required"
        for field in _NONEMPTY_FIELDS:
            value = getattr(classification, field)
            assert isinstance(value, str) and value.strip(), field


def test_frozen_map_rejects_mutation() -> None:
    registry = load_component_mandatoriness()

    with pytest.raises(TypeError):
        registry["new_component"] = ComponentClassification(  # type: ignore[index]  — frozen map rejects item assignment (raises TypeError at runtime, asserted here); mypy flags the assignment
            component_id="new_component",
            classification="non_required",
            failure_category="n/a",
            safety_role="n/a",
            safely_disableable_functions=frozenset(),
            startup_consequence="n/a",
            observability=frozenset(),
            owner="n/a",
            authority_adr="n/a",
            rationale="n/a",
        )


def test_unknown_component_raises_typed_error() -> None:
    registry = load_component_mandatoriness()

    with pytest.raises(UnknownComponentError, match="ghost_server"):
        get_classification(registry, "ghost_server")


def test_classification_conflict_raises_typed_error() -> None:
    registry = load_component_mandatoriness()

    with pytest.raises(ClassificationConflictError, match="cicd"):
        check_required_agreement(registry, "cicd", config_required=False)


def _pop_owner(entry: dict) -> None:
    del entry["owner"]


def _empty_classification(entry: dict) -> None:
    entry["classification"] = ""


def _bad_classification(entry: dict) -> None:
    entry["classification"] = "sometimes"


@pytest.mark.parametrize(
    ("transform", "match"),
    [
        pytest.param(_pop_owner, "missing field", id="missing-field"),
        pytest.param(
            _empty_classification,
            "classification must be one of",
            id="empty-classification",
        ),
        pytest.param(
            _bad_classification,
            "classification must be one of",
            id="unknown-classification",
        ),
    ],
)
def test_malformed_single_entry_rejected(tmp_path, transform, match) -> None:
    entry = _valid_entry()
    transform(entry)
    path = _write(tmp_path, [entry])

    with pytest.raises(ComponentMandatorinessError, match=match):
        load_component_mandatoriness(path)


def test_duplicate_component_id_rejected(tmp_path) -> None:
    base = _valid_entry()
    dup = _valid_entry(component_id="shell")  # same id as base
    path = _write(tmp_path, [base, dup])

    with pytest.raises(ComponentMandatorinessError, match="Duplicate component_id"):
        load_component_mandatoriness(path)


def test_empty_entries_load_as_empty_map(tmp_path) -> None:
    registry_file = tmp_path / "empty.yaml"
    registry_file.write_text(
        "version: 1\nentries: []\n",
        encoding="utf-8",
    )

    assert dict(load_component_mandatoriness(registry_file)) == {}


def test_missing_file_is_fatal(tmp_path) -> None:
    missing = tmp_path / "does_not_exist.yaml"

    with pytest.raises(ComponentMandatorinessError, match="not found"):
        load_component_mandatoriness(missing)


def test_unparsable_yaml_is_fatal(tmp_path) -> None:
    registry_file = tmp_path / "broken.yaml"
    registry_file.write_text(
        textwrap.dedent(
            """\
            version: 1
            entries:
              - : : : not valid yaml
                broken
            """
        ),
        encoding="utf-8",
    )

    with pytest.raises(ComponentMandatorinessError, match="parse"):
        load_component_mandatoriness(registry_file)


def test_check_required_agreement_unknown_component_raises() -> None:
    registry = load_component_mandatoriness()

    with pytest.raises(UnknownComponentError, match="ghost_server"):
        check_required_agreement(registry, "ghost_server", config_required=True)
