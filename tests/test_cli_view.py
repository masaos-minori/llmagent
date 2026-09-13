"""
tests/test_cli_view.py
Behavior-lock tests for CLIView.

readline is a C extension that reads/writes real files.  All readline
calls are patched so tests run without a real terminal or history file.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest
from agent.cli_view import CLIView, WriterBase
from agent.commands.output_port import CliOutputPort, OutputPort

if TYPE_CHECKING:
    from pytest import CaptureFixture

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


# ── display helpers ────────────────────────────────────────────────────────────


class TestDisplayHelpers:
    def test_write_token(self, view: CLIView, capsys: CaptureFixture[str]) -> None:
        view.write_token("hello")
        captured = capsys.readouterr()
        assert "hello" in captured.out

    def test_write_compress_notice(
        self, view: CLIView, capsys: CaptureFixture[str]
    ) -> None:
        view.write_compress_notice(3)
        captured = capsys.readouterr()
        assert (
            captured.out == "  [context] history compressed (3 messages summarized)\n"
        )

    def test_write_turn_start(self, view: CLIView, capsys: CaptureFixture[str]) -> None:
        view.write_turn_start()
        captured = capsys.readouterr()
        assert captured.out == "\n"

    def test_write_turn_end(self, view: CLIView, capsys: CaptureFixture[str]) -> None:
        view.write_turn_end()
        captured = capsys.readouterr()
        assert captured.out == "\n"

    def test_write_llm_error(self, view: CLIView, capsys: CaptureFixture[str]) -> None:
        view.write_llm_error(RuntimeError("connection failed"))
        captured = capsys.readouterr()
        assert "connection failed" in captured.out

    def test_write_progress(self, view: CLIView, capsys: CaptureFixture[str]) -> None:
        view.write_progress("searching...")
        captured = capsys.readouterr()
        assert "searching..." in captured.out

    def test_clear_progress(self, view: CLIView, capsys: CaptureFixture[str]) -> None:
        view.clear_progress()
        captured = capsys.readouterr()
        assert len(captured.out) >= 32

    def test_write_warning(self, view: CLIView, capsys: CaptureFixture[str]) -> None:
        view.write_warning("disk space low")
        captured = capsys.readouterr()
        assert captured.out == "[warn] disk space low\n"


# ── Delegation verification (T-002) ────────────────────────────────────────────


class TestDelegationVerification:
    """Verify CLIView delegates to OutputPort instance rather than implementing Writer directly."""

    @pytest.fixture
    def mock_port(self) -> MagicMock:
        return MagicMock(spec=OutputPort)

    @pytest.fixture
    def view_with_mock_port(self, mock_rl: MagicMock, mock_port: MagicMock) -> CLIView:
        return CLIView(["/help", "/exit", "/session"], port=mock_port)

    def test_delegates_write_token_to_outputport(
        self, view_with_mock_port: CLIView, mock_port: MagicMock
    ) -> None:
        view_with_mock_port.write_token("hello")
        mock_port.write_token.assert_called_once_with("hello")

    def test_delegates_write_compress_notice_to_outputport(
        self, view_with_mock_port: CLIView, mock_port: MagicMock
    ) -> None:
        view_with_mock_port.write_compress_notice(3)
        mock_port.write_compress_notice.assert_called_once_with(3)

    def test_delegates_write_turn_start_to_outputport(
        self, view_with_mock_port: CLIView, mock_port: MagicMock
    ) -> None:
        view_with_mock_port.write_turn_start()
        mock_port.write_turn_start.assert_called_once()

    def test_delegates_write_turn_end_to_outputport(
        self, view_with_mock_port: CLIView, mock_port: MagicMock
    ) -> None:
        view_with_mock_port.write_turn_end()
        mock_port.write_turn_end.assert_called_once()

    def test_delegates_write_llm_error_to_outputport(
        self, view_with_mock_port: CLIView, mock_port: MagicMock
    ) -> None:
        exc = RuntimeError("connection failed")
        view_with_mock_port.write_llm_error(exc)
        mock_port.write_llm_error.assert_called_once_with(exc)

    def test_delegates_write_progress_to_outputport(
        self, view_with_mock_port: CLIView, mock_port: MagicMock
    ) -> None:
        view_with_mock_port.write_progress("searching...")
        mock_port.write_progress.assert_called_once_with("searching...")

    def test_delegates_clear_progress_to_outputport(
        self, view_with_mock_port: CLIView, mock_port: MagicMock
    ) -> None:
        view_with_mock_port.clear_progress()
        mock_port.clear_progress.assert_called_once()

    def test_delegates_write_warning_to_outputport(
        self, view_with_mock_port: CLIView, mock_port: MagicMock
    ) -> None:
        view_with_mock_port.write_warning("disk space low")
        mock_port.write_warning.assert_called_once_with("disk space low")

    def test_delegates_write_fatal_to_outputport(
        self, view_with_mock_port: CLIView, mock_port: MagicMock
    ) -> None:
        view_with_mock_port.write_fatal("unrecoverable error")
        mock_port.write_fatal.assert_called_once_with("unrecoverable error")

    def test_delegates_write_startup_banner_to_outputport(
        self, view_with_mock_port: CLIView, mock_port: MagicMock
    ) -> None:
        view_with_mock_port.write_startup_banner("12345", 10)
        mock_port.write_startup_banner.assert_called_once_with(
            "12345", 10, "", None
        )

    def test_delegates_write_table_to_outputport(
        self, view_with_mock_port: CLIView, mock_port: MagicMock
    ) -> None:
        headers = ["A", "B"]
        rows = [["1", "2"]]
        view_with_mock_port.write_table(headers, rows)
        mock_port.write_table.assert_called_once_with(headers, rows)

    def test_delegates_write_kv_to_outputport(
        self, view_with_mock_port: CLIView, mock_port: MagicMock
    ) -> None:
        pairs = [("key", "val")]
        view_with_mock_port.write_kv(pairs)
        mock_port.write_kv.assert_called_once_with(pairs, 22)

    def test_delegates_write_stderr_to_outputport(
        self, view_with_mock_port: CLIView, mock_port: MagicMock
    ) -> None:
        view_with_mock_port.write_stderr("stderr msg")
        mock_port.write_stderr.assert_called_once_with("stderr msg")

    def test_delegates_write_error_to_outputport(
        self, view_with_mock_port: CLIView, mock_port: MagicMock
    ) -> None:
        view_with_mock_port.write_error("fail")
        mock_port.write_error.assert_called_once_with("fail")

    def test_delegates_write_success_to_outputport(
        self, view_with_mock_port: CLIView, mock_port: MagicMock
    ) -> None:
        view_with_mock_port.write_success("ok")
        mock_port.write_success.assert_called_once_with("ok")

    def test_delegates_write_no_data_to_outputport(
        self, view_with_mock_port: CLIView, mock_port: MagicMock
    ) -> None:
        view_with_mock_port.write_no_data("empty")
        mock_port.write_no_data.assert_called_once_with("empty")

    def test_delegates_write_validation_error_to_outputport(
        self, view_with_mock_port: CLIView, mock_port: MagicMock
    ) -> None:
        view_with_mock_port.write_validation_error("bad input")
        mock_port.write_validation_error.assert_called_once_with("bad input")

    def test_delegates_write_file_to_outputport(
        self, view_with_mock_port: CLIView, mock_port: MagicMock
    ) -> None:
        view_with_mock_port.write_file("content", "/tmp/out.json", 10)
        mock_port.write_file.assert_called_once_with("content", "/tmp/out.json", 10)

    def test_cliview_uses_default_cliooutputport_when_none_provided(
        self, mock_rl: MagicMock
    ) -> None:
        view = CLIView(["/help"])
        assert isinstance(view.port, CliOutputPort)

    def test_cliview_uses_injected_outputport(
        self, mock_rl: MagicMock, mock_port: MagicMock
    ) -> None:
        view = CLIView(["/help"], port=mock_port)
        assert view.port is mock_port

    def test_t002_cliooutputport_satisfies_merged_protocol(self) -> None:
        """T-002: CliOutputPort satisfies the merged Protocol."""
        port = CliOutputPort()
        assert isinstance(port, OutputPort)

    def test_write_fatal(self, view: CLIView, capsys: CaptureFixture[str]) -> None:
        view.write_fatal("unrecoverable error")
        captured = capsys.readouterr()
        assert captured.out == "[fatal] unrecoverable error\n"


# ── write_startup_banner ───────────────────────────────────────────────────────


class TestWriteStartupBanner:
    def test_basic_banner(self, view: CLIView, capsys: CaptureFixture[str]) -> None:
        view.write_startup_banner("12345", 10)
        captured = capsys.readouterr()
        assert "DB: 12345 chunks | Tools: 10" in captured.out
        assert "Memory:" not in captured.out
        assert "Workflow:" not in captured.out
        assert "/help" in captured.out

    def test_with_workflow_status(
        self, view: CLIView, capsys: CaptureFixture[str]
    ) -> None:
        view.write_startup_banner("12345", 10, workflow_status="running")
        captured = capsys.readouterr()
        assert "Workflow: running" in captured.out

    def test_with_memory_mode_enabled(
        self, view: CLIView, capsys: CaptureFixture[str]
    ) -> None:
        view.write_startup_banner("12345", 10, memory_mode="enabled")
        captured = capsys.readouterr()
        assert "Memory: enabled" in captured.out

    def test_with_memory_mode_disabled(
        self, view: CLIView, capsys: CaptureFixture[str]
    ) -> None:
        view.write_startup_banner("12345", 10, memory_mode="disabled")
        captured = capsys.readouterr()
        assert "Memory: disabled" in captured.out

    def test_with_custom_memory_mode(
        self, view: CLIView, capsys: CaptureFixture[str]
    ) -> None:
        view.write_startup_banner(
            "12345", 10, memory_mode="Hybrid mode (semantic + FTS)"
        )
        captured = capsys.readouterr()
        assert "Memory: Hybrid mode (semantic + FTS)" in captured.out

    def test_all_fields_together(
        self, view: CLIView, capsys: CaptureFixture[str]
    ) -> None:
        view.write_startup_banner(
            "12345", 10, workflow_status="running", memory_mode="enabled"
        )
        captured = capsys.readouterr()
        assert "DB: 12345 chunks | Tools: 10" in captured.out
        assert "Memory: enabled" in captured.out
        assert "Workflow: running" in captured.out
        assert "/help" in captured.out


# ── spinner ──────────────────────────────────────────────────────────────────


class TestSpinner:
    @pytest.mark.asyncio
    async def test_start_stop_spinner(
        self, view: CLIView, capsys: CaptureFixture[str]
    ) -> None:
        await view.start_spinner("Loading")
        await asyncio.sleep(0.05)
        view.stop_spinner()
        captured = capsys.readouterr()
        assert "Loading" in captured.out

    @pytest.mark.asyncio
    async def test_stop_spinner_is_idempotent(
        self, view: CLIView, capsys: CaptureFixture[str]
    ) -> None:
        await view.start_spinner()
        view.stop_spinner()
        view.stop_spinner()
        view.stop_spinner()
        captured = capsys.readouterr()
        assert captured.out.count("\r") >= 3

    @pytest.mark.asyncio
    async def test_write_token_stops_spinner(
        self, view: CLIView, capsys: CaptureFixture[str]
    ) -> None:
        await view.start_spinner("Waiting")
        await asyncio.sleep(0.05)
        view.write_token("hello")
        await asyncio.sleep(0.15)
        view.stop_spinner()
        captured = capsys.readouterr()
        assert "hello" in captured.out
        assert "Waiting" in captured.out

    @pytest.mark.asyncio
    async def test_start_spinner_stops_previous(
        self, view: CLIView, capsys: CaptureFixture[str]
    ) -> None:
        await view.start_spinner("First")
        await asyncio.sleep(0.05)
        await view.start_spinner("Second")
        await asyncio.sleep(0.05)
        view.stop_spinner()
        captured = capsys.readouterr()
        assert "Second" in captured.out


# ── WriterBase / partial test double ──────────────────────────────────────────


class PartialWriter(WriterBase):
    """Partial test double: only implements write_token."""

    def write_token(self, token: str) -> None:
        print(f"[partial] {token}")


class FullWriter(WriterBase):
    """Full implementation satisfying all Writer methods."""

    def write_token(self, token: str) -> None:
        print(token)

    def write_compress_notice(self, n: int) -> None:
        print(n)

    def write_turn_start(self) -> None:
        pass

    def write_turn_end(self) -> None:
        pass

    def write_llm_error(self, e: Exception) -> None:
        print(e)

    def write_progress(self, msg: str) -> None:
        print(msg)

    def clear_progress(self) -> None:
        pass

    def write_warning(self, msg: str) -> None:
        print(msg)

    def write_fatal(self, msg: str) -> None:
        print(msg)

    def write_startup_banner(
        self,
        chunk_count: str,
        n_tools: int,
        workflow_status: str = "",
        memory_mode: str | None = None,
    ) -> None:
        print(chunk_count)


def test_partial_writer_satisfies_writer_base() -> None:
    pw = PartialWriter()
    assert isinstance(pw, WriterBase)


def test_full_writer_satisfies_writer_base() -> None:
    fw = FullWriter()
    assert isinstance(fw, WriterBase)


def test_partial_writer_raises_on_unimplemented_method() -> None:
    pw = PartialWriter()
    with pytest.raises(NotImplementedError, match="write_compress_notice"):
        pw.write_compress_notice(10)


def test_cliview_inherits_writerbase() -> None:
    view = CLIView([])
    assert isinstance(view, WriterBase)
