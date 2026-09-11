"""
Shared pytest fixtures for the llmagent test suite.
Adds scripts/ to sys.path so all project modules are importable without installation.
"""

import os
import sys
from collections.abc import Generator
from pathlib import Path

import pytest

# scripts/ and tools/ are not installed packages; add them to sys.path for all tests
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))

# git/cicd/web_search MCP servers load their standalone *_mcp_server.toml at
# module import time, and those files reference ${ENV:...}-style auth tokens
# (mcpauth, 2026-09-04). resolve_env_ref() only requires the variable to be
# *set*, not non-empty -- default to "" (not a real token) so import doesn't
# fail during test collection, while preserving these servers' pre-existing
# empty-token accept-all behavior that many tests rely on.
os.environ.setdefault("MCP_GIT_AUTH_TOKEN", "")
os.environ.setdefault("MCP_CICD_AUTH_TOKEN", "")
os.environ.setdefault("MCP_WEB_SEARCH_BROWSER_AUTH_TOKEN", "")


@pytest.fixture(autouse=True)
def _reset_tool_registry() -> Generator[None]:
    """Reset the global ToolRegistry singleton before and after every test.

    Several tests across the suite register throwaway tool names (e.g.
    "tool_a") into shared.tool_registry's process-wide singleton via
    get_registry(). Without a session-wide reset, a registration left behind
    by one test file leaks into another depending on test collection order,
    causing ValueError: "Tool already registered" or stale-drift false
    positives in unrelated tests.
    """
    from shared.tool_registry import _reset_registry_for_testing

    _reset_registry_for_testing()
    yield
    _reset_registry_for_testing()


@pytest.fixture(autouse=True)
def _reset_web_search_health_and_metrics() -> Generator[None]:
    """Reset web-search-mcp's in-process health/metrics singletons per test.

    mcp_servers.web_search.health and mcp_servers.web_search.metrics track
    state (e.g. consecutive_failures) in module-level singletons by design
    (single-worker process, no persistence). Without a session-wide reset,
    a failure recorded by one test file leaks into unrelated tests depending
    on test collection order, e.g. flipping web_search's /health to 503 in
    an unrelated test.

    browser_fetch's health/metrics tracking (merged into web-search-mcp from
    the retired standalone browser-mcp server) is a second, independent pair
    of module-level singletons (_browser_health/_browser_metrics) — reset
    those too for the same reason.
    """
    from mcp_servers.web_search import health, metrics

    health.reset()
    metrics.reset()
    health.reset_browser()
    metrics.reset_browser()
    yield
    health.reset()
    metrics.reset()
    health.reset_browser()
    metrics.reset_browser()
