"""tests/shared/test_write_outcome.py

Unit tests for shared/write_outcome.py: the write-outcome vocabulary, the no-auto-retry
set, and the write-audit field contract.
"""

from __future__ import annotations

import pytest
from shared.write_outcome import (
    APPLIED_AUDIT_FAILED,
    NO_AUTO_RETRY_OUTCOMES,
    OUTCOME_UNKNOWN,
    build_write_audit_fields,
)


def test_constants_match_the_vocabulary() -> None:
    assert OUTCOME_UNKNOWN == "outcome_unknown"
    assert APPLIED_AUDIT_FAILED == "applied_audit_failed"


def test_no_auto_retry_set_contains_both_outcomes() -> None:
    assert NO_AUTO_RETRY_OUTCOMES == frozenset({OUTCOME_UNKNOWN, APPLIED_AUDIT_FAILED})
    assert isinstance(NO_AUTO_RETRY_OUTCOMES, frozenset)


def test_field_order_is_op_phase_session_request_call() -> None:
    fields = build_write_audit_fields("create_issue", "intent", "s1", "r1", "c1")
    assert list(fields) == ["op", "phase", "session", "request", "call"]
    assert fields == {
        "op": "create_issue",
        "phase": "intent",
        "session": "s1",
        "request": "r1",
        "call": "c1",
    }


def test_both_phases_are_accepted() -> None:
    assert (
        build_write_audit_fields("merge", "completion", "s", "r", "c")["phase"]
        == "completion"
    )
    assert (
        build_write_audit_fields("merge", "intent", "s", "r", "c")["phase"] == "intent"
    )


def test_empty_identifiers_render_as_dash() -> None:
    fields = build_write_audit_fields("push_files", "completion", "", "", "")
    assert fields["session"] == "-"
    assert fields["request"] == "-"
    assert fields["call"] == "-"
    assert fields["op"] == "push_files"
    assert fields["phase"] == "completion"


def test_unknown_phase_raises() -> None:
    with pytest.raises(ValueError):
        build_write_audit_fields("create_issue", "post", "s", "r", "c")
