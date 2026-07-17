#!/usr/bin/env python3
"""mcp_servers/file/delete_formatter.py

Output formatters for file-delete-mcp operations.

Dependency direction: mcp_servers.file.delete_formatter → mcp_servers.file.delete_models
Import from here:  from mcp_servers.file.delete_formatter import DeleteFileFormatter
"""

from __future__ import annotations

from mcp_servers.file.delete_models import (
    DeleteDirectoryResponse,
    DeleteFileResponse,
)


class DeleteFileFormatter:
    """Format DeleteFileService results as plain text for the LLM."""

    @staticmethod
    def format_file_result(result: DeleteFileResponse) -> str:
        """Return a human-readable string describing the file deletion outcome."""
        if not result.deleted:
            return f"Dry-run: {result.path} ({result.file_info})"
        return f"Deleted: {result.path}"

    @staticmethod
    def format_directory_result(result: DeleteDirectoryResponse) -> str:
        """Return a human-readable string describing the directory deletion outcome."""
        if not result.deleted:
            return f"Dry-run: {result.path} ({result.dir_info})"
        return f"Directory deleted: {result.path}"
