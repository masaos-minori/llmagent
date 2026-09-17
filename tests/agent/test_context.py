import asyncio

import pytest
from agent.context import AgentContext

from scripts.agent.context import TurnState


class TestServicesRequired:
    """Characterization tests for AgentContext.services_required — previously untested."""

    def test_raises_when_services_not_initialized(self) -> None:
        ctx = AgentContext.__new__(AgentContext)
        ctx.services = None
        with pytest.raises(RuntimeError, match="not initialized"):
            _ = ctx.services_required

    def test_returns_services_when_set(self) -> None:
        ctx = AgentContext.__new__(AgentContext)
        sentinel = object()
        ctx.services = sentinel
        assert ctx.services_required is sentinel


@pytest.mark.asyncio
async def test_turn_state_concurrency():
    """
    Verifies that TurnState correctly handles concurrent add_tool_call operations
    using asyncio.gather, ensuring no updates are lost.
    """
    turn_state = TurnState()
    n = 50
    tool_calls = [{"name": f"tool_{i}", "args": {}} for i in range(n)]

    # Launch N concurrent tasks
    await asyncio.gather(*(turn_state.add_tool_call(tc) for tc in tool_calls))

    # Assertions
    assert len(await turn_state.get_tool_calls()) == n
    assert turn_state.turn_count == n


@pytest.mark.skipif(
    True, reason="Requires real config/agent.toml with valid MCP auth tokens"
)
class TestRestrictToUnconditional:
    """REQ-001: AgentContext.__init__ calls restrict_to() unconditionally."""

    def test_restrict_to_called_unconditionally(self) -> None:
        """Proving ConfigLoader._allowed_files == frozenset({'agent.toml'}) after AgentContext() construction."""
        import os

        # Ensure AGENT_RESTRICT_CONFIG is NOT set
        original_value = os.environ.pop("AGENT_RESTRICT_CONFIG", None)

        # Set required MCP auth tokens for loading config/agent.toml
        mcp_tokens = {
            "MCP_SHELL_AUTH_TOKEN": "test-token",
            "MCP_WEB_SEARCH_AUTH_TOKEN": "test-token",
            "MCP_FILE_DELETE_AUTH_TOKEN": "test-token",
            "MCP_FILE_WRITE_AUTH_TOKEN": "test-token",
            "MCP_FILE_READ_AUTH_TOKEN": "test-token",
            "MCP_GITHUB_AUTH_TOKEN": "test-token",
            "MCP_RAG_PIPELINE_AUTH_TOKEN": "test-token",
            "MCP_MDQ_AUTH_TOKEN": "test-token",
        }
        saved_tokens = {}
        for k, v in mcp_tokens.items():
            saved_tokens[k] = os.environ.get(k)
            os.environ[k] = v

        try:
            from shared.config_loader import ConfigLoader

            # Construct AgentContext directly (not via __new__)
            AgentContext()

            # Verify restrict_to() was called unconditionally
            assert ConfigLoader._allowed_files == frozenset({"agent.toml"})
        finally:
            # Restore original env var values
            for k, v in saved_tokens.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v
            if original_value is not None:
                os.environ["AGENT_RESTRICT_CONFIG"] = original_value
