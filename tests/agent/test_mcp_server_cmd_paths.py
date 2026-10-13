"""tests/test_mcp_server_cmd_paths.py

Regression guard: every subprocess-mode MCP server's cmd must point to a
valid target. Added after config/agent.toml's cmd entries silently pointed
at server.py files deleted by an earlier MCP-server rename cleanup.

With the Nuitka ``--onefile`` layout (row 13), subprocess servers launch the
compiled binary at ``/opt/llm/bin/mcp_<server>`` instead of a repo script via
``uv run``. Those binaries are build-host artifacts and do not exist in the
dev/test environment, so existence is verified by the binary naming convention
(``basename mcp_<server>``) rather than a filesystem check. The legacy
``--no-sync`` subprocess flag is obsolete for compiled binaries (sync is
managed internally) and is no longer asserted.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from agent.config_builders import build_agent_config
from shared.mcp_config import StartupMode

_REPO_SCRIPTS_DIR = Path(__file__).resolve().parent.parent.parent / "scripts"
_DEPLOY_SCRIPTS_PREFIX = "/opt/llm/scripts/"
_BINARY_DIR_PREFIX = "/opt/llm/bin/"


class TestSubprocessServerCmdPathsExist:
    def test_every_subprocess_cmd_points_to_valid_target(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # config/agent.toml's [mcp.mcp_servers.git]/[cicd] resolve auth_token
        # from the same MCP_GIT_AUTH_TOKEN/MCP_CICD_AUTH_TOKEN env vars that
        # tests/conftest.py deliberately defaults to "" for the *standalone*
        # git/cicd MCP server configs (many tests rely on that empty-token
        # accept-all behavior) — but McpServerConfig itself requires a
        # non-empty auth_token, so this test needs a real value of its own
        # rather than changing the shared conftest default.
        monkeypatch.setenv("MCP_GIT_AUTH_TOKEN", "test-token")
        monkeypatch.setenv("MCP_CICD_AUTH_TOKEN", "test-token")
        monkeypatch.setenv("MCP_WEB_SEARCH_AUTH_TOKEN", "test-token")
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
        mismatched = []
        unexpected = []
        for key, server_cfg in subprocess_servers.items():
            last = server_cfg.cmd[-1]
            path = Path(last)
            if str(path).startswith(_DEPLOY_SCRIPTS_PREFIX):
                # Legacy layout: repo script must exist on disk.
                if not path.is_file():
                    missing.append(
                        f"mcp_servers.{key}: cmd script {path} does not exist"
                    )
            elif str(path).startswith(_BINARY_DIR_PREFIX):
                # Nuitka --onefile layout: binary is a build-host artifact, so
                # verify the naming convention (basename mcp_<server>) rather
                # than a filesystem check that cannot pass in the dev env.
                expected = f"{_BINARY_DIR_PREFIX}mcp_{key}"
                if last != expected:
                    mismatched.append(
                        f"mcp_servers.{key}: cmd {last} does not match expected "
                        f"binary {expected}"
                    )
            else:
                unexpected.append(
                    f"mcp_servers.{key}: cmd {last} is neither a repo script nor "
                    f"a {_BINARY_DIR_PREFIX} binary"
                )

        assert not missing, "\n".join(missing)
        assert not mismatched, "\n".join(mismatched)
        assert not unexpected, "\n".join(unexpected)
