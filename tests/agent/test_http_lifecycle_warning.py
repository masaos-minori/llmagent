import logging
import os
import subprocess
from unittest.mock import AsyncMock, Mock, patch

import pytest
from agent.http_lifecycle import HttpServerLifecycleManager


@pytest.fixture
def mgr() -> HttpServerLifecycleManager:
    return HttpServerLifecycleManager()


@pytest.mark.asyncio
async def test_terminate_warning_when_no_pgid():
    """Unit test: Verify warning is logged when pgid is None and terminate succeeds."""
    mgr = HttpServerLifecycleManager()
    proc_mock = Mock(spec=subprocess.Popen)
    proc_mock.poll.return_value = None  # Not exited yet

    captured_warnings = []

    class WarningCapture(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            if record.levelno == logging.WARNING:
                captured_warnings.append(record.getMessage())

    logger = logging.getLogger("agent.http_lifecycle")
    handler = WarningCapture()
    logger.addHandler(handler)
    logger.setLevel(logging.WARNING)

    try:
        with (
            patch.object(mgr, "_wait_exited", new=AsyncMock(return_value=True)),
            patch.object(mgr, "_http_pgids", {}),  # Ensure pgid is None
        ):
            await mgr._terminate_with_timeout(proc_mock, "test-server", timeout=1.0)

        assert any(
            "terminated, but children may remain" in w for w in captured_warnings
        )
    finally:
        logger.removeHandler(handler)


@pytest.mark.asyncio
async def test_terminate_warning_when_killpg_fails():
    """Unit test: Verify warning is logged when os.killpg fails and terminate succeeds."""
    mgr = HttpServerLifecycleManager()
    proc_mock = Mock(spec=subprocess.Popen)
    proc_mock.poll.return_value = None

    captured_warnings = []

    class WarningCapture(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            if record.levelno == logging.WARNING:
                captured_warnings.append(record.getMessage())

    logger = logging.getLogger("agent.http_lifecycle")
    handler = WarningCapture()
    logger.addHandler(handler)
    logger.setLevel(logging.WARNING)

    try:
        with (
            patch.object(mgr, "_wait_exited", new=AsyncMock(return_value=True)),
            patch.object(mgr, "_http_pgids", {"test-server": 1234}),
            patch.object(os, "killpg", side_effect=OSError("No such process")),
        ):
            await mgr._terminate_with_timeout(proc_mock, "test-server", timeout=1.0)

        assert any(
            "terminated, but children may remain" in w for w in captured_warnings
        )
    finally:
        logger.removeHandler(handler)


@pytest.mark.asyncio
async def test_terminate_warning_integration_simulation():
    """Integration simulation: Verify warning when using terminate instead of killpg."""
    mgr = HttpServerLifecycleManager()
    proc_mock = Mock(spec=subprocess.Popen)
    proc_mock.poll.return_value = None

    captured_warnings = []

    class WarningCapture(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            if record.levelno == logging.WARNING:
                captured_warnings.append(record.getMessage())

    logger = logging.getLogger("agent.http_lifecycle")
    handler = WarningCapture()
    logger.addHandler(handler)
    logger.setLevel(logging.WARNING)

    try:
        # Simulate scenario where pgid exists but killpg fails, leading to proc.terminate()
        with (
            patch.object(mgr, "_wait_exited", new=AsyncMock(return_value=True)),
            patch.object(mgr, "_http_pgids", {"test-server": 1234}),
            patch.object(os, "killpg", side_effect=OSError("Permission denied")),
        ):
            await mgr._terminate_with_timeout(proc_mock, "test-server", timeout=1.0)

        assert any(
            "terminated, but children may remain" in w for w in captured_warnings
        )
    finally:
        logger.removeHandler(handler)
