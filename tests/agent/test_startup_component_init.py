"""tests/agent/test_startup_component_init.py

Behavior-lock tests for ComponentInitializer leaked-client cleanup: on a failure
before ctx.services is assigned, the httpx client exposed by the factory is
closed (aclose) before the original exception re-raises.
"""

from __future__ import annotations

import logging
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from agent.startup import StartupInterrupted
from agent.startup_component_init import ComponentInitializer

_UNSET: object = object()


class TestExposedClientCleanup:
    """initialize() closes the exposed client on a pre-assignment failure."""

    def _make_initializer(self, *, services: object = _UNSET) -> ComponentInitializer:
        ctx = MagicMock()
        if services is not _UNSET:
            ctx.services = services
        view = MagicMock()
        return ComponentInitializer(ctx, view)

    def _fake_factory(
        self,
        *,
        raise_after: BaseException | None = None,
        set_services: object | None = None,
        aclose_side_effect: object | None = None,
    ) -> tuple[object, dict]:
        """Replacement for build_agent_context.

        Records the on_client_created kwarg, invokes it with a stub client whose
        aclose is an AsyncMock when present, optionally assigns ctx.services, and
        optionally raises after the hook. Returns (fake, record).
        """
        record: dict = {}

        def fake(ctx: object, view: object, *, on_client_created=None) -> None:
            record["on_client_created"] = on_client_created
            if set_services is not None:
                ctx.services = set_services
            if on_client_created is not None:
                client = MagicMock()
                client.aclose = AsyncMock(side_effect=aclose_side_effect)
                record["client"] = client
                record["aclose"] = client.aclose
                on_client_created(client)
            if raise_after is not None:
                raise raise_after

        return fake, record

    @pytest.mark.asyncio
    async def test_pre_assignment_failure_closes_exposed_client(
        self,
    ) -> None:
        init = self._make_initializer(services=None)
        error = RuntimeError("builder failed")
        fake, record = self._fake_factory(raise_after=error)
        with patch(
            "agent.startup_component_init.build_agent_context", side_effect=fake
        ):
            with pytest.raises(RuntimeError) as exc_info:
                await init.initialize()
        assert exc_info.value is error
        assert record["on_client_created"].__func__ is (
            ComponentInitializer._on_client_created
        )
        assert record["aclose"].await_count == 1

    @pytest.mark.asyncio
    async def test_aclose_failure_does_not_mask_original(
        self, caplog: pytest.LogCaptureFixture, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        init = self._make_initializer(services=None)
        fake, record = self._fake_factory(
            raise_after=RuntimeError("builder failed"),
            aclose_side_effect=RuntimeError("close failed"),
        )
        # The module Logger sets propagate=False; allow caplog's root handler to
        # observe the contained warning during this test.
        import agent.startup_component_init as sci

        monkeypatch.setattr(sci.logger._logger, "propagate", True)
        with caplog.at_level(logging.WARNING, logger="agent.startup_component_init"):
            with patch(
                "agent.startup_component_init.build_agent_context",
                side_effect=fake,
            ):
                with pytest.raises(RuntimeError, match="builder failed"):
                    await init.initialize()
        assert "Failed to close the httpx client" in caplog.text

    @pytest.mark.asyncio
    async def test_base_exception_re_raised_after_close(
        self,
    ) -> None:
        init = self._make_initializer(services=None)
        fake, record = self._fake_factory(raise_after=StartupInterrupted("interrupted"))
        with patch(
            "agent.startup_component_init.build_agent_context", side_effect=fake
        ):
            with pytest.raises(StartupInterrupted):
                await init.initialize()
        assert record["aclose"].await_count == 1

    @pytest.mark.asyncio
    async def test_post_assignment_failure_closes_nothing(
        self,
    ) -> None:
        sentinel = object()
        init = self._make_initializer()
        fake, record = self._fake_factory(set_services=sentinel)
        with patch(
            "agent.startup_component_init.build_agent_context", side_effect=fake
        ):
            with patch.object(
                init,
                "_init_command_registry",
                side_effect=RuntimeError("registry failed"),
            ):
                with pytest.raises(RuntimeError, match="registry failed"):
                    await init.initialize()
        assert record["aclose"].await_count == 0

    @pytest.mark.asyncio
    async def test_success_closes_nothing(self) -> None:
        sentinel = object()
        init = self._make_initializer()
        fake, record = self._fake_factory(set_services=sentinel)
        with patch(
            "agent.startup_component_init.build_agent_context", side_effect=fake
        ):
            with (
                patch.object(
                    init,
                    "_init_command_registry",
                    side_effect=lambda: setattr(init, "_cmds", MagicMock()),
                ),
                patch.object(
                    init,
                    "_init_orchestrator",
                    side_effect=lambda: setattr(init, "_orchestrator", MagicMock()),
                ),
                patch.object(init, "_check_workflow_definition"),
                patch.object(init, "_check_workflow_schema"),
                patch(
                    "shared.llm_client.build_llm_url",
                    return_value="http://localhost:8080",
                ),
            ):
                await init.initialize()
        assert record["aclose"].await_count == 0
