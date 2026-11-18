"""tests/mcp_servers/shell/test_shell_command_arg_contract.py

Unit tests for the per-command argument-shape contract enforced by
``ShellService._check_command`` (REQ-001, REQ-002, REQ-004).

Code-execution (``python -c``) and mutating-git (``git push``, ``git branch -D``)
forms are rejected; read-only git and static-analysis shapes are accepted;
unrecognized shapes fail closed. No subprocess is launched: rejections fire on
the exception raised by ``_check_command`` before ``run_command`` builds the
subprocess argv.
"""

from __future__ import annotations

import dataclasses
from collections.abc import Iterable, Iterator
from pathlib import Path
from unittest.mock import patch

import pytest
from mcp_servers.shell.shell_models import (
    ShellAuthorizationError,
    ShellRunRequest,
)
from mcp_servers.shell.shell_service import ShellService

from tests.mcp_servers.shell.test_shell_mcp_service import _make_policy


@pytest.fixture(autouse=True)
def _firejail_present() -> Iterator[None]:
    """Make the firejail binary present so ShellService construction succeeds."""
    with patch(
        "mcp_servers.shell.shell_service_static_helpers.shutil.which",
        return_value="/usr/bin/firejail",
    ):
        yield


def _contract_service(tmp_path: Path, commands: Iterable[str]) -> ShellService:
    """Build a ``ShellService`` whose allowlist is exactly ``commands``.

    Reuses ``_make_policy`` from the sibling module and swaps only
    ``allowed_commands`` via ``dataclasses.replace`` (``ShellPolicy`` is frozen).
    """
    policy = dataclasses.replace(
        _make_policy(tmp_path), allowed_commands=frozenset(commands)
    )
    return ShellService(policy)


def _req(argv: list[str]) -> ShellRunRequest:
    """Build a request that drives the parsed-argv path (no shell injection)."""
    return ShellRunRequest(command=" ".join(argv), argv=argv)


# ── rejections: code execution (REQ-002) ─────────────────────────────────────


class TestInterpreterCodeExecutionRejected:
    def test_python_c_rejected(self, tmp_path: Path) -> None:
        svc = _contract_service(tmp_path, ["python", "python3", "git", "ruff", "mypy"])
        with pytest.raises(ShellAuthorizationError):
            svc._check_command(_req(["python", "-c", "print('hi')"]))

    def test_python3_c_rejected(self, tmp_path: Path) -> None:
        svc = _contract_service(tmp_path, ["python", "python3", "git", "ruff", "mypy"])
        with pytest.raises(ShellAuthorizationError):
            svc._check_command(_req(["python3", "-c", "import os"]))

    def test_python_module_flag_rejected(self, tmp_path: Path) -> None:
        svc = _contract_service(tmp_path, ["python", "python3"])
        with pytest.raises(ShellAuthorizationError):
            svc._check_command(_req(["python", "-m", "pip", "install", "x"]))


# ── rejections: mutating git (REQ-002) ───────────────────────────────────────


class TestMutatingGitRejected:
    def test_git_branch_delete_rejected(self, tmp_path: Path) -> None:
        svc = _contract_service(tmp_path, ["git"])
        with pytest.raises(ShellAuthorizationError):
            svc._check_command(_req(["git", "branch", "-D", "feature"]))

    def test_git_push_rejected(self, tmp_path: Path) -> None:
        svc = _contract_service(tmp_path, ["git"])
        with pytest.raises(ShellAuthorizationError):
            svc._check_command(_req(["git", "push"]))

    def test_git_reset_hard_rejected(self, tmp_path: Path) -> None:
        svc = _contract_service(tmp_path, ["git"])
        with pytest.raises(ShellAuthorizationError):
            svc._check_command(_req(["git", "reset", "--hard"]))


# ── acceptances: read-only git and static analysis (REQ-002) ─────────────────


class TestSafeFormsAccepted:
    def test_git_log_accepted(self, tmp_path: Path) -> None:
        svc = _contract_service(tmp_path, ["git"])
        assert svc._check_command(_req(["git", "log"])) == ["git", "log"]

    def test_git_status_accepted(self, tmp_path: Path) -> None:
        svc = _contract_service(tmp_path, ["git"])
        assert svc._check_command(_req(["git", "status"])) == ["git", "status"]

    def test_git_push_dry_run_accepted(self, tmp_path: Path) -> None:
        svc = _contract_service(tmp_path, ["git"])
        assert svc._check_command(_req(["git", "push", "--dry-run", "origin"])) == [
            "git",
            "push",
            "--dry-run",
            "origin",
        ]

    def test_git_branch_create_accepted(self, tmp_path: Path) -> None:
        svc = _contract_service(tmp_path, ["git"])
        assert svc._check_command(_req(["git", "branch", "feature"])) == [
            "git",
            "branch",
            "feature",
        ]

    def test_ruff_check_accepted(self, tmp_path: Path) -> None:
        svc = _contract_service(tmp_path, ["ruff"])
        assert svc._check_command(_req(["ruff", "check", "."])) == [
            "ruff",
            "check",
            ".",
        ]

    def test_mypy_path_accepted(self, tmp_path: Path) -> None:
        svc = _contract_service(tmp_path, ["mypy"])
        assert svc._check_command(_req(["mypy", "path"])) == ["mypy", "path"]


# ── fail closed: unrecognized shapes (REQ-001) ───────────────────────────────


class TestFailClosed:
    def test_unknown_subcommand_rejected(self, tmp_path: Path) -> None:
        # deny-by-default: an unknown git subcommand must not pass through.
        svc = _contract_service(tmp_path, ["git"])
        with pytest.raises(ShellAuthorizationError):
            svc._check_command(_req(["git", "foo", "bar"]))

    def test_unknown_flag_rejected(self, tmp_path: Path) -> None:
        svc = _contract_service(tmp_path, ["git"])
        with pytest.raises(ShellAuthorizationError):
            svc._check_command(_req(["git", "--unknown-flag"]))

    def test_unknown_flag_for_ruff_rejected(self, tmp_path: Path) -> None:
        svc = _contract_service(tmp_path, ["ruff"])
        with pytest.raises(ShellAuthorizationError):
            svc._check_command(_req(["ruff", "--bad-flag", "."]))

    def test_pytest_denied_by_default(self, tmp_path: Path) -> None:
        # pytest imports and runs repository code; shipped default fails closed.
        svc = _contract_service(tmp_path, ["pytest"])
        with pytest.raises(ShellAuthorizationError):
            svc._check_command(_req(["pytest", "tests/", "-q"]))


# ── backward compatibility: uncontracted commands pass through ────────────────


class TestUncontractedPassThrough:
    def test_ls_passes_through(self, tmp_path: Path) -> None:
        # ls has no contract entry; the basename allowlist is its sole check.
        svc = _contract_service(tmp_path, ["ls", "echo"])
        assert svc._check_command(_req(["ls", "-la"])) == ["ls", "-la"]


# ── no subprocess launched on rejection (REQ-004) ────────────────────────────


class TestNoSubprocessOnRejection:
    @pytest.mark.asyncio
    async def test_rejection_raises_before_subprocess(self, tmp_path: Path) -> None:
        svc = _contract_service(tmp_path, ["git", "python"])
        req = _req(["git", "push"])
        # If run_command reached subprocess construction it would raise here;
        # _check_command must reject first.
        with patch(
            "asyncio.create_subprocess_exec",
            side_effect=RuntimeError("subprocess must not be created"),
        ):
            with pytest.raises(ShellAuthorizationError):
                await svc.run_command(req)
