"""tests/mcp_servers/github/test_service_init.py

Characterization tests for scripts/mcp_servers/github/github_service_init.py.

The module builds its `_gh` / `_GITHUB_TOKEN` singletons at import time from the
`GITHUB_TOKEN` environment variable, so the "token is set" branch (line 24: an
authenticated `Github(auth=Auth.Token(...))` client, and the warning log at
line 26-29 being skipped) is never exercised by the existing test suite —
every other test imports this module with `GITHUB_TOKEN` unset (verified via
`rg GITHUB_TOKEN tests/` during the 04_refactor.md sweep of this subsystem;
baseline branch coverage was 82%, missing line 24 and branch 26->32). These
tests reload the module under both environment states to lock its current,
verbatim import-time behavior before any refactor.
"""

from __future__ import annotations

import importlib
import logging

import mcp_servers.github.github_service_init as service_init
from github import Auth, Github


class TestModuleLevelClientInitialization:
    """Lock the singleton client construction behavior at import time."""

    def test_no_token_builds_unauthenticated_client_and_warns(
        self, monkeypatch, caplog
    ) -> None:
        """With GITHUB_TOKEN unset, _gh is an unauthenticated Github() and a warning is logged."""
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)

        with caplog.at_level(
            logging.WARNING, logger="mcp_servers.github.github_service_init"
        ):
            reloaded = importlib.reload(service_init)

        try:
            assert reloaded._GITHUB_TOKEN == ""
            assert isinstance(reloaded._gh, Github)
            assert reloaded._gh.requester.auth is None
            assert any(
                "GITHUB_TOKEN is not set" in record.message for record in caplog.records
            )
        finally:
            monkeypatch.delenv("GITHUB_TOKEN", raising=False)
            importlib.reload(service_init)

    def test_token_set_builds_authenticated_client_without_warning(
        self, monkeypatch, caplog
    ) -> None:
        """With GITHUB_TOKEN set, _gh is authenticated via Auth.Token and no warning is logged."""
        monkeypatch.setenv("GITHUB_TOKEN", "test-token-value")

        with caplog.at_level(
            logging.WARNING, logger="mcp_servers.github.github_service_init"
        ):
            reloaded = importlib.reload(service_init)

        try:
            assert reloaded._GITHUB_TOKEN == "test-token-value"
            assert isinstance(reloaded._gh, Github)
            assert isinstance(reloaded._gh.requester.auth, Auth.Token)
            assert not any(
                "GITHUB_TOKEN is not set" in record.message for record in caplog.records
            )
        finally:
            monkeypatch.delenv("GITHUB_TOKEN", raising=False)
            importlib.reload(service_init)


class TestBuildService:
    """Lock the build_service factory's construction call."""

    def test_returns_github_service_wired_to_module_client_and_cfg(self) -> None:
        """build_service passes the module-level _gh singleton and cfg through verbatim."""
        from mcp_servers.github.github_models_config import GitHubConfig
        from mcp_servers.github.github_service_dispatch import GitHubService

        cfg = GitHubConfig()
        result = service_init.build_service(cfg)

        assert isinstance(result, GitHubService)
        assert result._gh is service_init._gh
        assert result._cfg is cfg
