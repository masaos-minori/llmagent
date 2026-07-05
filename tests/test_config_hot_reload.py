"""tests/test_config_hot_reload.py
Tests for ConfigLoader.load_all() — reload scope and shadowing precedence.
"""

from __future__ import annotations

from pathlib import Path

from shared.config_loader import ConfigLoader


def _write_toml(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


class TestReloadScope:
    def test_reload_loads_agent_toml_content(self, tmp_path: Path) -> None:
        """load_all() loads agent.toml and makes all flat keys accessible."""
        _write_toml(
            tmp_path / "agent.toml",
            'security_profile = "local"\ntool_cache_ttl = 300\n',
        )

        cfg = ConfigLoader(config_dir=tmp_path).load_all()

        assert cfg.get("security_profile") == "local"
        assert cfg.get("tool_cache_ttl") == 300

    def test_reload_loads_mcp_servers_section(self, tmp_path: Path) -> None:
        """load_all() exposes [mcp_servers.*] entries from agent.toml."""
        _write_toml(
            tmp_path / "agent.toml",
            '[mcp_servers.shell]\nurl = "http://127.0.0.1:8009"\n',
        )

        cfg = ConfigLoader(config_dir=tmp_path).load_all()

        assert (
            cfg.get("mcp_servers", {}).get("shell", {}).get("url")
            == "http://127.0.0.1:8009"
        )
