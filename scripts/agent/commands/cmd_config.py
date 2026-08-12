#!/usr/bin/env python3
"""scripts/agent/commands/cmd_config.py

Configuration and statistics mixin for CommandRegistry.

Split into sub-modules for single-responsibility:
  cmd_config_stats   — _collect_stats, _cmd_stats
  cmd_config_display — all _print_* helpers, _cmd_config

This file provides _ConfigMixin that inherits from all sub-mixins
and adds _cmd_reload (config reload at runtime).

Import from here:  from agent.commands.cmd_config import _ConfigMixin
"""

from __future__ import annotations

import logging
from typing import Any

from agent.commands.cmd_config_display import _ConfigDisplayMixin  # noqa: E402
from agent.commands.cmd_config_stats import _ConfigStatsMixin  # noqa: E402

logger = logging.getLogger(__name__)


class _ConfigMixin(
    _ConfigStatsMixin,
    _ConfigDisplayMixin,
):
    """Configuration and statistics slash-command handlers."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the config mixin via multiple inheritance constructors."""
        super().__init__(*args, **kwargs)

    def _write_item_list(self, items: list[str], header: str, item_label: str) -> None:
        """Write '<header>: [N items]' followed by one '  [item_label] - <item>' per item."""
        self._out.write(f"{header}: [{len(items)} items]")
        for item in items:
            self._out.write(f"  [{item_label}] - {item}")

    def _cmd_reload(self) -> None:
        """Reload all config/*.toml files and apply runtime-configurable parameters.

        Updates ctx.cfg fields and syncs them to each component so changes
        take effect immediately without restarting the agent.
        """
        from agent.services.config_reload import (
            ConfigReloadService,  # lazy: deferred to avoid import cost
        )

        try:
            from shared.config_loader import (
                _BASE_CONFIG_FILES,
                ConfigLoader,
            )

            new_cfg = ConfigLoader().load_all()
            result = ConfigReloadService(self._ctx).apply_config_dict(new_cfg)
            result.source_files = list(_BASE_CONFIG_FILES)

            if not result.applied and not result.needs_restart:
                if result.startup_only:
                    self._out.write(
                        "Config reloaded — startup-only settings cannot apply without restart"
                    )
                else:
                    self._out.write("No changes detected.")
            elif result.needs_restart:
                self._out.write("Config reloaded — some changes require restart")
            else:
                self._out.write("Config reloaded — all changes applied")
            if result.needs_restart:
                self._out.write(
                    "WARNING: Some settings require restart to take effect."
                )
                self._write_item_list(
                    result.needs_restart, "Restart required", "RESTART"
                )
            if result.applied:
                self._write_item_list(result.applied, "Applied (runtime)", "OK")
            if result.skipped:
                self._write_item_list(result.skipped, "Skipped", "SKIP")
            if result.startup_only:
                self._write_item_list(
                    result.startup_only, "Startup-only (ignored)", "STARTUP-ONLY"
                )
            logger.info(
                "Config reloaded: applied=%s, needs_restart=%s",
                result.applied,
                result.needs_restart,
            )
        except OSError as e:
            logger.warning("Config reload I/O error: %s", e)
            self._out.write(f"Reload failed (I/O error): {e}")
        except ValueError as e:
            logger.warning("Config reload failed: %s", e)
            self._out.write(f"Reload failed: {e}")


__all__ = ["_ConfigMixin"]
