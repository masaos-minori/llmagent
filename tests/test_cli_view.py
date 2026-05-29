"""
tests/test_cli_view.py
Behavior-lock tests for CLIView.

readline is a C extension that reads/writes real files.  All readline
calls are patched so tests run without a real terminal or history file.
"""

from __future__ import annotations

import asyncio
from unittest.mock import MagicMock, patch

import pytest
from agent.cli_view import CLIView

# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def mock_rl():
    """Patch the readline module used by cli_view."""
    with patch("agent.cli_view.readline") as rl:
        rl.get_history_length.return_value = 0
        yield rl


@pytest.fixture
def view(mock_rl: MagicMock) -> CLIView:
    return CLIView(["/help", "/exit", "/session"])


# ── setup_readline() ─────────────────────────────────────────────────────────


class TestSetupReadline:
    def test_calls_parse_and_bind(self, view: CLIView, mock_rl: MagicMock) -> None:
        view.setup_readline()
        assert mock_rl.parse_and_bind.called

    def test_no_error_when_history_file_missing(
        self, view: CLIView, mock_rl: MagicMock
    ) -> None:
        # HISTORY_FILE does not exist → read_history_file should not be called
        with patch.object(CLIView, "HISTORY_FILE") as fake_path:
            fake_path.exists.return_value = False
            view.setup_readline()
        mock_rl.read_history_file.assert_not_called()

    def test_silences_oserror_on_history_read(
        self, view: CLIView, mock_rl: MagicMock
    ) -> None:
        mock_rl.read_history_file.side_effect = OSError("permission denied")
        with patch.object(CLIView, "HISTORY_FILE") as fake_path:
            fake_path.exists.return_value = True
            fake_path.__str__ = lambda _: "/fake/.agent_history"  # type: ignore[method-assign, misc, assignment]  # MagicMock dunder override
            view.setup_readline()
        # No exception propagated

    def test_sets_history_length(self, view: CLIView, mock_rl: MagicMock) -> None:
        view.setup_readline()
        mock_rl.set_history_length.assert_called_once_with(1000)

    def test_registers_completer_for_slash_commands(
        self, view: CLIView, mock_rl: MagicMock
    ) -> None:
        view.setup_readline()
        mock_rl.set_completer.assert_called_once()
        completer_fn = mock_rl.set_completer.call_args[0][0]
        # Completer should suggest "/help" when given "/h"
        assert completer_fn("/h", 0) == "/help"
        assert completer_fn("/h", 1) is None  # no second match


# ── write_history() ───────────────────────────────────────────────────────────


class TestWriteHistory:
    def test_calls_write_history_file(self, view: CLIView, mock_rl: MagicMock) -> None:
        view.write_history()
        mock_rl.write_history_file.assert_called_once()

    def test_silences_oserror(self, view: CLIView, mock_rl: MagicMock) -> None:
        mock_rl.write_history_file.side_effect = OSError("disk full")
        view.write_history()  # must not raise


# ── read_multiline() ─────────────────────────────────────────────────────────


class TestReadMultiline:
    def _run(self, coro: object) -> str:
        return asyncio.get_event_loop().run_until_complete(coro)  # type: ignore[arg-type]

    def test_joins_continuation_lines(self, view: CLIView) -> None:
        # first_line ends with "\" → continuation expected
        # next input is "world" (no trailing \)
        with patch("builtins.input", side_effect=["world"]):
            loop = asyncio.new_event_loop()
            result = loop.run_until_complete(view.read_multiline(loop, "hello\\"))
            loop.close()
        assert result == "hello\nworld"

    def test_stops_on_empty_line(self, view: CLIView) -> None:
        with patch("builtins.input", side_effect=[""]):
            loop = asyncio.new_event_loop()
            result = loop.run_until_complete(view.read_multiline(loop, "first\\"))
            loop.close()
        assert result == "first"

    def test_chained_continuation(self, view: CLIView) -> None:
        with patch("builtins.input", side_effect=["line2\\", "line3"]):
            loop = asyncio.new_event_loop()
            result = loop.run_until_complete(view.read_multiline(loop, "line1\\"))
            loop.close()
        assert result == "line1\nline2\nline3"

    def test_stops_on_eof(self, view: CLIView) -> None:
        with patch("builtins.input", side_effect=EOFError):
            loop = asyncio.new_event_loop()
            result = loop.run_until_complete(view.read_multiline(loop, "partial\\"))
            loop.close()
        assert result == "partial"

    def test_stops_on_keyboard_interrupt(self, view: CLIView) -> None:
        with patch("builtins.input", side_effect=KeyboardInterrupt):
            loop = asyncio.new_event_loop()
            result = loop.run_until_complete(view.read_multiline(loop, "partial\\"))
            loop.close()
        assert result == "partial"
