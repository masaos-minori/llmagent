"""agent/commands/cmd_plugins.py
/plugin slash command: show plugin load status.
"""

from __future__ import annotations

from agent.commands.mixin_base import MixinBase


class _PluginsMixin(MixinBase):
    def _cmd_plugin(self, args: str = "") -> None:
        """Handle /plugin [status]."""
        from shared.plugin_registry import get_last_load_result  # noqa: PLC0415

        result = get_last_load_result()
        if result is None:
            self._out.write_no_data("Plugin registry not initialized")
            return

        rows = [
            ["Loaded", str(result.loaded_count)],
            ["Failed", str(len(result.failed))],
            ["Tool conflicts (shadowed)", str(result.tool_conflicts_shadowed)],
            ["Tool conflicts (allowed)", str(result.tool_conflicts_allowed)],
            ["Command shadows", str(result.command_shadows)],
        ]
        self._out.write_table(["Metric", "Count"], rows)
        if result.failed:
            self._out.write("Failed plugins:")
            for f in result.failed:
                self._out.write(f"  {f.path}: {f.error}")
