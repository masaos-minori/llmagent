import logging
import os
import subprocess
from unittest.mock import Mock, patch

import pytest
from agent.http_lifecycle import HttpServerLifecycleManager
from agent.http_lifecycle_errors import TerminationOutcome

_TERMINATOR_LOGGER = "agent.http_lifecycle_process_terminator"


@pytest.fixture
def mgr() -> HttpServerLifecycleManager:
    return HttpServerLifecycleManager()


class _LineCapture(logging.Handler):
    """Collect the terminator's emitted lines together with their severity."""

    def __init__(self) -> None:
        super().__init__()
        self.records: list[tuple[int, str]] = []

    def emit(self, record: logging.LogRecord) -> None:
        if record.levelno >= logging.WARNING:
            self.records.append((record.levelno, record.getMessage()))

    def warnings(self) -> list[str]:
        """Return the lines emitted at WARNING, the non-fatal severity."""
        return [msg for level, msg in self.records if level == logging.WARNING]

    def at_error_or_worse(self) -> list[str]:
        """Return the lines that would read as a failure to an operator."""
        return [msg for level, msg in self.records if level >= logging.ERROR]


def _attach(logger_name: str = _TERMINATOR_LOGGER) -> _LineCapture:
    """Attach a capture handler to *logger_name* and return it for later removal."""
    capture = _LineCapture()
    logger = logging.getLogger(logger_name)
    logger.addHandler(capture)
    logger.setLevel(logging.WARNING)
    return capture


def _assert_unconfirmed_termination_line(
    capture: _LineCapture, server_key: str
) -> None:
    """Assert the one operator-facing line a terminated-but-unconfirmed server produces.

    REQ-010, REQ-012, REQ-013: the line names the server key, states that the exit was
    not observed, stays a warning rather than an error or a fatal line, and carries no
    absolute path. Exactly one line: the shutdown report already counts the server, so
    the console must not duplicate it.
    """
    matched = [w for w in capture.warnings() if "proc.terminate() fallback" in w]
    assert len(matched) == 1, "expected exactly one unconfirmed-termination warning"
    line = matched[0]
    assert server_key in line
    assert "exit not observed" in line
    assert "/" not in line
    assert not capture.at_error_or_worse(), "the cleanup line must stay non-fatal"


@pytest.mark.asyncio
async def test_terminate_warning_when_no_pgid():
    """Unit test: Verify warning is logged when pgid is None and terminate succeeds."""
    mgr = HttpServerLifecycleManager()
    proc_mock = Mock(spec=subprocess.Popen)
    proc_mock.poll.return_value = None  # Not exited yet

    capture = _attach()

    try:
        outcome = await mgr._process_terminator.terminate_with_timeout(
            proc_mock, "test-server", timeout=1.0
        )

        assert outcome is TerminationOutcome.EXIT_UNCONFIRMED
        _assert_unconfirmed_termination_line(capture, "test-server")
    finally:
        logging.getLogger(_TERMINATOR_LOGGER).removeHandler(capture)


@pytest.mark.asyncio
async def test_terminate_warning_when_killpg_fails():
    """Unit test: Verify the SIGTERM-group failure warning and the proc.terminate() fallback."""
    mgr = HttpServerLifecycleManager()
    proc_mock = Mock(spec=subprocess.Popen)
    proc_mock.poll.return_value = None
    proc_mock.pid = 4242

    capture = _attach()

    try:
        with (
            patch.object(os, "getpgid", return_value=1234),
            patch.object(os, "killpg", side_effect=OSError("No such process")),
        ):
            outcome = await mgr._process_terminator.terminate_with_timeout(
                proc_mock, "test-server", timeout=1.0
            )

        assert outcome is TerminationOutcome.EXIT_UNCONFIRMED
        matched = [w for w in capture.warnings() if "os.killpg(SIGTERM) failed" in w]
        assert len(matched) == 1, "expected exactly one killpg-failure warning"
        assert "pid=4242" in matched[0]
        assert "pgid=1234" in matched[0]
        assert not capture.at_error_or_worse(), "the cleanup line must stay non-fatal"
    finally:
        logging.getLogger(_TERMINATOR_LOGGER).removeHandler(capture)


@pytest.mark.asyncio
async def test_terminate_warning_integration_simulation():
    """Integration simulation: Verify warning when using terminate instead of killpg."""
    mgr = HttpServerLifecycleManager()
    proc_mock = Mock(spec=subprocess.Popen)
    proc_mock.poll.return_value = None

    capture = _attach()

    try:
        # Simulate scenario where pgid is unavailable, leading to proc.terminate()
        with (
            patch.object(os, "killpg", side_effect=OSError("Permission denied")),
        ):
            outcome = await mgr._process_terminator.terminate_with_timeout(
                proc_mock, "test-server", timeout=1.0
            )

        assert outcome is TerminationOutcome.EXIT_UNCONFIRMED
        _assert_unconfirmed_termination_line(capture, "test-server")
    finally:
        logging.getLogger(_TERMINATOR_LOGGER).removeHandler(capture)
