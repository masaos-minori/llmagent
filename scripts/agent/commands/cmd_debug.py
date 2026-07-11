#!/usr/bin/env python3
"""agent/commands/cmd_debug.py
Debug-mode toggle mixin for CommandRegistry.

Provides _DebugMixin with:
  _cmd_debug  — /debug: toggle debug output, change log level
"""

import logging
from typing import Any

from agent.commands.mixin_base import MixinBase

logger = logging.getLogger(__name__)

_DEBUG_LOGGER_NAMES = ("agent_repl", "orchestrator")


class _DebugMixin(MixinBase):
    """Debug-mode slash-command handlers."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    def _cmd_debug(self, args: str = "") -> None:
        """Toggle RAG debug output, or change log level with '/debug verbose|normal'."""
        ctx = self._ctx
        sub = args.strip().lower()

        if sub == "verbose":
            for name in _DEBUG_LOGGER_NAMES:
                logging.getLogger(name).setLevel(logging.DEBUG)
            self._out.write("Log level: DEBUG")
            logger.info("Log level set to DEBUG")
            return

        if sub == "normal":
            for name in _DEBUG_LOGGER_NAMES:
                logging.getLogger(name).setLevel(logging.INFO)
            self._out.write("Log level: INFO")
            logger.info("Log level restored to INFO")
            return

        # No subcommand — toggle RAG pipeline step debug output
        if not sub:
            ctx.conv.debug_mode = not ctx.conv.debug_mode
            state = "ON" if ctx.conv.debug_mode else "OFF"
            logger.info("Debug mode toggled: %s", state)
            self._out.write(
                f"Debug mode: {state}  (use /debug verbose | normal for log level control)",
            )
        else:
            # Unknown subcommand — reject explicitly
            self._out.write(f"Unknown subcommand: {sub}")
            self._out.write("Usage: /debug [verbose|normal]")
