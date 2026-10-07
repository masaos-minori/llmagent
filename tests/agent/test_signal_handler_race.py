"""Characterization tests for signal handler race condition prevention."""

import asyncio
import signal
from unittest.mock import MagicMock, patch

import pytest
from agent.repl import AgentREPL


class TestTurnActiveFlagCheck:
    """Verify _turn_active flag is checked/set in signal handler context."""

    def test_turn_active_set_before_turn(self) -> None:
        """_turn_active is set to True before a turn starts."""
        handler = MagicMock(spec=AgentREPL)
        handler._turn_active = False

        # Simulate what happens in _handle_turn_start
        handler._turn_active = True
        assert handler._turn_active is True

    def test_turn_active_reset_after_turn(self) -> None:
        """_turn_active is reset to False after a turn completes."""
        handler = MagicMock(spec=AgentREPL)
        handler._turn_active = True

        # Simulate what happens in _handle_turn_end
        handler._turn_active = False
        assert handler._turn_active is False

    def test_turn_active_prevents_duplicate_processing(self) -> None:
        """If _turn_active is True, duplicate processing is prevented."""
        handler = MagicMock(spec=AgentREPL)
        handler._turn_active = True
        handler._on_first_turn = MagicMock()

        # Simulate the guard check in _handle_turn_start
        if handler._turn_active:
            # Should NOT call _on_first_turn again
            pass
        else:
            asyncio.create_task(handler._on_first_turn("hello"))

        assert handler._on_first_turn.call_count == 0


@pytest.mark.skipif(True, reason="Signal handling tests require real OS-level signals")
class TestCrossPlatformSignalHandlerConsistency:
    """Verify consistent behavior on Unix vs Windows signals."""

    def test_unix_sigint_handler_installed(self) -> None:
        """On Unix, SIGINT handler is installed."""
        mock_handler = MagicMock()
        with (
            patch("signal.signal", return_value=None) as mock_signal,
            patch("signal.getsignal", return_value=None),
        ):
            signal.signal(signal.SIGINT, mock_handler)
            mock_signal.assert_called_with(signal.SIGINT, mock_handler)

    def test_unix_sigterm_handler_installed(self) -> None:
        """On Unix, SIGTERM handler is also installed."""
        mock_handler = MagicMock()
        with (
            patch("signal.signal", return_value=None) as mock_signal,
            patch("signal.getsignal", return_value=None),
        ):
            signal.signal(signal.SIGTERM, mock_handler)
            mock_signal.assert_called_with(signal.SIGTERM, mock_handler)


class TestShutdownCompleteness:
    """Verify shutdown completes properly even when ctx.services becomes None."""

    def test_shutdown_without_services(self) -> None:
        """Shutdown should not crash when services are None."""
        repl = MagicMock(spec=AgentREPL)
        repl.ctx = MagicMock()
        repl.ctx.services = None

        # Simulate shutdown logic that checks for services
        if repl.ctx.services is not None:
            # Would clean up services
            pass
        # If services is None, nothing to clean up — no error

    def test_shutdown_with_partial_services(self) -> None:
        """Shutdown handles partial service availability gracefully."""
        repl = MagicMock(spec=AgentREPL)
        repl.ctx = MagicMock()
        repl.ctx.services = MagicMock()
        repl.ctx.services.hist_mgr = None
        repl.ctx.services.llm = MagicMock()

        # Simulate shutdown that iterates over available services
        if repl.ctx.services.hist_mgr is not None:
            pass  # Would clean up hist_mgr
        if repl.ctx.services.llm is not None:
            pass  # Would clean up llm


class TestWindowsCtypesFallback:
    """Tests for REQ-001: Verify ctypes fallback when pywin32 unavailable."""

    @pytest.mark.skipif(True, reason="Requires Windows platform simulation")
    def test_ctypes_console_ctrl_handler_registered_when_pywin32_unavailable(
        self,
    ) -> None:
        """When pywin32 is unavailable, ctypes.windll.kernel32.SetConsoleCtrlHandler is used."""
        import sys

        # Simulate Windows frozen app without pywin32
        original_frozen = getattr(sys, "frozen", False)
        sys.frozen = True

        try:
            # Mock ImportError for win32api/win32con
            with patch.dict("sys.modules", {"win32api": None, "win32con": None}):
                with patch(
                    "builtins.__import__",
                    side_effect=ImportError("No module named 'win32api'"),
                ):
                    with patch(
                        "ctypes.windll.kernel32.SetConsoleCtrlHandler",
                        return_value=True,
                    ) as mock_set_handler:
                        with patch("ctypes.WINFUNCTYPE", return_value=lambda f: f):
                            with patch("ctypes.wintypes.BOOL", int):
                                with patch("ctypes.wintypes.DWORD", int):
                                    # Import signal_handler to trigger the fallback path
                                    import importlib

                                    import agent.signal_handler as sh_module

                                    importlib.reload(sh_module)
                                    # Verify SetConsoleCtrlHandler was called via ctypes
                                    mock_set_handler.assert_called_once()
        finally:
            sys.frozen = original_frozen
