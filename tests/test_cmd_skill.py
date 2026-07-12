"""tests/test_cmd_skill.py
Tests for /skill command handler in cmd_skill.py.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from agent.commands.cmd_skill import _SkillMixin
from agent.commands.output_port import CliOutputPort


@pytest.fixture
def skills_root(tmp_path: Path) -> Path:
    (tmp_path / "alpha").mkdir()
    (tmp_path / "alpha" / "SKILL.md").write_text("Alpha content", encoding="utf-8")
    (tmp_path / "beta").mkdir()
    (tmp_path / "beta" / "SKILL.md").write_text("Beta content", encoding="utf-8")
    (tmp_path / "DESIGN.md").write_text("not a skill dir", encoding="utf-8")
    return tmp_path


def _make_mixin(skills_root: Path) -> _SkillMixin:
    mixin = object.__new__(_SkillMixin)
    mixin._out = MagicMock(spec=CliOutputPort)
    mixin._ctx = SimpleNamespace(conv=SimpleNamespace(history=[]))
    mixin._skills_dir = MagicMock(return_value=skills_root)
    return mixin


class TestSkillsDirResolution:
    def test_resolves_to_repo_root_skills(self) -> None:
        mixin = object.__new__(_SkillMixin)
        resolved = mixin._skills_dir()
        assert resolved.name == "skills"
        assert resolved.is_dir()
        assert (resolved / "python-implementation" / "SKILL.md").is_file()


class TestCmdSkillList:
    def test_no_args_lists_directories_only(self, skills_root: Path) -> None:
        mixin = _make_mixin(skills_root)
        mixin._cmd_skill("")
        written = [c.args[0] for c in mixin._out.write.call_args_list]
        assert written == ["alpha", "beta"]  # DESIGN.md excluded, sorted

    def test_list_does_not_touch_history(self, skills_root: Path) -> None:
        mixin = _make_mixin(skills_root)
        mixin._cmd_skill("")
        assert mixin._ctx.conv.history == []


class TestCmdSkillLoad:
    def test_unknown_skill_writes_error_no_history_mutation(
        self, skills_root: Path
    ) -> None:
        mixin = _make_mixin(skills_root)
        mixin._cmd_skill("nonexistent")
        mixin._out.write.assert_called_once_with("Unknown skill: nonexistent")
        assert mixin._ctx.conv.history == []

    def test_file_entry_treated_as_unknown(self, skills_root: Path) -> None:
        mixin = _make_mixin(skills_root)
        mixin._cmd_skill("DESIGN")
        mixin._out.write.assert_called_once_with("Unknown skill: DESIGN")
        assert mixin._ctx.conv.history == []

    def test_known_skill_appends_ephemeral_message(self, skills_root: Path) -> None:
        mixin = _make_mixin(skills_root)
        mixin._cmd_skill("alpha")
        assert len(mixin._ctx.conv.history) == 1
        msg = mixin._ctx.conv.history[0]
        assert msg["role"] == "system"
        assert msg["content"] == "Alpha content"
        assert msg["_ephemeral"] is True
        assert msg["_skill_ephemeral"] is True

    def test_args_appended_to_content(self, skills_root: Path) -> None:
        mixin = _make_mixin(skills_root)
        mixin._cmd_skill("alpha extra context")
        msg = mixin._ctx.conv.history[0]
        assert "Invocation args: extra context" in msg["content"]

    def test_repeated_call_replaces_previous_skill_message(
        self, skills_root: Path
    ) -> None:
        mixin = _make_mixin(skills_root)
        mixin._cmd_skill("alpha")
        mixin._cmd_skill("beta")
        assert len(mixin._ctx.conv.history) == 1
        assert mixin._ctx.conv.history[0]["content"] == "Beta content"

    def test_unrelated_ephemeral_messages_are_preserved(
        self, skills_root: Path
    ) -> None:
        mixin = _make_mixin(skills_root)
        mixin._ctx.conv.history.append(
            {"role": "system", "content": "mode hint", "_ephemeral": True}
        )
        mixin._ctx.conv.history.append(
            {"role": "system", "content": "memory", "_memory_injected": True}
        )
        mixin._cmd_skill("alpha")
        assert len(mixin._ctx.conv.history) == 3
        contents = [m["content"] for m in mixin._ctx.conv.history]
        assert "mode hint" in contents
        assert "memory" in contents
        assert "Alpha content" in contents
