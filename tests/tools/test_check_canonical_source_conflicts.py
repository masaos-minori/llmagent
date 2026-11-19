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
import tomllib
from pathlib import Path

import pytest

import tools.check_canonical_document_prose as prose_module
import tools.check_canonical_source_registry as registry_module
from tools.check_canonical_source_conflicts import (
    BlockingStatus,
    RegistryEntry,
    Severity,
    _wrap_validation_errors,
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
    detect_unrecognized_claim_type,
    detect_unregistered_authority_declaration,
    main,
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
            toml_content += "[[canonical_sources]]\n"
            for k, v in val.items():
                if isinstance(v, list):
                    items = ", ".join(f'"{i}"' for i in v)
                    toml_content += f"{k} = [{items}]\n"
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

    # Removed 2026-11-19 (plan adrchk010 seq 02): the "blocked on seq 01"/"blocked on
    # seq 02" stubs test_canonical_002_case and test_canonical_007_case were deleted.
    # The 002 stub assumed a precedence field removed by M-01-04; the 007 stub
    # (duplicate ADR IDs across docs/10_adr) is out of this plan's scope. Both code
    # classes are covered by the TestDetect* classes below and the seq 09 T08 fixture.


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
        # Plan AC-07 (REQ-007): unrecognized claim_type is a GV-021 blocking class.
        assert conflicts[0].severity == Severity.HIGH
        assert conflicts[0].blocking_status == BlockingStatus.BLOCKING

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


# -----------------------------------------------------------------------
# Regression tests for _wrap_validation_errors cross-product bug
# -----------------------------------------------------------------------


class TestWrapValidationErrorsCrossProduct:
    """Regression tests for _wrap_validation_errors cross-product bug."""

    def test_single_exempt_entry_no_false_positive(self) -> None:
        """A single exempt single-path entry must not produce cross-product findings.

        Note: the validator may emit a spurious "multiple source_paths (1)" error
        for runtime-behavior entries — this is a separate bug. Our fix ensures
        the error is attributed only to the matching entry, not duplicated across
        all entries.
        """
        entry = _entry(
            decision_target="eventbus.core-behavior",
            claim_type="runtime-behavior",
            source_paths=["scripts/eventbus/"],
        )
        errors = [
            "multiple source_paths (1) for claim_type 'runtime-behavior' "
            "on entry targeting 'eventbus.core-behavior': "
            "only 'runtime-behavior' allows multiple sources"
        ]
        conflicts = _wrap_validation_errors(errors, [entry])
        # After fix: exactly one finding for the matching entry only
        assert len(conflicts) == 1
        assert conflicts[0].code == "CANONICAL-006"

    def test_multi_entries_multi_errors_no_cross_product(self) -> None:
        """Multiple entries x multiple errors must not produce cross-product findings."""
        entry_a = _entry(
            decision_target="eventbus.core-behavior",
            claim_type="runtime-behavior",
            source_paths=["scripts/eventbus/"],
        )
        entry_b = _entry(
            decision_target="eventbus.persistence-schema",
            claim_type="database-schema",
            source_paths=["scripts/db/schema_sql.py", "scripts/eventbus/db.py"],
        )
        errors = [
            "multiple source_paths (2) for claim_type 'database-schema' "
            "on entry targeting 'eventbus.persistence-schema': "
            "only 'runtime-behavior' allows multiple sources"
        ]
        conflicts = _wrap_validation_errors(errors, [entry_a, entry_b])
        assert len(conflicts) == 1
        assert conflicts[0].code == "CANONICAL-006"
        assert conflicts[0].affected_files == [
            "scripts/db/schema_sql.py",
            "scripts/eventbus/db.py",
        ]


# -----------------------------------------------------------------------
# Plan adrchk010 seq 09 fixtures (T06-T09, T11, T12)
# Written test-first per Plan Phase 2; each red before its seq 02/03 fix.
# -----------------------------------------------------------------------


def _fixture_root(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    """Point the registry tool's repo-root anchor at tmp_path.

    detect_all_conflicts keeps its public signature; validate_registry_schema
    resolves the module-global REPO_ROOT at call time (REQ-002 anchoring), so
    patching it lets tmp fixtures carry real source files under tmp_path.
    """
    monkeypatch.setattr(registry_module, "REPO_ROOT", tmp_path)
    return tmp_path


def _write_fixture_registry(tmp_path: Path, version: str, entries: list[dict]) -> Path:
    """Write a fixture TOML registry under tmp_path and return its path."""
    lines = [f'version = "{version}"', ""]
    for entry in entries:
        lines.append("[[canonical_sources]]")
        for key, value in entry.items():
            if isinstance(value, list):
                rendered = ", ".join(f'"{v}"' for v in value)
                lines.append(f"{key} = [{rendered}]")
            else:
                lines.append(f'{key} = "{value}"')
        lines.append("")
    path = tmp_path / "fixture_registry.toml"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


class TestMainPathDetectorsT06:
    """T06 (AC-06, REQ-006): semantic findings appear without the fallback path."""

    def test_semantic_finding_on_main_path(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        root = _fixture_root(monkeypatch, tmp_path)
        (root / "guide.md").write_text("# area guide\n", encoding="utf-8")
        (root / "spec.md").write_text("# spec\n", encoding="utf-8")
        registry_path = _write_fixture_registry(
            root,
            "1",
            [
                {
                    "decision_target": "t-guide",
                    "claim_type": "documentation-metadata",
                    "source_paths": ["guide.md"],
                    "area": "Fixture",
                },
                {
                    "decision_target": "t-guide",
                    "claim_type": "functional-requirement",
                    "source_paths": ["spec.md"],
                    "area": "Fixture",
                },
            ],
        )
        conflicts = detect_all_conflicts(registry_path)
        # No validation errors exist; only the semantic detectors can produce
        # this finding (area guide vs functional-requirement for one target).
        assert [c.code for c in conflicts] == ["CANONICAL-010"]


class TestWrapperBlockingT07:
    """T07 (AC-07, REQ-007): errors without decision_target text are still reported."""

    def test_missing_path_and_invalid_claim_type_blocking(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        root = _fixture_root(monkeypatch, tmp_path)
        registry_path = _write_fixture_registry(
            root,
            "1",
            [
                {
                    "decision_target": "t-missing",
                    "claim_type": "functional-requirement",
                    "source_paths": ["missing/thing.md"],
                    "area": "Fixture",
                },
                {
                    "decision_target": "t-bogus",
                    "claim_type": "bogus-type",
                    "source_paths": ["missing/other.md"],
                    "area": "Fixture",
                },
            ],
        )
        conflicts = detect_all_conflicts(registry_path)
        assert sorted({c.code for c in conflicts}) == ["CANONICAL-004", "CANONICAL-013"]
        # GV-021 severity model: both classes are blocking HIGH findings.
        assert all(c.severity == Severity.HIGH for c in conflicts)
        assert all(c.blocking_status == BlockingStatus.BLOCKING for c in conflicts)
        missing_path = next(c for c in conflicts if c.code == "CANONICAL-013")
        assert "missing/thing.md" in missing_path.description


class TestWrapperDedupT08:
    """T08 (AC-08, REQ-008): one registry error yields exactly one finding."""

    def test_duplicate_pair_single_finding_per_code(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        root = _fixture_root(monkeypatch, tmp_path)
        (root / "d1.md").write_text("1\n", encoding="utf-8")
        (root / "d2.md").write_text("2\n", encoding="utf-8")
        registry_path = _write_fixture_registry(
            root,
            "1",
            [
                {
                    "decision_target": "t-dup",
                    "claim_type": "runtime-behavior",
                    "source_paths": ["d1.md"],
                    "area": "Fixture",
                },
                {
                    "decision_target": "t-dup",
                    "claim_type": "runtime-behavior",
                    "source_paths": ["d2.md"],
                    "area": "Fixture",
                },
            ],
        )
        conflicts = detect_all_conflicts(registry_path)
        wrapped = [c for c in conflicts if c.code == "CANONICAL-007"]
        detected = [c for c in conflicts if c.code == "CANONICAL-001"]
        assert len(wrapped) == 1
        assert len(detected) == 1
        # Both matching entries are preserved, deterministically ordered.
        assert wrapped[0].affected_files == ["d1.md", "d2.md"]


class TestCodeUniquenessT09:
    """T09 (AC-09, REQ-009): every finding code is unique; version error = CANONICAL-012."""

    def test_all_classes_unique_codes(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        root = _fixture_root(monkeypatch, tmp_path)
        for name in (
            "dup1.md",
            "dup2.md",
            "e0.md",
            "e1.md",
            "m1.md",
            "m2.md",
            "a0.md",
            "n1.md",
        ):
            (root / name).write_text(f"fixture {name}\n", encoding="utf-8")
        (root / "adr_proposed.md").write_text(
            "# ADR fixture\n\n## Status\n\nProposed\n\nbody\n", encoding="utf-8"
        )
        registry_path = _write_fixture_registry(
            root,
            "2",
            [
                {
                    "decision_target": "t-dup",
                    "claim_type": "documentation-metadata",
                    "source_paths": ["dup1.md"],
                    "area": "Fixture",
                },
                {
                    "decision_target": "t-dup",
                    "claim_type": "documentation-metadata",
                    "source_paths": ["dup2.md"],
                    "area": "Fixture",
                },
                {
                    "decision_target": "",
                    "claim_type": "runtime-behavior",
                    "source_paths": ["e0.md"],
                    "area": "Fixture",
                },
                {
                    "decision_target": "t-emptyclaim",
                    "claim_type": "",
                    "source_paths": ["e1.md"],
                    "area": "Fixture",
                },
                {
                    "decision_target": "t-emptypaths",
                    "claim_type": "runtime-behavior",
                    "source_paths": [],
                    "area": "Fixture",
                },
                {
                    "decision_target": "t-multipath",
                    "claim_type": "database-schema",
                    "source_paths": ["m1.md", "m2.md"],
                    "area": "Fixture",
                },
                {
                    "decision_target": "t-noarea",
                    "claim_type": "runtime-behavior",
                    "source_paths": ["a0.md"],
                    "area": "",
                },
                {
                    "decision_target": "t-adr",
                    "claim_type": "architecture-decision",
                    "source_paths": ["adr_proposed.md"],
                    "area": "Fixture",
                },
                {
                    "decision_target": "t-gone",
                    "claim_type": "runtime-behavior",
                    "source_paths": ["gone.md"],
                    "area": "Fixture",
                },
                {
                    "decision_target": "t-notes",
                    "claim_type": "runtime-behavior",
                    "source_paths": ["n1.md"],
                    "area": "Fixture",
                    "notes": "The authoritative source of truth for this target.",
                },
            ],
        )
        conflicts = detect_all_conflicts(registry_path)
        codes = sorted(c.code for c in conflicts)
        expected = sorted(
            [
                "CANONICAL-001",
                "CANONICAL-002",
                "CANONICAL-003",
                "CANONICAL-004",
                "CANONICAL-005",
                "CANONICAL-006",
                "CANONICAL-007",
                "CANONICAL-009",
                "CANONICAL-011",
                "CANONICAL-012",
                "CANONICAL-013",
                "CANONICAL-W-05",
            ]
        )
        assert codes == expected
        # AC-09: no code appears twice in a run.
        assert len(set(codes)) == len(codes)
        version = [c for c in conflicts if c.code == "CANONICAL-012"]
        assert len(version) == 1
        assert version[0].severity == Severity.HIGH
        assert version[0].blocking_status == BlockingStatus.BLOCKING
        # AC-01: the non-Accepted ADR class yields exactly one conflicts-side
        # warning finding (MEDIUM/NON_BLOCKING), not a second registry error.
        adr = [c for c in conflicts if c.code == "CANONICAL-011"]
        assert len(adr) == 1
        assert adr[0].severity == Severity.MEDIUM
        assert adr[0].blocking_status == BlockingStatus.NON_BLOCKING


class TestHelpDefaultT11:
    """T11 (AC-11, REQ-013): --help states the actual default registry path."""

    def test_help_text_default_registry(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        with pytest.raises(SystemExit) as exc_info:
            main(["--help"])
        assert exc_info.value.code == 0
        assert "config/documentation_canonical_sources.toml" in capsys.readouterr().out


class TestRegistryRowCorrectionsT12:
    """T12 (AC-12, REQ-014/015/016/019): defective rows vs corrected repo rows."""

    # The exact defective values probed 2026-11-19 from
    # config/documentation_canonical_sources.toml (pre-seq-03).
    DEFECTIVE_ROWS = [
        {
            "decision_target": "eventbus.persistence-schema.bootstrap-ddl",
            "claim_type": "database-schema",
            "source_paths": ["scripts/db/schema_sql.py"],
            "area": "EventBus",
            "notes": "Bootstrap DDL for eventbus.sqlite schema, backed by ADR-008.",
        },
        {
            "decision_target": "overview.architecture-overview",
            "claim_type": "documentation-metadata",
            "source_paths": ["docs/01_overview/overview_01_01-arch-process.md"],
            "area": "Overview",
            "notes": "Architecture process overview; candidate replacement for docs/architecture.md.",
        },
        {
            "decision_target": "governance.policy",
            "claim_type": "documentation-metadata",
            "source_paths": [
                "docs/00_governance/governance_01_documentation-policy.md"
            ],
            "area": "Governance",
            "notes": "Documentation policy is the governance authority.",
        },
        {
            "decision_target": "agent.posture-failure-handling",
            "claim_type": "architecture-decision",
            "source_paths": [
                "docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md"
            ],
            "area": "Agent",
            "notes": "ADR-004 fixes the failure-handling policy per environment posture (fail-closed in production, fail-open in development).",
        },
    ]

    def test_defective_rows_are_not_mechanically_detected(self, tmp_path: Path) -> None:
        """Evidence for REQ-014-REQ-019: the four defective rows pass every
        schema-level consumer, so the semantic defects must be fixed in config
        (seq 03), not by the checkers. Runs against the real repo root (no tmp
        repo-root patch): every source path exists and the ADR is Accepted."""
        registry_path = _write_fixture_registry(tmp_path, "1", self.DEFECTIVE_ROWS)
        assert registry_module.main(["--registry", str(registry_path)]) == 0
        assert main(["--registry", str(registry_path)]) == 0

    def test_corrected_repo_rows_match_governing_spec(self) -> None:
        """Pins the seq 03 outcomes (REQ-014/015/016/019) once landed.
        Red until seq 03 applies the row edits; UNK-04 freedom for the
        REQ-016/REQ-019 chosen values is preserved by pinning the defective
        values' removal, not one specific replacement."""
        toml_path = (
            Path(__file__).resolve().parent.parent.parent
            / "config"
            / "documentation_canonical_sources.toml"
        )
        rows = {
            row["decision_target"]: row
            for row in tomllib.loads(toml_path.read_text(encoding="utf-8"))[
                "canonical_sources"
            ]
        }
        # REQ-014: the DDL definition per the DB docs, not schema_sql.py.
        assert rows["eventbus.persistence-schema.bootstrap-ddl"]["source_paths"] == [
            "scripts/eventbus/schema.sql"
        ]
        # REQ-015 / ADR-004 Group 1 item 1: no environment-specific fail-open wording.
        assert "fail-open" not in rows["agent.posture-failure-handling"]["notes"]
        # REQ-016: the Matrix documentation-metadata row no longer contradicts.
        gov = rows["governance.policy"]
        assert gov["claim_type"] != "documentation-metadata" or not any(
            "governance_01_documentation-policy" in p for p in gov["source_paths"]
        )
        # REQ-019: the registered claim kind no longer pairs the overview document
        # with a claim type the Matrix does not authorize for it.
        overview = rows["overview.architecture-overview"]
        assert overview["claim_type"] != "documentation-metadata" or overview[
            "source_paths"
        ] != ["docs/01_overview/overview_01_01-arch-process.md"]

    def test_all_three_consumers_exit_zero_on_repo_registry(self) -> None:
        """AC-12 clean-run baseline: registry checker, conflicts checker and the
        prose checker all exit 0 on the (corrected) repo registry."""
        assert registry_module.main([]) == 0
        assert main([]) == 0
        assert prose_module.main([]) == 0
