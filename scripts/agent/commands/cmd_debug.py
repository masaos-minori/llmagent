#!/usr/bin/env python3
"""agent/commands/cmd_debug.py
Debug-mode toggle mixin for CommandRegistry.

Provides _DebugMixin with:
  _cmd_debug  — /debug: toggle debug output, show audit log, change log level
"""

import logging
import pathlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agent.context import AgentContext

logger = logging.getLogger(__name__)


class _DebugMixin:
    """Debug-mode slash-command handlers."""

    if TYPE_CHECKING:
        _ctx: "AgentContext"

    def _cmd_debug(self, args: str = "") -> None:
        """Toggle RAG debug output, or show audit log tail with '/debug audit'."""
        ctx = self._ctx
        sub = args.strip().lower()

        if sub == "audit":
            # Show the last 20 lines of audit.log for quick troubleshooting
            audit_path = pathlib.Path(ctx.cfg.obs.audit_log_file)
            if not audit_path.exists():
                print(f"Audit log not found: {audit_path}")
                return
            try:
                lines = audit_path.read_text(encoding="utf-8").splitlines()
                for line in lines[-20:]:
                    print(line)
            except OSError as e:
                print(f"Cannot read audit log: {e}")
            return

        if sub == "verbose":
            # Switch agent logger to DEBUG level for detailed output
            logging.getLogger("agent_repl").setLevel(logging.DEBUG)
            logging.getLogger("orchestrator").setLevel(logging.DEBUG)
            print("Log level: DEBUG")
            logger.info("Log level set to DEBUG")
            return

        if sub == "normal":
            logging.getLogger("agent_repl").setLevel(logging.INFO)
            logging.getLogger("orchestrator").setLevel(logging.INFO)
            print("Log level: INFO")
            logger.info("Log level restored to INFO")
            return

        # Default: toggle RAG pipeline step debug output
        ctx.debug_mode = not ctx.debug_mode
        state = "ON" if ctx.debug_mode else "OFF"
        logger.info(f"Debug mode toggled: {state}")
        print(
            f"Debug mode: {state}  (use /debug audit | verbose | normal for more options)",
        )
