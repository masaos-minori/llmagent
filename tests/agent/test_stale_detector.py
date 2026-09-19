"""tests/agent/test_stale_detector.py

Unit tests for scripts/agent/stale_detector.py:
StaleResult dataclass and detection functions.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from agent.stale_detector import (
    StaleResult,
    _check_before_blocks,
    _check_import_refs,
    _check_line_refs,
    _check_symbol_refs,
)

# ── StaleResult factory methods ──────────────────────────────────────────────


class TestStaleResultFactoryMethods:
    def test_clean_result_is_not_stale(self) -> None:
        result = StaleResult.clean()
        assert result.is_stale is False

    def test_stale_result_is_stale(self) -> None:
        result = StaleResult.stale(target_file="foo/bar.py")
        assert result.is_stale is True
        assert result.target_file == "foo/bar.py"

    def test_empty_result_is_not_stale(self) -> None:
        result = StaleResult.empty()
        assert result.is_stale is False

    def test_with_mismatch_sets_stale_and_records_mismatch(self) -> None:
        result = StaleResult.with_mismatch("symbol_missing", "Symbol 'x' not found in source")
        assert result.is_stale is True
        assert len(result.mismatches) == 1
        assert result.mismatches[0]["type"] == "symbol_missing"

    def test_with_mismatches_sets_stale_and_records_all_mismatches(self) -> None:
        mismatches = [("a", "detail-a"), ("b", "detail-b")]
        result = StaleResult.with_mismatches(mismatches)
        assert result.is_stale is True
        assert len(result.mismatches) == 2

    def test_target_file_preserved_through_factory(self) -> None:
        target = "scripts/agent/orchestrator.py"
        result = StaleResult.stale(target_file=target)
        assert result.target_file == target

# ── StaleResult instance methods ─────────────────────────────────────────────


class TestStaleResultInstanceMethods:
    def test_add_mismatch_marks_stale(self) -> None:
        result = StaleResult.clean()
        result.add_mismatch("symbol_missing", "Symbol 'x' not found")
        assert result.is_stale is True
        assert len(result.mismatches) == 1

    def test_merge_combines_results(self) -> None:
        r1 = StaleResult.with_mismatch("a", "detail-a")
        r2 = StaleResult.with_mismatch("b", "detail-b")
        r1.merge(r2)
        assert r1.is_stale is True
        assert len(r1.mismatches) == 2

    def test_merge_preserves_target_file_from_other(self) -> None:
        r1 = StaleResult.clean()
        r2 = StaleResult.stale(target_file="foo/bar.py")
        r1.merge(r2)
        assert r1.target_file == "foo/bar.py"

    def test_to_dict_serializes_correctly(self) -> None:
        result = StaleResult.with_mismatch("symbol_missing", "Symbol 'x' not found")
        d = result.to_dict()
        assert d["is_stale"] is True
        assert d["mismatches"][0]["type"] == "symbol_missing"

    def test_from_dict_deserializes_correctly(self) -> None:
        d = {"is_stale": True, "target_file": "foo/bar.py", "mismatches": [{"type": "a", "detail": "d"}]}
        result = StaleResult.from_dict(d)
        assert result.is_stale is True
        assert result.target_file == "foo/bar.py"
        assert len(result.mismatches) == 1

    def test_summary_non_stale(self) -> None:
        result = StaleResult.clean()
        assert "not stale" in result.summary

    def test_summary_stale_shows_mismatches(self) -> None:
        result = StaleResult.with_mismatches([("a", "detail-a"), ("b", "detail-b")])
        assert "2 mismatch" in result.summary
        assert "detail-a" in result.summary
        assert "detail-b" in result.summary

    def test_abort_execution_false_when_clean(self) -> None:
        result = StaleResult.clean()
        assert result.abort_execution is False

    def test_abort_execution_true_when_stale(self) -> None:
        result = StaleResult.stale()
        assert result.abort_execution is True

# ── from_procedure — file-not-found case ─────────────────────────────────────


class TestFromProcedureFileNotFound:
    def test_nonexistent_file_returns_stale(self) -> None:
        result = StaleResult.from_procedure("/nonexistent/path/file.md")
        assert result.is_stale is True
        assert any(m["type"] == "file_not_found" for m in result.mismatches)

# ── _check_line_refs ─────────────────────────────────────────────────────────


class TestCheckLineRefs:
    def test_valid_line_number_passes(self) -> None:
        result = StaleResult.clean()
        proc_text = "See Line 10"
        source_lines = [""] * 20
        _check_line_refs(result, proc_text, source_lines)
        assert result.is_stale is False

    def test_out_of_bounds_line_returns_stale(self) -> None:
        result = StaleResult.clean()
        proc_text = "See Line 9999"
        source_lines = [""] * 100
        _check_line_refs(result, proc_text, source_lines)
        assert result.is_stale is True
        assert any(m["type"] == "line_out_of_bounds" for m in result.mismatches)

    def test_line_range_exceeds_source_returns_stale(self) -> None:
        result = StaleResult.clean()
        proc_text = "See Lines 10-20"
        source_lines = [""] * 15
        _check_line_refs(result, proc_text, source_lines)
        assert result.is_stale is True

# ── _check_symbol_refs ───────────────────────────────────────────────────────


class TestCheckSymbolRefs:
    def test_existing_symbol_passes(self) -> None:
        result = StaleResult.clean()
        proc_text = "Use `LLMTurnRunner` here"
        source_content = "from agent.llm_turn_runner import LLMTurnRunner"
        _check_symbol_refs(result, proc_text, source_content)
        assert result.is_stale is False

    def test_missing_symbol_returns_stale(self) -> None:
        result = StaleResult.clean()
        proc_text = "Use `_missing_symbol` here"
        source_content = "# no such symbol exists"
        _check_symbol_refs(result, proc_text, source_content)
        assert result.is_stale is True
        assert any(m["type"] == "symbol_missing" for m in result.mismatches)

    def test_http_urls_filtered_out(self) -> None:
        result = StaleResult.clean()
        proc_text = "See `http://example.com`"
        source_content = ""
        _check_symbol_refs(result, proc_text, source_content)
        assert result.is_stale is False

    def test_paths_filtered_out(self) -> None:
        result = StaleResult.clean()
        proc_text = "See `/some/path`"
        source_content = ""
        _check_symbol_refs(result, proc_text, source_content)
        assert result.is_stale is False

# ── _check_import_refs ───────────────────────────────────────────────────────


class TestCheckImportRefs:
    def test_existing_import_passes(self) -> None:
        result = StaleResult.clean()
        proc_text = "from agent.llm_turn_runner import LLMTurnRunner"
        source_content = "from agent.llm_turn_runner import LLMTurnRunner"
        _check_import_refs(result, proc_text, source_content)
        assert result.is_stale is False

    def test_missing_import_returns_stale(self) -> None:
        result = StaleResult.clean()
        proc_text = "from agent.tool_loop_guard import ToolLoopGuard"
        source_content = "# no import here"
        _check_import_refs(result, proc_text, source_content)
        assert result.is_stale is True
        assert any(m["type"] == "import_missing" for m in result.mismatches)

# ── _check_before_blocks ─────────────────────────────────────────────────────


class TestCheckBeforeBlocks:
    def test_existing_before_block_passes(self) -> None:
        result = StaleResult.clean()
        proc_text = "# Before:\n    x = 1\n# After:"
        source_content = "    x = 1"
        _check_before_blocks(result, proc_text, source_content)
        assert result.is_stale is False

    def test_missing_before_block_returns_stale(self) -> None:
        result = StaleResult.clean()
        proc_text = "# Before:\n    y = 2\n# After:"
        source_content = "# no matching content"
        _check_before_blocks(result, proc_text, source_content)
        assert result.is_stale is True
        assert any(m["type"] == "before_block_missing" for m in result.mismatches)
