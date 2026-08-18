"""tests/mcp_servers/github/test_formatter.py

Characterization tests for scripts/mcp_servers/github/formatter.py.

dry_run_preview has no existing callers or test coverage (verified via
`rg dry_run_preview scripts/` during the 04_refactor.md sweep of this
subsystem); these tests lock its current, verbatim output so any future
change to this module is a deliberate, visible decision.
"""

from __future__ import annotations

from mcp_servers.github.formatter import dry_run_preview


class TestDryRunPreview:
    """Lock the exact formatting behavior of dry_run_preview."""

    def test_wraps_preview_with_standard_prefix(self) -> None:
        """Output starts with the fixed '[DRY RUN]' banner line."""
        result = dry_run_preview("would create file foo.py")

        assert result == (
            "[DRY RUN] The following would be executed:\nwould create file foo.py"
        )

    def test_preserves_multiline_preview_verbatim(self) -> None:
        """Multi-line preview content is preserved as-is after the banner."""
        preview = "line one\nline two"

        result = dry_run_preview(preview)

        assert result == f"[DRY RUN] The following would be executed:\n{preview}"

    def test_empty_preview(self) -> None:
        """Empty string input still produces the banner with a trailing newline."""
        result = dry_run_preview("")

        assert result == "[DRY RUN] The following would be executed:\n"

    def test_return_type_is_str(self) -> None:
        """Return type is a plain str (public API contract)."""
        result = dry_run_preview("x")

        assert isinstance(result, str)
