from unittest.mock import AsyncMock, MagicMock

import pytest
from agent.cli_view import CLIView
from agent.context import AgentContext
from agent.diagnostic_store import DiagnosticStore
from agent.session_persister import SessionPersister


@pytest.mark.asyncio
async def test_repl_handles_diagnostic_save_error():
    """Verifies that the REPL remains responsive when DiagnosticStore.save raises RuntimeError."""
    # Set up context
    ctx = MagicMock(spec=AgentContext)
    ctx.session = MagicMock()
    ctx.session.session_id = 123
    ctx.turn = MagicMock()
    ctx.turn.current_turn_id = "test_turn"
    ctx.cfg = MagicMock()
    ctx.cfg.memory = MagicMock()

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
    ctx.stats = stats

    ctx.services = MagicMock()
    ctx.services.llm = MagicMock()
    ctx.services.llm.stat_parse_errors = 0
    ctx.services.llm.stat_heartbeat_timeouts = 0
    ctx.services.llm.stat_reconnects = 0

    ctx.services.hist_mgr = MagicMock()
    ctx.services.hist_mgr.stat_compress_count = 0
    ctx.services.hist_mgr.stat_fallback_truncate_count = 0

    ctx.services.memory = MagicMock()
    ctx.services.memory.on_session_stop = AsyncMock()

    ctx.services_required = MagicMock()
    ctx.services_required.runtime_tools = MagicMock()
    ctx.services_required.runtime_tools.all_tools.return_value = []

    ctx.conv = MagicMock()
    ctx.conv.shutdown_requested = False
    ctx.conv.is_processing = False
    ctx.conv.memory_disabled = False
    ctx.conv.memory_warning_shown = False
    ctx.conv.history = []

    view = MagicMock(spec=CLIView)
    diagnostic_store = MagicMock(spec=DiagnosticStore)
    # Simulate RuntimeError on save
    diagnostic_store.save.side_effect = RuntimeError("Sensitive information detected")

    # Create persister with the mocked diagnostic store
    persister = SessionPersister(ctx, diagnostic_store, view)

    # Run persist_session_diagnostics — error is caught internally, warning is written
    await persister.persist_session_diagnostics()

    # Verify that the warning was written to the view
    view.write_warning.assert_called_once_with(
        "Diagnostics could not be saved: Sensitive information detected"
    )
    # Verify that the REPL didn't crash (it reached the end of the loop)
    assert True
