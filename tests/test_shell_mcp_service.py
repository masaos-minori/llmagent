"""
tests/test_shell_mcp_service.py
Unit tests for ShellService guard methods:
  - _filter_env: allowlist / denylist filtering
  - _resolve_cwd: default_cwd fallback
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi import HTTPException
from mcp.shell.models import ShellRunRequest
from mcp.shell.service import ShellService, _init_sandbox

# ── Fixtures ──────────────────────────────────────────────────────────────────


def _make_service(
    tmp_path: Path,
    *,
    default_cwd: str = "",
    env_allowlist: list[str] | None = None,
    env_denylist: list[str] | None = None,
) -> ShellService:
    """Create a minimal ShellService for testing; no real subprocesses are launched."""
    return ShellService(
        command_allowlist=["ls", "echo"],
        shell_cwd_allowed_dirs=[tmp_path],
        shell_path="/usr/bin:/bin",
        max_timeout_sec=30,
        max_output_kb=512,
        max_memory_mb=256,
        audit_log_path=str(tmp_path / "audit.log"),
        sandbox_backend="none",
        default_cwd=default_cwd,
        env_allowlist=env_allowlist,
        env_denylist=env_denylist,
    )


# ── _filter_env ───────────────────────────────────────────────────────────────


class TestFilterEnv:
    def test_no_filters_returns_env_unchanged(self, tmp_path: Path) -> None:
        svc = _make_service(tmp_path)
        env = {"HOME": "/root", "TERM": "xterm"}
        assert svc._filter_env(env) == env

    def test_allowlist_keeps_only_listed_keys(self, tmp_path: Path) -> None:
        svc = _make_service(tmp_path, env_allowlist=["HOME"])
        env = {"HOME": "/root", "TERM": "xterm", "LD_PRELOAD": "/evil.so"}
        result = svc._filter_env(env)
        assert result == {"HOME": "/root"}

    def test_allowlist_empty_value_matches_no_keys(self, tmp_path: Path) -> None:
        # Empty allowlist means denylist is used (or pass-through if also empty)
        svc = _make_service(tmp_path, env_allowlist=[], env_denylist=["LD_PRELOAD"])
        env = {"HOME": "/root", "LD_PRELOAD": "/evil.so"}
        result = svc._filter_env(env)
        assert "LD_PRELOAD" not in result
        assert "HOME" in result

    def test_denylist_removes_matching_keys(self, tmp_path: Path) -> None:
        svc = _make_service(tmp_path, env_denylist=["LD_PRELOAD", "LD_LIBRARY_PATH"])
        env = {"LD_PRELOAD": "/evil.so", "LD_LIBRARY_PATH": "/lib", "HOME": "/root"}
        result = svc._filter_env(env)
        assert "LD_PRELOAD" not in result
        assert "LD_LIBRARY_PATH" not in result
        assert result["HOME"] == "/root"

    def test_denylist_glob_pattern_removes_matching_keys(self, tmp_path: Path) -> None:
        svc = _make_service(tmp_path, env_denylist=["LD_*"])
        env = {"LD_PRELOAD": "/evil.so", "LD_LIBRARY_PATH": "/lib", "HOME": "/root"}
        result = svc._filter_env(env)
        assert "LD_PRELOAD" not in result
        assert "LD_LIBRARY_PATH" not in result
        assert "HOME" in result

    def test_allowlist_takes_priority_over_denylist(self, tmp_path: Path) -> None:
        # allowlist is non-empty, so denylist is ignored entirely
        svc = _make_service(
            tmp_path,
            env_allowlist=["HOME"],
            env_denylist=["HOME"],  # would remove HOME if applied, but allowlist wins
        )
        env = {"HOME": "/root", "TERM": "xterm"}
        result = svc._filter_env(env)
        # allowlist wins: only HOME is kept
        assert result == {"HOME": "/root"}

    def test_empty_env_dict_returns_empty(self, tmp_path: Path) -> None:
        svc = _make_service(tmp_path, env_denylist=["LD_PRELOAD"])
        assert svc._filter_env({}) == {}

    def test_denylist_with_no_matches_returns_env_unchanged(
        self, tmp_path: Path
    ) -> None:
        svc = _make_service(tmp_path, env_denylist=["LD_PRELOAD"])
        env = {"HOME": "/root", "TERM": "xterm"}
        assert svc._filter_env(env) == env


# ── _resolve_cwd ──────────────────────────────────────────────────────────────


class TestResolveCwd:
    def test_none_without_default_returns_none(self, tmp_path: Path) -> None:
        svc = _make_service(tmp_path, default_cwd="")
        assert svc._resolve_cwd(None) is None

    def test_none_with_default_returns_default(self, tmp_path: Path) -> None:
        svc = _make_service(tmp_path, default_cwd=str(tmp_path))
        result = svc._resolve_cwd(None)
        assert result == str(tmp_path.resolve())

    def test_explicit_cwd_inside_allowed_dirs_passes(self, tmp_path: Path) -> None:
        sub = tmp_path / "sub"
        sub.mkdir()
        svc = _make_service(tmp_path)
        result = svc._resolve_cwd(str(sub))
        assert result == str(sub.resolve())

    def test_explicit_cwd_outside_allowed_dirs_raises(self, tmp_path: Path) -> None:
        outside = tmp_path.parent
        svc = _make_service(tmp_path)
        with pytest.raises(HTTPException) as exc_info:
            svc._resolve_cwd(str(outside))
        assert exc_info.value.status_code == 403

    def test_default_cwd_outside_allowed_dirs_raises(self, tmp_path: Path) -> None:
        # default_cwd points outside the allowed dirs list
        svc = _make_service(tmp_path, default_cwd=str(tmp_path.parent))
        with pytest.raises(HTTPException) as exc_info:
            svc._resolve_cwd(None)
        assert exc_info.value.status_code == 403

    def test_explicit_cwd_at_root_of_allowed_dir_passes(self, tmp_path: Path) -> None:
        svc = _make_service(tmp_path)
        result = svc._resolve_cwd(str(tmp_path))
        assert result == str(tmp_path.resolve())


# ── _init_sandbox ─────────────────────────────────────────────────────────────


class TestInitSandbox:
    def test_none_backend_returns_none(self) -> None:
        assert _init_sandbox("none") == "none"

    def test_firejail_found_returns_firejail(self) -> None:
        with patch("mcp.shell.service.shutil.which", return_value="/usr/bin/firejail"):
            assert _init_sandbox("firejail") == "firejail"

    def test_firejail_not_found_falls_back_to_none(self) -> None:
        with patch("mcp.shell.service.shutil.which", return_value=None):
            assert _init_sandbox("firejail") == "none"


# ── _build_argv ───────────────────────────────────────────────────────────────


class TestBuildArgv:
    def test_none_sandbox_returns_argv_unchanged(self, tmp_path: Path) -> None:
        svc = _make_service(
            tmp_path,
        )
        assert svc._build_argv(["ls", "-la"]) == ["ls", "-la"]

    def test_firejail_sandbox_prepends_wrapper(self, tmp_path: Path) -> None:
        # Create ShellService with firejail backend bypassing _init_sandbox validation
        svc = _make_service(tmp_path)
        svc._sandbox_backend = "firejail"  # inject directly to avoid shutil.which
        result = svc._build_argv(["ls", "-la"])
        assert result[:2] == ["firejail", "--private"]
        assert "ls" in result
        assert "-la" in result


# ── _check_command ────────────────────────────────────────────────────────────


class TestCheckCommand:
    def test_argv_provided_skips_shlex(self, tmp_path: Path) -> None:
        svc = _make_service(tmp_path)
        req = ShellRunRequest(command="ignored", argv=["ls", "-la"])
        result = svc._check_command(req)
        assert result == ["ls", "-la"]

    def test_invalid_command_string_raises_400(self, tmp_path: Path) -> None:
        svc = _make_service(tmp_path)
        # Unclosed quote causes shlex.split to raise ValueError
        req = ShellRunRequest(command='ls "unclosed')
        with pytest.raises(HTTPException) as exc_info:
            svc._check_command(req)
        assert exc_info.value.status_code == 400

    def test_command_not_in_allowlist_raises_403(self, tmp_path: Path) -> None:
        svc = _make_service(tmp_path)
        req = ShellRunRequest(command="rm -rf /")
        with pytest.raises(HTTPException) as exc_info:
            svc._check_command(req)
        assert exc_info.value.status_code == 403


# ── _write_audit_log ──────────────────────────────────────────────────────────


class TestWriteAuditLog:
    def test_audit_record_written_with_all_fields(self, tmp_path: Path) -> None:
        svc = _make_service(tmp_path)
        svc._write_audit_log(
            command="ls",
            argv=["ls", "-la"],
            cwd="/tmp",
            exit_code=0,
            elapsed=0.12,
            truncated=False,
        )
        content = (tmp_path / "audit.log").read_text()
        assert "cmd='ls'" in content
        assert "argv=['ls', '-la']" in content
        assert "cwd='/tmp'" in content
        assert "exit=0" in content
        assert "truncated=False" in content

    def test_oserror_is_suppressed(self, tmp_path: Path) -> None:
        svc = _make_service(tmp_path)
        svc._audit_log_path = str(tmp_path / "nonexistent" / "audit.log")
        # Must not raise
        svc._write_audit_log("ls", ["ls"], None, 0, 0.1, False)


# ── output truncation ─────────────────────────────────────────────────────────


class TestOutputTruncation:
    @pytest.mark.asyncio
    async def test_output_over_limit_is_truncated(self, tmp_path: Path) -> None:
        from unittest.mock import AsyncMock, MagicMock, patch

        # Build a service with max_output_kb=1 (1 KB = 1024 bytes)
        svc2 = ShellService(
            command_allowlist=["echo"],
            shell_cwd_allowed_dirs=[tmp_path],
            shell_path="/usr/bin:/bin",
            max_timeout_sec=30,
            max_output_kb=1,
            max_memory_mb=256,
            audit_log_path=str(tmp_path / "audit.log"),
            sandbox_backend="none",
        )

        large_stdout = b"A" * 2048  # 2 KB > 1 KB limit
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.pid = 12345
        mock_proc.communicate = AsyncMock(return_value=(large_stdout, b""))

        req = ShellRunRequest(command="echo x", max_output_kb=1)
        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            result = await svc2.run_command(req)

        assert result.truncated is True
        assert len(result.stdout.encode()) <= 512  # half of 1 KB limit
