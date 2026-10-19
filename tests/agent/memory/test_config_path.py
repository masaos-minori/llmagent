"""tests/agent/memory/test_config_path.py

Unit tests for ``resolve_memory_jsonl_dir()`` — the shared resolver that returns the
flat ``memory_jsonl_dir`` config path via the builder's default (REQ-001).
"""

from __future__ import annotations

from pathlib import Path

import pytest
from agent.memory.config_path import resolve_memory_jsonl_dir
from shared.config_loader import ConfigLoader


def _write_temp_agent_toml(tmp_path: Path, *, memory_jsonl_dir: str | None) -> None:
    """Write a minimal agent.toml into tmp_path with an optional memory_jsonl_dir."""
    body = (
        "" if memory_jsonl_dir is None else f'memory_jsonl_dir = "{memory_jsonl_dir}"\n'
    )
    (tmp_path / "agent.toml").write_text(body)


def test_resolves_flat_key_under_temp_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The resolver returns the flat-key path from an isolated temp config."""
    expected = str(tmp_path / "archive")
    _write_temp_agent_toml(tmp_path, memory_jsonl_dir=expected)
    monkeypatch.setattr(
        "shared.config_loader.resolve_config_dir",
        lambda config_dir=None: tmp_path,
    )
    monkeypatch.setattr(ConfigLoader, "_allowed_files", None)

    assert resolve_memory_jsonl_dir() == expected


def test_defaults_to_builder_default_when_unset(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An unset key resolves to the builder default ``/opt/llm/memory``."""
    _write_temp_agent_toml(tmp_path, memory_jsonl_dir=None)
    monkeypatch.setattr(
        "shared.config_loader.resolve_config_dir",
        lambda config_dir=None: tmp_path,
    )
    monkeypatch.setattr(ConfigLoader, "_allowed_files", None)

    assert resolve_memory_jsonl_dir() == "/opt/llm/memory"
