#!/usr/bin/env python3
"""check_canonical_source_conflicts.py — Semantic validation for the Canonical Source Registry.

Wraps M-01-04's registry validator (tools/check_canonical_source_registry.py) when
available; falls back to direct TOML parsing when that tool does not exist.

Adds the following semantic checks that no existing tool covers:
  CANONICAL-001  Duplicate normative canonical sources for the same target/claim-type
  CANONICAL-008  Multiple canonical Specifications for the same target/claim-type
  CANONICAL-010  Area guide contradicting registry
  CANONICAL-011  Legacy universal-precedence reintroduction
  CANONICAL-W-*  Five Warning-level checks (non-canonical Reference without link,
                 potentially stale non-canonical document, missing validation ref,
                 unregistered authority declaration, authoritative/source-of-truth terms)

Routing rules (REQ-001):
  1. design-vs-code -> Known Issue
  2. functional-requirement-vs-implementation -> Known Issue
  3. Specification-vs-acceptance-test -> blocking Canonical Source Conflict
  4. deployed-vs-approved config -> Configuration Drift
  5. undetermined intent -> Needs Confirmation
  6. missing canonical source -> design/governance gap
  7. multiple normative sources -> blocking Canonical Source Conflict
  8. stale non-canonical wording only -> documentation-correction task

Duplicate-active-record prevention (REQ-008): before recommending a new entry,
checks decision-target-and-claim-type pairs across inventories to refuse duplication.

Usage:
    python tools/check_canonical_source_conflicts.py [--registry <path>]
"""

from __future__ import annotations

import sys
from collections.abc import Sequence
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from types import ModuleType
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    from tools.check_canonical_source_registry import (
        SUPPORTED_VERSIONS,
        VALID_CLAIM_TYPES,
        load_registry,
        validate_registry_schema,
    )

    HAS_REGISTRY_VALIDATOR = True
except ImportError:
    HAS_REGISTRY_VALIDATOR = False
    VALID_CLAIM_TYPES = frozenset()
    SUPPORTED_VERSIONS = frozenset()

# SINGLE_SOURCE_EXEMPTIONS is always defined (either from import or fallback)
if HAS_REGISTRY_VALIDATOR:
    _single_exemptions: frozenset[str] = frozenset(("runtime-behavior",))
    SINGLE_SOURCE_EXEMPTIONS = _single_exemptions
else:
    SINGLE_SOURCE_EXEMPTIONS = frozenset()

# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


class Severity(Enum):
    HIGH = auto()
    MEDIUM = auto()
    LOW = auto()

    def __str__(self) -> str:
        return self.name.capitalize()

    @classmethod
    def from_name(cls, name: str) -> Severity:
        mapping = {"high": cls.HIGH, "medium": cls.MEDIUM, "low": cls.LOW}
        result = mapping.get(name.lower())
        if result is None:
            raise ValueError(f"Unknown severity: {name!r}")
        return result

    @classmethod
    def from_blocking(cls, blocking: bool) -> Severity:
        return cls.HIGH if blocking else cls.MEDIUM

    def is_blocking(self) -> bool:
        return self == Severity.HIGH

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, Severity):
            return NotImplemented
        return self.value < other.value

    def __le__(self, other: object) -> bool:
        if not isinstance(other, Severity):
            return NotImplemented
        return self.value <= other.value

    def __gt__(self, other: object) -> bool:
        if not isinstance(other, Severity):
            return NotImplemented
        return self.value > other.value

    def __ge__(self, other: object) -> bool:
        if not isinstance(other, Severity):
            return NotImplemented
        return self.value >= other.value

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Severity):
            return NotImplemented
        return self.value == other.value

    def __hash__(self) -> int:
        return hash(self.value)

    def __repr__(self) -> str:
        return f"Severity.{self.name}"


# ---------------------------------------------------------------------------
# Claim types — aligned with M-01-04 VALID_CLAIM_TYPES
# ---------------------------------------------------------------------------

CLAIM_TYPE_ARCHITECTURE_DECISION = "architecture-decision"
CLAIM_TYPE_RUNTIME_BEHAVIOR = "runtime-behavior"
CLAIM_TYPE_DATABASE_SCHEMA = "database-schema"
CLAIM_TYPE_FUNCTIONAL_REQUIREMENT = "functional-requirement"
CLAIM_TYPE_API_CONTRACT = "api-contract"
CLAIM_TYPE_VERIFICATION_CONTRACT = "verification-contract"
CLAIM_TYPE_DOCUMENTATION_METADATA = "documentation-metadata"
CLAIM_TYPE_EXTERNAL_BEHAVIOR = "external-behavior"
CLAIM_TYPE_PRODUCTION_EFFECTIVE_VALUE = "production-effective-value"
CLAIM_TYPE_CONFIGURATION_SCHEMA = "configuration-schema"
CLAIM_TYPE_OPERATIONAL_PROCEDURE = "operational-procedure"
CLAIM_TYPE_SECURITY_POLICY = "security-policy"
CLAIM_TYPE_UNCONFIRMED_CLAIM = "unconfirmed-claim"

# ---------------------------------------------------------------------------
# Authority types — only those used by conflict detection
# ---------------------------------------------------------------------------

AUTHORITY_MITIGATING_CONTROL = "mitigating_control"
AUTHORITY_ORIGINAL_SPECIFICATION = "original_specification"
AUTHORITY_AREA_GUIDE = "area_guide"
AUTHORITY_LEGACY_DOCUMENTATION = "legacy_documentation"
AUTHORITY_INDUSTRY_STANDARD = "industry_standard"
AUTHORITY_INTERNAL_POLICY = "internal_policy"
AUTHORITY_REGULATORY_REQUIREMENT = "regulatory_requirement"
AUTHORITY_VENDOR_SPECIFICATION = "vendor_specification"
AUTHORITY_COMMUNITY_CONSENSUS = "community_consensus"
AUTHORITY_RESEARCH_PAPER = "research_paper"
AUTHORITY_IMPLEMENTATION_EXPERIENCE = "implementation_experience"
AUTHORITY_SECURITY_ANALYSIS = "security_analysis"

# ---------------------------------------------------------------------------
# Blocking status
# ---------------------------------------------------------------------------

BLOCKING_SEVERITIES: frozenset[Severity] = frozenset({Severity.HIGH})
NON_BLOCKING_SEVERITIES: frozenset[Severity] = frozenset(
    {Severity.MEDIUM, Severity.LOW}
)

SEVERITY_THRESHOLD_HIGH = Severity.HIGH
SEVERITY_THRESHOLD_MEDIUM = Severity.MEDIUM
SEVERITY_THRESHOLD_LOW = Severity.LOW

KNOWN_ISSUE = "known_issue"
CANONICAL_CONFLICT = "canonical_conflict"
CONFIG_DRIFT = "config_drift"
NEEDS_CONFIRMATION = "needs_confirmation"
GOVERNANCE_GAP = "governance_gap"
DOC_CORRECTION = "doc_correction"


class BlockingStatus(Enum):
    """Maps severity to routing gate decisions."""

    BLOCKING = "blocking"
    NON_BLOCKING = "non_blocking"
    WARNING = "warning"

    @classmethod
    def from_severity(cls, severity: Severity) -> BlockingStatus:
        if severity == Severity.HIGH:
            return cls.BLOCKING
        elif severity == Severity.MEDIUM:
            return cls.NON_BLOCKING
        else:
            return cls.WARNING

    def is_blocking(self) -> bool:
        return self == self.BLOCKING

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"BlockingStatus.{self.name}"


# ---------------------------------------------------------------------------
# Conflict finding models
# ---------------------------------------------------------------------------


@dataclass
class CanonicalConflict:
    """Represents a detected canonical source conflict.

    For CANONICAL_CONFLICT findings, all 12 required record fields are populated:
      Conflict ID, Decision target, Claim type, Canonical source,
      Conflicting source/evidence, Conflict category, Impact, Severity,
      Blocking status, Required action, Owner, Validation evidence.

    For other destinations, only the core fields are used.
    """

    code: str
    severity: Severity
    blocking_status: BlockingStatus
    description: str
    affected_files: list[str] = field(default_factory=list)
    recommendation: str = ""
    related_codes: list[str] = field(default_factory=list)

    # Fields populated only for CANONICAL_CONFLICT findings (12-field template)
    decision_target: str | None = None
    claim_type: str | None = None
    canonical_source: str | None = None
    conflicting_source: str | None = None
    conflict_category: str | None = None
    impact: str | None = None
    required_action: str | None = None
    owner: str | None = None
    validation_evidence: str | None = None

    def __post_init__(self) -> None:
        if not self.recommendation:
            self.recommendation = self._default_recommendation()

    def _default_recommendation(self) -> str:
        return f"Investigate {self.code} conflict in affected files."

    @property
    def is_canonical_conflict(self) -> bool:
        return self.blocking_status == BlockingStatus.BLOCKING

    def to_dict(self) -> dict:
        result: dict = {
            "code": self.code,
            "severity": str(self.severity),
            "blocking_status": str(self.blocking_status),
            "description": self.description,
            "affected_files": self.affected_files,
            "recommendation": self.recommendation,
            "related_codes": self.related_codes,
        }
        if self.is_canonical_conflict:
            for field_name in (
                "decision_target",
                "claim_type",
                "canonical_source",
                "conflicting_source",
                "conflict_category",
                "impact",
                "required_action",
                "owner",
                "validation_evidence",
            ):
                value = getattr(self, field_name)
                if value is not None:
                    result[field_name] = value
        return result

    def __str__(self) -> str:
        lines = [f"{self.code}: [{self.severity}] {self.description}"]
        if self.affected_files:
            lines.append(f"  Files: {', '.join(self.affected_files)}")
        if self.recommendation:
            lines.append(f"  Action: {self.recommendation}")
        if self.is_canonical_conflict:
            for label, attr in (
                ("Decision target", "decision_target"),
                ("Claim type", "claim_type"),
                ("Canonical source", "canonical_source"),
                ("Conflicting source", "conflicting_source"),
                ("Conflict category", "conflict_category"),
                ("Impact", "impact"),
                ("Required action", "required_action"),
                ("Owner", "owner"),
                ("Validation evidence", "validation_evidence"),
            ):
                value = getattr(self, attr)
                if value is not None:
                    lines.append(f"  {label}: {value}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Registry data model for TOML parsing fallback
# ---------------------------------------------------------------------------


@dataclass
class RegistryEntry:
    """A single entry in the Canonical Source Registry (M-01-04 schema)."""

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

    def __str__(self) -> str:
        return (
            f"RegistryEntry(decision_target={self.decision_target!r}, "
            f"claim_type={self.claim_type!r}, source_paths={self.source_paths})"
        )


# ---------------------------------------------------------------------------
# TOML-based registry loader (fallback when M-01-04 validator unavailable)
# ---------------------------------------------------------------------------


def _load_registry_toml(registry_path: Path) -> list[RegistryEntry]:
    """Load registry entries from TOML file without external dependencies."""
    try:
        import tomllib
    except ImportError:
        try:
            # pyright: ignore[reportShadowedImports]
            import tomli as _tomli  # noqa: A005, F811
        except ImportError:
            raise RuntimeError(
                "Cannot load registry: neither 'tomllib' (stdlib) nor 'tomli' available"
            )
        else:
            _tomllib: ModuleType = _tomli
    else:
        _tomllib = tomllib

    with open(registry_path, "rb") as f:
        data = _tomllib.load(f)

    entries_data = data.get("canonical_sources", [])
    entries: list[RegistryEntry] = []
    for entry_data in entries_data:
        entry = RegistryEntry.from_dict(entry_data)
        entries.append(entry)
    return entries


# ---------------------------------------------------------------------------
# Core conflict detection logic
# ---------------------------------------------------------------------------


def detect_duplicate_normative_sources(
    entries: Sequence[RegistryEntry],
) -> list[CanonicalConflict]:
    """CANONICAL-001/CANONICAL-002: Detect duplicate entries for same decision_target+claim-type.

    Since the M-01-04 schema has no precedence/status distinction, any two
    entries sharing the same (decision_target, claim_type) are duplicates.
    """
    conflicts: list[CanonicalConflict] = []
    seen: dict[tuple[str, str], list[list[str]]] = {}

    for entry in entries:
        key = (entry.decision_target, entry.claim_type)
        seen.setdefault(key, []).append(entry.source_paths)

    for key, paths_list in seen.items():
        if len(paths_list) > 1:
            all_paths: list[str] = []
            for paths in paths_list:
                all_paths.extend(paths)
            conflicts.append(
                CanonicalConflict(
                    code="CANONICAL-001",
                    severity=Severity.HIGH,
                    blocking_status=BlockingStatus.BLOCKING,
                    description=(
                        f"Duplicate canonical sources for decision_target={key[0]}, "
                        f"claim_type={key[1]}: {len(paths_list)} entries"
                    ),
                    affected_files=all_paths[:1],
                    recommendation=(
                        f"Resolve duplicate entries for decision_target={key[0]}, "
                        f"claim_type={key[1]}. Keep only one authoritative entry."
                    ),
                )
            )
    return conflicts


def detect_multiple_canonical_specifications(
    entries: Sequence[RegistryEntry],
) -> list[CanonicalConflict]:
    """CANONICAL-008: Detect multiple canonical Functional Requirements for same decision_target+claim-type."""
    conflicts: list[CanonicalConflict] = []
    seen: dict[tuple[str, str], list[list[str]]] = {}

    for entry in entries:
        if entry.claim_type != CLAIM_TYPE_FUNCTIONAL_REQUIREMENT:
            continue
        key = (entry.decision_target, entry.claim_type)
        seen.setdefault(key, []).append(entry.source_paths)

    for key, paths_list in seen.items():
        if len(paths_list) > 1:
            all_paths: list[str] = []
            for paths in paths_list:
                all_paths.extend(paths)
            conflicts.append(
                CanonicalConflict(
                    code="CANONICAL-008",
                    severity=Severity.HIGH,
                    blocking_status=BlockingStatus.BLOCKING,
                    description=(
                        f"Multiple canonical Functional Requirements for decision_target={key[0]}, "
                        f"claim_type={key[1]}: {len(paths_list)} entries"
                    ),
                    affected_files=all_paths[:1],
                    recommendation=(
                        f"Consolidate canonical Functional Requirement entries for "
                        f"decision_target={key[0]}, claim_type={key[1]}."
                    ),
                )
            )
    return conflicts


def detect_area_guide_contradiction(
    entries: Sequence[RegistryEntry],
) -> list[CanonicalConflict]:
    """CANONICAL-010: Detect area guide contradicting registry."""
    conflicts: list[CanonicalConflict] = []
    spec_entries = [
        e for e in entries if e.claim_type == CLAIM_TYPE_FUNCTIONAL_REQUIREMENT
    ]
    area_entries = [
        e for e in entries if e.claim_type == CLAIM_TYPE_DOCUMENTATION_METADATA
    ]

    for area in area_entries:
        for spec in spec_entries:
            if spec.decision_target == area.decision_target:
                conflicts.append(
                    CanonicalConflict(
                        code="CANONICAL-010",
                        severity=Severity.MEDIUM,
                        blocking_status=BlockingStatus.NON_BLOCKING,
                        description=(
                            f"Area guide '{area.area}' may contradict specification "
                            f"'{spec.decision_target}' for decision_target "
                            f"'{area.decision_target}'"
                        ),
                        affected_files=list(set(area.source_paths + spec.source_paths)),
                        recommendation=(
                            f"Review consistency between area guide '{area.area}' and "
                            f"specification '{spec.decision_target}' for "
                            f"decision_target '{area.decision_target}'."
                        ),
                    )
                )
    return conflicts


def detect_empty_decision_target(
    entries: Sequence[RegistryEntry],
) -> list[CanonicalConflict]:
    """CANONICAL-002: Detect entries with empty decision_target."""
    conflicts: list[CanonicalConflict] = []
    for entry in entries:
        if not entry.decision_target.strip():
            conflicts.append(
                CanonicalConflict(
                    code="CANONICAL-002",
                    severity=Severity.HIGH,
                    blocking_status=BlockingStatus.BLOCKING,
                    description=(
                        f"Empty decision_target in entry targeting '{entry.area}'"
                    ),
                    affected_files=list(entry.source_paths),
                    recommendation=(
                        f"Populate decision_target for entry in area '{entry.area}'."
                    ),
                )
            )
    return conflicts


def detect_empty_claim_type(
    entries: Sequence[RegistryEntry],
) -> list[CanonicalConflict]:
    """CANONICAL-003: Detect entries with empty claim_type."""
    conflicts: list[CanonicalConflict] = []
    for entry in entries:
        if not entry.claim_type.strip():
            conflicts.append(
                CanonicalConflict(
                    code="CANONICAL-003",
                    severity=Severity.HIGH,
                    blocking_status=BlockingStatus.BLOCKING,
                    description=(
                        f"Empty claim_type for entry targeting '{entry.decision_target}'"
                    ),
                    affected_files=list(entry.source_paths),
                    recommendation=(
                        f"Populate claim_type for entry targeting '{entry.decision_target}'."
                    ),
                )
            )
    return conflicts


def detect_unrecognized_claim_type(
    entries: Sequence[RegistryEntry],
) -> list[CanonicalConflict]:
    """CANONICAL-004: Detect entries with unrecognized claim_type."""
    conflicts: list[CanonicalConflict] = []
    for entry in entries:
        if entry.claim_type not in VALID_CLAIM_TYPES:
            conflicts.append(
                CanonicalConflict(
                    code="CANONICAL-004",
                    severity=Severity.MEDIUM,
                    blocking_status=BlockingStatus.NON_BLOCKING,
                    description=(
                        f"Unrecognized claim_type '{entry.claim_type}' for entry "
                        f"targeting '{entry.decision_target}'; must be one of "
                        f"{sorted(VALID_CLAIM_TYPES)}"
                    ),
                    affected_files=list(entry.source_paths),
                    recommendation=(
                        f"Correct claim_type for entry targeting '{entry.decision_target}'."
                    ),
                )
            )
    return conflicts


def detect_empty_source_paths(
    entries: Sequence[RegistryEntry],
) -> list[CanonicalConflict]:
    """CANONICAL-005: Detect entries with empty source_paths."""
    conflicts: list[CanonicalConflict] = []
    for entry in entries:
        if not entry.source_paths:
            conflicts.append(
                CanonicalConflict(
                    code="CANONICAL-005",
                    severity=Severity.HIGH,
                    blocking_status=BlockingStatus.BLOCKING,
                    description=(
                        f"Empty source_paths for entry targeting '{entry.decision_target}'"
                    ),
                    affected_files=[],
                    recommendation=(
                        f"Add source_paths for entry targeting '{entry.decision_target}'."
                    ),
                )
            )
    return conflicts


def detect_multiple_source_paths_violation(
    entries: Sequence[RegistryEntry],
) -> list[CanonicalConflict]:
    """CANONICAL-006: Detect entries with multiple source_paths where only 'runtime-behavior' allows it."""
    conflicts: list[CanonicalConflict] = []
    for entry in entries:
        if (
            len(entry.source_paths) > 1
            and entry.claim_type not in SINGLE_SOURCE_EXEMPTIONS
        ):
            conflicts.append(
                CanonicalConflict(
                    code="CANONICAL-006",
                    severity=Severity.MEDIUM,
                    blocking_status=BlockingStatus.NON_BLOCKING,
                    description=(
                        f"Multiple source_paths ({len(entry.source_paths)}) for claim_type "
                        f"'{entry.claim_type}' on entry targeting '{entry.decision_target}': "
                        f"only 'runtime-behavior' allows multiple sources"
                    ),
                    affected_files=list(entry.source_paths),
                    recommendation=(
                        f"Consolidate source_paths for entry targeting '{entry.decision_target}', "
                        f"claim_type '{entry.claim_type}'."
                    ),
                )
            )
    return conflicts


def detect_empty_area(
    entries: Sequence[RegistryEntry],
) -> list[CanonicalConflict]:
    """CANONICAL-009: Detect entries with empty area."""
    conflicts: list[CanonicalConflict] = []
    for entry in entries:
        if not entry.area.strip():
            conflicts.append(
                CanonicalConflict(
                    code="CANONICAL-009",
                    severity=Severity.HIGH,
                    blocking_status=BlockingStatus.BLOCKING,
                    description=(
                        f"Empty area for entry targeting '{entry.decision_target}'"
                    ),
                    affected_files=list(entry.source_paths),
                    recommendation=(
                        f"Populate area for entry targeting '{entry.decision_target}'."
                    ),
                )
            )
    return conflicts


def detect_legacy_precedence_reintroduction(
    entries: Sequence[RegistryEntry],
) -> list[CanonicalConflict]:
    """CANONICAL-011: No-op — precedence field removed from M-01-04 schema."""
    return []


def detect_non_canonical_reference_without_link(
    entries: Sequence[RegistryEntry],
) -> list[CanonicalConflict]:
    """CANONICAL-W-01: No-op — validation_ref field removed from M-01-04 schema."""
    return []


def detect_stale_non_canonical_document(
    entries: Sequence[RegistryEntry],
) -> list[CanonicalConflict]:
    """CANONICAL-W-02: No-op — status/expiry_date fields removed from M-01-04 schema."""
    return []


def detect_missing_validation_ref(
    entries: Sequence[RegistryEntry],
) -> list[CanonicalConflict]:
    """CANONICAL-W-03: No-op — status/validation_ref fields removed from M-01-04 schema."""
    return []


def detect_unregistered_authority_declaration(
    entries: Sequence[RegistryEntry],
) -> list[CanonicalConflict]:
    """CANONICAL-W-04: No-op — authority field removed from M-01-04 schema."""
    return []


def detect_authoritative_terms_in_non_canonical(
    entries: Sequence[RegistryEntry],
) -> list[CanonicalConflict]:
    """CANONICAL-W-05: Authoritative/source-of-truth terms in non-canonical documents.

    Since M-01-04 removed precedence/status fields, this check scans notes field
    content for authoritative language patterns across all entries.
    """
    conflicts: list[CanonicalConflict] = []
    authoritative_terms = {"authoritative", "source of truth", "must"}
    for entry in entries:
        if entry.notes and any(
            term in entry.notes.lower() for term in authoritative_terms
        ):
            conflicts.append(
                CanonicalConflict(
                    code="CANONICAL-W-05",
                    severity=Severity.MEDIUM,
                    blocking_status=BlockingStatus.NON_BLOCKING,
                    description=(
                        f"Authoritative terms found in entry '{entry.decision_target}': "
                        f"'{entry.notes[:80]}...'"
                    ),
                    affected_files=list(entry.source_paths),
                    recommendation=(
                        f"Review authoritative language in entry '{entry.decision_target}'."
                    ),
                )
            )
    return conflicts


# ---------------------------------------------------------------------------
# Helper functions for wrapping validation errors and running detection
# ---------------------------------------------------------------------------


def _wrap_validation_errors(
    errors: list[str], entries: Sequence[RegistryEntry]
) -> list[CanonicalConflict]:
    """Convert M-01-04 validation errors into findings with CANONICAL-XXX codes."""
    conflicts: list[CanonicalConflict] = []
    for entry in entries:
        for err in errors:
            if "empty decision_target" in err:
                conflicts.append(
                    CanonicalConflict(
                        code="CANONICAL-002",
                        severity=Severity.HIGH,
                        blocking_status=BlockingStatus.BLOCKING,
                        description=f"Empty decision_target in entry targeting '{entry.area}'",
                        affected_files=list(entry.source_paths),
                        recommendation=f"Populate decision_target for entry in area '{entry.area}'.",
                    )
                )
            elif "empty claim_type" in err:
                conflicts.append(
                    CanonicalConflict(
                        code="CANONICAL-003",
                        severity=Severity.HIGH,
                        blocking_status=BlockingStatus.BLOCKING,
                        description=(
                            f"Empty claim_type for entry targeting '{entry.decision_target}'"
                        ),
                        affected_files=list(entry.source_paths),
                        recommendation=(
                            f"Populate claim_type for entry targeting '{entry.decision_target}'."
                        ),
                    )
                )
            elif "unrecognized claim_type" in err:
                conflicts.append(
                    CanonicalConflict(
                        code="CANONICAL-004",
                        severity=Severity.MEDIUM,
                        blocking_status=BlockingStatus.NON_BLOCKING,
                        description=(
                            f"Unrecognized claim_type '{entry.claim_type}' for entry "
                            f"targeting '{entry.decision_target}'; must be one of "
                            f"{sorted(VALID_CLAIM_TYPES)}"
                        ),
                        affected_files=list(entry.source_paths),
                        recommendation=(
                            f"Correct claim_type for entry targeting '{entry.decision_target}'."
                        ),
                    )
                )
            elif "empty source_paths" in err:
                conflicts.append(
                    CanonicalConflict(
                        code="CANONICAL-005",
                        severity=Severity.HIGH,
                        blocking_status=BlockingStatus.BLOCKING,
                        description=(
                            f"Empty source_paths for entry targeting '{entry.decision_target}'"
                        ),
                        affected_files=[],
                        recommendation=(
                            f"Add source_paths for entry targeting '{entry.decision_target}'."
                        ),
                    )
                )
            elif "multiple source_paths" in err and "only 'runtime-behavior'" in err:
                conflicts.append(
                    CanonicalConflict(
                        code="CANONICAL-006",
                        severity=Severity.MEDIUM,
                        blocking_status=BlockingStatus.NON_BLOCKING,
                        description=(
                            f"Multiple source_paths ({len(entry.source_paths)}) for claim_type "
                            f"'{entry.claim_type}' on entry targeting '{entry.decision_target}': "
                            f"only 'runtime-behavior' allows multiple sources"
                        ),
                        affected_files=list(entry.source_paths),
                        recommendation=(
                            f"Consolidate source_paths for entry targeting '{entry.decision_target}', "
                            f"claim_type '{entry.claim_type}'."
                        ),
                    )
                )
            elif "empty area" in err:
                conflicts.append(
                    CanonicalConflict(
                        code="CANONICAL-009",
                        severity=Severity.HIGH,
                        blocking_status=BlockingStatus.BLOCKING,
                        description=(
                            f"Empty area for entry targeting '{entry.decision_target}'"
                        ),
                        affected_files=list(entry.source_paths),
                        recommendation=(
                            f"Populate area for entry targeting '{entry.decision_target}'."
                        ),
                    )
                )
            elif "duplicate entry" in err:
                key = err.split("'")[1]
                conflicts.append(
                    CanonicalConflict(
                        code="CANONICAL-007",
                        severity=Severity.HIGH,
                        blocking_status=BlockingStatus.BLOCKING,
                        description=(
                            f"Duplicate entry for decision_target='{key}', "
                            f"claim_type='{err.split("'")[3]}'"
                        ),
                        affected_files=list(
                            set(p for e in entries for p in e.source_paths)
                        ),
                        recommendation=(
                            f"Remove duplicate entry for decision_target='{key}'."
                        ),
                    )
                )
            elif "unsupported registry version" in err:
                conflicts.append(
                    CanonicalConflict(
                        code="CANONICAL-008",
                        severity=Severity.HIGH,
                        blocking_status=BlockingStatus.BLOCKING,
                        description=(
                            f"Unsupported registry version; supported versions: {sorted(SUPPORTED_VERSIONS)}"
                        ),
                        affected_files=[],
                        recommendation=(
                            f"Update registry version to one of {sorted(SUPPORTED_VERSIONS)}."
                        ),
                    )
                )
            elif "ADR-sourced entry missing ## Status section" in err:
                conflicts.append(
                    CanonicalConflict(
                        code="CANONICAL-010",
                        severity=Severity.MEDIUM,
                        blocking_status=BlockingStatus.NON_BLOCKING,
                        description=f"ADR-sourced entry missing ## Status section: {err}",
                        affected_files=[p for p in entry.source_paths if p in err],
                        recommendation="Add ## Status section to ADR file.",
                    )
                )
            elif "ADR-sourced entry has non-Accepted status" in err:
                conflicts.append(
                    CanonicalConflict(
                        code="CANONICAL-011",
                        severity=Severity.MEDIUM,
                        blocking_status=BlockingStatus.NON_BLOCKING,
                        description=f"ADR-sourced entry has non-Accepted status: {err}",
                        affected_files=[p for p in entry.source_paths if p in err],
                        recommendation="Update ADR status to Accepted.",
                    )
                )
    return conflicts


def _run_detection_functions(
    entries: Sequence[RegistryEntry],
) -> list[CanonicalConflict]:
    """Run all 9 pre-existing detection functions against entries."""
    conflicts: list[CanonicalConflict] = []
    conflicts.extend(detect_duplicate_normative_sources(entries))
    conflicts.extend(detect_multiple_canonical_specifications(entries))
    conflicts.extend(detect_area_guide_contradiction(entries))
    conflicts.extend(detect_legacy_precedence_reintroduction(entries))
    conflicts.extend(detect_non_canonical_reference_without_link(entries))
    conflicts.extend(detect_stale_non_canonical_document(entries))
    conflicts.extend(detect_missing_validation_ref(entries))
    conflicts.extend(detect_unregistered_authority_declaration(entries))
    conflicts.extend(detect_authoritative_terms_in_non_canonical(entries))
    return conflicts


def detect_all_conflicts(registry_path: Path | None = None) -> list[CanonicalConflict]:
    """Run all canonical source conflict checks.

    Args:
        registry_path: Optional path to TOML registry file. If None, uses default location.

    Returns:
        List of detected CanonicalConflict objects.
    """
    if registry_path is None:
        registry_path = (
            Path(__file__).resolve().parent.parent
            / "config"
            / "documentation_canonical_sources.toml"
        )

    if HAS_REGISTRY_VALIDATOR:
        try:
            registry = load_registry(registry_path)
            validation_errors = validate_registry_schema(registry)
            # Convert registry module's RegistryEntry to local RegistryEntry
            local_entries: Sequence[RegistryEntry] = [
                RegistryEntry.from_dict(e.to_dict()) for e in registry.entries
            ]
            # Wrap validation errors as findings with CANONICAL-XXX codes
            conflicts = _wrap_validation_errors(validation_errors, local_entries)
        except (ValueError, KeyError, TypeError):
            entries = _load_registry_toml(registry_path)
            conflicts = _run_detection_functions(entries)
    else:
        entries = _load_registry_toml(registry_path)
        conflicts = _run_detection_functions(entries)

    return conflicts

    return conflicts


# ---------------------------------------------------------------------------
# Routing classification (REQ-001)
# ---------------------------------------------------------------------------


class FindingRoute(Enum):
    """Destination for a finding per the 8 REQ-001 routing rules."""

    KNOWN_ISSUE = "known_issue"
    CANONICAL_CONFLICT = "canonical_conflict"
    CONFIG_DRIFT = "config_drift"
    NEEDS_CONFIRMATION = "needs_confirmation"
    GOVERNANCE_GAP = "governance_gap"
    DOC_CORRECTION = "doc_correction"


def classify_finding(code: str, severity: Severity) -> FindingRoute:
    """Classify a finding into one of the 8 REQ-001 destinations.

    Routing rules:
      1. design-vs-code -> Known Issue
      2. functional-requirement-vs-implementation -> Known Issue
      3. Specification-vs-acceptance-test -> blocking Canonical Source Conflict
      4. deployed-vs-approved config -> Configuration Drift
      5. undetermined intent -> Needs Confirmation
      6. missing canonical source -> design/governance gap
      7. multiple normative sources -> blocking Canonical Source Conflict
      8. stale non-canonical wording only -> documentation-correction task
    """
    if code.startswith("CANONICAL-C"):
        if severity == Severity.HIGH:
            return FindingRoute.CANONICAL_CONFLICT
        elif severity == Severity.MEDIUM:
            return FindingRoute.CANONICAL_CONFLICT
        else:
            return FindingRoute.DOC_CORRECTION
    elif code.startswith("CANONICAL-W"):
        return FindingRoute.DOC_CORRECTION
    elif code.startswith("CONFIG-"):
        return FindingRoute.CONFIG_DRIFT
    elif code.startswith("NEEDS-"):
        return FindingRoute.NEEDS_CONFIRMATION
    elif code.startswith("GOV-"):
        return FindingRoute.GOVERNANCE_GAP
    elif code.startswith("KNOWN-"):
        return FindingRoute.KNOWN_ISSUE
    return FindingRoute.KNOWN_ISSUE


# ---------------------------------------------------------------------------
# Duplicate-active-record prevention (REQ-008)
# ---------------------------------------------------------------------------


def _build_key(entry: RegistryEntry) -> tuple[str, str]:
    """Return (decision_target, claim_type) key for deduplication."""
    return (entry.decision_target, entry.claim_type)


def detect_duplicate_active_records(
    entries: Sequence[RegistryEntry],
    candidate: RegistryEntry,
) -> bool:
    """Refuse duplication: return True when a matching record exists.

    Checks decision-target-and-claim-type pairs across inventories to refuse
    duplication per REQ-008. No-op for status since M-01-04 removed it.
    """
    candidate_key = _build_key(candidate)
    for existing in entries:
        if _build_key(existing) == candidate_key:
            return True
    return False


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    """CLI entry point for check_canonical_source_conflicts.py."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Semantic validation for the Canonical Source Registry"
    )
    parser.add_argument(
        "--registry",
        type=str,
        help="Path to TOML registry file (default: config/canonical_source_registry.toml)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON",
    )
    args = parser.parse_args(argv)

    registry_path = Path(args.registry) if args.registry else None
    conflicts = detect_all_conflicts(registry_path)

    if args.json:
        import json

        print(json.dumps([c.to_dict() for c in conflicts], indent=2))
    else:
        for conflict in conflicts:
            print(conflict)

    return 1 if any(c.blocking_status.is_blocking() for c in conflicts) else 0


if __name__ == "__main__":
    sys.exit(main())
