"""tests/mcp_servers/file/test_delete_formatter.py

Characterization tests for mcp_servers.file.delete_formatter — locks the exact
plain-text output strings returned to the LLM for file_delete/directory_delete
MCP tool results.
"""

from __future__ import annotations

from mcp_servers.file.delete_formatter import DeleteFileFormatter
from mcp_servers.file.delete_models import (
    DeleteDirectoryResponse,
    DeleteFileResponse,
)


class TestFormatFileResult:
    def test_deleted_true_returns_deleted_message(self):
        result = DeleteFileResponse(path="/tmp/a.txt", deleted=True)

        formatted = DeleteFileFormatter.format_file_result(result)

        assert formatted == "Deleted: /tmp/a.txt"

    def test_deleted_false_returns_dry_run_message_with_file_info(self):
        result = DeleteFileResponse(
            path="/tmp/a.txt", deleted=False, file_info="size=5 mode=0o644"
        )

        formatted = DeleteFileFormatter.format_file_result(result)

        assert formatted == "Dry-run: /tmp/a.txt (size=5 mode=0o644)"

    def test_deleted_false_with_empty_file_info(self):
        result = DeleteFileResponse(path="/tmp/a.txt", deleted=False, file_info="")

        formatted = DeleteFileFormatter.format_file_result(result)

        assert formatted == "Dry-run: /tmp/a.txt ()"

    def test_deleted_true_ignores_file_info(self):
        # file_info is irrelevant once deleted=True; the message must not include it.
        result = DeleteFileResponse(
            path="/tmp/a.txt", deleted=True, file_info="size=5 mode=0o644"
        )

        formatted = DeleteFileFormatter.format_file_result(result)

        assert formatted == "Deleted: /tmp/a.txt"
        assert "size=5" not in formatted


class TestFormatDirectoryResult:
    def test_deleted_true_returns_directory_deleted_message(self):
        result = DeleteDirectoryResponse(path="/tmp/dir", deleted=True)

        formatted = DeleteFileFormatter.format_directory_result(result)

        assert formatted == "Directory deleted: /tmp/dir"

    def test_deleted_false_returns_dry_run_message_with_dir_info(self):
        result = DeleteDirectoryResponse(
            path="/tmp/dir", deleted=False, dir_info="files=3 dirs=1"
        )

        formatted = DeleteFileFormatter.format_directory_result(result)

        assert formatted == "Dry-run: /tmp/dir (files=3 dirs=1)"

    def test_deleted_false_with_empty_dir_info(self):
        result = DeleteDirectoryResponse(path="/tmp/dir", deleted=False, dir_info="")

        formatted = DeleteFileFormatter.format_directory_result(result)

        assert formatted == "Dry-run: /tmp/dir ()"

    def test_deleted_true_ignores_dir_info(self):
        # dir_info is irrelevant once deleted=True; the message must not include it.
        result = DeleteDirectoryResponse(
            path="/tmp/dir", deleted=True, dir_info="files=3 dirs=1"
        )

        formatted = DeleteFileFormatter.format_directory_result(result)

        assert formatted == "Directory deleted: /tmp/dir"
        assert "files=3" not in formatted
