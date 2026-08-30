"""tests/mcp_servers/git/test_git_models.py

Characterization tests for scripts/mcp_servers/git/git_models.py.

These tests lock the exact validation behavior of ``GitConfig.from_dict``
(the three type-guard branches were previously uncovered by any test) so a
later refactor of this module can be verified not to change behavior.
"""

from __future__ import annotations

import pytest
from mcp_servers.git.errors import GitServiceError
from mcp_servers.git.git_models import GitConfig


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


class TestGitServiceError:
    def test_is_a_runtime_error(self) -> None:
        err = GitServiceError("boom")
        assert isinstance(err, RuntimeError)
        assert str(err) == "boom"
