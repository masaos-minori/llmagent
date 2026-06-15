#!/usr/bin/env python3
"""agent/commands/cmd_config.py
Configuration and statistics mixin for CommandRegistry.

Split into sub-modules for single-responsibility:
  cmd_config_stats   — _collect_stats, _cmd_stats
  cmd_config_display — all _print_* helpers, _cmd_config
  cmd_config_set     — _set_temperature, _set_max_tokens, _cmd_set

This file provides _ConfigMixin that inherits from all sub-mixins
and adds _cmd_reload (config reload at runtime).

Import from here:  from agent.commands.cmd_config import _ConfigMixin
"""

from __future__ import annotations

import logging

from agent.commands.cmd_config_display import _ConfigDisplayMixin  # noqa: E402
from agent.commands.cmd_config_set import _ConfigSetMixin  # noqa: E402
from agent.commands.cmd_config_stats import _ConfigStatsMixin  # noqa: E402

logger = logging.getLogger(__name__)


class _ConfigMixin(
    _ConfigStatsMixin,
    _ConfigDisplayMixin,
    _ConfigSetMixin,
):
    """Configuration and statistics slash-command handlers."""

    def _cmd_reload(self) -> None:
        """Reload config/agent.toml and apply runtime-configurable parameters.

        Updates ctx.cfg fields and syncs them to each component so changes
        take effect immediately without restarting the agent.
        """
        from agent.services.config_reload import (
            ConfigReloadService,  # noqa: PLC0415 — lazy: deferred to avoid import cost
        )

        try:
            from shared.config_loader import ConfigLoader

            new_cfg = ConfigLoader().load("common.toml", "agent.toml")
            result = ConfigReloadService(self._ctx).apply_config_dict(new_cfg)  
            logger.info("Config reloaded")
            if result.needs_restart:
                self._out.write(  
                    f"Restart required for: {', '.join(result.needs_restart)}"
                )
            self._out.write("Config reloaded.")  
        except OSError as e:
            logger.warning("Config reload I/O error: %s", e)
            self._out.write(f"Reload failed (I/O error): {e}")  
        except ValueError as e:
            logger.warning("Config reload failed: %s", e)
            self._out.write(f"Reload failed: {e}")  


__all__ = ["_ConfigMixin"]
