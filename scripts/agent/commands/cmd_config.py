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
from typing import TYPE_CHECKING, Any

from shared.config_field_types import ConfigFieldTypeError  # noqa: E402

from agent.commands.cmd_config_display import _ConfigDisplayMixin  # noqa: E402
from agent.commands.cmd_config_stats import _ConfigStatsMixin  # noqa: E402
from agent.services.exceptions import ConfigReloadError  # noqa: E402

if TYPE_CHECKING:
    from agent.services.config_reload import ConfigReloadOutcome

logger = logging.getLogger(__name__)


def _reload_summary_line(result: ConfigReloadOutcome) -> str:
    """Return the one-line summary that matches what the reload reported.

    The wording is the existing CLI contract; only the stage line around it is new.
    """
    if not result.applied and not result.needs_restart and not result.always_live:
        if result.startup_only:
            return (
                "Config reloaded — startup-only settings cannot apply without restart"
            )
        return "No changes detected."
    if result.needs_restart:
        return "Config reloaded — some changes require restart"
    return "Config reloaded — all changes applied"


def _reload_error_lines(error: ConfigFieldTypeError) -> list[str]:
    """Render a config error from the stage and the field path it names, never a value.

    `ConfigFieldTypeError` carries the field path and the rule name, so the printed
    line is built from them.  A commit or rollback failure names a live service
    rather than a field and carries the stage the transaction reached, which is
    printed first so the reported stage matches the live state (REQ-005, REQ-011).
    """
    lines: list[str] = []
    if isinstance(error, ConfigReloadError) and error.stage:
        lines.append(f"Reload stage: {error.stage}")
    if error.field_path:
        lines.append(f"Reload failed: {error.field_path} [{error.rule}]: {error}")
    else:
        lines.append(f"Reload failed: {error}")
    return lines


class _ConfigMixin(
    _ConfigStatsMixin,
    _ConfigDisplayMixin,
):
    """Configuration and statistics slash-command handlers."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the config mixin via multiple inheritance constructors."""
        super().__init__(*args, **kwargs)

    def _cmd_reload(self) -> None:
        """Reload all config/*.toml files and apply runtime-configurable parameters.

        Updates ctx.cfg fields and syncs them to each component so changes
        take effect immediately without restarting the agent.

        Prints the stage the reload ended in first, then the applied list, then the
        pending list, so a startup-only change is visibly pending rather than reported
        as applied (REQ-005, REQ-009; AC-5).
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

            self._out.write(f"Reload stage: {result.stage}")
            self._out.write(_reload_summary_line(result))
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
            if result.always_live:
                self._write_item_list(
                    result.always_live, "LIVE (always effective)", "LIVE"
                )
            # The pending list is the container's state, not this command's report:
            # it names every startup-only field still waiting for the restart,
            # including one an earlier /reload recorded (REQ-009, AC-5).
            self._print_pending_config(self._ctx)
            logger.info(
                "Config reloaded: applied=%s, needs_restart=%s",
                result.applied,
                result.needs_restart,
            )
        except OSError as e:
            logger.warning("Config reload I/O error: %s", e)
            self._out.write(f"Reload failed (I/O error): {e}")
        except ConfigFieldTypeError as e:
            # `ConfigReloadError` and its subclasses are `ConfigFieldTypeError`
            # subclasses, so one catch covers a validator failure and a commit or
            # rollback failure with the same structured fields (REQ-011).
            logger.warning("Config reload failed: %s", e)
            for line in _reload_error_lines(e):
                self._out.write(line)
        except ValueError as e:
            logger.warning("Config reload failed: %s", e)
            self._out.write(f"Reload failed: {e}")


__all__ = ["_ConfigMixin"]
