#!/usr/bin/env python3
"""scripts/agent/commands/cmd_debug.py

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
        """Initialize the debug mixin via MixinBase constructor."""
        super().__init__(*args, **kwargs)

    def _set_log_level(self, level: int, label: str, info_msg: str) -> None:
        """Set _DEBUG_LOGGER_NAMES loggers to level, then report label and log info_msg."""
        for name in _DEBUG_LOGGER_NAMES:
            logging.getLogger(name).setLevel(level)
        self._out.write(f"Log level: {label}")
        logger.info(info_msg)

    def _cmd_debug(self, args: str = "") -> None:
        """Toggle RAG debug output, or change log level with '/debug verbose|normal'."""
        ctx = self._ctx
        sub = args.strip().lower()

        if sub == "verbose":
            self._set_log_level(logging.DEBUG, "DEBUG", "Log level set to DEBUG")
            return

        if sub == "normal":
            self._set_log_level(logging.INFO, "INFO", "Log level restored to INFO")
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
