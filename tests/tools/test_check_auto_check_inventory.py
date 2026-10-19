"""tests/tools/test_check_auto_check_inventory.py

Tests for tools/check_auto_check_inventory.py.

Each scenario builds small in-memory Markdown tables and calls the parser /
classifier / audit functions directly -- matching the direct-function-call
pattern used by tests/tools/test_check_adr_structure.py. The real repository
corpus (governance_04 + routing.md against the actual tools/ tree) is asserted
clean exactly once here, per REQ-004; it is not duplicated as unit fixtures.
"""

from __future__ import annotations

from pathlib import Path

from tools.check_auto_check_inventory import (
    ROOT_DIR,
    ToolIndex,
    _classify,
    _default_sources,
    audit,
    iter_table_rows,
    parse_governance_rows,
    parse_routing_rows,
)


def _row(*cells: str) -> str:
    return "|" + "|".join(f" {c} " for c in cells) + "|"


def _table(*rows: str) -> str:
    return "\n".join(rows) + "\n"


class TestIterTableRows:
    def test_skips_code_fence_content(self) -> None:
        text = _table(
            "| GV-001 | Auto | tools/check_a.py |",
            "```",
            "| GV-999 | Auto | tools/inside_fence.py |",
            "```",
            "| GV-002 | Manual | tools/check_b.py |",
        )
        rows = list(iter_table_rows(text))
        tokens = [tok for _, cells in rows for tok in cells]
        assert "tools/inside_fence.py" not in tokens
        assert "tools/check_a.py" in tokens
        assert "tools/check_b.py" in tokens

    def test_line_numbers_are_1_based_and_accurate(self) -> None:
        text = _table(
            "| header row |",
            "| GV-001 | Auto | tools/check_a.py |",
        )
        rows = list(iter_table_rows(text))
        assert [line_no for line_no, _ in rows] == [1, 2]

    def test_non_table_lines_are_ignored(self) -> None:
        text = _table(
            "plain prose mentioning tools/foo.py",
            "| GV-001 | Auto | tools/check_a.py |",
        )
        rows = list(iter_table_rows(text))
        assert len(rows) == 1


class TestParseGovernanceRows:
    def test_only_auto_rows_contribute_tokens(self) -> None:
        text = _table(
            _row("GV-001", "Description", "Auto", "tools/check_auto.py"),
            _row("GV-002", "Manual check", "Manual", "tools/check_manual.py"),
        )
        findings = parse_governance_rows(text)
        tokens = [tok for tok, _ in findings]
        assert tokens == ["tools/check_auto.py"]
        assert all("manual" not in t.lower() for t in tokens)

    def test_line_number_points_at_the_auto_row(self) -> None:
        text = _table(
            _row("GV-001", "Manual", "tools/check_manual.py"),
            _row("GV-002", "Auto", "tools/check_auto.py"),
        )
        findings = parse_governance_rows(text)
        assert findings == [("tools/check_auto.py", 2)]

    def test_token_spanning_multiple_cells_is_captured(self) -> None:
        text = _table(_row("GV-001", "see", "tools/check_multi.py", "Auto"))
        assert parse_governance_rows(text) == [("tools/check_multi.py", 1)]


class TestParseRoutingRows:
    def test_all_table_rows_contribute(self) -> None:
        text = _table(
            _row("check-suppression-justification", "Manual", "follow-up"),
            _row("check_glossary_term_classification.py", "Auto"),
        )
        findings = parse_routing_rows(text)
        tokens = [tok for tok, _ in findings]
        assert tokens == ["check_glossary_term_classification.py"]

    def test_code_fence_rows_are_skipped(self) -> None:
        text = _table(
            "| check_visible.py | Auto |",
            "```",
            "| check_hidden.py | Auto |",
            "```",
        )
        tokens = [tok for tok, _ in parse_routing_rows(text)]
        assert tokens == ["check_visible.py"]


class TestClassify:
    def test_ok_via_exact_rel_path(self) -> None:
        index = ToolIndex(basenames={"check_a.py"}, rel_paths={"tools/check_a.py"})
        assert _classify("tools/check_a.py", index) == ("ok", "")

    def test_ok_via_basename(self) -> None:
        index = ToolIndex(basenames={"check_a.py"}, rel_paths=set())
        assert _classify("check_a.py", index) == ("ok", "")

    def test_absent_when_no_candidate(self) -> None:
        index = ToolIndex(basenames={"check_a.py"}, rel_paths=set())
        status, detail = _classify("tools/missing_check.py", index)
        assert status == "absent"
        assert detail == ""

    def test_drift_when_close_candidate_exists(self) -> None:
        index = ToolIndex(
            basenames={"check_glossary_term_classification.py"},
            rel_paths=set(),
        )
        status, detail = _classify("check_glossary_term_classificatio.py", index)
        assert status == "drift"
        assert detail == "check_glossary_term_classification.py"


class TestAudit:
    def test_absent_documented_tool_produces_warning(self, tmp_path: Path) -> None:
        gov = tmp_path / "governance_04.md"
        gov.write_text(
            _table(_row("GV-001", "Auto", "tools/never_created.py")) + "\n",
            encoding="utf-8",
        )
        index = ToolIndex(basenames=set(), rel_paths=set())
        issues = audit([(gov, parse_governance_rows)], index)
        assert len(issues) == 1
        finding = issues[0]
        assert finding.severity == "WARNING"
        assert "documented-but-absent" in finding.message
        assert "tools/never_created.py" in finding.message

    def test_drift_documented_tool_produces_warning(self, tmp_path: Path) -> None:
        routing = tmp_path / "routing.md"
        routing.write_text(
            _table(_row("check_glossary_term_classificatio.py", "Auto")) + "\n",
            encoding="utf-8",
        )
        index = ToolIndex(
            basenames={"check_glossary_term_classification.py"},
            rel_paths=set(),
        )
        issues = audit([(routing, parse_routing_rows)], index)
        assert len(issues) == 1
        assert issues[0].severity == "WARNING"
        assert "name drift" in issues[0].message

    def test_existing_tool_is_not_flagged(self, tmp_path: Path) -> None:
        gov = tmp_path / "governance_04.md"
        gov.write_text(
            _table(_row("GV-001", "Auto", "tools/check_present.py")) + "\n",
            encoding="utf-8",
        )
        index = ToolIndex(
            basenames={"check_present.py"},
            rel_paths={"tools/check_present.py"},
        )
        assert audit([(gov, parse_governance_rows)], index) == []

    def test_alternative_invocations_are_suppressed(self, tmp_path: Path) -> None:
        routing = tmp_path / "routing.md"
        routing.write_text(_table(_row("lint", "CI job")) + "\n", encoding="utf-8")
        # Even though no script named `lint` exists, this is an allowed
        # alternative invocation name and must not be flagged.
        index = ToolIndex(basenames=set(), rel_paths=set())
        assert audit([(routing, parse_routing_rows)], index) == []


class TestRealCorpus:
    def test_default_sources_are_clean_against_real_tools_tree(self) -> None:
        # REQ-004: the authoritative sources must resolve cleanly against the
        # real tools/ + scripts/ tree. Any finding here means a documented
        # auto-check has no runnable script, or a name has drifted.
        issues = audit(_default_sources(ROOT_DIR), ToolIndex.discover(ROOT_DIR))
        assert issues == [], [f"{i.file}:{i.line_no} — {i.message}" for i in issues]
