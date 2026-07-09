"""Static and unit tests for the security audit config isolation boundary."""

from __future__ import annotations

import pathlib
from unittest.mock import MagicMock, patch

import pytest

_FORBIDDEN_SECURITY_IMPORTS = [
    "from mcp.shell.models",
    "from mcp.git.models",
    "from mcp.github.models_config",
    "from mcp.cicd.models",
]
_AUDIT_MODULE = "security_audit_config.py"
_AGENT_DIR = pathlib.Path("scripts/agent")


def test_only_audit_module_imports_security_server_config() -> None:
    violations: list[str] = []
    for py_file in _AGENT_DIR.rglob("*.py"):
        if py_file.name == _AUDIT_MODULE:
            continue
        content = py_file.read_text()
        for pattern in _FORBIDDEN_SECURITY_IMPORTS:
            if pattern in content:
                violations.append(f"{py_file}: {pattern}")
    assert not violations, (
        "Direct security server config imports outside audit module:\n"
        + "\n".join(violations)
    )


# --- load_shell_audit_config ---


def test_load_shell_audit_config_returns_none_on_import_error() -> None:
    with patch.dict("sys.modules", {"mcp.shell.models": None}):
        from agent.security_audit_config import load_shell_audit_config

        result = load_shell_audit_config()
    assert result is None


def test_load_shell_audit_config_raises_on_load_failure() -> None:
    mock_cls = MagicMock()
    mock_cls.load.side_effect = ValueError("bad config")
    with patch("mcp.shell.models.ShellConfig", mock_cls):
        from agent.security_audit_config import load_shell_audit_config

        with pytest.raises(RuntimeError, match="shell config"):
            load_shell_audit_config()


def test_load_shell_audit_config_success() -> None:
    from agent.security_audit_config import ShellAuditConfig

    mock_cfg = MagicMock()
    mock_cfg.shell_sandbox_backend = "docker"
    mock_cfg.command_allowlist = ["git", "ls"]
    mock_cls = MagicMock()
    mock_cls.load.return_value = mock_cfg
    with patch("mcp.shell.models.ShellConfig", mock_cls):
        from agent.security_audit_config import load_shell_audit_config

        result = load_shell_audit_config()
    assert result == ShellAuditConfig(
        sandbox_backend="docker", command_allowlist=["git", "ls"]
    )


# --- load_git_audit_config ---


def test_load_git_audit_config_returns_none_on_import_error() -> None:
    with patch.dict("sys.modules", {"mcp.git.models": None}):
        from agent.security_audit_config import load_git_audit_config

        result = load_git_audit_config()
    assert result is None


def test_load_git_audit_config_raises_on_load_failure() -> None:
    mock_cls = MagicMock()
    mock_cls.load.side_effect = FileNotFoundError("missing")
    with patch("mcp.git.models.GitConfig", mock_cls):
        from agent.security_audit_config import load_git_audit_config

        with pytest.raises(RuntimeError, match="git config"):
            load_git_audit_config()


def test_load_git_audit_config_success() -> None:
    from agent.security_audit_config import GitAuditConfig

    mock_cfg = MagicMock()
    mock_cfg.allowed_repo_paths = ["/home/user/repo"]
    mock_cls = MagicMock()
    mock_cls.load.return_value = mock_cfg
    with patch("mcp.git.models.GitConfig", mock_cls):
        from agent.security_audit_config import load_git_audit_config

        result = load_git_audit_config()
    assert result == GitAuditConfig(allowed_repo_paths=["/home/user/repo"])


# --- load_github_audit_config ---


def test_load_github_audit_config_returns_none_on_import_error() -> None:
    with patch.dict("sys.modules", {"mcp.github.models_config": None}):
        from agent.security_audit_config import load_github_audit_config

        result = load_github_audit_config()
    assert result is None


def test_load_github_audit_config_raises_on_load_failure() -> None:
    mock_cls = MagicMock()
    mock_cls.load.side_effect = OSError("io error")
    with patch("mcp.github.models_config.GitHubConfig", mock_cls):
        from agent.security_audit_config import load_github_audit_config

        with pytest.raises(RuntimeError, match="GitHub config"):
            load_github_audit_config()


def test_load_github_audit_config_success() -> None:
    from agent.security_audit_config import GitHubAuditConfig

    mock_cfg = MagicMock()
    mock_cfg.allowed_repos = ["owner/repo"]
    mock_cfg.allowed_repos_mode = "fail_closed"
    mock_cfg.allow_force_push = True
    mock_cfg.require_pr_review = False
    mock_cls = MagicMock()
    mock_cls.load.return_value = mock_cfg
    with patch("mcp.github.models_config.GitHubConfig", mock_cls):
        from agent.security_audit_config import load_github_audit_config

        result = load_github_audit_config()
    assert result == GitHubAuditConfig(
        allowed_repos=["owner/repo"],
        allowed_repos_mode="fail_closed",
        allow_force_push=True,
        require_pr_review=False,
    )


# --- load_cicd_audit_config ---


def test_load_cicd_audit_config_returns_none_on_import_error() -> None:
    with patch.dict("sys.modules", {"mcp.cicd.models": None}):
        from agent.security_audit_config import load_cicd_audit_config

        result = load_cicd_audit_config()
    assert result is None


def test_load_cicd_audit_config_raises_on_load_failure() -> None:
    mock_cls = MagicMock()
    mock_cls.load.side_effect = ValueError("schema error")
    with patch("mcp.cicd.models.CicdConfig", mock_cls):
        from agent.security_audit_config import load_cicd_audit_config

        with pytest.raises(RuntimeError, match="CI/CD config"):
            load_cicd_audit_config()


def test_load_cicd_audit_config_success() -> None:
    from agent.security_audit_config import CicdAuditConfig

    mock_cfg = MagicMock()
    mock_cfg.workflow_allowlist = ["deploy", "test"]
    mock_cls = MagicMock()
    mock_cls.load.return_value = mock_cfg
    with patch("mcp.cicd.models.CicdConfig", mock_cls):
        from agent.security_audit_config import load_cicd_audit_config

        result = load_cicd_audit_config()
    assert result == CicdAuditConfig(workflow_allowlist=["deploy", "test"])
