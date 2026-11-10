"""tests/agent/commands/test_agent_rag.py
Unit tests for the /debug verbose and normal subcommands.
"""

from __future__ import annotations

from unittest.mock import MagicMock

# ── _ToolingMixin._cmd_debug verbose/normal ───────────────────────────────────


class TestCmdDebugVerboseNormal:
    """_cmd_debug の verbose/normal サブコマンドのログレベル変更をテストする。"""

    def _make_mixin(self) -> object:
        from agent.commands.cmd_debug import _DebugMixin

        class Mixin(_DebugMixin):
            def __init__(self) -> None:
                self._ctx = MagicMock()
                self._ctx.cfg.rag_audit_log_path = ""
                self._ctx.conv.debug_mode = False

        return Mixin()

    def test_verbose_sets_debug_level(self) -> None:
        import logging
        from unittest.mock import patch

        mixin = self._make_mixin()
        with patch.object(logging, "getLogger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
            mixin._cmd_debug("verbose")  # type: ignore[attr-defined]

        # agent_repl と orchestrator の 2 つのロガーが DEBUG にセットされること
        calls = mock_get_logger.call_args_list
        names = [c.args[0] for c in calls]
        assert "agent_repl" in names
        assert "orchestrator" in names
        mock_logger.setLevel.assert_called_with(logging.DEBUG)

    def test_normal_sets_info_level(self) -> None:
        import logging
        from unittest.mock import patch

        mixin = self._make_mixin()
        with patch.object(logging, "getLogger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
            mixin._cmd_debug("normal")  # type: ignore[attr-defined]

        calls = mock_get_logger.call_args_list
        names = [c.args[0] for c in calls]
        assert "agent_repl" in names
        assert "orchestrator" in names
        mock_logger.setLevel.assert_called_with(logging.INFO)
