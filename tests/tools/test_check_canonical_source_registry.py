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

from tools.check_canonical_source_registry import (
    VALID_CLAIM_TYPES,
    CanonicalSourceRegistry,
    RegistryEntry,
    load_registry,
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
