"""tests/tools/test_check_canonical_source_conflicts_routing.py

Tests for routing classification (REQ-001) and duplicate-active-record detection
(REQ-008) added to tools/check_canonical_source_conflicts.py.

Each scenario uses only in-memory fixtures — no filesystem writes.
"""

from __future__ import annotations

import pytest

from tools.check_canonical_source_conflicts import (
    FindingRoute,
    RegistryEntry,
    Severity,
    classify_finding,
    detect_duplicate_active_records,
)


def _entry(
    target: str = "target-a",
    claim_type: str = "specification",
) -> RegistryEntry:
    return RegistryEntry(
        decision_target=target,
        claim_type=claim_type,
        source_paths=[f"docs/{target}.md"],
        area="test-area",
    )


# -----------------------------------------------------------------------
# Routing classification (REQ-001)
# -----------------------------------------------------------------------


class TestClassifyFinding:
    """Verify each of the 8 REQ-001 routing rules maps exactly one destination."""

    @pytest.mark.parametrize(
        ("code", "severity", "expected"),
        [
            # Rule 1: design-vs-code -> Known Issue
            ("KNOWN-001", Severity.HIGH, FindingRoute.KNOWN_ISSUE),
            ("KNOWN-001", Severity.MEDIUM, FindingRoute.KNOWN_ISSUE),
            ("KNOWN-001", Severity.LOW, FindingRoute.KNOWN_ISSUE),
            # Rule 3: Specification-vs-acceptance-test -> blocking Canonical Source Conflict
            ("CANONICAL-C001", Severity.HIGH, FindingRoute.CANONICAL_CONFLICT),
            ("CANONICAL-C001", Severity.MEDIUM, FindingRoute.CANONICAL_CONFLICT),
            # Rule 4: deployed-vs-approved config -> Configuration Drift
            ("CONFIG-001", Severity.HIGH, FindingRoute.CONFIG_DRIFT),
            ("CONFIG-001", Severity.MEDIUM, FindingRoute.CONFIG_DRIFT),
            # Rule 5: undetermined intent -> Needs Confirmation
            ("NEEDS-001", Severity.HIGH, FindingRoute.NEEDS_CONFIRMATION),
            # Rule 6: missing canonical source -> design/governance gap
            ("GOV-001", Severity.HIGH, FindingRoute.GOVERNANCE_GAP),
            # Rule 7: multiple normative sources -> blocking Canonical Source Conflict
            ("CANONICAL-C002", Severity.HIGH, FindingRoute.CANONICAL_CONFLICT),
            # Rule 8: stale non-canonical wording only -> documentation-correction task
            ("CANONICAL-W001", Severity.LOW, FindingRoute.DOC_CORRECTION),
            # Unknown code falls back to Known Issue
            ("UNKNOWN-001", Severity.HIGH, FindingRoute.KNOWN_ISSUE),
        ],
    )
    def test_classify_finding_routes_correctly(
        self, code: str, severity: Severity, expected: FindingRoute
    ) -> None:
        result = classify_finding(code, severity)
        assert result == expected


# -----------------------------------------------------------------------
# Duplicate-active-record prevention (REQ-008)
# -----------------------------------------------------------------------


class TestDetectDuplicateActiveRecords:
    """Before recommending a new entry, decision-target-and-claim-type pairs
    across inventories must be compared to refuse duplication."""

    def test_no_duplicate_when_no_matching_entry(self) -> None:
        entries = [_entry(target="x", claim_type="specification")]
        candidate = _entry(target="y", claim_type="specification")
        assert detect_duplicate_active_records(entries, candidate) is False

    def test_duplicate_detected_when_matching_entry(self) -> None:
        """M-01-04 removed the status field from RegistryEntry, so a matching
        decision_target+claim_type pair is always a duplicate — there is no
        longer a status-based exemption (see detect_duplicate_active_records's
        own docstring: "No-op for status since M-01-04 removed it")."""
        entries = [_entry(target="b", claim_type="specification")]
        candidate = _entry(target="b", claim_type="specification")
        assert detect_duplicate_active_records(entries, candidate) is True

    def test_no_duplicate_different_claim_type(self) -> None:
        entries = [_entry(target="c", claim_type="specification")]
        candidate = _entry(target="c", claim_type="acceptance_test")
        assert detect_duplicate_active_records(entries, candidate) is False
