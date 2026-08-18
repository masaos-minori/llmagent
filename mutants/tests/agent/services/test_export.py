"""tests/test_export.py
Error-path and behavior tests for export_formatter service.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest


class FakeOut:
    """Test double implementing ExportOutputPort."""

    def __init__(self) -> None:
        self.written: list[str] = []
        self.file_written: list[tuple[str, str, int]] = []

    def write(self, content: str) -> None:
        self.written.append(content)

    def write_file(self, content: str, path: str, n_messages: int) -> None:
        self.file_written.append((content, path, n_messages))


class TestWriteExport:
    def test_write_to_stdout_calls_write(self) -> None:
        from agent.services.export_formatter import write_export

        out = FakeOut()
        write_export("hello content", None, 3, out)
        assert out.written == ["hello content"]
        assert out.file_written == []

    def test_write_to_file_calls_write_file(self, tmp_path) -> None:
        from agent.services.export_formatter import write_export

        target = tmp_path / "out.md"
        out = FakeOut()
        write_export("content", str(target), 5, out)
        assert target.read_text(encoding="utf-8") == "content"
        assert len(out.file_written) == 1
        assert out.file_written[0][1] == str(target)
        assert out.file_written[0][2] == 5

    def test_write_file_os_error_raises_export_write_error(self, tmp_path) -> None:
        from agent.services.exceptions import ExportWriteError
        from agent.services.export_formatter import write_export

        out = FakeOut()
        with patch("pathlib.Path.write_text", side_effect=OSError("disk full")):
            with pytest.raises(ExportWriteError, match="disk full"):
                write_export("content", str(tmp_path / "out.txt"), 5, out)


class TestRenderExport:
    def test_render_json_format(self) -> None:
        from agent.services.enums import ExportFormat
        from agent.services.export_formatter import render_export

        history = [{"role": "user", "content": "hi"}]
        result = render_export(history, ExportFormat.JSON)
        assert '"role"' in result
        assert '"user"' in result

    def test_render_markdown_format(self) -> None:
        from agent.services.enums import ExportFormat
        from agent.services.export_formatter import render_export

        history = [{"role": "user", "content": "hello"}]
        result = render_export(history, ExportFormat.MARKDOWN)
        assert "## User" in result
        assert "hello" in result

    def test_render_markdown_skips_system(self) -> None:
        from agent.services.enums import ExportFormat
        from agent.services.export_formatter import render_export

        history = [
            {"role": "system", "content": "sys prompt"},
            {"role": "user", "content": "hello"},
        ]
        result = render_export(history, ExportFormat.MARKDOWN)
        assert "sys prompt" not in result
        assert "hello" in result
