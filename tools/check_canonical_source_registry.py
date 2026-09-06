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

DEFAULT_REGISTRY_PATH: Path = Path("config/documentation_canonical_sources.toml")


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

    def clone(self) -> RegistryEntry:
        return RegistryEntry(
            decision_target=self.decision_target,
            claim_type=self.claim_type,
            source_paths=list(self.source_paths),
            area=self.area,
            notes=self.notes,
        )

    def diff(self, other: RegistryEntry) -> dict[str, Any]:
        diffs: dict[str, Any] = {}
        if self.decision_target != other.decision_target:
            diffs["decision_target"] = (self.decision_target, other.decision_target)
        if self.claim_type != other.claim_type:
            diffs["claim_type"] = (self.claim_type, other.claim_type)
        if self.source_paths != other.source_paths:
            diffs["source_paths"] = (self.source_paths, other.source_paths)
        if self.area != other.area:
            diffs["area"] = (self.area, other.area)
        if self.notes != other.notes:
            diffs["notes"] = (self.notes, other.notes)
        return diffs

    def get_effective_area(self) -> str:
        return self.area or "unassigned"

    def is_architecture_decision(self) -> bool:
        return self.claim_type == "architecture-decision"

    def is_runtime_behavior(self) -> bool:
        return self.claim_type == "runtime-behavior"

    def has_multiple_sources(self) -> bool:
        return len(self.source_paths) > 1

    def requires_single_source_enforcement(self) -> bool:
        return self.claim_type not in SINGLE_SOURCE_EXEMPTIONS

    def can_have_multiple_sources(self) -> bool:
        return self.claim_type in SINGLE_SOURCE_EXEMPTIONS

    def validate_path_exists(self, repo_root: Path) -> bool:
        for p in self.source_paths:
            resolved = (repo_root / p).resolve()
            if not resolved.exists():
                return False
        return True

    def validate_claim_type(self) -> bool:
        return self.claim_type in VALID_CLAIM_TYPES

    def validate_not_empty(self) -> bool:
        return (
            bool(self.decision_target.strip())
            and bool(self.claim_type.strip())
            and bool(self.area.strip())
        )

    def find_missing_paths(self, repo_root: Path) -> list[str]:
        missing: list[str] = []
        for p in self.source_paths:
            resolved = (repo_root / p).resolve()
            if not resolved.exists():
                missing.append(p)
        return missing

    def find_existing_paths(self, repo_root: Path) -> list[Path]:
        existing: list[Path] = []
        for p in self.source_paths:
            resolved = (repo_root / p).resolve()
            if resolved.exists():
                existing.append(resolved)
        return existing

    @staticmethod
    def create_valid_entry(
        target: str,
        claim_type: str,
        paths: list[str],
        area: str,
        notes: str | None = None,
    ) -> RegistryEntry:
        return RegistryEntry(
            decision_target=target,
            claim_type=claim_type,
            source_paths=paths,
            area=area,
            notes=notes,
        )

    @staticmethod
    def from_toml_table(table: dict[str, Any]) -> RegistryEntry:
        return RegistryEntry.from_dict(table)

    def to_toml_table(self) -> dict[str, Any]:
        return self.to_dict()

    def get_all_source_paths(self) -> list[str]:
        return list(self.source_paths)

    def get_unique_source_paths(self) -> list[str]:
        seen: set[str] = set()
        unique: list[str] = []
        for p in self.source_paths:
            if p not in seen:
                seen.add(p)
                unique.append(p)
        return unique

    def count_source_paths(self) -> int:
        return len(self.source_paths)

    def is_single_source(self) -> bool:
        return len(self.source_paths) == 1

    def is_multi_source(self) -> bool:
        return len(self.source_paths) > 1

    def add_note(self, note: str) -> None:
        if self.notes is None:
            self.notes = note
        else:
            self.notes += "\n" + note

    def merge_notes(self, other: RegistryEntry) -> None:
        if other.notes:
            if self.notes:
                self.notes += "\n" + other.notes
            else:
                self.notes = other.notes

    def sort_source_paths(self) -> None:
        self.source_paths.sort()

    def reverse_source_paths(self) -> None:
        self.source_paths.reverse()

    def deduplicate_source_paths(self) -> None:
        seen: set[str] = set()
        unique: list[str] = []
        for p in self.source_paths:
            if p not in seen:
                seen.add(p)
                unique.append(p)
        self.source_paths = unique

    def contains_path(self, path: str) -> bool:
        return path in self.source_paths

    def remove_source_path(self, path: str) -> bool:
        if path in self.source_paths:
            self.source_paths.remove(path)
            return True
        return False

    def add_source_path(self, path: str) -> None:
        if path not in self.source_paths:
            self.source_paths.append(path)

    def clear_source_paths(self) -> None:
        self.source_paths.clear()

    def replace_source_paths(self, new_paths: list[str]) -> None:
        self.source_paths = list(new_paths)

    def update_source_path(self, old: str, new: str) -> bool:
        if old in self.source_paths:
            idx = self.source_paths.index(old)
            self.source_paths[idx] = new
            return True
        return False

    def get_first_source_path(self) -> str | None:
        if self.source_paths:
            return self.source_paths[0]
        return None

    def get_last_source_path(self) -> str | None:
        if self.source_paths:
            return self.source_paths[-1]
        return None

    def get_source_path_at_index(self, index: int) -> str | None:
        if 0 <= index < len(self.source_paths):
            return self.source_paths[index]
        return None

    def get_shortest_source_path(self) -> str | None:
        if not self.source_paths:
            return None
        return min(self.source_paths, key=len)

    def get_longest_source_path(self) -> str | None:
        if not self.source_paths:
            return None
        return max(self.source_paths, key=len)

    def get_average_source_path_length(self) -> float:
        if not self.source_paths:
            return 0.0
        return sum(len(p) for p in self.source_paths) / len(self.source_paths)

    def get_total_source_path_length(self) -> int:
        return sum(len(p) for p in self.source_paths)

    def get_source_path_depth(self, path: str) -> int:
        parts = Path(path).parts
        return len(parts) - 1

    def get_max_source_path_depth(self) -> int:
        if not self.source_paths:
            return 0
        return max(self.get_source_path_depth(p) for p in self.source_paths)

    def get_min_source_path_depth(self) -> int:
        if not self.source_paths:
            return 0
        return min(self.get_source_path_depth(p) for p in self.source_paths)

    def get_source_path_directories(self) -> set[str]:
        dirs: set[str] = set()
        for p in self.source_paths:
            parent = Path(p).parent
            if str(parent) != ".":
                dirs.add(str(parent))
        return dirs

    def get_source_path_files(self) -> set[str]:
        files: set[str] = set()
        for p in self.source_paths:
            name = Path(p).name
            if name:
                files.add(name)
        return files

    def get_source_path_extensions(self) -> set[str]:
        exts: set[str] = set()
        for p in self.source_paths:
            ext = Path(p).suffix
            if ext:
                exts.add(ext)
        return exts

    def get_source_path_base_names(self) -> set[str]:
        bases: set[str] = set()
        for p in self.source_paths:
            base = Path(p).stem
            if base:
                bases.add(base)
        return bases

    def filter_source_paths_by_prefix(self, prefix: str) -> list[str]:
        return [p for p in self.source_paths if p.startswith(prefix)]

    def filter_source_paths_by_suffix(self, suffix: str) -> list[str]:
        return [p for p in self.source_paths if p.endswith(suffix)]

    def filter_source_paths_by_contains(self, substring: str) -> list[str]:
        return [p for p in self.source_paths if substring in p]

    def get_source_paths_with_extension(self, ext: str) -> list[str]:
        return [p for p in self.source_paths if p.endswith(ext)]

    def get_source_paths_without_extension(self, ext: str) -> list[str]:
        return [p for p in self.source_paths if not p.endswith(ext)]

    def get_source_paths_in_directory(self, directory: str) -> list[str]:
        return [p for p in self.source_paths if p.startswith(directory)]

    def get_source_paths_outside_directory(self, directory: str) -> list[str]:
        return [p for p in self.source_paths if not p.startswith(directory)]

    def get_source_path_common_prefix(self) -> str:
        if not self.source_paths:
            return ""
        common_parts: list[str] = []
        for parts in zip(*(Path(p).parts for p in self.source_paths)):
            if len(set(parts)) == 1:
                common_parts.append(parts[0])
            else:
                break
        return "/".join(common_parts)

    def get_source_path_intersection(self, other: RegistryEntry) -> list[str]:
        my_set = set(self.source_paths)
        other_set = set(other.source_paths)
        return sorted(my_set & other_set)

    def get_source_path_union(self, other: RegistryEntry) -> list[str]:
        my_set = set(self.source_paths)
        other_set = set(other.source_paths)
        return sorted(my_set | other_set)

    def get_source_path_difference(self, other: RegistryEntry) -> list[str]:
        my_set = set(self.source_paths)
        other_set = set(other.source_paths)
        return sorted(my_set - other_set)

    def get_source_path_symmetric_difference(self, other: RegistryEntry) -> list[str]:
        my_set = set(self.source_paths)
        other_set = set(other.source_paths)
        return sorted(my_set ^ other_set)

    def get_source_path_subset_of(self, other: RegistryEntry) -> bool:
        my_set = set(self.source_paths)
        other_set = set(other.source_paths)
        return my_set.issubset(other_set)

    def get_source_path_superset_of(self, other: RegistryEntry) -> bool:
        my_set = set(self.source_paths)
        other_set = set(other.source_paths)
        return my_set.issuperset(other_set)

    def get_source_path_disjoint_from(self, other: RegistryEntry) -> bool:
        my_set = set(self.source_paths)
        other_set = set(other.source_paths)
        return my_set.isdisjoint(other_set)

    def get_source_path_equal_to(self, other: RegistryEntry) -> bool:
        my_set = set(self.source_paths)
        other_set = set(other.source_paths)
        return my_set == other_set

    def get_source_path_proper_subset_of(self, other: RegistryEntry) -> bool:
        my_set = set(self.source_paths)
        other_set = set(other.source_paths)
        return my_set < other_set

    def get_source_path_proper_superset_of(self, other: RegistryEntry) -> bool:
        my_set = set(self.source_paths)
        other_set = set(other.source_paths)
        return my_set > other_set

    def get_source_path_partial_overlap(self, other: RegistryEntry) -> bool:
        my_set = set(self.source_paths)
        other_set = set(other.source_paths)
        return (
            bool(my_set & other_set)
            and not my_set.issubset(other_set)
            and not my_set.issuperset(other_set)
        )

    def get_source_path_all_exist(self, repo_root: Path) -> bool:
        return all((repo_root / p).resolve().exists() for p in self.source_paths)

    def get_source_path_any_exists(self, repo_root: Path) -> bool:
        return any((repo_root / p).resolve().exists() for p in self.source_paths)

    def get_source_path_none_exist(self, repo_root: Path) -> bool:
        return not any((repo_root / p).resolve().exists() for p in self.source_paths)

    @staticmethod
    def create_dummy_entry() -> RegistryEntry:
        return RegistryEntry(
            decision_target="",
            claim_type="",
            source_paths=[],
            area="",
            notes=None,
        )

    def to_toml_string(self) -> str:
        lines = [f'decision_target = "{self.decision_target}"']
        lines.append(f'claim_type = "{self.claim_type}"')
        lines.append(f"source_paths = {self.source_paths}")
        lines.append(f'area = "{self.area}"')
        if self.notes is not None:
            lines.append(f'notes = "{self.notes}"')
        return "\n".join(lines)


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

    def add_entry(self, entry: RegistryEntry) -> None:
        self.entries.append(entry)

    def get_entries_by_area(self, area: str) -> list[RegistryEntry]:
        return [e for e in self.entries if e.area == area]

    def get_entries_for_target(self, target: str) -> list[RegistryEntry]:
        return [e for e in self.entries if e.decision_target == target]

    def get_entries_by_claim_type(self, claim_type: str) -> list[RegistryEntry]:
        return [e for e in self.entries if e.claim_type == claim_type]

    def find_conflicts(self) -> list[tuple[RegistryEntry, RegistryEntry]]:
        conflicts: list[tuple[RegistryEntry, RegistryEntry]] = []
        seen: dict[tuple[str, str], RegistryEntry] = {}
        for entry in self.entries:
            key = (entry.decision_target, entry.claim_type)
            if key in seen:
                conflicts.append((seen[key], entry))
            seen[key] = entry
        return conflicts

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

    def export_toml(self) -> str:
        lines = [f'version = "{self.version}"']
        for entry in self.entries:
            lines.append("")
            lines.append("[[canonical_sources]]")
            for k, v in entry.to_dict().items():
                if isinstance(v, list):
                    lines.append(f"{k} = {v}")
                elif isinstance(v, str):
                    lines.append(f'{k} = "{v}"')
                else:
                    lines.append(f"{k} = {v}")
        return "\n".join(lines)

    @staticmethod
    def from_toml(toml_str: str) -> CanonicalSourceRegistry:
        data = tomllib.loads(toml_str)
        version = data.get("version", "")
        entries_data = data.get("canonical_sources", [])
        entries = [RegistryEntry.from_dict(e) for e in entries_data]
        return CanonicalSourceRegistry(version=version, entries=entries)

    @staticmethod
    def from_path(path: Path) -> CanonicalSourceRegistry:
        with open(path, "rb") as f:
            data = tomllib.load(f)
        version = data.get("version", "")
        entries_data = data.get("canonical_sources", [])
        entries = [RegistryEntry.from_dict(e) for e in entries_data]
        return CanonicalSourceRegistry(version=version, entries=entries)

    def resolve_source_paths(self, repo_root: Path) -> list[Path]:
        resolved: list[Path] = []
        for entry in self.entries:
            for p in entry.source_paths:
                full = (repo_root / p).resolve()
                if full.exists():
                    resolved.append(full)
        return resolved

    def report(self, repo_root: Path) -> str:
        errors = self.validate(repo_root)
        lines = [
            "Registry validation results:",
            f"  Version: {self.version}",
            f"  Entries: {len(self.entries)}",
        ]
        if errors:
            lines.append(f"  Errors: {len(errors)}")
            for err in errors:
                lines.append(f"    - {err}")
        else:
            lines.append("  Status: OK")
        return "\n".join(lines)

    def merge(self, other: CanonicalSourceRegistry) -> CanonicalSourceRegistry:
        merged_entries = list(self.entries)
        existing_keys = {(e.decision_target, e.claim_type) for e in self.entries}
        for entry in other.entries:
            key = (entry.decision_target, entry.claim_type)
            if key not in existing_keys:
                merged_entries.append(entry)
        return CanonicalSourceRegistry(version=self.version, entries=merged_entries)

    def filter_by_area(self, area: str) -> CanonicalSourceRegistry:
        filtered = [e for e in self.entries if e.area == area]
        return CanonicalSourceRegistry(version=self.version, entries=filtered)

    def filter_by_claim_type(self, claim_type: str) -> CanonicalSourceRegistry:
        filtered = [e for e in self.entries if e.claim_type == claim_type]
        return CanonicalSourceRegistry(version=self.version, entries=filtered)

    def diff(self, other: CanonicalSourceRegistry) -> dict[str, list[RegistryEntry]]:
        my_keys = {(e.decision_target, e.claim_type) for e in self.entries}
        other_keys = {(e.decision_target, e.claim_type) for e in other.entries}
        added = [
            e
            for e in other.entries
            if (e.decision_target, e.claim_type) in other_keys - my_keys
        ]
        removed = [
            e
            for e in self.entries
            if (e.decision_target, e.claim_type) in my_keys - other_keys
        ]
        changed: list[RegistryEntry] = []
        for e in self.entries:
            key = (e.decision_target, e.claim_type)
            if key in other_keys:
                other_entry = next(
                    o for o in other.entries if (o.decision_target, o.claim_type) == key
                )
                if e != other_entry:
                    changed.append(e)
        return {"added": added, "removed": removed, "changed": changed}

    def copy(self) -> CanonicalSourceRegistry:
        return CanonicalSourceRegistry(
            version=self.version,
            entries=[RegistryEntry(**e.to_dict()) for e in self.entries],
        )

    def clone_with_version(self, new_version: str) -> CanonicalSourceRegistry:
        return CanonicalSourceRegistry(version=new_version, entries=list(self.entries))

    def sort_by_area_then_target(self) -> CanonicalSourceRegistry:
        sorted_entries = sorted(self.entries, key=lambda e: (e.area, e.decision_target))
        return CanonicalSourceRegistry(version=self.version, entries=sorted_entries)

    def deduplicate(self) -> CanonicalSourceRegistry:
        seen: dict[tuple[str, str], RegistryEntry] = {}
        deduped: list[RegistryEntry] = []
        for entry in self.entries:
            key = (entry.decision_target, entry.claim_type)
            if key not in seen:
                seen[key] = entry
                deduped.append(entry)
        return CanonicalSourceRegistry(version=self.version, entries=deduped)

    def count_by_area(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for entry in self.entries:
            counts[entry.area] = counts.get(entry.area, 0) + 1
        return counts

    def count_by_claim_type(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for entry in self.entries:
            counts[entry.claim_type] = counts.get(entry.claim_type, 0) + 1
        return counts

    def has_multiple_sources(self, target: str, claim_type: str) -> bool:
        entries = self.get_entries_for_target(target)
        matching = [e for e in entries if e.claim_type == claim_type]
        return any(len(e.source_paths) > 1 for e in matching)

    def get_source_count(self, target: str, claim_type: str) -> int:
        entries = self.get_entries_for_target(target)
        matching = [e for e in entries if e.claim_type == claim_type]
        total = 0
        for e in matching:
            total += len(e.source_paths)
        return total

    def find_orphaned_sources(self, repo_root: Path) -> list[str]:
        orphaned: list[str] = []
        for entry in self.entries:
            for p in entry.source_paths:
                resolved = (repo_root / p).resolve()
                if not resolved.exists():
                    orphaned.append(p)
        return orphaned

    def find_missing_adr_status(self, repo_root: Path) -> list[str]:
        missing: list[str] = []
        for entry in self.entries:
            if entry.claim_type == "architecture-decision":
                for p in entry.source_paths:
                    resolved = (repo_root / p).resolve()
                    if resolved.exists() and resolved.is_file():
                        try:
                            content = resolved.read_text(encoding="utf-8")
                            status_line = _find_status_section(content)
                            if status_line is None:
                                missing.append(p)
                        except OSError:
                            pass
        return missing

    def find_non_accepted_adr(self, repo_root: Path) -> list[str]:
        non_accepted: list[str] = []
        for entry in self.entries:
            if entry.claim_type == "architecture-decision":
                for p in entry.source_paths:
                    resolved = (repo_root / p).resolve()
                    if resolved.exists() and resolved.is_file():
                        try:
                            content = resolved.read_text(encoding="utf-8")
                            status_line = _find_status_section(content)
                            if status_line is not None and status_line != "Accepted":
                                non_accepted.append(f"{p}: {status_line}")
                        except OSError:
                            pass
        return non_accepted

    def find_unrecognized_claim_types(self) -> list[str]:
        unrecognized: list[str] = []
        for entry in self.entries:
            if entry.claim_type not in VALID_CLAIM_TYPES:
                unrecognized.append(
                    f"'{entry.claim_type}' (target: '{entry.decision_target}')"
                )
        return unrecognized

    def find_multi_source_on_single_source_type(self) -> list[str]:
        violations: list[str] = []
        for entry in self.entries:
            if (
                len(entry.source_paths) > 1
                and entry.claim_type not in SINGLE_SOURCE_EXEMPTIONS
            ):
                violations.append(
                    f"'{entry.claim_type}' on '{entry.decision_target}': {len(entry.source_paths)} sources"
                )
        return violations

    def find_duplicate_entries(self) -> list[tuple[str, str]]:
        seen: dict[tuple[str, str], int] = {}
        duplicates: list[tuple[str, str]] = []
        for entry in self.entries:
            key = (entry.decision_target, entry.claim_type)
            if key in seen:
                if key not in duplicates:
                    duplicates.append(key)
            seen[key] = seen.get(key, 0) + 1
        return duplicates

    def validate_all(self, repo_root: Path) -> dict[str, Any]:
        result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "summary": {},
        }
        errors = self.validate(repo_root)
        if errors:
            result["valid"] = False
            result["errors"].extend(errors)
        warnings = self.find_non_accepted_adr(repo_root)
        if warnings:
            result["warnings"].extend(warnings)
        result["summary"] = self.summary()
        return result

    def generate_report(self, repo_root: Path) -> str:
        result = self.validate_all(repo_root)
        lines = [
            "=" * 60,
            "Canonical Source Registry Validation Report",
            "=" * 60,
            f"Version: {self.version}",
            f"Total entries: {len(self.entries)}",
            "",
        ]
        summary = result.get("summary", {})
        areas = summary.get("areas", {})
        claim_types = summary.get("claim_types", {})
        if areas:
            lines.append("Areas:")
            for area, count in sorted(areas.items()):
                lines.append(f"  - {area}: {count}")
            lines.append("")
        if claim_types:
            lines.append("Claim types:")
            for ct, count in sorted(claim_types.items()):
                lines.append(f"  - {ct}: {count}")
            lines.append("")
        if result.get("errors"):
            lines.append("Errors:")
            for err in result["errors"]:
                lines.append(f"  - {err}")
            lines.append("")
        if result.get("warnings"):
            lines.append("Warnings:")
            for warn in result["warnings"]:
                lines.append(f"  - {warn}")
            lines.append("")
        if result["valid"]:
            lines.append("Status: OK")
        else:
            lines.append("Status: FAILED")
        lines.append("=" * 60)
        return "\n".join(lines)

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

    def export_csv(self) -> str:
        lines = ["decision_target,claim_type,source_paths,area,notes"]
        for entry in self.entries:
            source_paths_str = ";".join(entry.source_paths)
            notes_str = entry.notes.replace(",", ";") if entry.notes else ""
            lines.append(
                f'{entry.decision_target},{entry.claim_type},"{source_paths_str}",{entry.area},"{notes_str}"'
            )
        return "\n".join(lines)

    def to_json(self) -> str:
        import json

        return json.dumps(
            {
                "version": self.version,
                "entries": [e.to_dict() for e in self.entries],
            },
            indent=2,
            ensure_ascii=False,
        )

    @classmethod
    def from_json(cls, json_str: str) -> CanonicalSourceRegistry:
        import json

        data = json.loads(json_str)
        version = data.get("version", "")
        entries_data = data.get("entries", [])
        entries = [RegistryEntry.from_dict(e) for e in entries_data]
        return cls(version=version, entries=entries)


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
        repo_root = Path.cwd()
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
    repo_root = Path.cwd()
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
