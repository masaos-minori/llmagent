"""tests/mcp_servers/file/test_write_formatter.py

Characterization tests for mcp_servers.file.write_formatter — locks the exact
plain-text output strings returned to the LLM for file_write/edit_file/
directory_create/file_move MCP tool results.
"""

from __future__ import annotations

from mcp_servers.file.write_formatter import WriteFileFormatter
from mcp_servers.file.write_models import (
    CreateDirectoryResponse,
    EditFileResponse,
    MoveFileResponse,
    WriteFileResponse,
)


class TestFormatWriteResult:
    def test_applied_true_returns_written_message(self):
        result = WriteFileResponse(path="/tmp/a.txt", size=5, applied=True, diff="")

        formatted = WriteFileFormatter.format_write_result(result)

        assert formatted == "Written: /tmp/a.txt (5 bytes)"

    def test_applied_true_ignores_diff(self):
        # diff is irrelevant once applied=True; the message must not include it.
        result = WriteFileResponse(
            path="/tmp/a.txt", size=5, applied=True, diff="--- a\n+++ b"
        )

        formatted = WriteFileFormatter.format_write_result(result)

        assert formatted == "Written: /tmp/a.txt (5 bytes)"
        assert "--- a" not in formatted

    def test_applied_false_with_diff_returns_dry_run_with_diff(self):
        result = WriteFileResponse(
            path="/tmp/a.txt", size=5, applied=False, diff="--- a\n+++ b"
        )

        formatted = WriteFileFormatter.format_write_result(result)

        assert formatted == "Dry-run: /tmp/a.txt (5 bytes)\n--- a\n+++ b"

    def test_applied_false_without_diff_returns_new_file_marker(self):
        result = WriteFileResponse(path="/tmp/a.txt", size=5, applied=False, diff="")

        formatted = WriteFileFormatter.format_write_result(result)

        assert formatted == "Dry-run: /tmp/a.txt (5 bytes) [new file]"


class TestFormatEditResult:
    def test_no_diff_returns_no_changes(self):
        result = EditFileResponse(path="/tmp/a.txt", diff="", applied=True)

        formatted = WriteFileFormatter.format_edit_result(result)

        assert formatted == "No changes."

    def test_no_diff_returns_no_changes_even_when_not_applied(self):
        result = EditFileResponse(path="/tmp/a.txt", diff="", applied=False)

        formatted = WriteFileFormatter.format_edit_result(result)

        assert formatted == "No changes."

    def test_diff_and_applied_true_returns_edited_message(self):
        result = EditFileResponse(path="/tmp/a.txt", diff="--- a\n+++ b", applied=True)

        formatted = WriteFileFormatter.format_edit_result(result)

        assert formatted == "Edited\n--- a\n+++ b"

    def test_diff_and_applied_false_returns_dry_run_message(self):
        result = EditFileResponse(path="/tmp/a.txt", diff="--- a\n+++ b", applied=False)

        formatted = WriteFileFormatter.format_edit_result(result)

        assert formatted == "Diff only (dry_run)\n--- a\n+++ b"


class TestFormatDirectoryResult:
    def test_dry_run_info_returns_dry_run_message(self):
        result = CreateDirectoryResponse(
            path="/tmp/dir", created=False, dry_run_info="parent missing"
        )

        formatted = WriteFileFormatter.format_directory_result(result)

        assert formatted == "Dry-run: /tmp/dir [parent missing]"

    def test_created_true_returns_created_message(self):
        result = CreateDirectoryResponse(path="/tmp/dir", created=True, dry_run_info="")

        formatted = WriteFileFormatter.format_directory_result(result)

        assert formatted == "Directory created: /tmp/dir"

    def test_created_false_returns_already_exists_message(self):
        result = CreateDirectoryResponse(
            path="/tmp/dir", created=False, dry_run_info=""
        )

        formatted = WriteFileFormatter.format_directory_result(result)

        assert formatted == "Directory already exists: /tmp/dir"


class TestFormatMoveResult:
    def test_dry_run_info_returns_dry_run_message(self):
        result = MoveFileResponse(
            source="/tmp/a.txt", destination="/tmp/b.txt", dry_run_info="ok"
        )

        formatted = WriteFileFormatter.format_move_result(result)

        assert formatted == "Dry-run: /tmp/a.txt → /tmp/b.txt [ok]"

    def test_no_dry_run_info_returns_moved_message(self):
        result = MoveFileResponse(
            source="/tmp/a.txt", destination="/tmp/b.txt", dry_run_info=""
        )

        formatted = WriteFileFormatter.format_move_result(result)

        assert formatted == "Moved: /tmp/a.txt → /tmp/b.txt"
