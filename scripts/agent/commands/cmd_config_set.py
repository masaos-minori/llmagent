#!/usr/bin/env python3
"""agent/commands/cmd_config_set.py
Runtime parameter override for _ConfigMixin.

Provides:
  _set_temperature    — parse and apply llm_temperature
  _set_max_tokens     — parse and apply llm_max_tokens
  _cmd_set            — /set: runtime LLM param override

Import from here:  from agent.commands.cmd_config_set import _ConfigSetMixin
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from agent.commands.mixin_base import MixinBase

if TYPE_CHECKING:
    from agent.context import AgentContext

logger = logging.getLogger(__name__)

MAX_TEMPERATURE = 2.0
SET_PARTS_COUNT = 2


class _ConfigSetMixin(MixinBase):
    """Runtime LLM parameter override for slash commands."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    def _set_temperature(self, ctx: AgentContext, value_str: str) -> None:
        """Parse and apply llm_temperature from value_str."""
        try:
            val = float(value_str)
            if not 0.0 <= val <= MAX_TEMPERATURE:
                raise ValueError
        except ValueError:
            self._out.write(f"temperature must be a float in [0.0, {MAX_TEMPERATURE}]")
            return
        ctx.cfg.llm.llm_temperature = val
        if ctx.services_required.llm is not None:
            ctx.services_required.llm.apply_config(temperature=val)
        logger.info("llm_temperature set to %s", val)
        self._out.write(f"temperature set to {val}")

    def _set_max_tokens(self, ctx: AgentContext, value_str: str) -> None:
        """Parse and apply llm_max_tokens from value_str."""
        try:
            val = int(value_str)
            if val < 1:
                raise ValueError
        except ValueError:
            self._out.write("max_tokens must be a positive integer")
            return
        ctx.cfg.llm.llm_max_tokens = val
        if ctx.services_required.llm is not None:
            ctx.services_required.llm.apply_config(max_tokens=val)
        logger.info("llm_max_tokens set to %s", val)
        self._out.write(f"max_tokens set to {val}")

    def _cmd_set(self, args: str) -> None:
        """Set a runtime LLM generation parameter.

        Usage:
          /set temperature <float>  LLM generation temperature (0.0–2.0)
          /set max_tokens <int>     Maximum tokens per LLM response (>=1)
        With no arguments, prints current values.
        """
        ctx = self._ctx
        parts = args.strip().split()
        if not parts:
            self._out.write(
                f"  temperature : {ctx.cfg.llm.llm_temperature}\n"
                f"  max_tokens  : {ctx.cfg.llm.llm_max_tokens}\n"
                "Use: /set temperature <float> | /set max_tokens <int>",
            )
            return
        if len(parts) != SET_PARTS_COUNT:
            self._out.write("Usage: /set temperature <float> | /set max_tokens <int>")
            return
        param, value_str = parts
        if param == "temperature":
            self._set_temperature(ctx, value_str)
        elif param == "max_tokens":
            self._set_max_tokens(ctx, value_str)
        else:
            self._out.write(f"Unknown parameter: {param!r}")
            self._out.write("Settable: temperature, max_tokens")
