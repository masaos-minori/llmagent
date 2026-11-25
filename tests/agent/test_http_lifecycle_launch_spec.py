"""tests/agent/test_http_lifecycle_launch_spec.py

Contract tests for the immutable launch specification (cliplc006 REQ-001,
REQ-006, REQ-007): frozen spec, fixed process options, minimal per-server
environment, credential isolation, key-names-only audit, and identity re-check.
"""

from __future__ import annotations

import dataclasses
import os
import subprocess
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from agent.http_lifecycle_launch_spec import (
    LaunchSpec,
    build_child_env,
    build_launch_spec,
)
from shared.mcp_config import McpServerConfig, StartupMode, TransportType

# The REQ-006 fixed runtime set (cliplc006 row 2/3): everything build_child_env
# may inherit from the parent, besides the server's own tokens and declared names.
_FIXED_RUNTIME_VARS = [
    "PATH",
    "HOME",
    "USER",
    "LOGNAME",
    "SHELL",
    "TMPDIR",
    "TMP",
    "TEMP",
    "LANG",
    "LLMAGENT_CONFIG_DIR",
    "LLMAGENT_SUDACHI_DICT",
]


def _make_cfg(key: str, **overrides: object) -> McpServerConfig:
    defaults: dict[str, object] = dict(
        transport=TransportType.HTTP,
        url="http://localhost:8080",
        startup_mode=StartupMode.SUBPROCESS,
        cmd=[f"/opt/llm/bin/mcp_{key}"],
        call_timeout_sec=60.0,
        auth_token="test-token",
        key=key,
    )
    defaults.update(overrides)
    return McpServerConfig(**defaults)


def _exe_fixture(tmp_path: Path, name: str = "mcp_github") -> Path:
    exe = tmp_path / name
    exe.write_text("#!/bin/sh\nexit 0\n")
    exe.chmod(0o755)
    return exe


def _fixed_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Deterministic parent environment: the fixed set present, nothing else."""
    for var in _FIXED_RUNTIME_VARS:
        monkeypatch.setenv(var, f"parent-{var}")
    monkeypatch.setenv("LC_ALL", "C")
    for unrelated in ("AWS_SECRET_ACCESS_KEY", "https_proxy", "UV_INDEX_URL"):
        monkeypatch.delenv(unrelated, raising=False)


def _tokens(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MCP_GITHUB_AUTH_TOKEN", "gtok-value")
    monkeypatch.setenv("MCP_GITHUB_CONTROL_TOKEN", "gctl-value")
    monkeypatch.setenv("MCP_CICD_AUTH_TOKEN", "ctok-value")
    monkeypatch.setenv("MCP_CICD_CONTROL_TOKEN", "cctl-value")
    monkeypatch.setenv("GITHUB_TOKEN", "ght-value")


def _make_spec(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    key: str = "github",
    **cfg_overrides: object,
):
    exe = _exe_fixture(tmp_path, f"mcp_{key}")
    monkeypatch.setenv("LLMAGENT_BINARY_DIR", str(exe.parent))
    cfg = _make_cfg(key, cmd=[str(exe)], **cfg_overrides)
    stat = os.stat(exe)
    stderr_fh = MagicMock(name="stderr_fh")
    spec = build_launch_spec(key, cfg, str(exe), (stat.st_dev, stat.st_ino), stderr_fh)
    return spec, exe, stderr_fh


class TestSpecImmutability:
    """REQ-001: one construction site, no mutation, argv[0] is the validated path."""

    def test_frozen_spec_rejects_mutation(self, tmp_path, monkeypatch):
        spec, _, _ = _make_spec(tmp_path, monkeypatch)
        assert isinstance(spec, LaunchSpec)
        assert isinstance(spec.env_items, tuple)
        with pytest.raises(dataclasses.FrozenInstanceError):
            spec.argv = ("/tmp/evil",)
        with pytest.raises(dataclasses.FrozenInstanceError):
            spec.expected_identity = (0, 0)

    def test_argv_holds_the_validated_absolute_path(self, tmp_path, monkeypatch):
        spec, exe, _ = _make_spec(tmp_path, monkeypatch)
        assert spec.argv[0] == str(exe)
        assert os.path.isabs(spec.argv[0])
        assert isinstance(spec.argv, tuple)

    def test_relative_argv0_rejected(self, tmp_path, monkeypatch):
        exe = _exe_fixture(tmp_path)
        cfg = _make_cfg("github", cmd=[str(exe)])
        stderr_fh = MagicMock()
        with pytest.raises(ValueError, match="absolute"):
            build_launch_spec("github", cfg, "mcp_github", (0, 0), stderr_fh)

    def test_non_string_argument_rejected(self, tmp_path, monkeypatch):
        exe = _exe_fixture(tmp_path)
        cfg = _make_cfg("github", cmd=[str(exe), 5])
        stderr_fh = MagicMock()
        with pytest.raises(ValueError, match="str"):
            build_launch_spec("github", cfg, str(exe), (0, 0), stderr_fh)

    def test_invalid_server_key_rejected_before_any_path_use(
        self, tmp_path, monkeypatch
    ):
        exe = _exe_fixture(tmp_path)
        cfg = _make_cfg("github", cmd=[str(exe)])
        stderr_fh = MagicMock()
        with pytest.raises(ValueError, match="server identifier"):
            build_launch_spec("a/b", cfg, str(exe), (0, 0), stderr_fh)


class TestFixedProcessOptions:
    """REQ-001/REQ-002: popen_kwargs() is the only keyword source and is fixed."""

    def test_kwargs_are_exactly_the_fixed_set(self, tmp_path, monkeypatch):
        _fixed_env(monkeypatch)
        spec, _, stderr_fh = _make_spec(tmp_path, monkeypatch)
        kwargs = spec.popen_kwargs()
        assert set(kwargs) == {"start_new_session", "stdout", "stderr", "env"}
        assert kwargs["start_new_session"] is True
        assert kwargs["stdout"] is subprocess.DEVNULL
        assert kwargs["stderr"] is stderr_fh

    def test_no_override_keyword_ever_appears(self, tmp_path, monkeypatch):
        _fixed_env(monkeypatch)
        spec, _, _ = _make_spec(tmp_path, monkeypatch)
        kwargs = spec.popen_kwargs()
        for forbidden in ("shell", "preexec_fn", "cwd", "close_fds"):
            assert forbidden not in kwargs


class TestMinimalEnvironment:
    """REQ-006: the child env is the fixed set plus this server's own names."""

    def test_returns_dict_when_cfg_env_empty(self, tmp_path, monkeypatch):
        _fixed_env(monkeypatch)
        cfg = _make_cfg("github")
        env = build_child_env("github", cfg)
        assert isinstance(env, dict)
        for var in _FIXED_RUNTIME_VARS:
            assert env[var] == f"parent-{var}"
        assert env["LC_ALL"] == "C"

    def test_unrelated_parent_vars_absent(self, tmp_path, monkeypatch):
        _fixed_env(monkeypatch)
        monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "secret")
        env = build_child_env("github", _make_cfg("github"))
        assert "AWS_SECRET_ACCESS_KEY" not in env

    def test_denylisted_cfg_env_key_dropped(self, tmp_path, monkeypatch):
        _fixed_env(monkeypatch)
        cfg = _make_cfg("github")
        # The parser rejects a denylisted `env` key (row 1); this is the defense-in-depth
        # filter that still applies if such a value reaches the builder.
        cfg.env["PYTHONPATH"] = "/tmp/evil"
        env = build_child_env("github", cfg)
        assert "PYTHONPATH" not in env

    def test_protected_var_override_refused(self, tmp_path, monkeypatch):
        _fixed_env(monkeypatch)
        cfg = _make_cfg("github", env={"HOME": "/tmp/evil-home"})
        env = build_child_env("github", cfg)
        assert env["HOME"] == "parent-HOME"


class TestCredentialIsolation:
    """REQ-006/REQ-007 (AC-3): each server holds its own tokens only."""

    def test_github_spec_holds_own_tokens_and_declared_name(
        self, tmp_path, monkeypatch
    ):
        _fixed_env(monkeypatch)
        _tokens(monkeypatch)
        cfg = _make_cfg("github", credential_env=("GITHUB_TOKEN",))
        env = build_child_env("github", cfg)
        assert env["MCP_GITHUB_AUTH_TOKEN"] == "gtok-value"
        assert env["MCP_GITHUB_CONTROL_TOKEN"] == "gctl-value"
        assert env["GITHUB_TOKEN"] == "ght-value"
        assert "MCP_CICD_AUTH_TOKEN" not in env
        assert "MCP_CICD_CONTROL_TOKEN" not in env

    def test_cicd_spec_holds_no_github_token(self, tmp_path, monkeypatch):
        _fixed_env(monkeypatch)
        _tokens(monkeypatch)
        cfg = _make_cfg("cicd")
        env = build_child_env("cicd", cfg)
        assert env["MCP_CICD_AUTH_TOKEN"] == "ctok-value"
        assert env["MCP_CICD_CONTROL_TOKEN"] == "cctl-value"
        assert "GITHUB_TOKEN" not in env
        assert "MCP_GITHUB_AUTH_TOKEN" not in env

    def test_declared_name_absent_from_parent_is_not_added(self, tmp_path, monkeypatch):
        _fixed_env(monkeypatch)
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        cfg = _make_cfg("github", credential_env=("GITHUB_TOKEN",))
        env = build_child_env("github", cfg)
        assert "GITHUB_TOKEN" not in env


class TestAuditLine:
    """REQ-007: the launch audit records key names only, never values."""

    def test_audit_names_keys_not_values(self, tmp_path, monkeypatch, caplog):
        _fixed_env(monkeypatch)
        _tokens(monkeypatch)
        cfg = _make_cfg("github", credential_env=("GITHUB_TOKEN",))
        with caplog.at_level("INFO"):
            build_child_env("github", cfg)
        assert "MCP_GITHUB_AUTH_TOKEN" in caplog.text
        for value in ("gtok-value", "gctl-value", "ght-value"):
            assert value not in caplog.text


class TestIdentityRecheck:
    """REQ-003: verify_identity detects a swapped file before the spawn."""

    def test_identity_matches_after_validation(self, tmp_path, monkeypatch):
        spec, _, _ = _make_spec(tmp_path, monkeypatch)
        assert spec.verify_identity() is None

    def test_stale_identity_aborts_the_recheck(self, tmp_path, monkeypatch):
        spec, exe, _ = _make_spec(tmp_path, monkeypatch)
        # An identity that cannot match the file on disk: the re-check must abort.
        stale = dataclasses.replace(spec, expected_identity=(0, 0))
        reason = stale.verify_identity()
        assert reason is not None
        assert "github" in reason
        assert str(exe) in reason

    def test_missing_target_aborts_the_recheck(self, tmp_path, monkeypatch):
        spec, exe, _ = _make_spec(tmp_path, monkeypatch)
        exe.unlink()
        reason = spec.verify_identity()
        assert reason is not None
        assert "github" in reason
        assert str(exe) in reason
