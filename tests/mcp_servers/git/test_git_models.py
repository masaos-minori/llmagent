"""tests/mcp_servers/git/test_git_models.py

Characterization tests for scripts/mcp_servers/git/git_models.py.

These tests lock the exact validation behavior of ``GitConfig.from_dict``
(the three type-guard branches were previously uncovered by any test) so a
later refactor of this module can be verified not to change behavior.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from mcp_servers.git.errors import GitServiceError
from mcp_servers.git.git_models import GitConfig, GitPullRequest, GitPushRequest
from pydantic import ValidationError


class TestAllowedRepoPathsHomeExpansion:
    def test_leading_tilde_is_expanded_to_the_home_directory(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        monkeypatch.setenv("HOME", str(tmp_path))
        cfg = GitConfig.from_dict({"allowed_repo_paths": ["~/llmagent", "/opt/llm"]})
        assert cfg.allowed_repo_paths == [str(tmp_path / "llmagent"), "/opt/llm"]

    def test_entries_without_tilde_are_unchanged(self) -> None:
        cfg = GitConfig.from_dict({"allowed_repo_paths": ["/opt/repos", "rel/path"]})
        assert cfg.allowed_repo_paths == ["/opt/repos", "rel/path"]

    def test_checked_in_configuration_resolves_under_the_current_home(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        import tomllib

        monkeypatch.setenv("HOME", str(tmp_path))
        raw = tomllib.loads(
            (
                Path(__file__).resolve().parents[3] / "config" / "git_mcp_server.toml"
            ).read_text(encoding="utf-8")
        )
        cfg = GitConfig.from_dict(raw)
        assert cfg.allowed_repo_paths == [str(tmp_path / "llmagent")]


class TestGitConfigFromDict:
    def test_valid_dict_populates_all_fields(self) -> None:
        cfg = GitConfig.from_dict(
            {
                "allowed_repo_paths": ["/opt/repos"],
                "read_only": False,
                "auth_token": "secret",
                "max_log_entries": 100,
                "audit_log_path": "/var/log/git.log",
            }
        )
        assert cfg.allowed_repo_paths == ["/opt/repos"]
        assert cfg.read_only is False
        assert cfg.auth_token == "secret"
        assert cfg.max_log_entries == 100
        assert cfg.audit_log_path == "/var/log/git.log"

    def test_missing_optional_fields_use_defaults(self) -> None:
        cfg = GitConfig.from_dict(
            {"allowed_repo_paths": [], "read_only": True, "max_log_entries": 50}
        )
        assert cfg.auth_token == ""
        assert cfg.audit_log_path == ""

    def test_allowed_repo_paths_not_a_list_raises(self) -> None:
        with pytest.raises(ValueError, match="'allowed_repo_paths' must be a list"):
            GitConfig.from_dict(
                {
                    "allowed_repo_paths": "not-a-list",
                    "read_only": True,
                    "max_log_entries": 50,
                }
            )

    def test_allowed_repo_paths_missing_uses_default(self) -> None:
        cfg = GitConfig.from_dict({"read_only": True, "max_log_entries": 50})
        assert cfg.allowed_repo_paths == []

    def test_read_only_not_a_bool_raises(self) -> None:
        with pytest.raises(ValueError, match="'read_only' must be a boolean"):
            GitConfig.from_dict(
                {"allowed_repo_paths": [], "read_only": "true", "max_log_entries": 50}
            )

    def test_max_log_entries_not_an_int_raises(self) -> None:
        with pytest.raises(ValueError, match="'max_log_entries' must be an integer"):
            GitConfig.from_dict(
                {"allowed_repo_paths": [], "read_only": True, "max_log_entries": "50"}
            )

    def test_allowed_remote_urls_parsed_from_dict(self) -> None:
        cfg = GitConfig.from_dict(
            {
                "allowed_repo_paths": [],
                "read_only": True,
                "max_log_entries": 50,
                "allowed_remote_urls": ["https://example.com/repo.git"],
            }
        )
        assert cfg.allowed_remote_urls == ["https://example.com/repo.git"]

    def test_allowed_remote_urls_missing_uses_default(self) -> None:
        cfg = GitConfig.from_dict(
            {"allowed_repo_paths": [], "read_only": True, "max_log_entries": 50}
        )
        assert cfg.allowed_remote_urls == []


class TestGitConfigDefaults:
    def test_default_construction(self) -> None:
        cfg = GitConfig()
        assert cfg.allowed_repo_paths == []
        assert cfg.read_only is True
        assert cfg.auth_token == ""
        assert cfg.max_log_entries == 50
        assert cfg.audit_log_path == ""


class TestGitConfigLoad:
    def test_load_reads_protected_branches_from_shipped_config(self) -> None:
        cfg = GitConfig.load()
        assert cfg.protected_branches == ["main", "master", "release"]

    def test_load_reads_allowed_remote_urls_from_shipped_config(self) -> None:
        cfg = GitConfig.load()
        assert cfg.allowed_remote_urls == []


class TestGitServiceError:
    def test_is_a_runtime_error(self) -> None:
        err = GitServiceError("boom")
        assert isinstance(err, RuntimeError)
        assert str(err) == "boom"


class TestWriteRequestBranchRequired:
    """REQ-004: git_pull/git_push require a non-empty branch (mirrors the JSON
    schema in git_tools.py, which lists ``branch`` in ``required`` with no
    default)."""

    def test_git_pull_requires_branch(self) -> None:
        with pytest.raises(ValidationError):
            GitPullRequest(repo_path="/tmp/allowed/repo", remote="origin")

    def test_git_push_requires_branch(self) -> None:
        with pytest.raises(ValidationError):
            GitPushRequest(repo_path="/tmp/allowed/repo", remote="origin")

    def test_git_pull_accepts_explicit_branch(self) -> None:
        req = GitPullRequest(
            repo_path="/tmp/allowed/repo", remote="origin", branch="develop"
        )
        assert req.branch == "develop"

    def test_git_push_accepts_explicit_branch(self) -> None:
        req = GitPushRequest(
            repo_path="/tmp/allowed/repo", remote="origin", branch="develop"
        )
        assert req.branch == "develop"
