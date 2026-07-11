#!/usr/bin/env python3
"""agent/commands/cmd_tooling.py
Plan-mode mixin for CommandRegistry.

Provides _ToolingMixin with:
  _cmd_plan  — /plan: toggle plan mode
"""

import logging
from typing import Any

from agent.commands.mixin_base import MixinBase

logger = logging.getLogger(__name__)


class _ToolingMixin(MixinBase):
    """Plan-mode slash-command handler."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    def _cmd_plan(self) -> None:
        """Toggle plan mode. In plan mode, plan_blocked_tools are automatically blocked.

        This prevents destructive file operations from being executed while the agent
        is drafting a plan, guarding against accidental writes before the user has
        reviewed the proposal.
        """
        ctx = self._ctx
        ctx.conv.plan_mode = not ctx.conv.plan_mode
        state = "ON" if ctx.conv.plan_mode else "OFF"
        logger.info("Plan mode toggled: %s", state)
        self._out.write(f"Plan mode: {state}")
        if ctx.conv.plan_mode and ctx.cfg.tool.plan_blocked_tools:
            self._out.write("  Blocked tools:")
            for t in ctx.cfg.tool.plan_blocked_tools:
                self._out.write(f"    - {t}")
