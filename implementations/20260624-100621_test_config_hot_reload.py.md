# Implementation and Test Procedure: tests/test_config_hot_reload.py

## Goal

Create `tests/test_config_hot_reload.py` with two tests:
1. `test_reload_includes_security_and_tools` — verify `/reload` loads all 12 config files including security and tools sections
2. `test_configuration_shadowing_precedence` — verify that user-level config keys shadow base config keys

## Scope

**In:**
- New file `tests/test_config_hot_reload.py`

**Out:**
- Modifying `shared/config_loader.py` (already implemented — `load_all()` exists at line 51)
- Modifying `cmd_config.py` (already implemented — `_cmd_reload()` calls `ConfigLoader().load_all()`)

## Assumptions

1. `ConfigLoader().load_all()` is already implemented and loads all 12 files in `_BASE_CONFIG_FILES`.
2. `_BASE_CONFIG_FILES` is importable from `shared.config_loader`.
3. Tests use `tmp_path` fixture for isolated config dir.
4. `ConfigLoader(config_dir=Path(...))` accepts a custom config directory.
5. Security-related and tool-related config sections are present in the config file list.

## Implementation

### Target file
`tests/test_config_hot_reload.py`

### Procedure
Create a new test file with two test functions using `tmp_path` to create minimal TOML config files.

### Method
Use `pytest`'s `tmp_path` fixture. Write minimal TOML files. Call `ConfigLoader(config_dir=tmp_path).load_all()`. Assert the merged dict contains expected keys.

### Details

```python
"""tests/test_config_hot_reload.py
Tests for ConfigLoader.load_all() — reload scope and shadowing precedence.
"""
from __future__ import annotations
from pathlib import Path
import pytest
from shared.config_loader import ConfigLoader, _BASE_CONFIG_FILES


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
        _write_toml(tmp_path / "tools.toml", '[tools]\nmax_tool_turns = 5\n')

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
        _write_toml(tmp_path / last,  "[common]\nenv = 'override'\n")

        cfg = ConfigLoader(config_dir=tmp_path).load_all()

        assert cfg["common"]["env"] == "override"
```

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Tests pass | `uv run pytest tests/test_config_hot_reload.py -v` | all pass |
| Lint | `uv run ruff check tests/test_config_hot_reload.py` | 0 errors |
