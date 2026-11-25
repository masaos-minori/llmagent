"""tests/mcp_servers/github/test_service_init.py

Tests for scripts/mcp_servers/github/github_service_init.py (mcpai006 REQ-002).

The module no longer builds a client at import time: `build_client` constructs
the client from the token and the configured timeouts with library retry
disabled, and `build_service` wires it into `GitHubService`. These tests pin the
no-retry construction, the `(connect, read)` timeout tuple passed to `requests`
(accepted at runtime although the annotation says `int`), the warning for an
empty token, the environment read at import, and the factory wiring.
"""

from __future__ import annotations

import importlib
import logging

import mcp_servers.github.github_service_init as service_init
from github import Auth, Github


class TestBuildClient:
    def test_retry_is_disabled(self) -> None:
        gh = service_init.build_client("test-token-value", 5.0, 30.0)
        assert isinstance(gh, Github)
        assert gh.requester.kwargs["retry"] is None

    def test_configured_timeouts_are_kept_as_a_tuple(self) -> None:
        gh = service_init.build_client("test-token-value", 2.5, 12.0)
        assert gh.requester.kwargs["timeout"] == (2.5, 12.0)

    def test_token_builds_authenticated_client_without_warning(
        self, monkeypatch, caplog
    ) -> None:
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        with caplog.at_level(
            logging.WARNING, logger="mcp_servers.github.github_service_init"
        ):
            gh = service_init.build_client("test-token-value", 5.0, 30.0)
        assert isinstance(gh.requester.auth, Auth.Token)
        assert gh.requester.kwargs["retry"] is None
        assert gh.requester.kwargs["timeout"] == (5.0, 30.0)
        assert not any(
            "GITHUB_TOKEN is not set" in record.message for record in caplog.records
        )

    def test_no_token_builds_unauthenticated_client_and_warns(
        self, monkeypatch, caplog
    ) -> None:
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        with caplog.at_level(
            logging.WARNING, logger="mcp_servers.github.github_service_init"
        ):
            gh = service_init.build_client("", 5.0, 30.0)
        assert gh.requester.auth is None
        assert gh.requester.kwargs["retry"] is None
        assert gh.requester.kwargs["timeout"] == (5.0, 30.0)
        assert any(
            "GITHUB_TOKEN is not set" in record.message for record in caplog.records
        )

    def test_github_token_is_read_from_the_environment_at_import(
        self, monkeypatch
    ) -> None:
        monkeypatch.setenv("GITHUB_TOKEN", "env-token-at-import")
        importlib.reload(service_init)
        try:
            assert service_init._GITHUB_TOKEN == "env-token-at-import"
        finally:
            importlib.reload(service_init)

    def test_no_module_level_client_is_constructed_at_import(self) -> None:
        assert not hasattr(service_init, "_gh")


class TestBuildService:
    def test_returns_github_service_wired_to_a_built_client_and_cfg(self) -> None:
        from mcp_servers.github.github_models_config import GitHubConfig
        from mcp_servers.github.github_service_dispatch import GitHubService

        cfg = GitHubConfig()
        result = service_init.build_service(cfg)

        assert isinstance(result, GitHubService)
        assert isinstance(result._gh, Github)
        assert result._gh is not service_init  # built, not a module singleton
        assert result._gh.requester.kwargs["retry"] is None
        assert result._gh.requester.kwargs["timeout"] == (5.0, 30.0)
        assert result._cfg is cfg
