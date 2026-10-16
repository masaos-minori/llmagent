"""Tests for check_command_contracts in tools/check_docs_consistency.py (GV-023)."""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

from agent.commands.command_defs import (
    ArgSpec,
    CommandDef,
    SubcommandSpec,
)

from tools import check_docs_consistency as mod

_REGISTRY = [
    CommandDef(
        name="/thing",
        prefix=True,
        is_async=False,
        handler="_cmd_thing",
        help="list|get",
        subcommands=[
            SubcommandSpec("list", "List", (ArgSpec("n", default="20"),)),
            SubcommandSpec("get", "Get", (ArgSpec("id", required=True),)),
        ],
    ),
    CommandDef(
        name="/skip",
        prefix=True,
        is_async=False,
        handler="_cmd_skip",
        help="x",
        args=(ArgSpec("a"),),
    ),
]


def _run(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, chapter: str) -> list[str]:
    agent_dir = tmp_path / mod.DOMAIN_SUBFOLDERS["agent"]
    agent_dir.mkdir(parents=True)
    (agent_dir / "agent_07_07_x.md").write_text(chapter, encoding="utf-8")
    monkeypatch.setattr(mod, "_load_registered_commands", lambda root: list(_REGISTRY))
    monkeypatch.setitem(mod._CONTRACT_EXEMPT_COMMANDS, "/skip", "TEST-001")
    return [i.message for i in mod.check_command_contracts(tmp_path, tmp_path)]


_GOOD = (
    "| Form | Effect |\n|---|---|\n"
    "| `/thing list [n]` | Lists (default 20) |\n"
    "| `/thing get <id>` | Gets |\n"
)


def test_matching_docs_pass(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    assert _run(tmp_path, monkeypatch, _GOOD) == []


def test_removed_subcommand_in_docs_is_reported(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    messages = _run(
        tmp_path, monkeypatch, _GOOD.replace("| `/thing get <id>` | Gets |\n", "")
    )
    assert any("`/thing get <id>` is not documented" in m for m in messages)


def test_added_documented_subcommand_is_reported(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    messages = _run(tmp_path, monkeypatch, _GOOD + "| `/thing purge` | Purges |\n")
    assert any("`/thing purge` is not a registered usage" in m for m in messages)


def test_renamed_argument_is_reported(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    messages = _run(tmp_path, monkeypatch, _GOOD.replace("<id>", "<key>"))
    assert any("`/thing get <key>` is not a registered usage" in m for m in messages)
    assert any("`/thing get <id>` is not documented" in m for m in messages)


def test_required_optional_change_is_reported(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    messages = _run(tmp_path, monkeypatch, _GOOD.replace("<id>", "[id]"))
    assert any("`/thing get [id]` is not a registered usage" in m for m in messages)


def test_changed_default_is_reported(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    messages = _run(tmp_path, monkeypatch, _GOOD.replace("default 20", "default 50"))
    assert any("default '20'" in m for m in messages)


def test_exempt_command_is_not_checked(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    assert _run(tmp_path, monkeypatch, _GOOD + "| `/skip whatever` | x |\n") == []


def test_live_agent_docs_match_the_registry() -> None:
    issues = mod.check_command_contracts(REPO_ROOT / "docs", REPO_ROOT)
    assert [i.message for i in issues] == []


def test_memory_command_is_not_exempt() -> None:
    assert "/memory" not in mod._CONTRACT_EXEMPT_COMMANDS
