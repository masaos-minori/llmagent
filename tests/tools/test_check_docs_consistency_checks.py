"""tests/tools/test_check_docs_consistency_checks.py

Tests for `check_tool_name_drift()` name-prefix handling and
`check_config_key_presence()` handling of keys that `DbConfig` defaults.
"""

from __future__ import annotations

from pathlib import Path

import pytest

import tools.check_docs_consistency as cdc
from tools.check_docs_consistency import (
    DocFile,
    check_config_key_presence,
    check_tool_name_drift,
)


def _mk_file(lines: list[str]) -> DocFile:
    return DocFile(path=Path("/fake/doc.md"), rel_path="doc.md", lines=lines)


def _repo_with_tool(tmp_path: Path, tool_name: str) -> Path:
    server = tmp_path / "scripts" / "mcp_servers" / "demo"
    server.mkdir(parents=True)
    (server / "svc.py").write_text(f'TOOL_LIST = [{{"name": "{tool_name}"}}]\n')
    return tmp_path


def test_tool_name_prefix_is_not_reported(tmp_path: Path) -> None:
    repo = _repo_with_tool(tmp_path, "demo_do_thing")
    doc = _mk_file(["**Tools:** All prefixed with `demo_`: `demo_do_thing`"])
    assert check_tool_name_drift(tmp_path, [doc], repo) == []


def test_unknown_tool_name_is_still_reported(tmp_path: Path) -> None:
    repo = _repo_with_tool(tmp_path, "demo_do_thing")
    doc = _mk_file(["**Tools:** `demo_missing_tool`"])
    issues = check_tool_name_drift(tmp_path, [doc], repo)
    assert len(issues) == 1
    assert "demo_missing_tool" in issues[0].message


@pytest.fixture()
def _repo_with_db_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    (tmp_path / "scripts" / "db").mkdir(parents=True)
    (tmp_path / "scripts" / "db" / "config.py").write_text(
        "class DbConfig:\n"
        "    rag_db_path: str\n"
        '    workflow_db_path: str = "/opt/llm/db/workflow.sqlite"\n'
    )
    toml = tmp_path / "agent.toml"
    toml.write_text('rag_db_path = "/opt/llm/db/rag.sqlite"\n')
    monkeypatch.setattr(cdc, "_AGENT_TOML", toml)
    return tmp_path


def test_defaulted_db_path_key_is_not_reported(_repo_with_db_config: Path) -> None:
    doc = _mk_file(["| `workflow.sqlite` | `workflow_db_path` |"])
    assert (
        check_config_key_presence(_repo_with_db_config, [doc], _repo_with_db_config)
        == []
    )


def test_configured_db_path_key_is_not_reported(_repo_with_db_config: Path) -> None:
    doc = _mk_file(["| `rag.sqlite` | `rag_db_path` |"])
    assert (
        check_config_key_presence(_repo_with_db_config, [doc], _repo_with_db_config)
        == []
    )


def test_undefaulted_unset_db_path_key_is_reported(_repo_with_db_config: Path) -> None:
    doc = _mk_file(["| `session.sqlite` | `session_db_path` |"])
    issues = check_config_key_presence(
        _repo_with_db_config, [doc], _repo_with_db_config
    )
    assert len(issues) == 1
    assert "session_db_path" in issues[0].message


def _command_repo(tmp_path: Path, commands: list[str]) -> Path:
    cmd_dir = tmp_path / "scripts" / "agent" / "commands"
    cmd_dir.mkdir(parents=True)
    body = "".join(f'    CommandDef(name="{c}", prefix=False),\n' for c in commands)
    (cmd_dir / "command_defs_list.py").write_text(f"_COMMANDS = [\n{body}]\n")
    return tmp_path


def _write_agent_docs(docs: Path, index_cmds: list[str], chapter_text: str) -> None:
    agent = docs / "23_agent"
    agent.mkdir(parents=True)
    rows = "".join(f"| `{c}` | purpose |\n" for c in index_cmds)
    (agent / "agent_07_03_registry.md").write_text(
        f"| Command | Purpose |\n|---|---|\n{rows}"
    )
    (agent / "agent_07_07_chapter.md").write_text(chapter_text)


def test_command_coverage_clean(tmp_path: Path) -> None:
    repo = _command_repo(tmp_path, ["/help", "/debug"])
    _write_agent_docs(
        tmp_path / "docs", ["/help", "/debug", "/exit"], "`/help` `/debug`\n"
    )
    assert cdc.check_command_coverage(tmp_path / "docs", repo) == []


def test_command_coverage_reports_missing_index_and_chapter(tmp_path: Path) -> None:
    repo = _command_repo(tmp_path, ["/help", "/audit"])
    _write_agent_docs(tmp_path / "docs", ["/help"], "`/help`\n")
    messages = [i.message for i in cdc.check_command_coverage(tmp_path / "docs", repo)]
    assert any("'/audit'" in m and "Built-in Command Index" in m for m in messages)
    assert any("'/audit'" in m and "per-command chapter" in m for m in messages)
    assert not any("'/help'" in m for m in messages)


def test_command_coverage_reports_unregistered_index_row(tmp_path: Path) -> None:
    repo = _command_repo(tmp_path, ["/help"])
    _write_agent_docs(tmp_path / "docs", ["/help", "/skill"], "`/help`\n")
    issues = cdc.check_command_coverage(tmp_path / "docs", repo)
    assert [i.severity for i in issues] == ["ERROR"]
    assert "'/skill'" in issues[0].message


def test_command_coverage_does_not_match_a_longer_command_name(tmp_path: Path) -> None:
    repo = _command_repo(tmp_path, ["/mem"])
    _write_agent_docs(tmp_path / "docs", ["/mem"], "`/memory`\n")
    messages = [i.message for i in cdc.check_command_coverage(tmp_path / "docs", repo)]
    assert any("per-command chapter" in m for m in messages)
