"""tests/test_mcp_server_cmd_paths.py

Regression guard: every subprocess-mode MCP server's cmd script path must
exist on disk. Added after config/agent.toml's cmd entries silently pointed
at server.py files deleted by an earlier MCP-server rename cleanup.
"""

from __future__ import annotations

from pathlib import Path

from agent.config_builders import build_agent_config
from shared.mcp_config import StartupMode

_REPO_SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
_DEPLOY_SCRIPTS_PREFIX = "/opt/llm/scripts/"


def _repo_relative_cmd_path(cmd: list[str]) -> Path:
    script_arg = cmd[-1]
    assert script_arg.startswith(_DEPLOY_SCRIPTS_PREFIX), (
        f"expected cmd's last element to start with {_DEPLOY_SCRIPTS_PREFIX!r}, got {script_arg!r}"
    )
    return _REPO_SCRIPTS_DIR / script_arg[len(_DEPLOY_SCRIPTS_PREFIX) :]


class TestSubprocessServerCmdPathsExist:
    def test_every_subprocess_cmd_script_exists(self) -> None:
        cfg = build_agent_config()
        subprocess_servers = {
            key: server_cfg
            for key, server_cfg in cfg.mcp.mcp_servers.items()
            if server_cfg.startup_mode == StartupMode.SUBPROCESS
        }
        assert subprocess_servers, (
            "expected at least one subprocess-mode MCP server in config"
        )

        missing = []
        for key, server_cfg in subprocess_servers.items():
            script_path = _repo_relative_cmd_path(server_cfg.cmd)
            if not script_path.is_file():
                missing.append(
                    f"mcp_servers.{key}: cmd script {script_path} does not exist"
                )

        assert not missing, "\n".join(missing)
