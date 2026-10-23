"""tests/mcp_servers/shell/test_shell_command_env.py — Environment given to sandboxed shell commands."""

from __future__ import annotations

import sys
from collections.abc import Iterator
from pathlib import Path
from unittest.mock import patch

import pytest
from mcp_servers.shell.shell_models import ShellRunRequest
from mcp_servers.shell.shell_service import ShellService
from mcp_servers.shell.shell_service_static_helpers import (
    build_command_env,
    is_secret_env_key,
)
from mcp_servers.shell.subprocess_runner import SubprocessRunner
from shared.protocols.shell import ShellPolicy


@pytest.fixture(autouse=True)
def _firejail_present() -> Iterator[None]:
    """Make the firejail binary present so no test depends on the host."""
    with patch(
        "mcp_servers.shell.shell_service_static_helpers.shutil.which",
        return_value="/usr/bin/firejail",
    ):
        yield


def _make_service(
    tmp_path: Path,
    *,
    env_allowlist: tuple[str, ...] = (),
    env_denylist: tuple[str, ...] = (),
) -> ShellService:
    return ShellService(
        ShellPolicy(
            allowed_commands=frozenset([Path(sys.executable).name, "python3"]),
            cwd_allowed_dirs=(str(tmp_path),),
            default_cwd=str(tmp_path),
            timeout_sec=30,
            max_output_kb=512,
            max_memory_mb=1024,
            kill_policy="sigterm_then_sigkill",
            kill_grace_sec=2.0,
            execution_user="",
            shell_path="/usr/bin:/bin",
            audit_log_path=str(tmp_path / "audit.log"),
            sandbox_backend="firejail",
            env_allowlist=env_allowlist,
            env_denylist=env_denylist,
        )
    )


class TestIsSecretEnvKey:
    @pytest.mark.parametrize(
        "key",
        [
            "MCP_GIT_AUTH_TOKEN",
            "GITHUB_TOKEN",
            "API_KEY",
            "OPENAI_API_KEY",
            "DB_PASSWORD",
            "CLIENT_SECRET",
            "AWS_CREDENTIALS",
            "token",
        ],
    )
    def test_secret_shaped_keys_are_detected(self, key: str) -> None:
        assert is_secret_env_key(key) is True

    @pytest.mark.parametrize(
        "key", ["HOME", "LC_ALL", "TOKENIZERS_PARALLELISM", "PATH", "API", "KEYBOARD"]
    )
    def test_harmless_keys_are_kept(self, key: str) -> None:
        assert is_secret_env_key(key) is False


class TestBuildCommandEnv:
    def test_only_base_keys_are_copied(self) -> None:
        base = {"HOME": "/h", "LANG": "C", "LC_ALL": "C", "EDITOR": "vi", "PATH": "/x"}
        env = build_command_env(base, "/usr/bin", {})
        assert env == {"HOME": "/h", "LANG": "C", "LC_ALL": "C", "PATH": "/usr/bin"}

    def test_server_tokens_are_never_forwarded(self) -> None:
        base = {
            "HOME": "/h",
            "MCP_SHELL_AUTH_TOKEN": "fake-a",
            "MCP_GITHUB_AUTH_TOKEN": "fake-b",
            "GITHUB_TOKEN": "fake-c",
        }
        env = build_command_env(base, "/usr/bin", {})
        assert not [k for k in env if "TOKEN" in k]

    def test_secret_keys_in_req_env_are_dropped_but_others_kept(self) -> None:
        env = build_command_env(
            {}, "/usr/bin", {"GITHUB_TOKEN": "x", "TOKENIZERS_PARALLELISM": "false"}
        )
        assert env == {"PATH": "/usr/bin", "TOKENIZERS_PARALLELISM": "false"}

    def test_req_env_can_still_override_path(self) -> None:
        env = build_command_env({}, "/usr/bin", {"PATH": "/custom"})
        assert env["PATH"] == "/custom"

    def test_inputs_are_not_mutated(self) -> None:
        base = {"HOME": "/h", "GITHUB_TOKEN": "x"}
        req = {"FOO": "1"}
        build_command_env(base, "/usr/bin", req)
        assert base == {"HOME": "/h", "GITHUB_TOKEN": "x"}
        assert req == {"FOO": "1"}


class TestRunCommandEnvironment:
    @pytest.mark.asyncio
    async def test_command_cannot_see_server_token_variables(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("MCP_SHELL_AUTH_TOKEN", "fake-shell-token")
        monkeypatch.setenv("MCP_GITHUB_AUTH_TOKEN", "fake-github-token")
        monkeypatch.setenv("GITHUB_TOKEN", "fake-gh-token")
        svc = _make_service(tmp_path)
        script = "import os; print(sorted(k for k in os.environ if 'TOKEN' in k))"
        req = ShellRunRequest(command=f'{Path(sys.executable).name} -c "{script}"')
        with (
            patch.object(SubprocessRunner, "build_argv", lambda _self, argv: argv),
            patch.dict("os.environ", {"PATH": str(Path(sys.executable).parent)}),
        ):
            svc._path = str(Path(sys.executable).parent)
            result = await svc.run_command(req)
        assert result.exit_code == 0, result.stderr
        assert result.stdout.strip() == "[]"

    @pytest.mark.asyncio
    async def test_req_env_allowlist_still_filters_before_the_secret_pass(
        self, tmp_path: Path
    ) -> None:
        svc = _make_service(tmp_path, env_allowlist=("KEEP_ME",))
        filtered = svc._filter_env(
            {"KEEP_ME": "1", "DROP_ME": "2", "GITHUB_TOKEN": "x"}
        )
        assert filtered == {"KEEP_ME": "1"}

    @pytest.mark.asyncio
    async def test_req_env_denylist_still_applies(self, tmp_path: Path) -> None:
        svc = _make_service(tmp_path, env_denylist=("LD_*",))
        assert svc._filter_env({"LD_PRELOAD": "x", "FOO": "1"}) == {"FOO": "1"}
