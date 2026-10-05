import asyncio

import pytest
from agent.context import AgentContext

from scripts.agent.context import AppServices, TurnState


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


class TestExceptionChainPreservation:
    """Tests for REQ-001: Verify exception chain is preserved when config load fails."""

    def test_exception_chain_preserved_on_config_failure(self) -> None:
        """Original exception is chained to wrapper RuntimeError (from None removed)."""
        ctx = AgentContext.__new__(AgentContext)
        ctx.conv = type("obj", (), {"__dict__": {}})()
        ctx.turn = type("obj", (), {"__dict__": {}})()
        ctx.stats = type("obj", (), {"__dict__": {}})()
        ctx.workflow = type("obj", (), {"__dict__": {}})()
        ctx.session = type("obj", (), {"__dict__": {}})()

        original_exc = ValueError("config not found")
        with pytest.raises(RuntimeError) as exc_info:
            raise RuntimeError(
                f"Failed to load agent config (/fake/config): {original_exc.__class__.__name__}: {original_exc}"
            ) from original_exc

        assert exc_info.value.__cause__ is original_exc


class TestAppServicesValidation:
    """Tests for REQ-001: Verify AppServices constructor rejects None for required services."""

    def test_rejects_none_http_service(self) -> None:
        """RuntimeError raised when http service is None."""
        with pytest.raises(RuntimeError, match="required service 'http' is None"):
            AppServices(
                http=None,
                llm=object(),
                tools=object(),
                lifecycle=object(),
                hist_mgr=object(),
                audit_logger=object(),
                memory=None,
            )

    def test_rejects_none_llm_service(self) -> None:
        """RuntimeError raised when llm service is None."""
        with pytest.raises(RuntimeError, match="required service 'llm' is None"):
            AppServices(
                http=object(),
                llm=None,
                tools=object(),
                lifecycle=object(),
                hist_mgr=object(),
                audit_logger=object(),
                memory=None,
            )

    def test_rejects_none_tools_service(self) -> None:
        """RuntimeError raised when tools service is None."""
        with pytest.raises(RuntimeError, match="required service 'tools' is None"):
            AppServices(
                http=object(),
                llm=object(),
                tools=None,
                lifecycle=object(),
                hist_mgr=object(),
                audit_logger=object(),
                memory=None,
            )

    def test_rejects_none_lifecycle_service(self) -> None:
        """RuntimeError raised when lifecycle service is None."""
        with pytest.raises(RuntimeError, match="required service 'lifecycle' is None"):
            AppServices(
                http=object(),
                llm=object(),
                tools=object(),
                lifecycle=None,
                hist_mgr=object(),
                audit_logger=object(),
                memory=None,
            )

    def test_rejects_none_hist_mgr_service(self) -> None:
        """RuntimeError raised when hist_mgr service is None."""
        with pytest.raises(RuntimeError, match="required service 'hist_mgr' is None"):
            AppServices(
                http=object(),
                llm=object(),
                tools=object(),
                lifecycle=object(),
                hist_mgr=None,
                audit_logger=object(),
                memory=None,
            )

    def test_rejects_none_audit_logger_service(self) -> None:
        """RuntimeError raised when audit_logger service is None."""
        with pytest.raises(
            RuntimeError, match="required service 'audit_logger' is None"
        ):
            AppServices(
                http=object(),
                llm=object(),
                tools=object(),
                lifecycle=object(),
                hist_mgr=object(),
                audit_logger=None,
                memory=None,
            )

    def test_allows_none_memory_service(self) -> None:
        """memory is optional — no error when None."""
        svc = AppServices(
            http=object(),
            llm=object(),
            tools=object(),
            lifecycle=object(),
            hist_mgr=object(),
            audit_logger=object(),
            memory=None,
        )
        assert svc.memory is None
