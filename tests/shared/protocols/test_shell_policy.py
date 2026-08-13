"""
tests/shared/protocols/test_shell_policy.py
Characterization tests for ShellPolicy.__post_init__ validation branches.

These lock the exact ValueError raise conditions and message text before
scripts/shared/protocols/shell.py is refactored, so the refactor can be
verified to preserve behavior byte-for-byte.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from shared.protocols.shell import ShellPolicy


def _valid_kwargs(tmp_path: Path) -> dict[str, Any]:
    return {
        "allowed_commands": frozenset(["ls"]),
        "cwd_allowed_dirs": (str(tmp_path),),
        "default_cwd": "",
        "timeout_sec": 30,
        "max_output_kb": 512,
        "max_memory_mb": 256,
        "kill_policy": "sigterm_then_sigkill",
        "kill_grace_sec": 2.0,
        "execution_user": "",
        "shell_path": "/usr/bin:/bin",
        "audit_log_path": str(tmp_path / "audit.log"),
        "sandbox_backend": "none",
        "env_allowlist": (),
        "env_denylist": (),
    }


class TestValidConstruction:
    def test_valid_kwargs_construct_without_error(self, tmp_path: Path) -> None:
        policy = ShellPolicy(**_valid_kwargs(tmp_path))
        assert policy.timeout_sec == 30
        assert policy.kill_policy == "sigterm_then_sigkill"
        assert policy.sandbox_backend == "none"


class TestKillPolicyValidation:
    def test_invalid_kill_policy_raises_value_error(self, tmp_path: Path) -> None:
        kwargs = _valid_kwargs(tmp_path)
        kwargs["kill_policy"] = "bogus"
        with pytest.raises(ValueError, match=r"kill_policy must be one of"):
            ShellPolicy(**kwargs)

    def test_invalid_kill_policy_message_contains_value(self, tmp_path: Path) -> None:
        kwargs = _valid_kwargs(tmp_path)
        kwargs["kill_policy"] = "bogus"
        with pytest.raises(ValueError, match=r"got 'bogus'"):
            ShellPolicy(**kwargs)


class TestSandboxBackendValidation:
    def test_invalid_sandbox_backend_raises_value_error(self, tmp_path: Path) -> None:
        kwargs = _valid_kwargs(tmp_path)
        kwargs["sandbox_backend"] = "docker"
        with pytest.raises(ValueError, match=r"sandbox_backend must be one of"):
            ShellPolicy(**kwargs)

    def test_invalid_sandbox_backend_message_contains_value(
        self, tmp_path: Path
    ) -> None:
        kwargs = _valid_kwargs(tmp_path)
        kwargs["sandbox_backend"] = "docker"
        with pytest.raises(ValueError, match=r"got 'docker'"):
            ShellPolicy(**kwargs)


class TestNumericBoundaryValidation:
    def test_timeout_sec_zero_raises_value_error(self, tmp_path: Path) -> None:
        kwargs = _valid_kwargs(tmp_path)
        kwargs["timeout_sec"] = 0
        with pytest.raises(ValueError, match=r"timeout_sec must be >= 1, got 0"):
            ShellPolicy(**kwargs)

    def test_max_output_kb_zero_raises_value_error(self, tmp_path: Path) -> None:
        kwargs = _valid_kwargs(tmp_path)
        kwargs["max_output_kb"] = 0
        with pytest.raises(ValueError, match=r"max_output_kb must be >= 1, got 0"):
            ShellPolicy(**kwargs)

    def test_max_memory_mb_zero_raises_value_error(self, tmp_path: Path) -> None:
        kwargs = _valid_kwargs(tmp_path)
        kwargs["max_memory_mb"] = 0
        with pytest.raises(ValueError, match=r"max_memory_mb must be >= 1, got 0"):
            ShellPolicy(**kwargs)

    def test_kill_grace_sec_negative_raises_value_error(self, tmp_path: Path) -> None:
        kwargs = _valid_kwargs(tmp_path)
        kwargs["kill_grace_sec"] = -0.5
        with pytest.raises(ValueError, match=r"kill_grace_sec must be >= 0, got -0.5"):
            ShellPolicy(**kwargs)

    def test_kill_grace_sec_zero_is_allowed(self, tmp_path: Path) -> None:
        kwargs = _valid_kwargs(tmp_path)
        kwargs["kill_grace_sec"] = 0.0
        policy = ShellPolicy(**kwargs)
        assert policy.kill_grace_sec == 0.0
