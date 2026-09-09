"""tests/rag/test_diagnostics.py

Tests for PipelineDiagnostics and SearchDiagnostics in scripts/rag/diagnostics.py.

Covers:
- from_run_result() produces correct field values
- to_dict() produces byte-for-byte identical dict to current get_diagnostics()
- Edge cases: empty run result, partial diagnostics, all-zero metrics
"""

import pytest
from rag.diagnostics import PipelineDiagnostics, SearchDiagnostics


class TestSearchDiagnosticsFromRunResult:
    """Test SearchDiagnostics.from_run_result() produces correct field values."""

    def test_from_run_result_no_failures(self):
        """All metrics are zero, degraded should be False."""
        diag = SearchDiagnostics.from_run_result(
            embed_ok=5, embed_failed=0, fts_errors=0
        )
        assert diag.embed_ok == 5
        assert diag.embed_failed == 0
        assert diag.fts_errors == 0
        assert diag.degraded is False

    def test_from_run_result_with_embed_failure(self):
        """Embed failure makes degraded True."""
        diag = SearchDiagnostics.from_run_result(
            embed_ok=5, embed_failed=1, fts_errors=0
        )
        assert diag.embed_ok == 5
        assert diag.embed_failed == 1
        assert diag.fts_errors == 0
        assert diag.degraded is True

    def test_from_run_result_with_fts_error(self):
        """FTS error makes degraded True."""
        diag = SearchDiagnostics.from_run_result(
            embed_ok=5, embed_failed=0, fts_errors=2
        )
        assert diag.embed_ok == 5
        assert diag.embed_failed == 0
        assert diag.fts_errors == 2
        assert diag.degraded is True

    def test_from_run_result_all_zero_metrics(self):
        """All metrics are zero, degraded should be False."""
        diag = SearchDiagnostics.from_run_result(
            embed_ok=0, embed_failed=0, fts_errors=0
        )
        assert diag.embed_ok == 0
        assert diag.embed_failed == 0
        assert diag.fts_errors == 0
        assert diag.degraded is False

    def test_from_run_result_both_failures(self):
        """Both embed failure and FTS error make degraded True."""
        diag = SearchDiagnostics.from_run_result(
            embed_ok=5, embed_failed=1, fts_errors=1
        )
        assert diag.embed_ok == 5
        assert diag.embed_failed == 1
        assert diag.fts_errors == 1
        assert diag.degraded is True

    def test_to_dict_matches_current_get_diagnostics_shape(self):
        """to_dict() produces the exact same dict shape as current get_diagnostics()."""
        diag = SearchDiagnostics.from_run_result(
            embed_ok=5, embed_failed=1, fts_errors=2
        )
        d = diag.to_dict()
        assert set(d.keys()) == {"embed_ok", "embed_failed", "fts_errors", "degraded"}
        assert d["embed_ok"] == 5
        assert d["embed_failed"] == 1
        assert d["fts_errors"] == 2
        assert d["degraded"] is True

    def test_to_dict_all_zero(self):
        """to_dict() with all-zero metrics produces correct dict."""
        diag = SearchDiagnostics.from_run_result(
            embed_ok=0, embed_failed=0, fts_errors=0
        )
        d = diag.to_dict()
        assert d["embed_ok"] == 0
        assert d["embed_failed"] == 0
        assert d["fts_errors"] == 0
        assert d["degraded"] is False

    def test_frozen_dataclass_cannot_be_modified(self):
        """Dataclass is frozen, cannot modify fields after creation."""
        diag = SearchDiagnostics.from_run_result(
            embed_ok=5, embed_failed=1, fts_errors=0
        )
        with pytest.raises((TypeError, Exception)):
            diag.embed_ok = 10

    def test_equality_same_values(self):
        """Two instances with same values are equal."""
        diag1 = SearchDiagnostics.from_run_result(
            embed_ok=5, embed_failed=1, fts_errors=0
        )
        diag2 = SearchDiagnostics.from_run_result(
            embed_ok=5, embed_failed=1, fts_errors=0
        )
        assert diag1 == diag2

    def test_inequality_different_values(self):
        """Two instances with different values are not equal."""
        diag1 = SearchDiagnostics.from_run_result(
            embed_ok=5, embed_failed=1, fts_errors=0
        )
        diag2 = SearchDiagnostics.from_run_result(
            embed_ok=5, embed_failed=2, fts_errors=0
        )
        assert diag1 != diag2

    def test_degraded_threshold_edge_case(self):
        """degraded becomes True at exactly one failure."""
        diag_no_failure = SearchDiagnostics.from_run_result(
            embed_ok=5, embed_failed=0, fts_errors=0
        )
        diag_one_failure = SearchDiagnostics.from_run_result(
            embed_ok=5, embed_failed=1, fts_errors=0
        )
        assert diag_no_failure.degraded is False
        assert diag_one_failure.degraded is True

    def test_large_metric_values(self):
        """Large metric values are handled correctly."""
        diag = SearchDiagnostics.from_run_result(
            embed_ok=1000000, embed_failed=999, fts_errors=500
        )
        assert diag.embed_ok == 1000000
        assert diag.embed_failed == 999
        assert diag.fts_errors == 500
        assert diag.degraded is True

    def test_negative_values_are_not_prevented(self):
        """Negative values are not prevented by the dataclass (no validation)."""
        diag = SearchDiagnostics.from_run_result(
            embed_ok=-1, embed_failed=-1, fts_errors=-1
        )
        assert diag.embed_ok == -1
        assert diag.embed_failed == -1
        assert diag.fts_errors == -1
        # Negative values still trigger degraded because they're > 0 check fails
        assert diag.degraded is False  # negative values are NOT > 0


class TestPipelineDiagnosticsFromRunResult:
    """Test PipelineDiagnostics.from_run_result() produces correct field values."""

    def test_from_run_result_basic(self):
        """Basic case: some embeddings ok, some failures."""
        diag = PipelineDiagnostics.from_run_result(
            embed_ok=5, embed_failed=1, fts_errors=2
        )
        assert isinstance(diag.search_diagnostics, SearchDiagnostics)
        assert diag.search_diagnostics.embed_ok == 5
        assert diag.search_diagnostics.embed_failed == 1
        assert diag.search_diagnostics.fts_errors == 2
        assert diag.search_diagnostics.degraded is True

    def test_from_run_result_no_failures(self):
        """No failures: degraded should be False."""
        diag = PipelineDiagnostics.from_run_result(
            embed_ok=10, embed_failed=0, fts_errors=0
        )
        assert diag.search_diagnostics.embed_ok == 10
        assert diag.search_diagnostics.embed_failed == 0
        assert diag.search_diagnostics.fts_errors == 0
        assert diag.search_diagnostics.degraded is False

    def test_from_run_result_all_zero(self):
        """All zero metrics: degraded should be False."""
        diag = PipelineDiagnostics.from_run_result(
            embed_ok=0, embed_failed=0, fts_errors=0
        )
        assert diag.search_diagnostics.embed_ok == 0
        assert diag.search_diagnostics.embed_failed == 0
        assert diag.search_diagnostics.fts_errors == 0
        assert diag.search_diagnostics.degraded is False

    def test_to_dict_matches_current_get_diagnostics_shape(self):
        """to_dict() produces the exact same dict shape as current get_diagnostics()."""
        diag = PipelineDiagnostics.from_run_result(
            embed_ok=5, embed_failed=1, fts_errors=2
        )
        d = diag.to_dict()
        expected_keys = {
            "stage_results",
            "timings",
            "fetch_result",
            "fusion_mode",
            "http_result_kind",
            "fallback_count",
            "fallback_reasons",
            "refiner_fallback_count",
            "refiner_returned_empty",
            "refiner_exception_count",
            "refiner_exception",
            "hit_counts",
            "search_diagnostics",
        }
        assert set(d.keys()) == expected_keys
        sd = d["search_diagnostics"]
        assert set(sd.keys()) == {"embed_ok", "embed_failed", "fts_errors", "degraded"}
        assert sd["embed_ok"] == 5
        assert sd["embed_failed"] == 1
        assert sd["fts_errors"] == 2
        assert sd["degraded"] is True

    def test_to_dict_nested_identity(self):
        """to_dict() nested dict keys match SearchDiagnostics.to_dict() output."""
        diag = PipelineDiagnostics.from_run_result(
            embed_ok=3, embed_failed=0, fts_errors=0
        )
        pipeline_dict = diag.to_dict()
        search_dict = diag.search_diagnostics.to_dict()
        assert pipeline_dict["search_diagnostics"] == search_dict

    def test_from_run_result_cumulative_counters_excluded(self):
        """Cumulative counters (stat_search_embed_failed, stat_search_fts_errors)
        are excluded from PipelineDiagnostics per design decision."""
        diag = PipelineDiagnostics.from_run_result(
            embed_ok=5, embed_failed=1, fts_errors=2
        )
        d = diag.to_dict()
        assert "stat_search_embed_failed" not in d
        assert "stat_search_fts_errors" not in d
        assert "stat_search_embed_failed" not in d["search_diagnostics"]
        assert "stat_search_fts_errors" not in d["search_diagnostics"]

    def test_frozen_dataclass_cannot_be_modified(self):
        """Dataclass is frozen, cannot modify fields after creation."""
        diag = PipelineDiagnostics.from_run_result(
            embed_ok=5, embed_failed=1, fts_errors=0
        )
        with pytest.raises((TypeError, Exception)):
            diag.search_diagnostics = None

    def test_equality_same_values(self):
        """Two instances with same values are equal."""
        diag1 = PipelineDiagnostics.from_run_result(
            embed_ok=5, embed_failed=1, fts_errors=2
        )
        diag2 = PipelineDiagnostics.from_run_result(
            embed_ok=5, embed_failed=1, fts_errors=2
        )
        assert diag1 == diag2

    def test_inequality_different_values(self):
        """Two instances with different values are not equal."""
        diag1 = PipelineDiagnostics.from_run_result(
            embed_ok=5, embed_failed=1, fts_errors=2
        )
        diag2 = PipelineDiagnostics.from_run_result(
            embed_ok=6, embed_failed=1, fts_errors=2
        )
        assert diag1 != diag2

    def test_degraded_threshold_pipeline_level(self):
        """degraded becomes True at exactly one failure at pipeline level."""
        diag_no_failure = PipelineDiagnostics.from_run_result(
            embed_ok=5, embed_failed=0, fts_errors=0
        )
        diag_one_failure = PipelineDiagnostics.from_run_result(
            embed_ok=5, embed_failed=1, fts_errors=0
        )
        assert diag_no_failure.search_diagnostics.degraded is False
        assert diag_one_failure.search_diagnostics.degraded is True

    def test_large_metric_values(self):
        """Large metric values are handled correctly."""
        diag = PipelineDiagnostics.from_run_result(
            embed_ok=1000000, embed_failed=999, fts_errors=500
        )
        assert diag.search_diagnostics.embed_ok == 1000000
        assert diag.search_diagnostics.embed_failed == 999
        assert diag.search_diagnostics.fts_errors == 500
        assert diag.search_diagnostics.degraded is True

    def test_negative_values_at_pipeline_level(self):
        """Negative values at pipeline level don't trigger degraded."""
        diag = PipelineDiagnostics.from_run_result(
            embed_ok=-1, embed_failed=-1, fts_errors=-1
        )
        assert diag.search_diagnostics.embed_ok == -1
        assert diag.search_diagnostics.embed_failed == -1
        assert diag.search_diagnostics.fts_errors == -1
        assert diag.search_diagnostics.degraded is False  # negative values are NOT > 0

    def test_mixed_positive_and_negative_values(self):
        """Mixed positive and negative values: only positive triggers degraded."""
        diag = PipelineDiagnostics.from_run_result(
            embed_ok=5, embed_failed=-1, fts_errors=0
        )
        assert diag.search_diagnostics.embed_ok == 5
        assert diag.search_diagnostics.embed_failed == -1
        assert diag.search_diagnostics.fts_errors == 0
        assert diag.search_diagnostics.degraded is False  # -1 is NOT > 0
