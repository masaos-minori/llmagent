"""
Shared pytest fixtures for the llmagent test suite.
Adds scripts/ to sys.path so all project modules are importable without installation.
"""

import datetime
import sys
from collections.abc import Generator
from pathlib import Path

import pytest

# scripts/ and tools/ are not installed packages; add them to sys.path for all tests
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))
# tests/ helpers are importable as plain modules
sys.path.insert(0, str(Path(__file__).parent))

# True when the sqlite-vec .so is present; used to skipif vec0 tests.
_VEC_AVAILABLE: bool = Path("/opt/llm/sqlite-vec/vec0.so").exists()


@pytest.fixture(autouse=True)
def _reset_tool_registry() -> Generator[None]:
    """Reset the global ToolRegistry singleton before and after every test.

    Several tests across the suite register throwaway tool names (e.g.
    "tool_a") into shared.tool_registry's process-wide singleton via
    get_registry(). Without a session-wide reset, a registration left behind
    by one test file leaks into another depending on pytest-randomly's test
    order, causing ValueError: "Tool already registered" or stale-drift
    false positives in unrelated tests.
    """
    from shared.tool_registry import _reset_registry_for_testing

    _reset_registry_for_testing()
    yield
    _reset_registry_for_testing()


# ── Test case logging: track which test was running when SSH disconnects ──

_LOG_PATH = Path("/tmp/test_lifecycle_crash.log")


def _ts() -> str:
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]


def pytest_runtest_setup(item):
    """Log before each test starts."""
    with open(_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"[{_ts()}] SETUP START {item.nodeid}\n")


def pytest_runtest_teardown(item, nextitem):
    """Log after each test finishes."""
    with open(_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"[{_ts()}] TEARDOWN OK   {item.nodeid}\n")


def pytest_sessionfinish(session, exitstatus):
    """Log session end status."""
    with open(_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(
            f"[{_ts()}] SESSION END   exit={exitstatus} ({session.testscollected} tests)\n"
        )
