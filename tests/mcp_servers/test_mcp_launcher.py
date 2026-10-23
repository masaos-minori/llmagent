"""tests/mcp_servers/test_mcp_launcher.py — Static discovery and launch order of scripts/mcp_launcher.py."""

from __future__ import annotations

import os
import subprocess  # nosec B404 — fixed argv, no shell
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import mcp_launcher
import pytest

_SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"
_EXPECTED_KEYS = {
    "cicd",
    "file-delete",
    "file-read",
    "file-write",
    "git",
    "github",
    "mdq",
    "rag-pipeline",
    "shell",
    "web-search",
}


def test_static_scan_finds_the_ten_servers() -> None:
    registry = mcp_launcher.discover_server_metadata()
    assert set(registry) == _EXPECTED_KEYS
    shell = registry["shell"]
    assert shell.module == "mcp_servers.shell.shell_server"
    assert shell.class_name == "ShellMCPServer"
    assert shell.own_config_file == "shell_mcp_server.toml"
    assert shell.http_port == 8009


def test_list_imports_no_server_module() -> None:
    env = {key: os.environ[key] for key in ("PATH", "HOME") if key in os.environ}
    env["PYTHONPATH"] = str(_SCRIPTS)
    script = (
        "import sys, runpy\n"
        "sys.argv = ['mcp_launcher', '--list']\n"
        "runpy.run_path('scripts/mcp_launcher.py', run_name='__main__')\n"
        "bad = [m for m in sys.modules if m.startswith('mcp_servers.') and m.endswith('_server')]\n"
        "print('IMPORTED', bad)\n"
    )
    result = subprocess.run(  # nosec B603 — fixed argv, no shell
        [sys.executable, "-c", script],
        env=env,
        cwd=_SCRIPTS.parent,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    assert result.returncode == 0, result.stderr
    assert "IMPORTED []" in result.stdout


def test_launch_restricts_config_before_importing_only_the_chosen_module(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    order: list[str] = []
    instance = MagicMock()
    fake_cls = MagicMock(return_value=instance)
    fake_module = SimpleNamespace(ShellMCPServer=fake_cls)

    def _import(name: str) -> SimpleNamespace:
        order.append(f"import:{name}")
        return fake_module

    monkeypatch.setattr(sys, "argv", ["mcp_launcher", "shell"])
    with (
        patch.object(mcp_launcher, "port_is_responding", return_value=False),
        patch.object(
            mcp_launcher.ConfigLoader,
            "restrict_to",
            side_effect=lambda name: order.append(f"restrict:{name}"),
        ),
        patch.object(mcp_launcher.importlib, "import_module", side_effect=_import),
    ):
        mcp_launcher.main()
    assert order == [
        "restrict:shell_mcp_server.toml",
        "import:mcp_servers.shell.shell_server",
    ]
    instance.run_http.assert_called_once_with()


def test_unknown_key_exits_with_status_1(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", ["mcp_launcher", "nope"])
    with pytest.raises(SystemExit) as excinfo:
        mcp_launcher.main()
    assert excinfo.value.code == 1


def test_running_server_blocks_launch_unless_forced(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sys, "argv", ["mcp_launcher", "shell"])
    with (
        patch.object(mcp_launcher, "port_is_responding", return_value=True),
        pytest.raises(SystemExit) as excinfo,
    ):
        mcp_launcher.main()
    assert excinfo.value.code == 1
