"""tests/tools/test_check_canonical_document_prose.py

Tests for tools/check_canonical_document_prose.py: registry-overlap (REQ-002),
duplicate-prose grouping (REQ-003), negation/incidental exclusion (REQ-001/004),
and a corpus run proving zero benign false positives (REQ-004).

Does NOT touch the existing canonical-tool suites; their regression is covered by
the full-suite run in the validation sequence.
"""

from __future__ import annotations

from pathlib import Path

from tools.check_canonical_document_prose import (
    BlockingStatus,
    CanonicalClaim,
    Severity,
    check_document_prose,
    derive_area_key,
    find_duplicate_prose,
    find_multi_primary_per_area,
    find_registry_overlaps,
    load_registry,
    scan_claims,
)

# Registered subjects reused across fixtures.
REGISTERED_PY = "scripts/db/schema_sql.py"
REGISTERED_DECISION_TARGET = "eventbus.core-behavior"


def _write(tmp_path: Path, name: str, content: str) -> Path:
    path = tmp_path / name
    path.write_text(content, encoding="utf-8")
    return path


def _claim(
    subject: str, source_file: str = "docs/test.md", line_number: int = 1
) -> CanonicalClaim:
    return CanonicalClaim(
        subject=subject,
        source_file=source_file,
        line_number=line_number,
        matched_text="canonical source for",
        context="fixture claim",
    )


# ---------------------------------------------------------------------------
# REQ-002: registry overlap
# ---------------------------------------------------------------------------


class TestFindRegistryOverlaps:
    def test_py_subject_matches_registered_path(self) -> None:
        findings = find_registry_overlaps([_claim(REGISTERED_PY)], load_registry())
        assert len(findings) == 1
        finding = findings[0]
        assert finding.code == "CANONICAL-PROSE-001"
        assert finding.severity == Severity.MEDIUM
        assert finding.blocking_status == BlockingStatus.WARNING
        assert not finding.blocking_status.is_blocking()

    def test_decision_target_matches_registered_target(self) -> None:
        findings = find_registry_overlaps(
            [_claim(REGISTERED_DECISION_TARGET)], load_registry()
        )
        assert len(findings) == 1
        assert findings[0].code == "CANONICAL-PROSE-001"

    def test_directory_prefix_overlap(self) -> None:
        findings = find_registry_overlaps(
            [_claim("scripts/agent/tool_policy.py")], load_registry()
        )
        assert len(findings) == 1
        assert findings[0].code == "CANONICAL-PROSE-001"

    def test_no_overlap_when_unregistered(self) -> None:
        findings = find_registry_overlaps(
            [_claim("scripts/unknown/elsewhere.py")], load_registry()
        )
        assert findings == []

    def test_only_first_overlap_reported_per_claim(self) -> None:
        # A claim overlapping two registered entries yields one finding.
        findings = find_registry_overlaps([_claim(REGISTERED_PY)], load_registry())
        assert len(findings) == 1


# ---------------------------------------------------------------------------
# REQ-003: duplicate prose grouping
# ---------------------------------------------------------------------------


class TestFindDuplicateProse:
    def test_duplicate_subject_flagged(self) -> None:
        claims = [
            _claim("scripts/agent/tool_policy.py", "docs/a.md", 1),
            _claim("scripts/agent/tool_policy.py", "docs/b.md", 2),
        ]
        findings = find_duplicate_prose(claims)
        assert len(findings) == 1
        assert findings[0].code == "CANONICAL-PROSE-002"
        assert findings[0].blocking_status == BlockingStatus.WARNING

    def test_single_claim_not_flagged(self) -> None:
        assert find_duplicate_prose([_claim("scripts/agent/tool_policy.py")]) == []

    def test_different_subjects_not_flagged(self) -> None:
        claims = [
            _claim("scripts/agent/tool_policy.py", "docs/a.md", 1),
            _claim("scripts/agent/tool_approval.py", "docs/b.md", 2),
        ]
        assert find_duplicate_prose(claims) == []


# ---------------------------------------------------------------------------
# GV-010: area grouping + multi-primary-per-area detection
# ---------------------------------------------------------------------------


class TestDeriveAreaKey:
    def test_uses_explicit_area_token_in_context(self) -> None:
        claim = CanonicalClaim(
            subject="scripts/other/a.py",
            source_file="docs/99_other.md",
            line_number=1,
            matched_text="canonical source for",
            context="The EventBus canonical source for model provisioning.",
        )
        assert derive_area_key(claim) == "eventbus"

    def test_falls_back_to_document_area(self) -> None:
        claim = CanonicalClaim(
            subject="scripts/other/a.py",
            source_file="docs/24_eventbus/x.md",
            line_number=1,
            matched_text="canonical source for",
            context="This is the canonical source for model provisioning.",
        )
        assert derive_area_key(claim) == "24_eventbus"

    def test_no_token_and_no_docs_path_is_ungrouped(self) -> None:
        claim = CanonicalClaim(
            subject="scripts/other/a.py",
            source_file="elsewhere/x.md",
            line_number=1,
            matched_text="canonical source for",
            context="This is the canonical source for model provisioning.",
        )
        assert derive_area_key(claim) is None


class TestFindMultiPrimaryPerArea:
    def test_multi_primary_flagged(self) -> None:
        claims = [
            CanonicalClaim(
                subject="scripts/other/a.py",
                source_file="docs/24_eventbus/a.md",
                line_number=1,
                matched_text="canonical source for",
                context="The EventBus canonical source for provisioning.",
            ),
            CanonicalClaim(
                subject="scripts/other/b.py",
                source_file="docs/24_eventbus/b.md",
                line_number=1,
                matched_text="canonical source for",
                context="The EventBus canonical source for migration.",
            ),
        ]
        findings = find_multi_primary_per_area(claims)
        assert len(findings) == 1
        finding = findings[0]
        assert finding.code == "CANONICAL-PROSE-003"
        assert finding.severity == Severity.MEDIUM
        assert finding.blocking_status == BlockingStatus.WARNING
        assert not finding.blocking_status.is_blocking()

    def test_single_primary_not_flagged(self) -> None:
        claims = [
            CanonicalClaim(
                subject="scripts/other/a.py",
                source_file="docs/24_eventbus/a.md",
                line_number=1,
                matched_text="canonical source for",
                context="The EventBus canonical source for provisioning.",
            ),
        ]
        assert find_multi_primary_per_area(claims) == []

    def test_same_subject_not_multi_primary(self) -> None:
        # Two claims naming the SAME document is not multi-primary (that is
        # duplicate-prose, CANONICAL-PROSE-002); it must not be flagged here.
        claims = [
            CanonicalClaim(
                subject="scripts/other/a.py",
                source_file="docs/24_eventbus/a.md",
                line_number=1,
                matched_text="canonical source for",
                context="The EventBus canonical source for provisioning.",
            ),
            CanonicalClaim(
                subject="scripts/other/a.py",
                source_file="docs/24_eventbus/c.md",
                line_number=1,
                matched_text="canonical source for",
                context="The EventBus canonical source for provisioning again.",
            ),
        ]
        assert find_multi_primary_per_area(claims) == []

    def test_ungrouped_claims_not_flagged(self) -> None:
        claims = [
            CanonicalClaim(
                subject="scripts/other/a.py",
                source_file="elsewhere/a.md",
                line_number=1,
                matched_text="canonical source for",
                context="This is the canonical source for provisioning.",
            ),
            CanonicalClaim(
                subject="scripts/other/b.py",
                source_file="elsewhere/b.md",
                line_number=1,
                matched_text="canonical source for",
                context="This is the canonical source for migration.",
            ),
        ]
        assert find_multi_primary_per_area(claims) == []

    def test_end_to_end_via_scan(self, tmp_path: Path) -> None:
        docs_root = tmp_path / "docs" / "24_eventbus"
        docs_root.mkdir(parents=True)
        (docs_root / "a.md").write_text(
            "# Guide\n\n"
            "The EventBus canonical source for provisioning is "
            "`scripts/other/a.py`.\n",
            encoding="utf-8",
        )
        (docs_root / "b.md").write_text(
            "# Guide\n\n"
            "The EventBus canonical source for migration is "
            "`scripts/other/b.py`.\n",
            encoding="utf-8",
        )
        claims = scan_claims(tmp_path / "docs")
        findings = find_multi_primary_per_area(claims)
        assert len(findings) == 1
        assert findings[0].code == "CANONICAL-PROSE-003"

    def test_end_to_end_single_primary_not_flagged(self, tmp_path: Path) -> None:
        docs_root = tmp_path / "docs" / "24_eventbus"
        docs_root.mkdir(parents=True)
        (docs_root / "a.md").write_text(
            "# Guide\n\n"
            "The EventBus canonical source for provisioning is "
            "`scripts/other/a.py`.\n",
            encoding="utf-8",
        )
        claims = scan_claims(tmp_path / "docs")
        assert find_multi_primary_per_area(claims) == []


# ---------------------------------------------------------------------------
# REQ-001 / REQ-004: scan, subject extraction, negation + incidental exclusion
# ---------------------------------------------------------------------------


class TestScanClaims:
    def _write(self, tmp_path: Path, name: str, content: str) -> Path:
        path = tmp_path / name
        path.write_text(content, encoding="utf-8")
        return path

    def test_positive_match_with_subject(self, tmp_path: Path) -> None:
        _write(
            tmp_path,
            "guide.md",
            "# Guide\n\n"
            "This section is the canonical source for the bootstrap DDL. "
            "See `scripts/db/schema_sql.py`.\n",
        )
        claims = scan_claims(tmp_path)
        assert len(claims) == 1
        assert claims[0].subject == REGISTERED_PY

    def test_negation_excluded(self, tmp_path: Path) -> None:
        self._write(
            tmp_path,
            "guide.md",
            "# Guide\n\n"
            "This document is not the canonical source for X; "
            "see `scripts/db/schema_sql.py`.\n",
        )
        assert scan_claims(tmp_path) == []

    def test_incidental_canonical_not_matched(self, tmp_path: Path) -> None:
        self._write(
            tmp_path,
            "guide.md",
            "# Guide\n\n"
            "Register claims in the Canonical Source Registry.\n"
            "SQLite is the authoritative source of truth here.\n",
        )
        assert scan_claims(tmp_path) == []

    def test_no_subject_is_skipped(self, tmp_path: Path) -> None:
        self._write(
            tmp_path,
            "guide.md",
            "# Guide\n\nThis is the canonical source for model provisioning.\n",
        )
        assert scan_claims(tmp_path) == []

    def test_nearest_subject_wins(self, tmp_path: Path) -> None:
        _write(
            tmp_path,
            "guide.md",
            "# Guide\n\n"
            "The normative reference for schemas is `scripts/db/schema_sql.py`, "
            "not `other.py`.\n",
        )
        claims = scan_claims(tmp_path)
        assert len(claims) == 1
        assert claims[0].subject == "scripts/db/schema_sql.py"


# ---------------------------------------------------------------------------
# REQ-004: corpus run against the live docs/ tree
# ---------------------------------------------------------------------------


class TestCorpusRun:
    def test_current_docs_have_no_benign_false_positives(self) -> None:
        findings = check_document_prose(Path("docs"), load_registry())
        assert findings == [], (
            f"unexpected findings on current corpus: {[f.to_dict() for f in findings]}"
        )


# ---------------------------------------------------------------------------
# CLI contract: WARNING-only, non-blocking exit
# ---------------------------------------------------------------------------


class TestMainContract:
    def test_main_exits_zero_on_warnings(self, tmp_path: Path) -> None:
        registry = (
            Path(__file__).resolve().parents[2]
            / "config"
            / "documentation_canonical_sources.toml"
        )
        _write(
            tmp_path,
            "guide.md",
            f"# Guide\n\nThis is the canonical source for X. See `{REGISTERED_PY}`.\n",
        )
        import io
        from contextlib import redirect_stdout

        from tools.check_canonical_document_prose import main

        argv = ["--registry", str(registry), "--docs", str(tmp_path)]
        # Capture stdout to keep the test log clean.
        with redirect_stdout(io.StringIO()):
            rc = main(argv)
        assert rc == 0
