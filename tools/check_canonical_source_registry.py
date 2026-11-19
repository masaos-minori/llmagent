#!/usr/bin/env python3
"""check_canonical_source_registry.py — Schema conformance validator for the Canonical Source Registry.

Validates the registry file against the M-01-04 canonical source registry schema:
dataclass definition, path existence, single-normative-source enforcement,
claim-type membership, ADR-status checking, and schema-version verification.

Built against the registry file's actual current fields:
  decision_target: str, claim_type: str, source_paths: list[str], area: str, notes: str | None

Not built against this Plan's originally-proposed nested-table schema.

Usage:
    uv run python tools/check_canonical_source_registry.py [--registry <path>]
"""

from __future__ import annotations

import argparse
import sys
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

VALID_CLAIM_TYPES: frozenset[str] = frozenset(
    (
        "architecture-decision",
        "functional-requirement",
        "external-behavior",
        "api-contract",
        "runtime-behavior",
        "verification-contract",
        "production-effective-value",
        "configuration-schema",
        "database-schema",
        "operational-procedure",
        "security-policy",
        "documentation-metadata",
        "unconfirmed-claim",
    )
)

SINGLE_SOURCE_EXEMPTIONS: frozenset[str] = frozenset(("runtime-behavior",))

SUPPORTED_VERSIONS: frozenset[str] = frozenset(("1",))

# Repository root anchored so findings are identical from any cwd (REQ-002);
# mirrors the Path(__file__)-anchored resolution in check_canonical_source_conflicts.py.
REPO_ROOT: Path = Path(__file__).resolve().parent.parent

DEFAULT_REGISTRY_PATH: Path = (
    REPO_ROOT / "config" / "documentation_canonical_sources.toml"
)


def _find_status_section(content: str) -> str | None:
    """Find the ## Status section value in an ADR document."""
    lines = content.split("\n")
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped == "## Status":
            # Next non-empty line after the header
            for j in range(i + 1, len(lines)):
                next_line = lines[j].strip()
                if next_line:
                    return next_line
            return None
    return None


@dataclass
class RegistryEntry:
    decision_target: str
    claim_type: str
    source_paths: list[str]
    area: str
    notes: str | None = None

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> RegistryEntry:
        return cls(
            decision_target=d["decision_target"],
            claim_type=d["claim_type"],
            source_paths=list(d["source_paths"]),
            area=d["area"],
            notes=d.get("notes"),
        )

    def to_dict(self) -> dict[str, Any]:
        # Kept by UNK-03: referenced cross-module by
        # tools/check_canonical_source_conflicts.py (detect_all_conflicts).
        result: dict[str, Any] = {
            "decision_target": self.decision_target,
            "claim_type": self.claim_type,
            "source_paths": self.source_paths,
            "area": self.area,
        }
        if self.notes is not None:
            result["notes"] = self.notes
        return result

    def validate(self, repo_root: Path) -> list[str]:
        errors: list[str] = []
        if not self.decision_target.strip():
            errors.append(f"empty decision_target for entry in area '{self.area}'")
        if not self.claim_type.strip():
            errors.append(
                f"empty claim_type for entry targeting '{self.decision_target}'"
            )
        if self.claim_type not in VALID_CLAIM_TYPES:
            errors.append(
                f"unrecognized claim_type '{self.claim_type}' for entry targeting '{self.decision_target}'; "
                f"must be one of {sorted(VALID_CLAIM_TYPES)}"
            )
        if not self.source_paths:
            errors.append(
                f"empty source_paths for entry targeting '{self.decision_target}'"
            )
        else:
            for p in self.source_paths:
                resolved = (repo_root / p).resolve()
                if not resolved.exists():
                    errors.append(f"source path does not exist: {p}")
            if (
                len(self.source_paths) > 1
                and self.claim_type not in SINGLE_SOURCE_EXEMPTIONS
            ):
                errors.append(
                    f"multiple source_paths ({len(self.source_paths)}) for claim_type '{self.claim_type}' "
                    f"on entry targeting '{self.decision_target}': only 'runtime-behavior' allows multiple sources"
                )
        if not self.area.strip():
            errors.append(f"empty area for entry targeting '{self.decision_target}'")
        if self.claim_type == "architecture-decision":
            for p in self.source_paths:
                resolved = (repo_root / p).resolve()
                if resolved.exists() and resolved.is_file():
                    try:
                        content = resolved.read_text(encoding="utf-8")
                        status_line = _find_status_section(content)
                        if status_line is None:
                            errors.append(
                                f"ADR-sourced entry missing ## Status section: {p}"
                            )
                        elif status_line != "Accepted":
                            errors.append(
                                f"ADR-sourced entry has non-Accepted status '{status_line}': {p}"
                            )
                    except OSError as exc:
                        errors.append(f"cannot read ADR file {p}: {exc}")
        return errors

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, RegistryEntry):
            return NotImplemented
        return (
            self.decision_target == other.decision_target
            and self.claim_type == other.claim_type
            and self.source_paths == other.source_paths
            and self.area == other.area
            and self.notes == other.notes
        )

    def __hash__(self) -> int:
        return hash(
            (
                self.decision_target,
                self.claim_type,
                tuple(self.source_paths),
                self.area,
                self.notes,
            )
        )

    def __repr__(self) -> str:
        return f"RegistryEntry({self.decision_target!r}, {self.claim_type!r})"

    def __str__(self) -> str:
        return f"{self.decision_target} ({self.claim_type}): {self.source_paths}"


@dataclass
class CanonicalSourceRegistry:
    version: str
    entries: list[RegistryEntry] = field(default_factory=list)

    def validate(self, repo_root: Path) -> list[str]:
        errors: list[str] = []
        if self.version not in SUPPORTED_VERSIONS:
            errors.append(
                f"unsupported registry version '{self.version}'; supported versions: {sorted(SUPPORTED_VERSIONS)}"
            )
        seen_targets: set[tuple[str, str]] = set()
        for entry in self.entries:
            key = (entry.decision_target, entry.claim_type)
            if key in seen_targets:
                errors.append(
                    f"duplicate entry for decision_target='{key[0]}', claim_type='{key[1]}'"
                )
            seen_targets.add(key)
            errors.extend(entry.validate(repo_root))
        return errors

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, CanonicalSourceRegistry):
            return NotImplemented
        return self.version == other.version and self.entries == other.entries

    def __hash__(self) -> int:
        return hash((self.version, tuple(e.__hash__() for e in self.entries)))

    def __repr__(self) -> str:
        return f"CanonicalSourceRegistry(version={self.version!r}, entries={len(self.entries)})"

    def __str__(self) -> str:
        lines = [f"CanonicalSourceRegistry(version={self.version!r})"]
        for i, entry in enumerate(self.entries):
            lines.append(
                f"  [{i}] {entry.decision_target} ({entry.claim_type}): {entry.source_paths}"
            )
        return "\n".join(lines)

    def summary(self) -> dict[str, Any]:
        areas: dict[str, int] = {}
        claim_types: dict[str, int] = {}
        for entry in self.entries:
            areas[entry.area] = areas.get(entry.area, 0) + 1
            claim_types[entry.claim_type] = claim_types.get(entry.claim_type, 0) + 1
        return {
            "version": self.version,
            "total_entries": len(self.entries),
            "areas": areas,
            "claim_types": claim_types,
        }

    @staticmethod
    def from_path(path: Path) -> CanonicalSourceRegistry:
        with open(path, "rb") as f:
            data = tomllib.load(f)
        version = data.get("version", "")
        entries_data = data.get("canonical_sources", [])
        entries = [RegistryEntry.from_dict(e) for e in entries_data]
        return CanonicalSourceRegistry(version=version, entries=entries)

    def validate_all(self, repo_root: Path) -> dict[str, Any]:
        result: dict[str, Any] = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "summary": {},
        }
        errors = self.validate(repo_root)
        if errors:
            result["valid"] = False
            result["errors"].extend(errors)
        # Plan adrchk010 AC-01 (REQ-001): the non-Accepted ADR class is reported
        # only as an error by RegistryEntry.validate; the duplicate warning class
        # via find_non_accepted_adr was removed (conflicts-side warning is owned
        # by check_canonical_source_conflicts.py).
        result["summary"] = self.summary()
        return result

    def __iter__(self):
        return iter(self.entries)

    def __len__(self):
        return len(self.entries)

    def __getitem__(self, index):
        return self.entries[index]

    def __contains__(self, item):
        if isinstance(item, RegistryEntry):
            return item in self.entries
        return False

    def __bool__(self):
        return bool(self.entries)


def load_registry(path: Path | None = None) -> CanonicalSourceRegistry:
    """Load the registry from a TOML file."""
    if path is None:
        path = DEFAULT_REGISTRY_PATH
    return CanonicalSourceRegistry.from_path(path)


def validate_registry_schema(
    registry: CanonicalSourceRegistry, repo_root: Path | None = None
) -> list[str]:
    """Validate the registry schema and return a list of error strings."""
    if repo_root is None:
        repo_root = REPO_ROOT
    return registry.validate(repo_root)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate the Canonical Source Registry"
    )
    parser.add_argument(
        "--registry", type=str, default=None, help="Path to the registry TOML file"
    )
    args = parser.parse_args(argv)
    registry_path = Path(args.registry) if args.registry else DEFAULT_REGISTRY_PATH
    if not registry_path.exists():
        print(f"Registry file not found: {registry_path}", file=sys.stderr)
        return 1
    try:
        registry = CanonicalSourceRegistry.from_path(registry_path)
    except (tomllib.TOMLDecodeError, FileNotFoundError) as exc:
        print(f"Failed to parse registry file: {exc}", file=sys.stderr)
        return 1
    repo_root = REPO_ROOT
    errors = registry.validate(repo_root)
    if errors:
        print(f"Validation failed with {len(errors)} error(s):", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1
    print("Registry validation passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
