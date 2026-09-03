"""tests/agent/test_startup_prompt_setup.py

Behavior-lock tests for agent/startup_prompt_setup.py: PromptSetup class.

Migrated from TestStartupOrchestratorSetupPrompt and TestStartupMemoryFailures
in tests/test_startup.py when _setup_prompt + _classify_memory_failure were
extracted to PromptSetup (REQ-006).
"""

from __future__ import annotations

import sqlite3
from unittest.mock import MagicMock, patch

import pytest
from agent.context import ConversationState
from agent.output_tags import OutputTag
from agent.startup_prompt_setup import PromptSetup

# ── Helpers ───────────────────────────────────────────────────────────────────


def _make_prompt_setup(
    memory=None,
    system_prompt_name="default",
    system_prompt_tool="Initial prompt",
    max_snippets=10,
    session_id="test-session",
    memory_disabled=False,
) -> tuple[PromptSetup, MagicMock, MagicMock]:
    """Return a PromptSetup with mocked ctx/view for setup_prompt() tests."""
    ctx = MagicMock()
    ctx.services_required.memory = memory
    ctx.conv = ConversationState()
    ctx.conv.system_prompt_name = system_prompt_name
    ctx.cfg.tool.system_prompts = {system_prompt_name: system_prompt_tool}
    ctx.cfg.agent_memory_max_startup_snippets = max_snippets
    ctx.session.session_id = session_id
    ctx.conv.memory_disabled = memory_disabled
    view = MagicMock()
    view.write_warning = MagicMock()
    ps = PromptSetup(ctx, view)
    return ps, ctx, view


# ── PromptSetup._classify_memory_failure ──────────────────────────────────────


class TestPromptSetupClassifyFailure:
    """Tests for PromptSetup._classify_memory_failure()."""

    def test_network_transient_classification(self) -> None:
        """ConnectionError should classify as NETWORK_TRANSIENT."""
        ps, _, _ = _make_prompt_setup()
        result = ps._classify_memory_failure(ConnectionError("refused"))
        assert result == "NETWORK_TRANSIENT"

    def test_database_or_io_classification(self) -> None:
        """sqlite3.Error should classify as DATABASE_OR_IO."""
        ps, _, _ = _make_prompt_setup()
        result = ps._classify_memory_failure(sqlite3.Error("disk error"))
        assert result == "DATABASE_OR_IO"

    def test_unknown_classification(self) -> None:
        """ValueError should classify as UNKNOWN."""
        ps, _, _ = _make_prompt_setup()
        result = ps._classify_memory_failure(ValueError("invalid value"))
        assert result == "UNKNOWN"

    def test_timeout_error_classified_as_network(self) -> None:
        """TimeoutError should classify as NETWORK_TRANSIENT."""
        ps, _, _ = _make_prompt_setup()
        result = ps._classify_memory_failure(TimeoutError("timeout"))
        assert result == "NETWORK_TRANSIENT"

    def test_os_error_classified_as_db_io(self) -> None:
        """OSError should classify as DATABASE_OR_IO."""
        ps, _, _ = _make_prompt_setup()
        result = ps._classify_memory_failure(OSError("no such file"))
        assert result == "DATABASE_OR_IO"


# ── PromptSetup.setup_prompt ──────────────────────────────────────────────────


class TestPromptSetupSetupPrompt:
    """Regression tests for PromptSetup.setup_prompt() — pinned notes must NOT be injected."""

    @pytest.mark.asyncio
    async def test_no_pinned_notes_block_injected(self) -> None:
        """[Pinned Notes] block must NOT appear in system prompt."""
        ps, ctx, _ = _make_prompt_setup(memory=None)

        await ps.setup_prompt()

        assert "[Pinned Notes]" not in ctx.conv.system_prompt_content
        assert ctx.conv.history == [{"role": "system", "content": "Initial prompt"}]

    @pytest.mark.asyncio
    async def test_memory_snippets_are_injected_when_enabled(self) -> None:
        """Memory snippets ARE injected when memory is enabled."""
        snippet = MagicMock()
        snippet.text = "test memory"
        mock_mem = MagicMock()
        mock_mem.on_session_start.return_value = [snippet]
        ps, ctx, _ = _make_prompt_setup(memory=mock_mem)

        await ps.setup_prompt()

        assert "--- USER MEMORY ---" in ctx.conv.system_prompt_content
        assert "test memory" in ctx.conv.system_prompt_content

    @pytest.mark.asyncio
    async def test_no_memory_injection_when_disabled(self) -> None:
        """System prompt is unchanged when memory is disabled."""
        ps, ctx, _ = _make_prompt_setup(memory=None)

        await ps.setup_prompt()

        assert "[Relevant memories]" not in ctx.conv.system_prompt_content
        assert ctx.conv.system_prompt_content == "Initial prompt"

    @pytest.mark.asyncio
    async def test_history_set_to_system_message(self) -> None:
        """conv.history is set to [system message] after setup_prompt."""
        ps, ctx, _ = _make_prompt_setup(memory=None)

        await ps.setup_prompt()

        assert len(ctx.conv.history) == 1
        assert ctx.conv.history[0] == {"role": "system", "content": "Initial prompt"}

    @pytest.mark.asyncio
    async def test_memory_snippets_truncated_when_exceeds_limit(self) -> None:
        """Memory snippets are truncated when exceeding the configured limit."""
        snippets = [MagicMock(text=f"memory {i}") for i in range(15)]
        mock_mem = MagicMock()
        mock_mem.on_session_start.return_value = snippets
        ps, ctx, _ = _make_prompt_setup(memory=mock_mem, max_snippets=10)

        await ps.setup_prompt()

        assert "--- USER MEMORY ---" in ctx.conv.system_prompt_content
        assert "memory 9" in ctx.conv.system_prompt_content
        assert "memory 10" not in ctx.conv.system_prompt_content

    @pytest.mark.asyncio
    async def test_memory_disabled_flag_on_failure(self) -> None:
        """ctx.conv.memory_disabled is set to True on failure."""
        mock_mem = MagicMock()
        mock_mem.on_session_start.side_effect = RuntimeError("fail")
        ps, ctx, view = _make_prompt_setup(memory=mock_mem)

        await ps.setup_prompt()

        assert ctx.conv.memory_disabled is True
        view.write_warning.assert_called_once()


# ── PromptSetup memory failure categorized logging ────────────────────────────


class TestPromptSetupMemoryFailures:
    """Tests for PromptSetup.setup_prompt() categorized logging on memory failure."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "exception_class, log_method, exception_msg, expected_log_prefix",
        [
            (sqlite3.Error, "error", "database error", "(DB/IO error)"),
            (ConnectionError, "warning", "connection refused", "(network transient)"),
            (ValueError, "info", "invalid value", "(unknown error)"),
        ],
    )
    async def test_memory_injection_categorized_logging(
        self, exception_class, log_method, exception_msg, expected_log_prefix
    ) -> None:
        mock_mem = MagicMock()
        mock_mem.on_session_start.side_effect = exception_class(exception_msg)
        ps, ctx, view = _make_prompt_setup(memory=mock_mem)

        with patch("shared.logger.Logger") as MockLogger:
            mock_logger_instance = MagicMock()
            MockLogger.return_value = mock_logger_instance
            await ps.setup_prompt()

        assert ctx.conv.memory_disabled is True

        # Verify correct log level was used based on the category
        log_func = getattr(mock_logger_instance, log_method)
        log_func.assert_called_once()

        # Check if message contains the expected part
        args, _ = log_func.call_args
        assert (
            f"Memory injection failed during startup {expected_log_prefix}" in args[0]
        )
        assert exception_msg in str(args[1]) if len(args) > 1 else ""

        # Verify view.write_warning was called
        view.write_warning.assert_called_once()
        warn_msg = str(view.write_warning.call_args[0][0])
        assert "Memory injection failed" in warn_msg
        assert exception_msg in warn_msg

    @pytest.mark.asyncio
    async def test_memory_failure_view_warning_contains_output_tag(self) -> None:
        """view.write_warning output contains OutputTag.NON_FATAL prefix."""
        mock_mem = MagicMock()
        mock_mem.on_session_start.side_effect = ConnectionError("refused")
        ps, ctx, view = _make_prompt_setup(memory=mock_mem)

        await ps.setup_prompt()

        warn_call = str(view.write_warning.call_args[0][0])
        assert OutputTag.NON_FATAL in warn_call
