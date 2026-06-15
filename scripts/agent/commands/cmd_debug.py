#!/usr/bin/env python3
"""agent/commands/cmd_debug.py
Debug-mode toggle mixin for CommandRegistry.

Provides _DebugMixin with:
  _cmd_debug  — /debug: toggle debug output, show audit log, change log level
"""

import logging
import pathlib

from agent.commands.mixin_base import MixinBase

logger = logging.getLogger(__name__)

_AUDIT_TAIL_LINES = 20
_DEBUG_LOGGER_NAMES = ("agent_repl", "orchestrator")


class _DebugMixin(MixinBase):
    """Debug-mode slash-command handlers."""

    def _cmd_debug(self, args: str = "") -> None:
        """Toggle RAG debug output, or show audit log tail with '/debug audit'."""
        ctx = self._ctx
        sub = args.strip().lower()

        if sub == "audit":
            # Show the last 20 lines of audit.log for quick troubleshooting
            audit_path = pathlib.Path(ctx.cfg.obs.audit_log_file)
            if not audit_path.exists():
                self._out.write(f"Audit log not found: {audit_path}")
                return
            try:
                lines = audit_path.read_text(encoding="utf-8").splitlines()
                for line in lines[-_AUDIT_TAIL_LINES:]:
                    self._out.write(line)
            except OSError as e:
                self._out.write(f"Cannot read audit log: {e}")
            return

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

        # Default: toggle RAG pipeline step debug output
        ctx.conv.debug_mode = not ctx.conv.debug_mode
        state = "ON" if ctx.conv.debug_mode else "OFF"
        logger.info("Debug mode toggled: %s", state)
        self._out.write(
            f"Debug mode: {state}  (use /debug audit | verbose | normal for more options)",
        )
