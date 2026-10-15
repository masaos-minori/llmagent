"""tests/tools/test_check_adr_preservation.py — Tests for the ADR content-preservation comparison."""

from __future__ import annotations

from tools.check_adr_preservation import compare

_BASE = """---
title: "ADR-999: Demo"
---

# ADR-999: Demo

## Decision

The service MUST NOT bypass the engine.

## Invariants

- INV-01: A caller MUST NOT bypass the engine.
- INV-02: State is persisted.

## Known Deviations

Not applicable

## Related ADRs

- ADR-001: Engine

## Implementation References

- `scripts/x.py` (`run()`)
- Tests: `tests/test_x.py::test_run`
"""


def _messages(new: str) -> list[tuple[str, str]]:
    return [(i.severity, i.message) for i in compare("adr.md", _BASE, new)]


def test_identical_text_has_no_issues() -> None:
    assert _messages(_BASE) == []


def test_whitespace_only_change_has_no_issues() -> None:
    assert _messages(_BASE.replace("\n\n", "\n\n\n")) == []


def test_reworded_invariant_is_an_error() -> None:
    new = _BASE.replace("State is persisted.", "State is kept.")
    assert ("ERROR", "INV-02 text changed") in _messages(new)


def test_removed_invariant_is_an_error() -> None:
    new = _BASE.replace("- INV-02: State is persisted.\n", "")
    assert ("ERROR", "INV-02 removed") in _messages(new)


def test_removed_test_citation_is_an_error() -> None:
    new = _BASE.replace("- Tests: `tests/test_x.py::test_run`\n", "")
    messages = _messages(new)
    assert ("ERROR", "test citation removed: tests/test_x.py::test_run") in messages


def test_changed_related_adr_is_an_error() -> None:
    new = _BASE.replace("ADR-001: Engine", "ADR-002: Other")
    severities = {sev for sev, msg in _messages(new) if "Related ADRs" in msg}
    assert severities == {"ERROR"}


def test_changed_known_deviations_is_an_error() -> None:
    new = _BASE.replace("Not applicable", "Known Issue X-1")
    assert ("ERROR", "section 'Known Deviations' text changed") in _messages(new)


def test_changed_decision_and_weaker_keyword_are_warnings() -> None:
    new = _BASE.replace(
        "MUST NOT bypass the engine.", "should not bypass the engine.", 1
    )
    warnings = [msg for sev, msg in _messages(new) if sev == "WARNING"]
    assert any("'Decision'" in m for m in warnings)
    assert any("MUST NOT count decreased" in m for m in warnings)


def test_changed_h2_sequence_is_an_error() -> None:
    new = _BASE.replace("## Known Deviations", "## Deviations")
    assert ("ERROR", "H2 heading sequence changed") in _messages(new)


_DOC = """---
title: "Demo"
---

# Demo

## API

POST /publish returns 200 or 422. See `scripts/eventbus/app.py`.

<!-- AUTO-GENERATED: x -->
| a |
<!-- END AUTO-GENERATED -->
"""


def _generic(new: str) -> list[tuple[str, str]]:
    from tools.check_adr_preservation import compare_generic

    return [(i.severity, i.message) for i in compare_generic("d.md", _DOC, new)]


def test_generic_identical_has_no_issues() -> None:
    assert _generic(_DOC) == []


def test_generic_autogen_edit_is_an_error() -> None:
    assert ("ERROR", "AUTO-GENERATED block changed") in _generic(
        _DOC.replace("| a |", "| b |")
    )


def test_generic_front_matter_change_is_an_error() -> None:
    assert ("ERROR", "front matter changed") in _generic(
        _DOC.replace('title: "Demo"', 'title: "Other"')
    )


def test_generic_unbalanced_fence_is_an_error() -> None:
    assert ("ERROR", "unbalanced fenced code block") in _generic(_DOC + "```\n")


def test_tokens_collects_endpoints_status_and_paths() -> None:
    from tools.check_adr_preservation import tokens

    assert tokens(_DOC) == {
        "POST /publish",
        "status 200",
        "status 422",
        "scripts/eventbus/app.py",
    }
