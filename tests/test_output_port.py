#!/usr/bin/env python3
"""tests/test_output_port.py

Tests for the merged OutputPort Protocol — verifies that the unified
Protocol covers all methods previously split between Writer and
ExportOutputPort Protocols.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from agent.commands.output_port import CliOutputPort, OutputPort
from agent.output_tags import OutputTag


class TestOutputPortProtocolCoverage:
    """Verify T-001: OutputPort Protocol covers all methods previously split."""

    @pytest.fixture
    def mock_port(self) -> MagicMock:
        return MagicMock(spec=OutputPort)

    @pytest.mark.parametrize(
        "method_name",
        [
            "write",
            "write_table",
            "write_error",
            "write_success",
            "write_no_data",
            "write_validation_error",
            "write_kv",
            "write_token",
            "write_compress_notice",
            "write_turn_start",
            "write_turn_end",
            "write_llm_error",
            "write_progress",
            "clear_progress",
            "write_warning",
            "write_fatal",
            "write_startup_banner",
            "write_file",
            "write_stderr",
        ],
    )
    def test_all_protocol_methods_callable_via_single_interface(
        self, mock_port: MagicMock, method_name: str
    ) -> None:
        """T-001: All protocol methods callable via single interface."""
        assert hasattr(mock_port, method_name), f"{method_name} not on OutputPort"
        method = getattr(mock_port, method_name)
        assert callable(method), f"{method_name} is not callable"

    def test_write_method(self, mock_port: MagicMock) -> None:
        mock_port.write("hello")
        mock_port.write.assert_called_once_with("hello")

    def test_write_table_method(self, mock_port: MagicMock) -> None:
        headers = ["A", "B"]
        rows = [["1", "2"], ["3", "4"]]
        mock_port.write_table(headers, rows)
        mock_port.write_table.assert_called_once_with(headers, rows)

    def test_write_error_method(self, mock_port: MagicMock) -> None:
        mock_port.write_error("fail")
        mock_port.write_error.assert_called_once_with("fail")

    def test_write_success_method(self, mock_port: MagicMock) -> None:
        mock_port.write_success("ok")
        mock_port.write_success.assert_called_once_with("ok")

    def test_write_no_data_method(self, mock_port: MagicMock) -> None:
        mock_port.write_no_data("empty")
        mock_port.write_no_data.assert_called_once_with("empty")

    def test_write_validation_error_method(self, mock_port: MagicMock) -> None:
        mock_port.write_validation_error("bad input")
        mock_port.write_validation_error.assert_called_once_with("bad input")

    def test_write_kv_method(self, mock_port: MagicMock) -> None:
        pairs = [("key", "val")]
        mock_port.write_kv(pairs)
        mock_port.write_kv.assert_called_once_with(pairs)

    def test_write_kv_method_with_key_width(self, mock_port: MagicMock) -> None:
        pairs = [("key", "val")]
        mock_port.write_kv(pairs, key_width=30)
        mock_port.write_kv.assert_called_once_with(pairs, key_width=30)

    def test_write_token_method(self, mock_port: MagicMock) -> None:
        mock_port.write_token("token")
        mock_port.write_token.assert_called_once_with("token")

    def test_write_compress_notice_method(self, mock_port: MagicMock) -> None:
        mock_port.write_compress_notice(5)
        mock_port.write_compress_notice.assert_called_once_with(5)

    def test_write_turn_start_method(self, mock_port: MagicMock) -> None:
        mock_port.write_turn_start()
        mock_port.write_turn_start.assert_called_once()

    def test_write_turn_end_method(self, mock_port: MagicMock) -> None:
        mock_port.write_turn_end()
        mock_port.write_turn_end.assert_called_once()

    def test_write_llm_error_method(self, mock_port: MagicMock) -> None:
        exc = ValueError("timeout")
        mock_port.write_llm_error(exc)
        mock_port.write_llm_error.assert_called_once_with(exc)

    def test_write_progress_method(self, mock_port: MagicMock) -> None:
        mock_port.write_progress("loading")
        mock_port.write_progress.assert_called_once_with("loading")

    def test_clear_progress_method(self, mock_port: MagicMock) -> None:
        mock_port.clear_progress()
        mock_port.clear_progress.assert_called_once()

    def test_write_warning_method(self, mock_port: MagicMock) -> None:
        mock_port.write_warning("disk low")
        mock_port.write_warning.assert_called_once_with("disk low")

    def test_write_fatal_method(self, mock_port: MagicMock) -> None:
        mock_port.write_fatal("crash")
        mock_port.write_fatal.assert_called_once_with("crash")

    def test_write_startup_banner_method(self, mock_port: MagicMock) -> None:
        mock_port.write_startup_banner("42", 5, "running", "sqlite")
        mock_port.write_startup_banner.assert_called_once_with(
            "42", 5, "running", "sqlite"
        )

    def test_write_file_method(self, mock_port: MagicMock) -> None:
        mock_port.write_file("data", "/tmp/out.json", 10)
        mock_port.write_file.assert_called_once_with("data", "/tmp/out.json", 10)

    def test_write_stderr_method(self, mock_port: MagicMock) -> None:
        mock_port.write_stderr("stderr msg")
        mock_port.write_stderr.assert_called_once_with("stderr msg")

    def test_mock_replaces_both_writer_and_outputport_mocks(
        self, mock_port: MagicMock
    ) -> None:
        """Single OutputPort mock replaces both Writer and OutputPort mocks."""
        # Previously needed two separate mocks; now one suffices
        mock_port.write("plain")
        mock_port.write_error("err")
        mock_port.write_success("ok")
        mock_port.write_warning("warn")
        mock_port.write_token("tok")
        mock_port.write_table(["h"], [["r"]])
        mock_port.write_kv([("k", "v")])
        mock_port.write_stderr("err")
        mock_port.write_file("c", "p", 1)
        assert mock_port.write.call_count == 1
        assert mock_port.write_error.call_count == 1
        assert mock_port.write_success.call_count == 1
        assert mock_port.write_warning.call_count == 1
        assert mock_port.write_token.call_count == 1
        assert mock_port.write_table.call_count == 1
        assert mock_port.write_kv.call_count == 1
        assert mock_port.write_stderr.call_count == 1
        assert mock_port.write_file.call_count == 1

    def test_runtime_checkable_protocol(self) -> None:
        """CliOutputPort instance passes isinstance check against OutputPort."""
        port = CliOutputPort()
        assert isinstance(port, OutputPort)

    def test_clioutputport_write_to_stdout(self, capsys: Any) -> None:
        port = CliOutputPort()
        port.write("hello")
        captured = capsys.readouterr()
        assert captured.out.strip() == "hello"

    def test_clioutputport_write_error_prefix(self, capsys: Any) -> None:
        port = CliOutputPort()
        port.write_error("fail")
        captured = capsys.readouterr()
        assert captured.out.strip() == "[error] fail"

    def test_clioutputport_write_success_prefix(self, capsys: Any) -> None:
        port = CliOutputPort()
        port.write_success("ok")
        captured = capsys.readouterr()
        assert captured.out.strip() == "ok"

    def test_clioutputport_write_no_data_prefix(self, capsys: Any) -> None:
        port = CliOutputPort()
        port.write_no_data("empty")
        captured = capsys.readouterr()
        assert captured.out.strip() == "empty"

    def test_clioutputport_write_validation_error_prefix(self, capsys: Any) -> None:
        port = CliOutputPort()
        port.write_validation_error("bad")
        captured = capsys.readouterr()
        assert captured.out.strip() == f"{OutputTag.USAGE} bad"

    def test_clioutputport_write_warning_prefix(self, capsys: Any) -> None:
        port = CliOutputPort()
        port.write_warning("low disk")
        captured = capsys.readouterr()
        assert captured.out.strip() == f"{OutputTag.WARN} low disk"

    def test_clioutputport_write_fatal_prefix(self, capsys: Any) -> None:
        port = CliOutputPort()
        port.write_fatal("crash")
        captured = capsys.readouterr()
        assert captured.out.strip() == f"{OutputTag.FATAL} crash"

    def test_clioutputport_write_token_no_newline(self, capsys: Any) -> None:
        port = CliOutputPort()
        port.write_token("tok")
        captured = capsys.readouterr()
        assert captured.out == "tok"

    def test_clioutputport_write_turn_start_blank_line(self, capsys: Any) -> None:
        port = CliOutputPort()
        port.write_turn_start()
        captured = capsys.readouterr()
        assert captured.out.strip() == ""

    def test_clioutputport_write_turn_end_blank_line(self, capsys: Any) -> None:
        port = CliOutputPort()
        port.write_turn_end()
        captured = capsys.readouterr()
        assert captured.out.strip() == ""

    @patch("builtins.print")
    def test_clioutputport_write_llm_error_prints_tagged_message(
        self, mock_print: MagicMock
    ) -> None:
        port = CliOutputPort()
        exc = ValueError("timeout")
        port.write_llm_error(exc)
        args = mock_print.call_args[0]
        assert len(args) >= 1
        assert "[error]" in str(args[0])

    @patch("builtins.print")
    def test_clioutputport_write_progress_overwrites_line(
        self, mock_print: MagicMock
    ) -> None:
        port = CliOutputPort()
        port.write_progress("loading")
        args = mock_print.call_args[0]
        kwargs = mock_print.call_args[1]
        assert "loading" in str(args[0])
        assert kwargs.get("end") == "\r"

    def test_clioutputport_clear_progress(self, capsys: Any) -> None:
        port = CliOutputPort()
        with patch("builtins.print"):
            port.clear_progress()

    def test_clioutputport_write_kv_aligned(self, capsys: Any) -> None:
        port = CliOutputPort()
        pairs = [("a", "1"), ("bb", "2")]
        port.write_kv(pairs, key_width=5)
        captured = capsys.readouterr()
        lines = [ln for ln in captured.out.split("\n") if ln.strip()]
        assert len(lines) == 2
        # key_width=5: 'a'→'a    ' (5文字), 'bb'→'bb   ' (5文字)
        assert any("a    : 1" in ln for ln in lines)
        assert any("bb   : 2" in ln for ln in lines)

    def test_clioutputport_write_file_confirms_export(self, capsys: Any) -> None:
        port = CliOutputPort()
        port.write_file("content", "/tmp/out.json", 10)
        captured = capsys.readouterr()
        assert "Exported 10 messages to /tmp/out.json" in captured.out

    def test_clioutputport_write_stderr_to_stderr(self, capsys: Any) -> None:
        port = CliOutputPort()
        port.write_stderr("stderr msg")
        captured = capsys.readouterr()
        assert captured.err.strip() == "stderr msg"
