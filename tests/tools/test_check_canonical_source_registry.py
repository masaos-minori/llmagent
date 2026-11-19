"""tests/tools/test_check_canonical_source_registry.py

Unit tests for tools/check_canonical_source_registry.py covering REQ-008's six
cases: valid-registry pass; missing-source-path failure; source_paths-length
violation on single-source claim type; non-Accepted ADR failure; unrecognized
claim-type failure; schema-version-mismatch handling.

Built against seq 02's actual schema decision, not the Plan's originally-proposed
nested-table schema.
"""

from __future__ import annotations

from pathlib import Path

import pytest

import tools.check_canonical_source_registry as registry_module
from tools.check_canonical_source_registry import (
    VALID_CLAIM_TYPES,
    CanonicalSourceRegistry,
    RegistryEntry,
    load_registry,
    main,
    validate_registry_schema,
)

# -------------------------------------------------------------------
# Fixture builder — mirrors the sibling test file's _entry() pattern
# -------------------------------------------------------------------


def _entry(
    target: str = "target-a",
    claim_type: str = "functional-requirement",
    paths: list[str] | None = None,
    area: str = "architecture",
    notes: str | None = None,
) -> RegistryEntry:
    if paths is None:
        paths = ["config/documentation_canonical_sources.toml"]
    return RegistryEntry(
        decision_target=target,
        claim_type=claim_type,
        source_paths=paths,
        area=area,
        notes=notes,
    )


def _registry(
    version: str = "1",
    entries: list[RegistryEntry] | None = None,
) -> CanonicalSourceRegistry:
    if entries is None:
        entries = [_entry()]
    return CanonicalSourceRegistry(version=version, entries=entries)


# -------------------------------------------------------------------
# Valid registry pass (REQ-008 case 1)
# -------------------------------------------------------------------


class TestValidRegistryPass:
    """A registry with supported version and all-valid entries passes validation."""

    def test_valid_registry_passes(self) -> None:
        entry = _entry(
            target="valid-target",
            claim_type="functional-requirement",
            paths=["config/documentation_canonical_sources.toml"],
            area="governance",
        )
        reg = _registry(version="1", entries=[entry])
        errors = validate_registry_schema(reg)
        assert errors == []


# -------------------------------------------------------------------
# Missing source path (REQ-008 case 2)
# -------------------------------------------------------------------


class TestMissingSourcePath:
    """An entry whose source_paths contains a nonexistent path fails."""

    def test_missing_source_path_fails(self, tmp_path: Path) -> None:
        entry = _entry(
            target="missing-path-target",
            claim_type="functional-requirement",
            paths=[str(tmp_path / "nonexistent_file.md")],
            area="governance",
        )
        reg = _registry(version="1", entries=[entry])
        errors = validate_registry_schema(reg, repo_root=tmp_path)
        assert len(errors) >= 1
        assert any("does not exist" in e for e in errors)


# -------------------------------------------------------------------
# source_paths length violation on single-source claim type (REQ-008 case 3)
# -------------------------------------------------------------------


class TestSourcePathsEnforcement:
    """Multiple source_paths on a single-source claim type must fail;
    runtime-behavior exemption must pass."""

    def test_multiple_sources_on_single_source_claim_type_fails(self) -> None:
        entry = _entry(
            target="multi-source-violation",
            claim_type="functional-requirement",
            paths=["docs/a.md", "docs/b.md"],
            area="governance",
        )
        reg = _registry(version="1", entries=[entry])
        errors = validate_registry_schema(reg)
        assert len(errors) >= 1
        assert any("multiple source_paths" in e for e in errors)

    def test_multiple_sources_on_runtime_behavior_passes(self, tmp_path: Path) -> None:
        a_file = tmp_path / "a.md"
        b_file = tmp_path / "b.md"
        a_file.write_text("# A\n")
        b_file.write_text("# B\n")
        entry = _entry(
            target="runtime-multi-source",
            claim_type="runtime-behavior",
            paths=[str(a_file), str(b_file)],
            area="operations",
        )
        reg = _registry(version="1", entries=[entry])
        errors = validate_registry_schema(reg, repo_root=tmp_path)
        assert errors == []


# -------------------------------------------------------------------
# Non-Accepted ADR status check (REQ-008 case 4)
# -------------------------------------------------------------------


class TestAdrStatusCheck:
    """ADR-sourced entries require ## Status section with Accepted value."""

    def test_accepted_adr_passes(self, tmp_path: Path) -> None:
        adr_file = tmp_path / "ADR-001.md"
        adr_file.write_text("# ADR-001\n\n## Status\n\nAccepted\n")
        entry = _entry(
            target="adr-target",
            claim_type="architecture-decision",
            paths=[str(adr_file)],
            area="architecture",
        )
        reg = _registry(version="1", entries=[entry])
        errors = validate_registry_schema(reg, repo_root=tmp_path)
        assert errors == []

    def test_non_accepted_adr_fails(self, tmp_path: Path) -> None:
        adr_file = tmp_path / "ADR-002.md"
        adr_file.write_text("# ADR-002\n\n## Status\n\nDraft\n")
        entry = _entry(
            target="adr-target-draft",
            claim_type="architecture-decision",
            paths=[str(adr_file)],
            area="architecture",
        )
        reg = _registry(version="1", entries=[entry])
        errors = validate_registry_schema(reg, repo_root=tmp_path)
        assert len(errors) >= 1
        assert any("non-Accepted" in e or "Accepted" in e for e in errors)


# -------------------------------------------------------------------
# Unrecognized claim type (REQ-008 case 5)
# -------------------------------------------------------------------


class TestClaimTypeValidation:
    """Claim types outside the 13 defined types must fail."""

    def test_unrecognized_claim_type_fails(self) -> None:
        entry = _entry(
            target="bad-claim-target",
            claim_type="invalid-claim-type",
            paths=["config/documentation_canonical_sources.toml"],
            area="governance",
        )
        reg = _registry(version="1", entries=[entry])
        errors = validate_registry_schema(reg)
        assert len(errors) >= 1
        assert any("unrecognized claim_type" in e for e in errors)

    @pytest.mark.parametrize("claim_type", sorted(VALID_CLAIM_TYPES))
    def test_all_valid_claim_types_pass(self, claim_type: str) -> None:
        # architecture-decision needs a real ADR file with ## Status / Accepted
        if claim_type == "architecture-decision":
            return  # handled separately below
        entry = _entry(
            target=f"valid-{claim_type}",
            claim_type=claim_type,
            paths=["config/documentation_canonical_sources.toml"],
            area="governance",
        )
        reg = _registry(version="1", entries=[entry])
        errors = validate_registry_schema(reg)
        assert errors == []

    def test_architecture_decision_with_valid_adr(self, tmp_path: Path) -> None:
        adr_file = tmp_path / "ADR-003.md"
        adr_file.write_text("# ADR-003\n\n## Status\n\nAccepted\n")
        entry = _entry(
            target="adr-valid",
            claim_type="architecture-decision",
            paths=[str(adr_file)],
            area="architecture",
        )
        reg = _registry(version="1", entries=[entry])
        errors = validate_registry_schema(reg, repo_root=tmp_path)
        assert errors == []


# -------------------------------------------------------------------
# Schema version mismatch (REQ-008 case 6)
# -------------------------------------------------------------------


class TestSchemaVersion:
    """Unsupported or missing version values must fail."""

    def test_unsupported_version_fails(self) -> None:
        entry = _entry(target="version-test", claim_type="functional-requirement")
        reg = _registry(version="99", entries=[entry])
        errors = validate_registry_schema(reg)
        assert len(errors) >= 1
        assert any("unsupported registry version" in e for e in errors)

    def test_missing_version_fails(self) -> None:
        entry = _entry(target="no-version-test", claim_type="functional-requirement")
        reg = CanonicalSourceRegistry(version="", entries=[entry])
        errors = validate_registry_schema(reg)
        assert len(errors) >= 1
        assert any("unsupported registry version" in e for e in errors)

    def test_supported_version_passes(self) -> None:
        entry = _entry(target="good-version-test", claim_type="functional-requirement")
        reg = _registry(version="1", entries=[entry])
        errors = validate_registry_schema(reg)
        assert errors == []


# -------------------------------------------------------------------
# load_registry() file-parsing exercise
# -------------------------------------------------------------------


class TestLoadRegistry:
    """Exercise load_registry() against a real TOML file via tmp_path."""

    def test_load_registry_from_file(self, tmp_path: Path) -> None:
        toml_content = """version = "1"

[[canonical_sources]]
decision_target = "test-target"
claim_type = "functional-requirement"
source_paths = ["config/documentation_canonical_sources.toml"]
area = "governance"
"""
        toml_file = tmp_path / "registry.toml"
        toml_file.write_text(toml_content)
        registry = load_registry(path=toml_file)
        assert registry.version == "1"
        assert len(registry.entries) == 1
        assert registry.entries[0].decision_target == "test-target"
        assert registry.entries[0].claim_type == "functional-requirement"


# -------------------------------------------------------------------
# T01-T05 fixture regression tests (adrchk010 AC-01-AC-05)
# Written test-first per procedure docs 08/01; T03/T05 pass at baseline
# as behavior locks, T01/T02/T04 fail until the seq 01 fixes land.
# -------------------------------------------------------------------

_T01_ADR_TEXT = "# ADR-099\n\n## Status\n\nDraft\n"

# Helpers targeted for removal by REQ-004 (vulture min-confidence 60 audit,
# 2026-11-19). find_non_accepted_adr is removed after the REQ-001 fix.
_REMOVED_REGISTRYENTRY_HELPERS: tuple[str, ...] = (
    "add_note",
    "add_source_path",
    "can_have_multiple_sources",
    "clear_source_paths",
    "clone",
    "contains_path",
    "count_source_paths",
    "create_dummy_entry",
    "create_valid_entry",
    "deduplicate_source_paths",
    "diff",
    "filter_source_paths_by_contains",
    "filter_source_paths_by_prefix",
    "filter_source_paths_by_suffix",
    "find_existing_paths",
    "find_missing_paths",
    "from_toml_table",
    "get_source_path_depth",
    "get_all_source_paths",
    "get_average_source_path_length",
    "get_effective_area",
    "get_first_source_path",
    "get_last_source_path",
    "get_longest_source_path",
    "get_max_source_path_depth",
    "get_min_source_path_depth",
    "get_shortest_source_path",
    "get_source_path_all_exist",
    "get_source_path_any_exists",
    "get_source_path_at_index",
    "get_source_path_base_names",
    "get_source_path_common_prefix",
    "get_source_path_difference",
    "get_source_path_directories",
    "get_source_path_disjoint_from",
    "get_source_path_equal_to",
    "get_source_path_extensions",
    "get_source_path_files",
    "get_source_path_intersection",
    "get_source_path_none_exist",
    "get_source_path_partial_overlap",
    "get_source_path_proper_subset_of",
    "get_source_path_proper_superset_of",
    "get_source_path_subset_of",
    "get_source_path_superset_of",
    "get_source_path_symmetric_difference",
    "get_source_path_union",
    "get_source_paths_in_directory",
    "get_source_paths_outside_directory",
    "get_source_paths_with_extension",
    "get_source_paths_without_extension",
    "get_total_source_path_length",
    "get_unique_source_paths",
    "has_multiple_sources",
    "is_architecture_decision",
    "is_multi_source",
    "is_runtime_behavior",
    "is_single_source",
    "merge_notes",
    "remove_source_path",
    "replace_source_paths",
    "requires_single_source_enforcement",
    "reverse_source_paths",
    "sort_source_paths",
    "to_toml_string",
    "to_toml_table",
    "update_source_path",
    "validate_claim_type",
    "validate_not_empty",
    "validate_path_exists",
)

_REMOVED_REGISTRY_HELPERS: tuple[str, ...] = (
    "add_entry",
    "clone_with_version",
    "copy",
    "count_by_area",
    "count_by_claim_type",
    "deduplicate",
    "diff",
    "export_csv",
    "export_toml",
    "filter_by_area",
    "filter_by_claim_type",
    "find_conflicts",
    "find_duplicate_entries",
    "find_missing_adr_status",
    "find_multi_source_on_single_source_type",
    "find_non_accepted_adr",
    "find_orphaned_sources",
    "find_unrecognized_claim_types",
    "from_json",
    "from_toml",
    "generate_report",
    "get_entries_by_area",
    "get_entries_by_claim_type",
    "get_entries_for_target",
    "get_source_count",
    "has_multiple_sources",
    "merge",
    "report",
    "resolve_source_paths",
    "sort_by_area_then_target",
    "to_json",
)


class TestSingleSeverityNonAcceptedAdr:
    """AC-01/T01: a non-Accepted ADR reference is reported exactly once, as an
    error; validate_all must not duplicate the class as a warning (REQ-001)."""

    def _fixture_registry(self, tmp_path: Path) -> CanonicalSourceRegistry:
        adr_file = tmp_path / "ADR-draft.md"
        adr_file.write_text(_T01_ADR_TEXT)
        entry = _entry(
            target="adrchk010-severity",
            claim_type="architecture-decision",
            paths=[str(adr_file)],
            area="architecture",
        )
        return _registry(version="1", entries=[entry])

    def test_non_accepted_adr_reports_exactly_one_error(self, tmp_path: Path) -> None:
        reg = self._fixture_registry(tmp_path)
        errors = validate_registry_schema(reg, repo_root=tmp_path)
        assert len(errors) == 1
        assert "non-Accepted status 'Draft'" in errors[0]

    def test_validate_all_does_not_duplicate_as_warning(self, tmp_path: Path) -> None:
        reg = self._fixture_registry(tmp_path)
        result = reg.validate_all(tmp_path)
        assert len(result["errors"]) == 1
        assert result["warnings"] == []  # Plan AC-01: single severity only
        assert result["valid"] is False


class TestRepoRootAnchoring:
    """AC-02/T02: findings are identical from any cwd (REQ-002)."""

    def test_default_invocation_identical_from_foreign_cwd(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        rc_repo = main([])
        out_repo, err_repo = capsys.readouterr()
        monkeypatch.chdir(tmp_path)
        rc_foreign = main([])
        out_foreign, err_foreign = capsys.readouterr()
        assert rc_repo == 0  # clean repo registry (AC-12 baseline)
        assert (rc_foreign, out_foreign, err_foreign) == (rc_repo, out_repo, err_repo)

    def test_fixture_findings_identical_from_foreign_cwd(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        adr_file = tmp_path / "ADR-draft.md"
        adr_file.write_text(_T01_ADR_TEXT)
        registry_file = tmp_path / "registry.toml"
        registry_file.write_text(
            'version = "1"\n\n'
            "[[canonical_sources]]\n"
            'decision_target = "t02-repo-relative"\n'
            'claim_type = "functional-requirement"\n'
            'source_paths = ["config/documentation_canonical_sources.toml"]\n'
            'area = "governance"\n\n'
            "[[canonical_sources]]\n"
            'decision_target = "t02-draft-adr"\n'
            'claim_type = "architecture-decision"\n'
            f'source_paths = ["{adr_file}"]\n'
            'area = "architecture"\n'
        )
        argv = ["--registry", str(registry_file)]
        rc_repo = main(argv)
        out_repo, err_repo = capsys.readouterr()
        monkeypatch.chdir(tmp_path)
        rc_foreign = main(argv)
        out_foreign, err_foreign = capsys.readouterr()
        assert rc_repo == 1
        assert "non-Accepted status 'Draft'" in err_repo
        assert (rc_foreign, out_foreign, err_foreign) == (rc_repo, out_repo, err_repo)


class TestUnknownOptionGuard:
    """AC-03/T03: unknown options exit 2 (REQ-003, behavior lock)."""

    def test_unknown_option_exits_2(self, capsys: pytest.CaptureFixture[str]) -> None:
        with pytest.raises(SystemExit) as exc_info:
            main(["--unknown-option"])
        assert exc_info.value.code == 2
        _, err = capsys.readouterr()
        assert "unrecognized arguments" in err


class TestDeadCodeRemoved:
    """AC-04/T04: helpers on the audited REQ-004 removal list stay removed
    (UNK-03: keep anything a passing test exercises)."""

    @pytest.mark.parametrize("name", _REMOVED_REGISTRYENTRY_HELPERS)
    def test_registryentry_helper_removed(self, name: str) -> None:
        assert not hasattr(RegistryEntry, name)

    @pytest.mark.parametrize("name", _REMOVED_REGISTRY_HELPERS)
    def test_registry_helper_removed(self, name: str) -> None:
        assert not hasattr(CanonicalSourceRegistry, name)

    def test_surviving_entry_points_kept(self) -> None:
        assert hasattr(registry_module, "load_registry")
        assert hasattr(registry_module, "validate_registry_schema")
        assert hasattr(registry_module, "SINGLE_SOURCE_EXEMPTIONS")
        assert hasattr(RegistryEntry, "validate")
        assert hasattr(CanonicalSourceRegistry, "validate")
        assert hasattr(CanonicalSourceRegistry, "validate_all")


class TestDeterministicOutput:
    """AC-05/T05: repeated validation runs produce byte-identical findings
    (REQ-005, behavior lock)."""

    def _fixture_file(self, tmp_path: Path) -> Path:
        registry_file = tmp_path / "registry.toml"
        registry_file.write_text(
            'version = "1"\n\n'
            "[[canonical_sources]]\n"
            'decision_target = "t05-target"\n'
            'claim_type = "functional-requirement"\n'
            'source_paths = ["nonexistent/t05.md"]\n'
            'area = "governance"\n\n'
            "[[canonical_sources]]\n"
            'decision_target = "t05-target"\n'
            'claim_type = "functional-requirement"\n'
            'source_paths = ["config/documentation_canonical_sources.toml"]\n'
            'area = "governance"\n\n'
            "[[canonical_sources]]\n"
            'decision_target = "t05-bad-claim"\n'
            'claim_type = "invalid-claim-type"\n'
            'source_paths = ["config/documentation_canonical_sources.toml"]\n'
            'area = "governance"\n'
        )
        return registry_file

    def test_cli_output_byte_identical_across_runs(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        registry_file = self._fixture_file(tmp_path)
        argv = ["--registry", str(registry_file)]
        rc_first = main(argv)
        out_first, err_first = capsys.readouterr()
        rc_second = main(argv)
        out_second, err_second = capsys.readouterr()
        assert rc_first == 1
        assert (rc_second, out_second, err_second) == (rc_first, out_first, err_first)

    def test_schema_validation_identical_across_runs(self, tmp_path: Path) -> None:
        registry_file = self._fixture_file(tmp_path)
        reg = load_registry(path=registry_file)
        first = validate_registry_schema(reg, repo_root=tmp_path)
        second = validate_registry_schema(reg, repo_root=tmp_path)
        assert first == second
        assert len(first) >= 3
