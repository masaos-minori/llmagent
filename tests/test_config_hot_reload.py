"""tests/test_config_hot_reload.py
Tests for ConfigLoader.load_all() — reload scope and shadowing precedence.
"""

from __future__ import annotations

from pathlib import Path

from shared.config_loader import _BASE_CONFIG_FILES, ConfigLoader


def _write_toml(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


class TestReloadScope:
    def test_reload_includes_security_and_tools(self, tmp_path: Path) -> None:
        """load_all() merges all config files including security and tools sections."""
        # Write minimal versions of all required config files
        for name in _BASE_CONFIG_FILES:
            _write_toml(tmp_path / name, "")
        # Write actual content for security and tools files
        _write_toml(tmp_path / "security.toml", '[security]\nallow_list = ["tool_a"]\n')
        _write_toml(tmp_path / "tools.toml", "[tools]\nmax_tool_turns = 5\n")

        cfg = ConfigLoader(config_dir=tmp_path).load_all()

        assert cfg.get("security", {}).get("allow_list") == ["tool_a"]
        assert cfg.get("tools", {}).get("max_tool_turns") == 5

    def test_configuration_shadowing_precedence(self, tmp_path: Path) -> None:
        """Later config files shadow earlier ones when keys conflict."""
        for name in _BASE_CONFIG_FILES:
            _write_toml(tmp_path / name, "")
        # Write two files that define the same key; last one wins
        # (depends on _BASE_CONFIG_FILES ordering — use first and last files)
        first = _BASE_CONFIG_FILES[0]
        last = _BASE_CONFIG_FILES[-1]
        _write_toml(tmp_path / first, "[common]\nenv = 'base'\n")
        _write_toml(tmp_path / last, "[common]\nenv = 'override'\n")

        cfg = ConfigLoader(config_dir=tmp_path).load_all()

        assert cfg["common"]["env"] == "override"
