"""
tests/test_shell_mcp_service.py
Unit tests for ShellService guard methods:
  - _filter_env: allowlist / denylist filtering
  - _resolve_cwd: default_cwd fallback
"""

from __future__ import annotations

import signal
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from mcp_servers.shell.models import (
    ShellAuthorizationError,
    ShellRunRequest,
    ShellValidationError,
    load_shell_policy,
)
from mcp_servers.shell.service import ShellService
from mcp_servers.shell.service_static_helpers import init_sandbox as _init_sandbox
from mcp_servers.shell.service_static_helpers import make_preexec as _make_preexec
from shared.protocols.shell import ShellPolicy

# ── Fixtures ──────────────────────────────────────────────────────────────────


def _make_policy(
    tmp_path: Path,
    *,
    default_cwd: str = "",
    env_allowlist: list[str] | None = None,
    env_denylist: list[str] | None = None,
    max_output_kb: int = 512,
) -> ShellPolicy:
    return ShellPolicy(
        allowed_commands=frozenset(["ls", "echo"]),
        cwd_allowed_dirs=(str(tmp_path),),
        default_cwd=default_cwd,
        timeout_sec=30,
        max_output_kb=max_output_kb,
        max_memory_mb=256,
        kill_policy="sigterm_then_sigkill",
        kill_grace_sec=2.0,
        execution_user="",
        shell_path="/usr/bin:/bin",
        audit_log_path=str(tmp_path / "audit.log"),
        sandbox_backend="none",
        env_allowlist=tuple(env_allowlist) if env_allowlist is not None else (),
        env_denylist=tuple(env_denylist) if env_denylist is not None else (),
    )


def _make_service(
    tmp_path: Path,
    *,
    default_cwd: str = "",
    env_allowlist: list[str] | None = None,
    env_denylist: list[str] | None = None,
) -> ShellService:
    """Create a minimal ShellService for testing; no real subprocesses are launched."""
    return ShellService(
        _make_policy(
            tmp_path,
            default_cwd=default_cwd,
            env_allowlist=env_allowlist,
            env_denylist=env_denylist,
        )
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

    def test_empty_allowlist_value_denies_all_keys(self, tmp_path: Path) -> None:
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

    def test_both_empty_returns_env_unchanged(self, tmp_path: Path) -> None:
        svc = _make_service(tmp_path, env_allowlist=[], env_denylist=[])
        env = {"HOME": "/root", "TERM": "xterm"}
        assert svc._filter_env(env) == env

    def test_allowlist_with_no_matches_returns_empty_dict(self, tmp_path: Path) -> None:
        svc = _make_service(tmp_path, env_allowlist=["NONEXISTENT_VAR"])
        env = {"HOME": "/root", "TERM": "xterm", "PATH": "/usr/bin"}
        assert svc._filter_env(env) == {}

    def test_denylist_glob_matching_all_removes_all(self, tmp_path: Path) -> None:
        svc = _make_service(tmp_path, env_denylist=["*"])
        env = {"HOME": "/root", "TERM": "xterm", "PATH": "/usr/bin"}
        assert svc._filter_env(env) == {}


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
        with pytest.raises(ShellAuthorizationError):
            svc._resolve_cwd(str(outside))

    def test_default_cwd_outside_allowed_dirs_raises(self, tmp_path: Path) -> None:
        # default_cwd points outside the allowed dirs list
        svc = _make_service(tmp_path, default_cwd=str(tmp_path.parent))
        with pytest.raises(ShellAuthorizationError):
            svc._resolve_cwd(None)

    def test_explicit_cwd_at_root_of_allowed_dir_passes(self, tmp_path: Path) -> None:
        svc = _make_service(tmp_path)
        result = svc._resolve_cwd(str(tmp_path))
        assert result == str(tmp_path.resolve())


# ── _init_sandbox ─────────────────────────────────────────────────────────────


class TestInitSandbox:
    def test_none_backend_returns_none(self) -> None:
        assert _init_sandbox("none") == "none"

    def test_firejail_found_returns_firejail(self) -> None:
        with patch(
            "mcp_servers.shell.service_static_helpers.shutil.which",
            return_value="/usr/bin/firejail",
        ):
            assert _init_sandbox("firejail") == "firejail"

    def test_firejail_not_found_raises_runtime_error(self) -> None:
        with patch(
            "mcp_servers.shell.service_static_helpers.shutil.which", return_value=None
        ):
            with pytest.raises(RuntimeError, match="firejail is not found in PATH"):
                _init_sandbox("firejail")


# ── _build_argv ───────────────────────────────────────────────────────────────


class TestBuildArgv:
    def test_none_sandbox_returns_argv_unchanged(self, tmp_path: Path) -> None:
        svc = _make_service(
            tmp_path,
        )
        assert svc._subprocess_runner.build_argv(["ls", "-la"]) == ["ls", "-la"]

    def test_firejail_sandbox_prepends_wrapper(self, tmp_path: Path) -> None:
        # Create ShellService with firejail backend bypassing _init_sandbox validation
        svc = _make_service(tmp_path)
        svc._subprocess_runner._sandbox_backend = (
            "firejail"  # inject directly to avoid shutil.which
        )
        result = svc._subprocess_runner.build_argv(["ls", "-la"])
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
        with pytest.raises(ShellValidationError):
            svc._check_command(req)

    def test_command_not_in_allowlist_raises_403(self, tmp_path: Path) -> None:
        svc = _make_service(tmp_path)
        req = ShellRunRequest(command="rm -rf /")
        with pytest.raises(ShellAuthorizationError):
            svc._check_command(req)


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
        svc2 = ShellService(_make_policy(tmp_path, max_output_kb=1))

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


# ── load_shell_policy ─────────────────────────────────────────────────────────


class TestLoadShellPolicy:
    def test_builds_policy_from_cfg(self, tmp_path: Path) -> None:
        from mcp_servers.shell.models import ShellConfig

        fake_cfg = ShellConfig(
            command_allowlist=["pytest", "git"],
            shell_cwd_allowed_dirs=[str(tmp_path)],
            default_cwd=str(tmp_path),
            max_timeout_sec=120,
            max_output_kb=1024,
            max_memory_mb=256,
            kill_policy="sigkill_only",
            kill_grace_sec=1.0,
            execution_user="",
            shell_path="/opt/venv/bin:/usr/bin",
            audit_log_path="/tmp/audit.log",
            shell_sandbox_backend="none",
            env_allowlist=[],
            env_denylist=["LD_PRELOAD"],
        )
        with patch.object(ShellConfig, "load", return_value=fake_cfg):
            policy = load_shell_policy()

        assert "pytest" in policy.allowed_commands
        assert policy.timeout_sec == 120
        assert policy.kill_policy == "sigkill_only"
        assert policy.kill_grace_sec == 1.0
        assert policy.env_denylist == ("LD_PRELOAD",)


# ── execution_user ────────────────────────────────────────────────────────────


class TestExecutionUser:
    def test_nonroot_execution_user_logs_warning(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        # Running as non-root: execution_user should trigger a warning
        policy = _make_policy(tmp_path)
        policy2 = ShellPolicy(
            allowed_commands=policy.allowed_commands,
            cwd_allowed_dirs=policy.cwd_allowed_dirs,
            default_cwd=policy.default_cwd,
            timeout_sec=policy.timeout_sec,
            max_output_kb=policy.max_output_kb,
            max_memory_mb=policy.max_memory_mb,
            kill_policy=policy.kill_policy,
            kill_grace_sec=policy.kill_grace_sec,
            execution_user="nonexistent_user_xyz",
            shell_path=policy.shell_path,
            audit_log_path=policy.audit_log_path,
            sandbox_backend=policy.sandbox_backend,
            env_allowlist=policy.env_allowlist,
            env_denylist=policy.env_denylist,
        )
        import logging

        with caplog.at_level(logging.WARNING, logger="mcp_servers.shell.service"):
            ShellService(policy2)
        # Either "requires CAP_SETUID" (non-root) or "not found in /etc/passwd" (root)
        assert any(
            "CAP_SETUID" in r.message or "not found" in r.message
            for r in caplog.records
        )


# ── _make_preexec ─────────────────────────────────────────────────────────────


class TestMakePreexec:
    def test_preexec_calls_resource_limits_when_no_uid_gid(self) -> None:
        preexec = _make_preexec(max_memory_mb=128, timeout_sec=10, uid=None, gid=None)
        with patch(
            "mcp_servers.shell.service_static_helpers.set_resource_limits"
        ) as mock_limits:
            preexec()
        mock_limits.assert_called_once_with(128, 10)


# ── kill policy ───────────────────────────────────────────────────────────────


class TestKillPolicy:
    @pytest.mark.asyncio
    async def test_sigkill_only_sends_sigkill_on_timeout(self, tmp_path: Path) -> None:
        from unittest.mock import AsyncMock, MagicMock

        policy = ShellPolicy(
            allowed_commands=frozenset(["echo"]),
            cwd_allowed_dirs=(str(tmp_path),),
            default_cwd=str(tmp_path),
            timeout_sec=30,
            max_output_kb=512,
            max_memory_mb=256,
            kill_policy="sigkill_only",
            kill_grace_sec=2.0,
            execution_user="",
            shell_path="/usr/bin:/bin",
            audit_log_path=str(tmp_path / "audit.log"),
            sandbox_backend="none",
            env_allowlist=(),
            env_denylist=(),
        )
        svc = ShellService(policy)

        mock_proc = MagicMock()
        mock_proc.returncode = -9
        mock_proc.pid = 99999
        mock_proc.communicate = AsyncMock(side_effect=TimeoutError())
        mock_proc.wait = AsyncMock(return_value=-9)

        req = ShellRunRequest(command="echo hello", timeout_sec=1)
        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            with patch("os.killpg") as mock_killpg:
                with patch(
                    "asyncio.wait_for",
                    side_effect=[
                        TimeoutError(),
                        -9,
                    ],  # communicate times out, then wait returns
                ):
                    result = await svc.run_command(req)

        assert result.timed_out is True
        mock_killpg.assert_called_with(99999, signal.SIGKILL)

    @pytest.mark.asyncio
    async def test_sigterm_then_sigkill_sends_sigterm_first(
        self, tmp_path: Path
    ) -> None:
        from unittest.mock import AsyncMock, MagicMock, call

        svc = ShellService(_make_policy(tmp_path))  # kill_policy="sigterm_then_sigkill"

        mock_proc = MagicMock()
        mock_proc.returncode = -15
        mock_proc.pid = 99998
        mock_proc.communicate = AsyncMock(side_effect=TimeoutError())
        mock_proc.wait = AsyncMock(return_value=-15)

        req = ShellRunRequest(command="echo hello", timeout_sec=1)
        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            with patch("os.killpg") as mock_killpg:
                # communicate times out; grace period wait returns immediately
                with patch(
                    "asyncio.wait_for",
                    side_effect=[TimeoutError(), -15, -15],
                ):
                    result = await svc.run_command(req)

        assert result.timed_out is True
        # SIGTERM must be sent first
        assert mock_killpg.call_args_list[0] == call(99998, signal.SIGTERM)


# ── _LazyShellService ─────────────────────────────────────────────────────────


class TestLazyShellService:
    def test_empty_cwd_dirs_logs_warning(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        import logging

        from mcp_servers.shell.service import build_service

        policy = ShellPolicy(
            allowed_commands=frozenset(["echo"]),
            cwd_allowed_dirs=(),  # empty
            default_cwd="",
            timeout_sec=30,
            max_output_kb=512,
            max_memory_mb=256,
            kill_policy="sigterm_then_sigkill",
            kill_grace_sec=2.0,
            execution_user="",
            shell_path="/usr/bin:/bin",
            audit_log_path=str(tmp_path / "audit.log"),
            sandbox_backend="none",
            env_allowlist=(),
            env_denylist=(),
        )
        with caplog.at_level(logging.WARNING, logger="mcp_servers.shell.service"):
            build_service(policy)
        assert any("cwd" in r.message for r in caplog.records)

    def test_empty_allowlist_logs_warning(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        import logging

        from mcp_servers.shell.service import build_service

        policy = ShellPolicy(
            allowed_commands=frozenset(),  # empty
            cwd_allowed_dirs=(str(tmp_path),),
            default_cwd="",
            timeout_sec=30,
            max_output_kb=512,
            max_memory_mb=256,
            kill_policy="sigterm_then_sigkill",
            kill_grace_sec=2.0,
            execution_user="",
            shell_path="/usr/bin:/bin",
            audit_log_path=str(tmp_path / "audit.log"),
            sandbox_backend="none",
            env_allowlist=(),
            env_denylist=(),
        )
        with caplog.at_level(logging.WARNING, logger="mcp_servers.shell.service"):
            build_service(policy)
        assert any("command_allowlist" in r.message for r in caplog.records)


# ── dry_run ───────────────────────────────────────────────────────────────────


class TestDryRun:
    @pytest.mark.asyncio
    async def test_dry_run_returns_preview_without_executing(
        self, tmp_path: Path
    ) -> None:
        import orjson

        svc = _make_service(tmp_path)
        # cwd must be inside allowed dirs for the request to be valid
        cwd = str(tmp_path)
        result = await svc.fmt_run_command(
            {"command": "ls -la", "dry_run": True, "cwd": cwd}
        )
        payload = orjson.loads(result)
        assert payload["dry_run"] is True
        assert "Would execute" in payload["preview"]
        assert "ls -la" in payload["preview"]

    @pytest.mark.asyncio
    async def test_dry_run_shows_default_cwd_when_cwd_not_provided(
        self, tmp_path: Path
    ) -> None:
        import orjson

        svc = _make_service(tmp_path, default_cwd=str(tmp_path))
        result = await svc.fmt_run_command({"command": "echo hi", "dry_run": True})
        payload = orjson.loads(result)
        assert payload["dry_run"] is True
        assert "(default)" in payload["preview"]

    @pytest.mark.asyncio
    async def test_dry_run_does_not_create_subprocess(self, tmp_path: Path) -> None:
        from unittest.mock import patch as mock_patch

        svc = _make_service(tmp_path)
        with mock_patch(
            "asyncio.create_subprocess_exec", side_effect=RuntimeError("must not call")
        ):
            # dry_run=True — subprocess must never be created
            await svc.fmt_run_command({"command": "ls", "dry_run": True})

    @pytest.mark.asyncio
    async def test_fmt_run_command_formats_success_result(self, tmp_path: Path) -> None:
        from mcp_servers.shell.models import ShellRunResponse

        svc = _make_service(tmp_path)
        mock_result = ShellRunResponse(
            stdout="hello\n",
            stderr="",
            exit_code=0,
            timed_out=False,
            truncated=False,
            elapsed_sec=0.1,
        )
        with patch.object(svc, "run_command", new=AsyncMock(return_value=mock_result)):
            result = await svc.fmt_run_command({"command": "echo hello"})
        assert "exit_code=0" in result
        assert "hello" in result

    @pytest.mark.asyncio
    async def test_fmt_run_command_timed_out_flag(self, tmp_path: Path) -> None:
        from mcp_servers.shell.models import ShellRunResponse

        svc = _make_service(tmp_path)
        mock_result = ShellRunResponse(
            stdout="",
            stderr="",
            exit_code=-1,
            timed_out=True,
            truncated=False,
            elapsed_sec=30.0,
        )
        with patch.object(svc, "run_command", new=AsyncMock(return_value=mock_result)):
            result = await svc.fmt_run_command({"command": "sleep 100"})
        assert "TIMED OUT" in result

    @pytest.mark.asyncio
    async def test_fmt_run_command_truncated_flag(self, tmp_path: Path) -> None:
        from mcp_servers.shell.models import ShellRunResponse

        svc = _make_service(tmp_path)
        mock_result = ShellRunResponse(
            stdout="a" * 1000,
            stderr="",
            exit_code=0,
            timed_out=False,
            truncated=True,
            elapsed_sec=0.5,
        )
        with patch.object(svc, "run_command", new=AsyncMock(return_value=mock_result)):
            result = await svc.fmt_run_command({"command": "ls -R"})
        assert "TRUNCATED" in result


class TestHealthResponse:
    def test_health_response_includes_sandbox_backend_in_details(
        self, monkeypatch
    ) -> None:
        from fastapi.testclient import TestClient
        from mcp_servers.shell import server as shell_server

        class _FakeService:
            sandbox_backend = "none"
            ready = True
            dependencies: dict = {}

        monkeypatch.setattr(shell_server, "_service", _FakeService())
        client = TestClient(shell_server.app)
        resp = client.get("/health")
        assert resp.status_code == 200
        body = resp.json()
        assert "sandbox_backend" not in body
        assert "sandbox_backend" in body.get("details", {})
        assert body["details"]["sandbox_backend"] in ("none", "firejail")
