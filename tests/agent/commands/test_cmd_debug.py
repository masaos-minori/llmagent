"""tests/test_cmd_debug.py

Tests for _DebugMixin._cmd_debug() CLI behavior after /debug audit removal.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch


def _make_mixin():
    """Return a _DebugMixin instance with minimal stubs."""
    from agent.commands.cmd_debug import _DebugMixin

    ctx = SimpleNamespace(
        conv=SimpleNamespace(debug_mode=False),
    )
    messages: list[str] = []

    def write(msg: str) -> None:
        messages.append(msg)

    out = SimpleNamespace(write=write)

    mixin = _DebugMixin.__new__(_DebugMixin)
    mixin._ctx = ctx
    mixin._out = out
    return mixin, messages


class TestDebugUnknownSubcommand:
    def test_debug_audit_rejected(self) -> None:
        """Unknown subcommand /debug audit is rejected."""
        mixin, msgs = _make_mixin()
        mixin._cmd_debug("audit")
        assert any("Unknown subcommand" in m for m in msgs), msgs

    def test_debug_foo_rejected(self) -> None:
        """Unknown subcommand /debug foo is rejected."""
        mixin, msgs = _make_mixin()
        mixin._cmd_debug("foo")
        assert any("Unknown subcommand" in m for m in msgs), msgs

    def test_debug_audit_does_not_toggle(self) -> None:
        """/debug audit does not toggle debug mode."""
        mixin, msgs = _make_mixin()
        mixin._cmd_debug("audit")
        assert mixin._ctx.conv.debug_mode is False, "debug_mode should remain False"

    def test_debug_audit_does_not_read_log(self) -> None:
        """/debug audit does not attempt to read the audit log."""
        mixin, msgs = _make_mixin()
        with patch("pathlib.Path.exists") as mock_exists:
            mixin._cmd_debug("audit")
        assert not mock_exists.called, "should not read audit log"

    def test_debug_usage_message_shown(self) -> None:
        """Unknown subcommand shows usage message."""
        mixin, msgs = _make_mixin()
        mixin._cmd_debug("invalid")
        assert any("Usage:" in m for m in msgs), msgs


class TestDebugValidSubcommands:
    def test_debug_toggles_mode(self) -> None:
        """/debug without args toggles debug mode."""
        mixin, msgs = _make_mixin()
        mixin._cmd_debug("")
        assert mixin._ctx.conv.debug_mode is True, "debug_mode should be toggled ON"

    def test_debug_toggle_off(self) -> None:
        """Second /debug toggle turns debug mode OFF."""
        mixin, msgs = _make_mixin()
        mixin._cmd_debug("")
        mixin._cmd_debug("")
        assert mixin._ctx.conv.debug_mode is False, "debug_mode should be toggled OFF"

    def test_debug_verbose_sets_debug_level(self) -> None:
        """/debug verbose sets DEBUG log level."""
        mixin, msgs = _make_mixin()
        with (
            patch("logging.getLogger") as mock_get_logger,
            patch("logging.DEBUG", 10),
        ):
            mock_logger = SimpleNamespace(setLevel=lambda level: None)
            mock_get_logger.return_value = mock_logger
            mixin._cmd_debug("verbose")
        assert any("DEBUG" in m for m in msgs), msgs

    def test_debug_normal_sets_info_level(self) -> None:
        """/debug normal sets INFO log level."""
        mixin, msgs = _make_mixin()
        with (
            patch("logging.getLogger") as mock_get_logger,
            patch("logging.INFO", 20),
        ):
            mock_logger = SimpleNamespace(setLevel=lambda level: None)
            mock_get_logger.return_value = mock_logger
            mixin._cmd_debug("normal")
        assert any("INFO" in m for m in msgs), msgs
