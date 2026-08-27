"""scripts/agent/commands/cmd_skill.py

/skill slash command: list skills or inject a skill's SKILL.md as ephemeral system context.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from agent.commands.mixin_base import MixinBase


class _SkillMixin(MixinBase):
    """Slash-command handler for skill listing (/skill)."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the skill mixin via MixinBase constructor."""
        super().__init__(*args, **kwargs)

    def _skills_dir(self) -> Path:
        """repo_root/skills — repo_root is 4 levels above this file."""
        return Path(__file__).resolve().parent.parent.parent.parent / "skills"

    async def _cmd_skill(self, args: str = "") -> None:
        """Handle /skill [name] [args]."""
        args = args.strip()
        if not args:
            for name in sorted(
                p.name for p in self._skills_dir().iterdir() if p.is_dir()
            ):
                self._out.write(name)
            return

        name, _, rest = args.partition(" ")
        skill_dir = self._skills_dir() / name
        if not skill_dir.is_dir():
            self._out.write(f"Unknown skill: {name}")
            return

        content = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
        rest = rest.strip()
        if rest:
            content = f"{content}\n\nInvocation args: {rest}"

        ctx = self._ctx
        ctx.conv.history = [
            m for m in ctx.conv.history if not m.get("_skill_ephemeral")
        ]
        # source="skill_mixin" only authorizes "_skill_ephemeral" in
        # TRUSTED_SOURCES (message_schema.py); "_ephemeral" is stripped by
        # append_message()'s sanitize-and-log fallback. With
        # Orchestrator._EPHEMERAL_KEYS extended to include "_skill_ephemeral",
        # the message is cleared by the orchestrator's generic ephemeral sweep
        # at the very next turn boundary, same as any other ephemeral message.
        # The file's own "_skill_ephemeral" filter on the next /skill
        # invocation remains harmless (no-op since the message was already
        # cleared). Do not restore "_ephemeral" for skill_mixin without review.
        await ctx.conv.append_message(
            {
                "role": "system",
                "content": content,
                "_ephemeral": True,
                "_skill_ephemeral": True,
            },
            source="skill_mixin",
        )
