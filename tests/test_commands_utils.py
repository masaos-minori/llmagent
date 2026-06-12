"""
tests/test_commands_utils.py
Unit tests for commands/utils.py: render_history_md, render_export, write_export.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from agent.services.export_formatter import (
    render_export,
    render_history_md,
    write_export,
)
from shared.types import LLMMessage


class TestRenderHistoryMd:
    def test_system_message_skipped(self) -> None:
        history: list[LLMMessage] = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello"},
        ]
        result = render_history_md(history)
        assert "## System" not in result
        assert "## User" in result
        assert "Hello" in result

    def test_user_role(self) -> None:
        history: list[LLMMessage] = [{"role": "user", "content": "Hi there"}]
        result = render_history_md(history)
        assert "## User" in result
        assert "Hi there" in result

    def test_assistant_role(self) -> None:
        history: list[LLMMessage] = [{"role": "assistant", "content": "Sure!"}]
        result = render_history_md(history)
        assert "## Assistant" in result
        assert "Sure!" in result

    def test_tool_role_wraps_code_fence(self) -> None:
        history: list[LLMMessage] = [
            {"role": "tool", "content": "result_data", "tool_call_id": "call_1"}
        ]
        result = render_history_md(history)
        assert "Tool (call_1)" in result
        assert "```" in result
        assert "result_data" in result

    def test_tool_role_without_tool_call_id(self) -> None:
        history: list[LLMMessage] = [{"role": "tool", "content": "data"}]
        result = render_history_md(history)
        assert "## Tool ()\n" in result

    def test_empty_content(self) -> None:
        history: list[LLMMessage] = [{"role": "user"}]
        result = render_history_md(history)
        assert "## User" in result

    def test_empty_history_returns_header(self) -> None:
        result = render_history_md([])
        assert result == "# Conversation Export\n"

    def test_multiple_messages(self) -> None:
        history: list[LLMMessage] = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "World"},
            {"role": "tool", "content": "data", "tool_call_id": "c1"},
        ]
        result = render_history_md(history)
        assert result.count("## ") == 3


class TestRenderExport:
    def test_markdown_format(self) -> None:
        history: list[LLMMessage] = [{"role": "user", "content": "Hi"}]
        result = render_export(history, "md")
        assert "## User" in result

    def test_json_format(self) -> None:
        history: list[LLMMessage] = [{"role": "user", "content": "Hi"}]
        result = render_export(history, "json")
        assert '"role"' in result
        assert '"Hi"' in result

    def test_json_empty_history(self) -> None:
        result = render_export([], "json")
        assert result == "[]"

    def test_unknown_format_falls_back_to_markdown(self) -> None:
        history: list[LLMMessage] = [{"role": "user", "content": "Hi"}]
        result = render_export(history, "unknown")
        assert "## User" in result


class TestWriteExport:
    def test_prints_to_stdout_when_no_outfile(
        self, capsys: pytest.CaptureFixture
    ) -> None:
        write_export("hello world", None, 5)
        captured = capsys.readouterr()
        assert captured.out.strip() == "hello world"

    def test_writes_to_file(self, tmp_path: Path) -> None:
        out = tmp_path / "export.md"
        write_export("content", str(out), 3)
        assert out.read_text(encoding="utf-8") == "content"

    def test_prints_success_message_on_write(
        self, capsys: pytest.CaptureFixture, tmp_path: Path
    ) -> None:
        out = tmp_path / "export.md"
        write_export("data", str(out), 7)
        captured = capsys.readouterr()
        assert "Exported 7 messages" in captured.out
        assert str(out) in captured.out

    def test_raises_export_write_error_on_oserror(self) -> None:
        from agent.services.exceptions import ExportWriteError

        with patch.object(Path, "write_text", side_effect=OSError("permission denied")):
            with pytest.raises(ExportWriteError, match="permission denied"):
                write_export("data", "/nonexistent/export.md", 3)
