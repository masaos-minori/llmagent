"""
tests/test_command_formatter.py
Unit tests for agent/commands/formatter.py.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import agent.commands.formatter as fmt_module
from agent.commands.formatter import (
    print_error,
    print_kv_list,
    print_no_data,
    print_success,
    print_table,
    print_validation_error,
)


class TestPrintFunctions:
    def test_print_success_delegates(self) -> None:
        mock_out = MagicMock()
        with patch.object(fmt_module, "_default_out", mock_out):
            print_success("ok")
        mock_out.write_success.assert_called_once_with("ok")

    def test_print_error_delegates(self) -> None:
        mock_out = MagicMock()
        with patch.object(fmt_module, "_default_out", mock_out):
            print_error("oops")
        mock_out.write_error.assert_called_once_with("oops")

    def test_print_no_data_delegates(self) -> None:
        mock_out = MagicMock()
        with patch.object(fmt_module, "_default_out", mock_out):
            print_no_data("nothing here")
        mock_out.write_no_data.assert_called_once_with("nothing here")

    def test_print_validation_error_delegates(self) -> None:
        mock_out = MagicMock()
        with patch.object(fmt_module, "_default_out", mock_out):
            print_validation_error("bad args")
        mock_out.write_validation_error.assert_called_once_with("bad args")

    def test_print_table_delegates(self) -> None:
        mock_out = MagicMock()
        headers = ["Name", "Value"]
        rows = [["a", "1"]]
        with patch.object(fmt_module, "_default_out", mock_out):
            print_table(headers, rows)
        mock_out.write_table.assert_called_once_with(headers, rows)

    def test_print_kv_list_delegates(self) -> None:
        mock_out = MagicMock()
        pairs = [("key", "val")]
        with patch.object(fmt_module, "_default_out", mock_out):
            print_kv_list(pairs, key_width=10)
        mock_out.write_kv.assert_called_once_with(pairs, 10)

    def test_print_kv_list_default_width(self) -> None:
        mock_out = MagicMock()
        pairs = [("key", "val")]
        with patch.object(fmt_module, "_default_out", mock_out):
            print_kv_list(pairs)
        mock_out.write_kv.assert_called_once_with(pairs, 22)
