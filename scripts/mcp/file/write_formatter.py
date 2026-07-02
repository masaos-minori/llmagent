#!/usr/bin/env python3
"""mcp/file/write_formatter.py

Output formatters for file-write-mcp operations.

Dependency direction: mcp.file.write_formatter → mcp.file.write_models
Import from here:  from mcp.file.write_formatter import WriteFileFormatter
"""

from __future__ import annotations

from mcp.file.write_models import (
    CreateDirectoryResponse,
    EditFileResponse,
    MoveFileResponse,
    WriteFileResponse,
)


class WriteFileFormatter:
    """Format WriteFileService results as plain text for the LLM."""

    @staticmethod
    def format_write_result(result: WriteFileResponse) -> str:
        if not result.applied:
            info = f"Dry-run: {result.path} ({result.size} bytes)"
            if result.diff:
                info += f"\n{result.diff}"
            else:
                info += " [new file]"
            return info
        return f"Written: {result.path} ({result.size} bytes)"

    @staticmethod
    def format_edit_result(result: EditFileResponse) -> str:
        if not result.diff:
            return "No changes."
        if result.applied:
            return f"Edited\n{result.diff}"
        return f"Diff only (dry_run)\n{result.diff}"

    @staticmethod
    def format_directory_result(result: CreateDirectoryResponse) -> str:
        if result.dry_run_info:
            return f"Dry-run: {result.path} [{result.dry_run_info}]"
        status = "created" if result.created else "already exists"
        return f"Directory {status}: {result.path}"

    @staticmethod
    def format_move_result(result: MoveFileResponse) -> str:
        if result.dry_run_info:
            return f"Dry-run: {result.source} → {result.destination} [{result.dry_run_info}]"
        return f"Moved: {result.source} → {result.destination}"
