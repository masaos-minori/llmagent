import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from agent.cli_view import CLIView
from agent.context import AgentContext
from agent.repl import AgentREPL


@pytest.mark.asyncio
async def test_repl_handles_diagnostic_save_error():
    """Verifies that the REPL remains responsive when DiagnosticStore.save raises RuntimeError."""
    repl = AgentREPL()

    # Mocking dependencies
    repl._ctx = MagicMock(spec=AgentContext)
    repl._ctx.session = MagicMock()
    repl._ctx.session.session_id = 123
    repl._ctx.turn = MagicMock()
    repl._ctx.turn.current_turn_id = "test_turn"

    # Config mocking
    repl._ctx.cfg = MagicMock()
    repl._ctx.cfg.memory = MagicMock()

    # Stats must be primitives for JSON serialization
    stats = MagicMock()
    stats.stat_turns = 1
    stats.stat_tool_calls = 1
    stats.stat_tool_errors = 0
    stats.stat_partial_completions = 0
    stats.stat_semantic_cache_hits = 0
    stats.stat_input_tokens = 10
    stats.stat_output_tokens = 20
    stats.stat_heartbeat_timeouts = 0
    stats.stat_reconnects = 0
    stats.stat_latency = {}
    repl._ctx.stats = stats

    # Services mocking
    repl._ctx.services = MagicMock()
    repl._ctx.services.llm = MagicMock()
    repl._ctx.services.llm.stat_parse_errors = 0
    repl._ctx.services.llm.stat_heartbeat_timeouts = 0
    repl._ctx.services.llm.stat_reconnects = 0

    repl._ctx.services.hist_mgr = MagicMock()
    repl._ctx.services.hist_mgr.stat_compress_count = 0
    repl._ctx.services.hist_mgr.stat_fallback_truncate_count = 0

    repl._ctx.services.memory = MagicMock()
    repl._ctx.services.memory.on_session_stop = AsyncMock()

    repl._ctx.conv = MagicMock()
    repl._ctx.conv.shutdown_requested = False
    repl._ctx.conv.is_processing = False
    repl._ctx.conv.memory_disabled = False
    repl._ctx.conv.memory_warning_shown = False
    repl._ctx.conv.history = []

    repl._view = MagicMock(spec=CLIView)
    repl._diagnostic_store = MagicMock()
    # Simulate RuntimeError on save
    repl._diagnostic_store.save.side_effect = RuntimeError(
        "Sensitive information detected"
    )

    # Initialize mandatory components to avoid "called before _init_components"
    repl._cmds = MagicMock()
    repl._orchestrator = MagicMock()

    # We also need to mock the loop control
    repl._shutdown_event = asyncio.Event()

    # Mock input to exit immediately
    with patch("builtins.input", return_value="/exit"):
        await repl._run_repl_loop()

    # Verify that the warning was written to the view
    repl._view.write_warning.assert_any_call(
        "Diagnostics could not be saved: Sensitive information detected"
    )
    # Verify that the REPL didn't crash (it reached the end of the loop)
    assert True
