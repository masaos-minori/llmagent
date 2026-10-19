#!/usr/bin/env python3
"""check_canonical_document_prose.py — Warning-level scan for unregistered canonical-document prose.

Scans ``docs/*.md`` for prose that asserts a document (or code path) is the
canonical / normative / authoritative source for a topic or claim type, then flags
such unregistered claims when they either

  * overlap a source already registered in the Canonical Source Registry
    (``config/documentation_canonical_sources.toml``) -- REQ-002, or
  * share their extracted subject with a second claim across ``docs/`` -- REQ-003.

This closes part of the documented ``Partial`` gap for GV-009 without changing the
registration process. It emits only non-blocking WARNING findings and always exits
0 for a WARNING-only run, preserving the CI exit contract.

It does NOT compare registered entries against each other (that is
``check_canonical_source_conflicts.py`` / GV-019) and it does not implement the
multiple-primary-per-area check (GV-010); it reads the registry TOML directly and
read-only.

Usage:
    uv run python tools/check_canonical_document_prose.py [--registry <path>] [--docs <dir>]
"""

from __future__ import annotations

import argparse
import re
import sys
import tomllib
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

DEFAULT_REGISTRY_PATH: Path = Path("config/documentation_canonical_sources.toml")

# ---------------------------------------------------------------------------
# Severity / blocking-status enums (mirror the sibling canonical tools)
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

    def is_blocking(self) -> bool:
        return self == Severity.HIGH


class BlockingStatus(Enum):
    BLOCKING = "blocking"
    NON_BLOCKING = "non_blocking"
    WARNING = "warning"

    def is_blocking(self) -> bool:
        return self == BlockingStatus.BLOCKING

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"BlockingStatus.{self.name}"


# ---------------------------------------------------------------------------
# Reviewed pattern set (UNK-02)
#
# Case-insensitive phrases that ASSERT canonical/normative/authoritative status.
# The bare label form ("- Canonical Source: `path`") and incidental uses
# ("authoritative source of truth", "is not a canonical source") are intentionally
# excluded; negations are additionally dropped at scan time. Tuned against the
# current ``docs/`` corpus so benign mentions produce no finding (REQ-004).
# ---------------------------------------------------------------------------

_CANONICAL_PHRASES: tuple[str, ...] = (
    r"canonical source (?:for|of)",
    r"normative reference (?:for|of)",
    r"normative source (?:for|of)",
    r"authoritative source for",
    r"canonical authority (?:for|of)",
    r"canonical definition (?:for|of)",
)

_PATTERN_RE = re.compile(r"|".join(_CANONICAL_PHRASES), re.IGNORECASE)

# Negation immediately preceding an assertion ("not"/"never"/"no" within ~20 chars).
# The matched phrase always begins with the assertion keyword, and the scan window
# ends at the match start (so the keyword itself is excluded from it); re-matching
# the keyword here would therefore never fire. We only need a negation keyword in
# the window preceding the match.
_NEGATION_BEFORE_RE = re.compile(r"(?i)(?<!\w)(?:not|never|no)\b[\w\s]{0,20}")

# Subject candidates, most specific first.
_SUBJECT_PY_RE = re.compile(r"\b[\w./-]+\.py\b")
_SUBJECT_DIR_RE = re.compile(r"\b(?:scripts|docs)/[\w./-]+")
# decision_target-like token: word.word(-word)* (contains a dot, no leading slash).
_SUBJECT_DECISION_TARGET_RE = re.compile(r"\b[a-z][\w]*(?:\.[\w]+)+(?:-[\w]+)*\b")

# File-extension tails that indicate a bare filename / markdown link target rather
# than a decision_target-style identifier (e.g. "policy.md" in a [..](path) link).
_NON_IDENTIFIER_EXTENSIONS: frozenset[str] = frozenset(
    ("md", "rst", "txt", "toml", "yaml", "yml", "json", "csv", "png", "jpg", "pdf")
)


def _is_identifier_candidate(token: str) -> bool:
    """True when ``token`` looks like a decision_target, not a bare filename."""
    dot = token.rfind(".")
    if dot == -1:
        return False
    return token[dot + 1 :].lower() not in _NON_IDENTIFIER_EXTENSIONS


# A registered subject that is only a directory prefix (e.g. "scripts/agent/") is
# matched as a substring of the prose subject; this regex recognises such prefixes.
_DIR_SUFFIX = "/"

# Registry area names used to recognise an explicit area/subsystem token in a
# claim's context. Kept static so area derivation does not depend on loading the
# registry (the scanner derives area keys independently of it).
_KNOWN_AREA_TOKENS: tuple[str, ...] = (
    "EventBus",
    "Overview",
    "Deployment",
    "Governance",
    "RAG",
    "MCP",
    "Agent",
    "Shared/DB",
)
_AREA_TOKEN_RE = re.compile(
    r"(?i)\b(?:" + "|".join(_KNOWN_AREA_TOKENS) + r")\b(?![/_])"
)


@dataclass
class CanonicalClaim:
    """A single unregistered canonical-status assertion found in ``docs/``."""

    subject: str
    source_file: str
    line_number: int
    matched_text: str
    context: str

    def __str__(self) -> str:
        return f"{self.source_file}:{self.line_number} -> {self.subject}"


@dataclass
class CanonicalProseFinding:
    """A single WARNING-level finding from the prose scan."""

    code: str
    severity: Severity
    blocking_status: BlockingStatus
    description: str
    source_file: str
    line_number: int
    subject: str
    recommendation: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "severity": str(self.severity),
            "blocking_status": str(self.blocking_status),
            "description": self.description,
            "source_file": self.source_file,
            "line_number": self.line_number,
            "subject": self.subject,
            "recommendation": self.recommendation,
        }

    def __str__(self) -> str:
        lines = [
            f"{self.code}: [{self.severity}] {self.description} "
            f"({self.source_file}:{self.line_number})"
        ]
        if self.subject:
            lines.append(f"  Subject: {self.subject}")
        if self.recommendation:
            lines.append(f"  Action: {self.recommendation}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Registry data model (M-01-04 schema subset)
# ---------------------------------------------------------------------------


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


@dataclass
class CanonicalRegistry:
    version: str
    entries: list[RegistryEntry] = field(default_factory=list)

    @property
    def all_source_paths(self) -> list[str]:
        paths: list[str] = []
        for entry in self.entries:
            paths.extend(entry.source_paths)
        return paths

    @property
    def all_decision_targets(self) -> list[str]:
        return [entry.decision_target for entry in self.entries]

    @staticmethod
    def from_path(path: Path) -> CanonicalRegistry:
        with open(path, "rb") as handle:
            data = tomllib.load(handle)
        entries_data = data.get("canonical_sources", [])
        entries = [RegistryEntry.from_dict(entry) for entry in entries_data]
        return CanonicalRegistry(version=str(data.get("version", "")), entries=entries)


def load_registry(path: Path | None = None) -> CanonicalRegistry:
    """Load the Canonical Source Registry TOML (read-only)."""
    registry_path = path or DEFAULT_REGISTRY_PATH
    return CanonicalRegistry.from_path(registry_path)


# ---------------------------------------------------------------------------
# Scan + subject extraction
# ---------------------------------------------------------------------------


def _extract_subject(line: str, match_start: int, match_end: int) -> str | None:
    """Return the nearest subject token around a match, or None.

    Preference order: a ``.py`` path, a ``scripts/`` or ``docs/`` path, then a
    ``decision_target``-like token (``word.word(-word)*``). Nearest to the match
    wins; ties favour the token that appears later on the line.
    """
    candidates: list[tuple[int, int, str]] = []

    for regex in (
        _SUBJECT_PY_RE,
        _SUBJECT_DIR_RE,
        _SUBJECT_DECISION_TARGET_RE,
    ):
        for candidate in regex.finditer(line):
            token = candidate.group()
            if token.startswith("/"):
                continue
            if regex is _SUBJECT_DECISION_TARGET_RE and not _is_identifier_candidate(
                token
            ):
                continue
            center = (candidate.start() + candidate.end()) // 2
            distance = abs(center - (match_start + match_end) // 2)
            candidates.append((distance, candidate.start(), token))

    if not candidates:
        return None

    candidates.sort(key=lambda item: (item[0], -item[1]))
    return candidates[0][2]


def _has_negation_before(line: str, match_start: int) -> bool:
    window = line[max(0, match_start - 25) : match_start]
    return bool(_NEGATION_BEFORE_RE.search(window))


def scan_claims(docs_dir: Path | None = None) -> list[CanonicalClaim]:
    """Scan ``docs/*.md`` for unregistered canonical-status assertions.

    Returns one :class:`CanonicalClaim` per assertion whose subject could be
    extracted. Claims whose subject cannot be extracted are skipped (fail safe
    toward no false positives, UNK-03).
    """
    docs_root = docs_dir or Path("docs")
    claims: list[CanonicalClaim] = []

    for doc_path in sorted(docs_root.glob("**/*.md")):
        try:
            text = doc_path.read_text(encoding="utf-8")
        except OSError:
            continue
        for line_number, line in enumerate(text.splitlines(), start=1):
            for match in _PATTERN_RE.finditer(line):
                if _has_negation_before(line, match.start()):
                    continue
                subject = _extract_subject(line, match.start(), match.end())
                if subject is None:
                    continue
                claims.append(
                    CanonicalClaim(
                        subject=subject,
                        source_file=str(doc_path),
                        line_number=line_number,
                        matched_text=match.group(),
                        context=line.strip(),
                    )
                )
    return claims


# ---------------------------------------------------------------------------
# Overlap + duplicate detection
# ---------------------------------------------------------------------------


def _subjects_overlap(subject: str, registered: str) -> bool:
    """True when ``subject`` and a registered path/target refer to the same thing.

    Token/substring based (not semantic): either is a substring of the other.
    Directory-prefix registrations (``scripts/agent/``) still overlap a more
    specific prose subject (``scripts/agent/foo.py``).
    """
    if not subject or not registered:
        return False
    if registered.endswith(_DIR_SUFFIX):
        return subject.startswith(registered) or registered.startswith(subject)
    return subject == registered or subject in registered or registered in subject


def find_registry_overlaps(
    claims: list[CanonicalClaim], registry: CanonicalRegistry
) -> list[CanonicalProseFinding]:
    """REQ-002: flag claims whose subject overlaps a registered source/target."""
    registered = [
        *registry.all_source_paths,
        *registry.all_decision_targets,
    ]
    findings: list[CanonicalProseFinding] = []
    for claim in claims:
        for target in registered:
            if _subjects_overlap(claim.subject, target):
                findings.append(
                    CanonicalProseFinding(
                        code="CANONICAL-PROSE-001",
                        severity=Severity.MEDIUM,
                        blocking_status=BlockingStatus.WARNING,
                        description=(
                            f"Unregistered canonical claim in {claim.source_file}:"
                            f" {claim.context!r} overlaps registered source "
                            f"'{target}'."
                        ),
                        source_file=claim.source_file,
                        line_number=claim.line_number,
                        subject=claim.subject,
                        recommendation=(
                            "Register the claimed source in the Canonical Source "
                            "Registry, or reword the prose to a non-normative "
                            "reference."
                        ),
                    )
                )
                break
    return findings


def find_duplicate_prose(claims: list[CanonicalClaim]) -> list[CanonicalProseFinding]:
    """REQ-003: flag subjects asserted by two or more distinct claims."""
    by_subject: dict[str, list[CanonicalClaim]] = {}
    for claim in claims:
        by_subject.setdefault(claim.subject, []).append(claim)

    findings: list[CanonicalProseFinding] = []
    for subject, matching in by_subject.items():
        if len(matching) < 2:
            continue
        locations = ", ".join(str(claim) for claim in matching)
        findings.append(
            CanonicalProseFinding(
                code="CANONICAL-PROSE-002",
                severity=Severity.MEDIUM,
                blocking_status=BlockingStatus.WARNING,
                description=(
                    f"Duplicate canonical claim for subject '{subject}' in "
                    f"{len(matching)} places:\n    {locations}"
                ),
                source_file=matching[0].source_file,
                line_number=matching[0].line_number,
                subject=subject,
                recommendation=(
                    "Consolidate the duplicate canonical assertions into the "
                    "single registered source."
                ),
            )
        )
    return findings


def derive_area_key(claim: CanonicalClaim) -> str | None:
    """Derive the area grouping key for a claim (UNK-01).

    Precedence: an explicit area/subsystem token in the claim's context, then the
    containing document's ``docs`` area directory (the path component after
    ``docs/``). Returns ``None`` when neither is available, leaving the claim
    ungrouped (not flagged -- fail safe toward no false positives, UNK-03).
    """
    token = _AREA_TOKEN_RE.search(claim.context)
    if token:
        return token.group().lower()
    parts = claim.source_file.split("/")
    if "docs" in parts:
        idx = parts.index("docs")
        if idx + 1 < len(parts):
            return parts[idx + 1]
    return None


def find_multi_primary_per_area(
    claims: list[CanonicalClaim],
) -> list[CanonicalProseFinding]:
    """GV-010: flag areas with two or more distinct designated primary documents.

    Groups claims by their area key (see :func:`derive_area_key`) and emits a
    WARNING for any area whose set of distinct subjects numbers two or more.
    Single-primary areas are not flagged. Claims that cannot be grouped are
    skipped (UNK-03). WARNING only; non-blocking contract preserved.
    """
    groups: dict[str, list[CanonicalClaim]] = {}
    for claim in claims:
        key = derive_area_key(claim)
        if key is None:
            continue
        groups.setdefault(key, []).append(claim)

    findings: list[CanonicalProseFinding] = []
    for key, group in groups.items():
        subjects = {c.subject for c in group}
        if len(subjects) < 2:
            continue
        competing = ", ".join(sorted(subjects))
        locations = ", ".join(str(c) for c in group)
        findings.append(
            CanonicalProseFinding(
                code="CANONICAL-PROSE-003",
                severity=Severity.MEDIUM,
                blocking_status=BlockingStatus.WARNING,
                description=(
                    f"Multiple primary canonical sources for area '{key}' in "
                    f"{len(subjects)} documents:\n    {locations}"
                ),
                source_file=group[0].source_file,
                line_number=group[0].line_number,
                subject=competing,
                recommendation=(
                    "Consolidate to a single canonical source per area, or "
                    "clarify that the documents cover distinct topics."
                ),
            )
        )
    return findings


def check_document_prose(
    docs_dir: Path | None = None,
    registry: CanonicalRegistry | None = None,
) -> list[CanonicalProseFinding]:
    """Run the full prose scan: scan, then detect overlap, duplicates, and
    multiple-primary-per-area (GV-010)."""
    claims = scan_claims(docs_dir)
    if registry is None:
        registry = load_registry()
    findings: list[CanonicalProseFinding] = []
    findings.extend(find_registry_overlaps(claims, registry))
    findings.extend(find_duplicate_prose(claims))
    findings.extend(find_multi_primary_per_area(claims))
    return findings


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    """CLI entry point for check_canonical_document_prose.py.

    WARNING-only, non-blocking gate: always exits 0 so the CI contract is
    preserved.
    """
    parser = argparse.ArgumentParser(
        description="Scan docs/ for unregistered canonical-document prose"
    )
    parser.add_argument(
        "--registry",
        type=str,
        default=None,
        help=f"Path to the registry TOML file (default: {DEFAULT_REGISTRY_PATH})",
    )
    parser.add_argument(
        "--docs",
        type=str,
        default=None,
        help="Directory to scan for *.md (default: docs)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON",
    )
    args = parser.parse_args(argv)

    docs_dir = Path(args.docs) if args.docs else Path("docs")
    registry_path = Path(args.registry) if args.registry else DEFAULT_REGISTRY_PATH

    try:
        registry = CanonicalRegistry.from_path(registry_path)
    except (tomllib.TOMLDecodeError, FileNotFoundError) as exc:
        print(f"Failed to load registry file: {exc}", file=sys.stderr)
        return 1

    findings = check_document_prose(docs_dir, registry)
    for finding in findings:
        print(finding)

    if args.json:
        import json

        print(json.dumps([f.to_dict() for f in findings], indent=2, ensure_ascii=False))

    # WARNING-only gate: never block on these findings.
    return 0


if __name__ == "__main__":
    sys.exit(main())
