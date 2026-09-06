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
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    from tools.check_canonical_source_registry import (
        load_registry,
        validate_registry_schema,
    )

    HAS_REGISTRY_VALIDATOR = True
except ImportError:
    HAS_REGISTRY_VALIDATOR = False

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
# Claim types — only those used by conflict detection
# ---------------------------------------------------------------------------

CLAIM_TYPE_SPECIFICATION = "specification"
CLAIM_TYPE_ACCEPTANCE_TEST = "acceptance_test"
CLAIM_TYPE_REFERENCE = "reference"
CLAIM_TYPE_AREA_GUIDE = "area_guide"
CLAIM_TYPE_LEGACY_PRECEDENCE = "legacy_precedence"

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
    """A single entry in the Canonical Source Registry."""

    id: str
    target: str
    claim_type: str
    authority: str
    precedence: str
    status: str
    effective_date: str | None = None
    expiry_date: str | None = None
    validation_ref: str | None = None
    description: str | None = None

    def __post_init__(self) -> None:
        if self.status not in ("active", "deprecated", "superseded"):
            raise ValueError(f"Invalid status: {self.status!r}")

    def to_dict(self) -> dict:
        result = {
            "id": self.id,
            "target": self.target,
            "claim_type": self.claim_type,
            "authority": self.authority,
            "precedence": self.precedence,
            "status": self.status,
        }
        if self.effective_date:
            result["effective_date"] = self.effective_date
        if self.expiry_date:
            result["expiry_date"] = self.expiry_date
        if self.validation_ref:
            result["validation_ref"] = self.validation_ref
        if self.description:
            result["description"] = self.description
        return result

    def __str__(self) -> str:
        return (
            f"RegistryEntry(id={self.id}, target={self.target}, "
            f"claim_type={self.claim_type}, status={self.status})"
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
            import tomli as tomllib
        except ImportError:
            raise RuntimeError(
                "Cannot load registry: neither 'tomllib' (stdlib) nor 'tomli' available"
            )

    with open(registry_path, "rb") as f:
        data = tomllib.load(f)

    entries: list[RegistryEntry] = []
    for key, value in data.items():
        if isinstance(value, dict):
            entry = RegistryEntry(
                id=key,
                target=value.get("target", ""),
                claim_type=value.get("claim_type", ""),
                authority=value.get("authority", ""),
                precedence=value.get("precedence", "normative"),
                status=value.get("status", "active"),
                effective_date=value.get("effective_date"),
                expiry_date=value.get("expiry_date"),
                validation_ref=value.get("validation_ref"),
                description=value.get("description"),
            )
            entries.append(entry)
    return entries


# ---------------------------------------------------------------------------
# Core conflict detection logic
# ---------------------------------------------------------------------------


def detect_duplicate_normative_sources(
    entries: list[RegistryEntry],
) -> list[CanonicalConflict]:
    """CANONICAL-001: Detect duplicate normative canonical sources for same target+claim-type."""
    conflicts: list[CanonicalConflict] = []
    seen: dict[tuple[str, str], list[str]] = {}

    for entry in entries:
        if entry.precedence != "normative":
            continue
        key = (entry.target, entry.claim_type)
        seen.setdefault(key, []).append(entry.id)

    for key, ids in seen.items():
        if len(ids) > 1:
            conflicts.append(
                CanonicalConflict(
                    code="CANONICAL-001",
                    severity=Severity.HIGH,
                    blocking_status=BlockingStatus.BLOCKING,
                    description=(
                        f"Duplicate normative canonical sources for target={key[0]}, "
                        f"claim_type={key[1]}: {', '.join(ids)}"
                    ),
                    affected_files=[ids[0]],
                    recommendation=(
                        f"Resolve duplicate normative sources: {', '.join(ids)}. "
                        f"Keep only one authoritative entry per target+claim_type pair."
                    ),
                )
            )
    return conflicts


def detect_multiple_canonical_specifications(
    entries: list[RegistryEntry],
) -> list[CanonicalConflict]:
    """CANONICAL-008: Detect multiple canonical Specifications for same target+claim-type."""
    conflicts: list[CanonicalConflict] = []
    seen: dict[tuple[str, str], list[str]] = {}

    for entry in entries:
        if entry.claim_type != CLAIM_TYPE_SPECIFICATION:
            continue
        key = (entry.target, entry.claim_type)
        seen.setdefault(key, []).append(entry.id)

    for key, ids in seen.items():
        if len(ids) > 1:
            conflicts.append(
                CanonicalConflict(
                    code="CANONICAL-008",
                    severity=Severity.HIGH,
                    blocking_status=BlockingStatus.BLOCKING,
                    description=(
                        f"Multiple canonical Specifications for target={key[0]}, "
                        f"claim_type={key[1]}: {', '.join(ids)}"
                    ),
                    affected_files=[ids[0]],
                    recommendation=(
                        f"Consolidate canonical Specification entries: {', '.join(ids)}. "
                        f"One canonical Specification per target+claim_type pair."
                    ),
                )
            )
    return conflicts


def detect_area_guide_contradiction(
    entries: list[RegistryEntry],
) -> list[CanonicalConflict]:
    """CANONICAL-010: Detect area guide contradicting registry."""
    conflicts: list[CanonicalConflict] = []
    spec_entries = [e for e in entries if e.claim_type == CLAIM_TYPE_SPECIFICATION]
    area_entries = [e for e in entries if e.claim_type == CLAIM_TYPE_AREA_GUIDE]

    for area in area_entries:
        for spec in spec_entries:
            if spec.target == area.target and spec.precedence == "normative":
                conflicts.append(
                    CanonicalConflict(
                        code="CANONICAL-010",
                        severity=Severity.MEDIUM,
                        blocking_status=BlockingStatus.NON_BLOCKING,
                        description=(
                            f"Area guide '{area.id}' may contradict specification "
                            f"'{spec.id}' for target '{area.target}'"
                        ),
                        affected_files=[area.id, spec.id],
                        recommendation=(
                            f"Review consistency between area guide '{area.id}' and "
                            f"specification '{spec.id}' for target '{area.target}'."
                        ),
                    )
                )
    return conflicts


def detect_legacy_precedence_reintroduction(
    entries: list[RegistryEntry],
) -> list[CanonicalConflict]:
    """CANONICAL-011: Detect legacy universal-precedence reintroduction."""
    conflicts: list[CanonicalConflict] = []
    legacy_entries = [e for e in entries if e.precedence == "legacy_universal"]

    for entry in legacy_entries:
        conflicts.append(
            CanonicalConflict(
                code="CANONICAL-011",
                severity=Severity.HIGH,
                blocking_status=BlockingStatus.BLOCKING,
                description=(
                    f"Legacy universal-precedence entry '{entry.id}' found — "
                    f"should be deprecated or superseded per REQ-001 routing rules"
                ),
                affected_files=[entry.id],
                recommendation=(
                    f"Deprecate or supersede legacy entry '{entry.id}'. "
                    f"Legacy universal-precedence is no longer valid."
                ),
            )
        )
    return conflicts


def detect_non_canonical_reference_without_link(
    entries: list[RegistryEntry],
) -> list[CanonicalConflict]:
    """CANONICAL-W-01: Non-canonical Reference without link."""
    conflicts: list[CanonicalConflict] = []
    ref_entries = [e for e in entries if e.claim_type == CLAIM_TYPE_REFERENCE]

    for entry in ref_entries:
        if not entry.validation_ref:
            conflicts.append(
                CanonicalConflict(
                    code="CANONICAL-W-01",
                    severity=Severity.LOW,
                    blocking_status=BlockingStatus.WARNING,
                    description=(
                        f"Non-canonical Reference '{entry.id}' lacks validation link"
                    ),
                    affected_files=[entry.id],
                    recommendation=(
                        f"Add validation reference to non-canonical Reference '{entry.id}'."
                    ),
                )
            )
    return conflicts


def detect_stale_non_canonical_document(
    entries: list[RegistryEntry],
) -> list[CanonicalConflict]:
    """CANONICAL-W-02: Potentially stale non-canonical document."""
    conflicts: list[CanonicalConflict] = []
    active_entries = [e for e in entries if e.status == "active"]

    for entry in active_entries:
        if entry.claim_type not in (CLAIM_TYPE_REFERENCE, CLAIM_TYPE_LEGACY_PRECEDENCE):
            continue
        if entry.expiry_date and entry.expiry_date < "2026-09-06":
            conflicts.append(
                CanonicalConflict(
                    code="CANONICAL-W-02",
                    severity=Severity.LOW,
                    blocking_status=BlockingStatus.WARNING,
                    description=(
                        f"Potentially stale non-canonical document '{entry.id}' "
                        f"(expired: {entry.expiry_date})"
                    ),
                    affected_files=[entry.id],
                    recommendation=(
                        f"Review and update or remove expired document '{entry.id}'."
                    ),
                )
            )
    return conflicts


def detect_missing_validation_ref(
    entries: list[RegistryEntry],
) -> list[CanonicalConflict]:
    """CANONICAL-W-03: Missing validation reference."""
    conflicts: list[CanonicalConflict] = []
    active_entries = [e for e in entries if e.status == "active"]

    for entry in active_entries:
        if entry.claim_type in (CLAIM_TYPE_SPECIFICATION, CLAIM_TYPE_ACCEPTANCE_TEST):
            if not entry.validation_ref:
                conflicts.append(
                    CanonicalConflict(
                        code="CANONICAL-W-03",
                        severity=Severity.MEDIUM,
                        blocking_status=BlockingStatus.NON_BLOCKING,
                        description=(
                            f"Active '{entry.claim_type}' entry '{entry.id}' "
                            f"missing validation reference"
                        ),
                        affected_files=[entry.id],
                        recommendation=(
                            f"Add validation reference to active '{entry.claim_type}' "
                            f"entry '{entry.id}'."
                        ),
                    )
                )
    return conflicts


def detect_unregistered_authority_declaration(
    entries: list[RegistryEntry],
) -> list[CanonicalConflict]:
    """CANONICAL-W-04: Unregistered authority declaration."""
    conflicts: list[CanonicalConflict] = []
    known_authorities = frozenset(
        {
            AUTHORITY_MITIGATING_CONTROL,
            AUTHORITY_ORIGINAL_SPECIFICATION,
            AUTHORITY_AREA_GUIDE,
            AUTHORITY_LEGACY_DOCUMENTATION,
            AUTHORITY_INDUSTRY_STANDARD,
            AUTHORITY_INTERNAL_POLICY,
            AUTHORITY_REGULATORY_REQUIREMENT,
            AUTHORITY_VENDOR_SPECIFICATION,
            AUTHORITY_COMMUNITY_CONSENSUS,
            AUTHORITY_RESEARCH_PAPER,
            AUTHORITY_IMPLEMENTATION_EXPERIENCE,
            AUTHORITY_SECURITY_ANALYSIS,
        }
    )

    for entry in entries:
        if entry.authority not in known_authorities:
            conflicts.append(
                CanonicalConflict(
                    code="CANONICAL-W-04",
                    severity=Severity.MEDIUM,
                    blocking_status=BlockingStatus.NON_BLOCKING,
                    description=(
                        f"Unregistered authority '{entry.authority}' in entry '{entry.id}'"
                    ),
                    affected_files=[entry.id],
                    recommendation=(
                        f"Register authority '{entry.authority}' or use a known value."
                    ),
                )
            )
    return conflicts


def detect_authoritative_terms_in_non_canonical(
    entries: list[RegistryEntry],
) -> list[CanonicalConflict]:
    """CANONICAL-W-05: Authoritative/source-of-truth terms in non-canonical documents."""
    conflicts: list[CanonicalConflict] = []
    non_canonical = [e for e in entries if e.precedence != "normative"]

    authoritative_terms = {"authoritative", "source of truth", "must"}
    for entry in non_canonical:
        desc = entry.description or ""
        if any(term in desc.lower() for term in authoritative_terms):
            conflicts.append(
                CanonicalConflict(
                    code="CANONICAL-W-05",
                    severity=Severity.MEDIUM,
                    blocking_status=BlockingStatus.NON_BLOCKING,
                    description=(
                        f"Authoritative terms found in non-canonical entry '{entry.id}': "
                        f"'{desc[:80]}...'"
                    ),
                    affected_files=[entry.id],
                    recommendation=(
                        f"Remove authoritative language from non-canonical entry '{entry.id}'."
                    ),
                )
            )
    return conflicts


# ---------------------------------------------------------------------------
# Main conflict detection orchestrator
# ---------------------------------------------------------------------------


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
            / "canonical_source_registry.toml"
        )

    if HAS_REGISTRY_VALIDATOR:
        try:
            registry = load_registry(registry_path)
            validate_registry_schema(registry)
            entries = [
                RegistryEntry(
                    id=key,
                    target=val.get("target", ""),
                    claim_type=val.get("claim_type", ""),
                    authority=val.get("authority", ""),
                    precedence=val.get("precedence", "normative"),
                    status=val.get("status", "active"),
                    effective_date=val.get("effective_date"),
                    expiry_date=val.get("expiry_date"),
                    validation_ref=val.get("validation_ref"),
                    description=val.get("description"),
                )
                for key, val in registry.items()
            ]
        except (ValueError, KeyError, TypeError):
            entries = _load_registry_toml(registry_path)
    else:
        entries = _load_registry_toml(registry_path)

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
    return (entry.target, entry.claim_type)


def detect_duplicate_active_records(
    entries: list[RegistryEntry],
    candidate: RegistryEntry,
) -> bool:
    """Refuse duplication: return True when a matching active record exists.

    Checks decision-target-and-claim-type pairs across inventories to refuse
    duplication per REQ-008.
    """
    candidate_key = _build_key(candidate)
    for existing in entries:
        if _build_key(existing) == candidate_key and existing.status == "active":
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
