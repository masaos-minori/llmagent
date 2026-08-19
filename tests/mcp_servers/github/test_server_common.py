"""tests/mcp_servers/github/test_server_common.py

Characterization tests for scripts/mcp_servers/github/github_server_common.py.

_get_service and _info are consumed by all four domain server modules
(server_file.py, server_issues.py, server_pull_requests.py, server_repository.py)
via `from mcp_servers.github.github_server_common import _get_service, _info`, but were
not exercised by any existing test (verified via `rg _get_service|_info tests/`
during the 04_refactor.md sweep of this subsystem) because those tests either
call `GitHubService` directly or override the FastAPI dependency. These tests
lock the current, verbatim behavior of both helpers before any refactor.
"""

from __future__ import annotations

import logging

import mcp_servers.github.github_server as github_server
from mcp_servers.github.github_server_common import _get_service, _info
from mcp_servers.github.github_service_dispatch import GitHubService


class TestGetService:
    """Lock the singleton-dependency behavior of _get_service."""

    def test_returns_the_module_singleton_instance(self) -> None:
        """_get_service returns the exact _service object from github_server."""
        result = _get_service()

        assert result is github_server._service

    def test_returned_object_is_a_github_service(self) -> None:
        """The singleton is a GitHubService instance."""
        result = _get_service()

        assert isinstance(result, GitHubService)


class TestInfo:
    """Lock the structured kv-log formatting behavior of _info."""

    def test_logs_message_with_kv_formatted_kwargs(self, caplog) -> None:
        """_info logs via github_server.logger at INFO with fmt_kvlog formatting."""
        with caplog.at_level(logging.INFO, logger=github_server.logger.name):
            _info("push_file", repo="org/repo", path="a.txt")

        assert len(caplog.records) == 1
        assert caplog.records[0].message == "op=push_file repo=org/repo path=a.txt"
        assert caplog.records[0].name == github_server.logger.name

    def test_logs_message_with_no_kwargs(self, caplog) -> None:
        """_info with no kwargs logs just the op= field."""
        with caplog.at_level(logging.INFO, logger=github_server.logger.name):
            _info("list_issues")

        assert caplog.records[0].message == "op=list_issues"

    def test_none_valued_kwargs_are_omitted(self, caplog) -> None:
        """None-valued kwargs are dropped from the formatted log message."""
        with caplog.at_level(logging.INFO, logger=github_server.logger.name):
            _info("get_file", repo="org/repo", ref=None)

        assert caplog.records[0].message == "op=get_file repo=org/repo"
