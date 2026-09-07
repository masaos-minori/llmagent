"""tests/tools/test_check_canonical_source_conflicts.py

Tests for the RegistryEntry-consuming rule-detection functions in
tools/check_canonical_source_conflicts.py.

Covers: CANONICAL-001, CANONICAL-002, CANONICAL-003, CANONICAL-004,
CANONICAL-005, CANONICAL-006, CANONICAL-007, CANONICAL-008, CANONICAL-009,
CANONICAL-010, and CANONICAL-W-05.

Does NOT re-test classify_finding() or detect_duplicate_active_records() —
those are covered by test_check_canonical_source_conflicts_routing.py.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.check_canonical_source_conflicts import (
    BlockingStatus,
    RegistryEntry,
    Severity,
    detect_all_conflicts,
    detect_area_guide_contradiction,
    detect_authoritative_terms_in_non_canonical,
    detect_duplicate_normative_sources,
    detect_empty_area,
    detect_empty_claim_type,
    detect_empty_decision_target,
    detect_empty_source_paths,
    detect_legacy_precedence_reintroduction,
    detect_missing_validation_ref,
    detect_multiple_canonical_specifications,
    detect_multiple_source_paths_violation,
    detect_non_canonical_reference_without_link,
    detect_stale_non_canonical_document,
    detect_unregistered_authority_declaration,
    detect_unrecognized_claim_type,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _entry(
    decision_target: str = "target-a",
    claim_type: str = "functional-requirement",
    source_paths: list[str] | None = None,
    area: str = "test-area",
    notes: str | None = None,
    **kwargs,
) -> RegistryEntry:
    """Build a RegistryEntry with minimal required fields; override via kwargs."""
    # Handle the case where source_paths=[] is explicitly passed (empty list is valid)
    if source_paths is None and "source_paths" not in kwargs:
        source_paths = [f"/path/to/{decision_target}-{claim_type}.md"]
    elif source_paths is None:
        source_paths = kwargs.get("source_paths")
    assert source_paths is not None, "source_paths must not be None"
    return RegistryEntry(
        decision_target=decision_target,
        claim_type=claim_type,
        source_paths=source_paths,
        area=area,
        notes=notes or kwargs.get("notes"),
    )

# -----------------------------------------------------------------------
# CANONICAL-001: Duplicate normative canonical sources
# -----------------------------------------------------------------------


class TestDetectDuplicateNormativeSources:
    def test_duplicate_normative_sources_detected(self) -> None:
        e1 = _entry(decision_target="t1", claim_type="functional-requirement")
        e2 = _entry(decision_target="t1", claim_type="functional-requirement")
        conflicts = detect_duplicate_normative_sources([e1, e2])
        assert len(conflicts) == 1
        assert conflicts[0].code == "CANONICAL-001"
        assert conflicts[0].severity == Severity.HIGH
        assert conflicts[0].blocking_status == BlockingStatus.BLOCKING

    def test_no_duplicate_when_different_targets(self) -> None:
        e1 = _entry(decision_target="t1", claim_type="functional-requirement")
        e2 = _entry(decision_target="t2", claim_type="functional-requirement")
        conflicts = detect_duplicate_normative_sources([e1, e2])
        assert conflicts == []

    def test_no_duplicate_different_claim_types(self) -> None:
        e1 = _entry(decision_target="t1", claim_type="functional-requirement")
        e2 = _entry(decision_target="t1", claim_type="architecture-decision")
        conflicts = detect_duplicate_normative_sources([e1, e2])
        assert conflicts == []

# -----------------------------------------------------------------------
# CANONICAL-008: Multiple canonical Specifications
# -----------------------------------------------------------------------


class TestDetectMultipleCanonicalSpecifications:
    def test_multiple_specifications_detected(self) -> None:
        e1 = _entry(decision_target="t1", claim_type="functional-requirement")
        e2 = _entry(decision_target="t1", claim_type="functional-requirement")
        conflicts = detect_multiple_canonical_specifications([e1, e2])
        assert len(conflicts) == 1
        assert conflicts[0].code == "CANONICAL-008"
        assert conflicts[0].severity == Severity.HIGH
        assert conflicts[0].blocking_status == BlockingStatus.BLOCKING

    def test_no_duplicate_different_claim_types(self) -> None:
        e1 = _entry(decision_target="t1", claim_type="functional-requirement")
        e2 = _entry(decision_target="t1", claim_type="architecture-decision")
        conflicts = detect_multiple_canonical_specifications([e1, e2])
        assert conflicts == []

# -----------------------------------------------------------------------
# CANONICAL-010: Area guide contradiction
# -----------------------------------------------------------------------


class TestDetectAreaGuideContradiction:
    def test_area_guide_contradiction_detected(self) -> None:
        area = _entry(decision_target="t1", claim_type="documentation-metadata")
        spec = _entry(decision_target="t1", claim_type="functional-requirement")
        conflicts = detect_area_guide_contradiction([area, spec])
        assert len(conflicts) == 1
        assert conflicts[0].code == "CANONICAL-010"
        assert conflicts[0].severity == Severity.MEDIUM
        assert conflicts[0].blocking_status == BlockingStatus.NON_BLOCKING

    def test_no_contradiction_when_different_targets(self) -> None:
        area = _entry(decision_target="t1", claim_type="documentation-metadata")
        spec = _entry(decision_target="t2", claim_type="functional-requirement")
        conflicts = detect_area_guide_contradiction([area, spec])
        assert conflicts == []

# -----------------------------------------------------------------------
# CANONICAL-011: Legacy universal-precedence reintroduction (no-op — field removed)
# -----------------------------------------------------------------------


class TestDetectLegacyPrecedenceReintroduction:
    def test_returns_empty_list(self) -> None:
        entry = _entry()
        conflicts = detect_legacy_precedence_reintroduction([entry])
        assert conflicts == []

# -----------------------------------------------------------------------
# CANONICAL-W-01: Non-canonical Reference without link (no-op — validation_ref removed)
# -----------------------------------------------------------------------


class TestDetectNonCanonicalReferenceWithoutLink:
    def test_returns_empty_list(self) -> None:
        entry = _entry(claim_type="api-contract")
        conflicts = detect_non_canonical_reference_without_link([entry])
        assert conflicts == []

# -----------------------------------------------------------------------
# CANONICAL-W-02: Potentially stale non-canonical document (no-op — status/expiry_date removed)
# -----------------------------------------------------------------------


class TestDetectStaleNonCanonicalDocument:
    def test_returns_empty_list(self) -> None:
        entry = _entry(claim_type="api-contract")
        conflicts = detect_stale_non_canonical_document([entry])
        assert conflicts == []

# -----------------------------------------------------------------------
# CANONICAL-W-03: Missing validation reference (no-op — validation_ref removed)
# -----------------------------------------------------------------------


class TestDetectMissingValidationRef:
    def test_returns_empty_list(self) -> None:
        entry = _entry(claim_type="functional-requirement")
        conflicts = detect_missing_validation_ref([entry])
        assert conflicts == []

# -----------------------------------------------------------------------
# CANONICAL-W-04: Unregistered authority declaration (no-op — authority removed)
# -----------------------------------------------------------------------


class TestDetectUnregisteredAuthorityDeclaration:
    def test_returns_empty_list(self) -> None:
        entry = _entry()
        conflicts = detect_unregistered_authority_declaration([entry])
        assert conflicts == []

# -----------------------------------------------------------------------
# CANONICAL-W-05: Authoritative terms in non-canonical documents
# -----------------------------------------------------------------------


class TestDetectAuthoritativeTermsInNonCanonical:
    def test_authoritative_term_in_notes_flagged(self) -> None:
        entry = _entry(notes="This is authoritative.")
        conflicts = detect_authoritative_terms_in_non_canonical([entry])
        assert len(conflicts) == 1
        assert conflicts[0].code == "CANONICAL-W-05"
        assert conflicts[0].severity == Severity.MEDIUM
        assert conflicts[0].blocking_status == BlockingStatus.NON_BLOCKING

    def test_source_of_truth_term_flagged(self) -> None:
        entry = _entry(notes="Source of truth for X.")
        conflicts = detect_authoritative_terms_in_non_canonical([entry])
        assert len(conflicts) == 1
        assert conflicts[0].code == "CANONICAL-W-05"

    def test_must_term_flagged(self) -> None:
        entry = _entry(notes="Must follow this rule.")
        conflicts = detect_authoritative_terms_in_non_canonical([entry])
        assert len(conflicts) == 1
        assert conflicts[0].code == "CANONICAL-W-05"

    def test_no_authoritative_terms_passes(self) -> None:
        entry = _entry(notes="Just a regular note.")
        conflicts = detect_authoritative_terms_in_non_canonical([entry])
        assert conflicts == []

    def test_none_notes_passes(self) -> None:
        entry = _entry(notes=None)
        conflicts = detect_authoritative_terms_in_non_canonical([entry])
        assert conflicts == []

# -----------------------------------------------------------------------
# Integration tests (tmp_path-based)
# -----------------------------------------------------------------------


class TestIntegrationWithTempRegistry:
    """Integration-level cases using tmp_path for TOML registry + doc tree."""

    def _write_registry_toml(self, tmp_path: Path, entries: dict) -> Path:
        """Write a minimal TOML registry file and return its path."""
        toml_content = 'version = "1"\n\n'
        for key, val in entries.items():
            toml_content += f"[[canonical_sources]]\n"
            for k, v in val.items():
                if isinstance(v, list):
                    items = ", ".join(f'"{i}"' for i in v)
                    toml_content += f'{k} = [{items}]\n'
                elif isinstance(v, str):
                    toml_content += f'{k} = "{v}"\n'
                else:
                    toml_content += f"{k} = {json.dumps(v)}\n"
            toml_content += "\n"
        path = tmp_path / "registry.toml"
        path.write_text(toml_content, encoding="utf-8")
        return path

    def test_valid_source_exits_zero_with_empty_entries(self, tmp_path: Path) -> None:
        """A valid source with no entries should exit 0 with no findings."""
        registry_path = self._write_registry_toml(tmp_path, {})
        conflicts = detect_all_conflicts(registry_path)
        assert conflicts == []

    def test_duplicate_normative_sources_detected_via_cli(self, tmp_path: Path) -> None:
        """Two entries for the same decision_target+claim_type should be detected."""
        registry_path = self._write_registry_toml(
            tmp_path,
            {
                "e1": {
                    "decision_target": "t1",
                    "claim_type": "functional-requirement",
                    "source_paths": ["/path/to/t1.md"],
                    "area": "test-area",
                },
                "e2": {
                    "decision_target": "t1",
                    "claim_type": "functional-requirement",
                    "source_paths": ["/path/to/t1-alt.md"],
                    "area": "test-area",
                },
            },
        )
        conflicts = detect_all_conflicts(registry_path)
        # When HAS_REGISTRY_VALIDATOR is True, M-01-04 validator returns CANONICAL-007
        # When HAS_REGISTRY_VALIDATOR is False, local detection returns CANONICAL-001
        assert any(c.code in ("CANONICAL-001", "CANONICAL-007") for c in conflicts)

    @pytest.mark.skip(
        reason=(
            "blocked on seq 01 — "
            "CANONICAL-002 through CANONICAL-006/-009 (REQ-001)"
        ),
    )
    def test_canonical_002_case(self, tmp_path: Path) -> None:
        # TODO(seq 01): Implement after M-01-04 lands.
        # Expected: when two entries share the same decision_target+claim_type
        # but one has precedence=normative and the other does not,
        # CANONICAL-002 should flag the conflict.
        pass

    @pytest.mark.skip(
        reason=(
            "blocked on seq 02 — "
            "CANONICAL-007 duplicate ADR ID (REQ-004)"
        ),
    )
    def test_canonical_007_case(self, tmp_path: Path) -> None:
        # TODO(seq 02): Implement after duplicate ADR ID check lands.
        # Expected: duplicate ADR identifiers across docs/adr/*.md files.
        pass

# -----------------------------------------------------------------------
# CANONICAL-002: Empty decision_target
# -----------------------------------------------------------------------


class TestDetectEmptyDecisionTarget:
    def test_empty_decision_target_flagged(self) -> None:
        entry = _entry(decision_target="")
        conflicts = detect_empty_decision_target([entry])
        assert len(conflicts) == 1
        assert conflicts[0].code == "CANONICAL-002"
        assert conflicts[0].severity == Severity.HIGH
        assert conflicts[0].blocking_status == BlockingStatus.BLOCKING

    def test_whitespace_only_decision_target_flagged(self) -> None:
        entry = _entry(decision_target="   ")
        conflicts = detect_empty_decision_target([entry])
        assert len(conflicts) == 1
        assert conflicts[0].code == "CANONICAL-002"

    def test_non_empty_decision_target_passes(self) -> None:
        entry = _entry(decision_target="valid-target")
        conflicts = detect_empty_decision_target([entry])
        assert conflicts == []

# -----------------------------------------------------------------------
# CANONICAL-003: Empty claim_type
# -----------------------------------------------------------------------


class TestDetectEmptyClaimType:
    def test_empty_claim_type_flagged(self) -> None:
        entry = _entry(claim_type="")
        conflicts = detect_empty_claim_type([entry])
        assert len(conflicts) == 1
        assert conflicts[0].code == "CANONICAL-003"
        assert conflicts[0].severity == Severity.HIGH
        assert conflicts[0].blocking_status == BlockingStatus.BLOCKING

    def test_whitespace_only_claim_type_flagged(self) -> None:
        entry = _entry(claim_type="   ")
        conflicts = detect_empty_claim_type([entry])
        assert len(conflicts) == 1
        assert conflicts[0].code == "CANONICAL-003"

    def test_non_empty_claim_type_passes(self) -> None:
        entry = _entry(claim_type="functional-requirement")
        conflicts = detect_empty_claim_type([entry])
        assert conflicts == []

# -----------------------------------------------------------------------
# CANONICAL-004: Unrecognized claim_type
# -----------------------------------------------------------------------


class TestDetectUnrecognizedClaimType:
    def test_unrecognized_claim_type_flagged(self) -> None:
        entry = _entry(claim_type="unknown-type")
        conflicts = detect_unrecognized_claim_type([entry])
        assert len(conflicts) == 1
        assert conflicts[0].code == "CANONICAL-004"
        assert conflicts[0].severity == Severity.MEDIUM
        assert conflicts[0].blocking_status == BlockingStatus.NON_BLOCKING

    def test_valid_claim_type_passes(self) -> None:
        entry = _entry(claim_type="functional-requirement")
        conflicts = detect_unrecognized_claim_type([entry])
        assert conflicts == []

# -----------------------------------------------------------------------
# CANONICAL-005: Empty source_paths
# -----------------------------------------------------------------------


class TestDetectEmptySourcePaths:
    def test_empty_source_paths_flagged(self) -> None:
        entry = _entry(source_paths=[])
        conflicts = detect_empty_source_paths([entry])
        assert len(conflicts) == 1
        assert conflicts[0].code == "CANONICAL-005"
        assert conflicts[0].severity == Severity.HIGH
        assert conflicts[0].blocking_status == BlockingStatus.BLOCKING

    def test_non_empty_source_paths_passes(self) -> None:
        entry = _entry(source_paths=["/path/to/file.md"])
        conflicts = detect_empty_source_paths([entry])
        assert conflicts == []

# -----------------------------------------------------------------------
# CANONICAL-006: Multiple source_paths violation
# -----------------------------------------------------------------------


class TestDetectMultipleSourcePathsViolation:
    def test_multiple_source_paths_violation_flagged(self) -> None:
        entry = _entry(
            claim_type="functional-requirement",
            source_paths=["/path/to/a.md", "/path/to/b.md"],
        )
        conflicts = detect_multiple_source_paths_violation([entry])
        assert len(conflicts) == 1
        assert conflicts[0].code == "CANONICAL-006"
        assert conflicts[0].severity == Severity.MEDIUM
        assert conflicts[0].blocking_status == BlockingStatus.NON_BLOCKING

    def test_single_source_path_passes(self) -> None:
        entry = _entry(
            claim_type="functional-requirement",
            source_paths=["/path/to/a.md"],
        )
        conflicts = detect_multiple_source_paths_violation([entry])
        assert conflicts == []

    def test_runtime_behavior_exemption_passes(self) -> None:
        entry = _entry(
            claim_type="runtime-behavior",
            source_paths=["/path/to/a.md", "/path/to/b.md"],
        )
        conflicts = detect_multiple_source_paths_violation([entry])
        assert conflicts == []

# -----------------------------------------------------------------------
# CANONICAL-009: Empty area
# -----------------------------------------------------------------------


class TestDetectEmptyArea:
    def test_empty_area_flagged(self) -> None:
        entry = _entry(area="")
        conflicts = detect_empty_area([entry])
        assert len(conflicts) == 1
        assert conflicts[0].code == "CANONICAL-009"
        assert conflicts[0].severity == Severity.HIGH
        assert conflicts[0].blocking_status == BlockingStatus.BLOCKING

    def test_whitespace_only_area_flagged(self) -> None:
        entry = _entry(area="   ")
        conflicts = detect_empty_area([entry])
        assert len(conflicts) == 1
        assert conflicts[0].code == "CANONICAL-009"

    def test_non_empty_area_passes(self) -> None:
        entry = _entry(area="test-area")
        conflicts = detect_empty_area([entry])
        assert conflicts == []
