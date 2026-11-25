"""tests/agent/services/test_config_pending_state.py

Pending contract for `PendingConfigState` (REQ-003, REQ-008, REQ-009, REQ-012; AC-2, AC-4, AC-5).

Every MCP case runs the real reload path against a live `RuntimeToolRegistry` and a
live lifecycle mock, so "nothing was applied" is an observed fact rather than a claim
about the report.  Cross-command survival is asserted the way `cmd_config.py` reaches
the state: a new service instance per command, one container.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest
from agent.services.config_field_registry import startup_only_for
from agent.services.config_pending_state import PendingConfigState, PendingMcpRecord
from agent.services.config_reload import ConfigReloadService
from agent.services.exceptions import ConfigReloadRollbackError
from agent.services.models import ConfigReloadRequest
from shared.config_undo import UndoToken
from shared.runtime_tool_registry import RuntimeToolRegistry

from tests.agent._config_test_defaults import (
    MIN_MCP_SERVERS,
    reload_fixture_ctx,
)
from tests.shared.runtime_tool_factory import build_fixture_runtime_tool

_ADDED_SERVER: dict[str, Any] = {
    "transport": "http",
    "url": "http://mcp.local:8101",
    "cmd": ["/opt/llm/bin/added_server"],
}
_SERVER_KEY = "fixture_server"


@pytest.fixture(autouse=True)
def prompt_source_env(tmp_path, monkeypatch) -> None:
    """Point the prompt reader at a temporary source for every test (row 15)."""
    manifest_dir = tmp_path / "manifests"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    (manifest_dir / "prompt_source.toml").write_text(
        'default = "fixture default prompt"\n', encoding="utf-8"
    )
    monkeypatch.setenv("LLMAGENT_REGISTRY_DIR", str(tmp_path))


def _live_registry() -> RuntimeToolRegistry:
    """Return a real registry, so a pending MCP change is checked against live tool state."""
    tool = build_fixture_runtime_tool(
        name="read_file",
        server_key=_SERVER_KEY,
        description="Read a file",
        input_schema={"type": "object"},
        status="active",
        is_write=False,
        agent_safety_tier="READ_ONLY",
        enabled_for_llm=True,
    )
    return RuntimeToolRegistry(
        tools={"read_file": tool}, allowed_servers=frozenset({_SERVER_KEY})
    )


def _reload_ctx() -> MagicMock:
    """Return a reload ctx whose container carries the real pending state and registry."""
    ctx = reload_fixture_ctx()
    services = ctx.services_required
    # `ctx.services` is the container `_pending_state()` reads; make both names the
    # same object the way a real AgentContext has them.
    ctx.services = services
    services.pending_config = PendingConfigState()
    services.runtime_tools = _live_registry()
    return ctx


def _mcp_payload(**servers: dict[str, Any]) -> dict[str, Any]:
    """Return an MCP payload that keeps the fixture server and adds the given ones."""
    return {"mcp_servers": {**MIN_MCP_SERVERS, **servers}}


def _reload(ctx: Any, payload: dict[str, Any]) -> Any:
    """Run one command's reload, as `cmd_config.py` does: a new service per command."""
    return ConfigReloadService(ctx).apply_config_dict(payload)


def _pending(ctx: Any) -> PendingConfigState:
    """Read the pending state through the container, the way the display commands do."""
    return ctx.services.pending_config


def _mcp_record(ctx: Any, server_key: str) -> PendingMcpRecord:
    """Return the one pending record the reload stored for ``server_key``."""
    matches = [
        record
        for record in _pending(ctx).pending_mcp_records()
        if record.server_key == server_key
    ]
    assert len(matches) == 1, [record.server_key for record in matches]
    return matches[0]


class TestPendingMcpRecords:
    """REQ-008, AC-4: an MCP definition change is recorded, never applied live."""

    def test_an_added_server_is_recorded_and_applies_nothing(self) -> None:
        ctx = _reload_ctx()
        before_mcp = ctx.cfg.mcp
        registry = ctx.services_required.runtime_tools
        before_tool = registry.get("read_file")

        outcome = _reload(ctx, _mcp_payload(added_server=_ADDED_SERVER))

        record = _mcp_record(ctx, "added_server")
        assert record.change == "added"
        assert record.field_paths == ("mcp_servers/added_server",)
        assert ctx.cfg.mcp is before_mcp
        assert "added_server" not in ctx.cfg.mcp.mcp_servers
        assert registry.get("read_file") == before_tool
        assert registry.resolve("read_file") == _SERVER_KEY
        assert "mcp" not in outcome.applied
        assert "mcp_servers/added_server (new server)" in outcome.needs_restart
        ctx.services_required.lifecycle.cleanup_server_resources.assert_not_called()

    def test_a_changed_definition_records_each_changed_field(self) -> None:
        ctx = _reload_ctx()
        servers = {
            **MIN_MCP_SERVERS,
            _SERVER_KEY: {
                **MIN_MCP_SERVERS[_SERVER_KEY],
                "url": "http://mcp.local:9999",
            },
        }

        outcome = _reload(ctx, {"mcp_servers": servers})

        record = _mcp_record(ctx, _SERVER_KEY)
        assert record.change == "changed"
        assert record.field_paths == (f"mcp_servers/{_SERVER_KEY}.url",)
        assert ctx.cfg.mcp.mcp_servers[_SERVER_KEY].url == "http://mcp.local:8100"
        assert "mcp" not in outcome.applied
        assert f"mcp_servers/{_SERVER_KEY}.url" in outcome.needs_restart

    def test_a_removed_server_is_recorded_without_a_lifecycle_call(self) -> None:
        ctx = _reload_ctx()

        outcome = _reload(ctx, {"mcp_servers": {"other_server": _ADDED_SERVER}})

        record = _mcp_record(ctx, _SERVER_KEY)
        assert record.change == "removed"
        assert record.field_paths == (f"mcp_servers/{_SERVER_KEY}",)
        assert _SERVER_KEY in ctx.cfg.mcp.mcp_servers
        assert "mcp" not in outcome.applied
        assert f"mcp_servers/{_SERVER_KEY} (removed server)" in outcome.needs_restart
        ctx.services_required.lifecycle.cleanup_server_resources.assert_not_called()

    def test_the_record_names_the_field_and_never_the_value(self) -> None:
        secret = "super-secret-token"
        ctx = _reload_ctx()
        servers = {
            **MIN_MCP_SERVERS,
            _SERVER_KEY: {**MIN_MCP_SERVERS[_SERVER_KEY], "auth_token": secret},
        }

        _reload(ctx, {"mcp_servers": servers})

        record = _mcp_record(ctx, _SERVER_KEY)
        assert record.field_paths == (f"mcp_servers/{_SERVER_KEY}.auth_token",)
        assert secret not in repr(record)

    def test_an_unchanged_definition_records_nothing(self) -> None:
        ctx = _reload_ctx()

        _reload(ctx, _mcp_payload())

        assert _pending(ctx).pending_mcp_records() == ()

    def test_the_live_registry_is_unchanged_by_a_pending_mcp_change(self) -> None:
        ctx = _reload_ctx()
        registry = ctx.services_required.runtime_tools
        before = [row["name"] for row in registry.llm_tool_definitions()]

        _reload(ctx, _mcp_payload(added_server=_ADDED_SERVER))

        assert [row["name"] for row in registry.llm_tool_definitions()] == before
        assert registry.resolve("read_file") == _SERVER_KEY


class TestPendingStartupOnlyFields:
    """REQ-003, AC-2: a startup-only field stays pending until a restart."""

    def test_set_startup_only_stores_the_registry_field_names(self) -> None:
        state = PendingConfigState()

        state.set_startup_only(startup_only_for("llm"))

        assert set(state.pending_startup_only()) == {
            entry.name for entry in startup_only_for("llm")
        }

    def test_a_startup_only_change_is_pending_and_never_applied(self) -> None:
        ctx = _reload_ctx()
        before = ctx.cfg.llm.context_char_limit

        outcome = _reload(ctx, {"context_char_limit": 1234})

        assert "context_char_limit" in outcome.startup_only
        assert "context_char_limit" in _pending(ctx).pending_startup_only()
        assert ctx.cfg.llm.context_char_limit == before
        assert "llm" not in outcome.applied

    def test_an_unchanged_field_records_nothing(self) -> None:
        ctx = _reload_ctx()

        _reload(ctx, {"llm_temperature": 0.4})

        assert _pending(ctx).pending_startup_only() == ()


class TestPendingSurvivesAcrossCommands:
    """REQ-009, AC-5: the pending view is container state, not one command's memory."""

    def test_a_record_from_one_command_is_visible_to_the_next(self) -> None:
        ctx = _reload_ctx()

        _reload(ctx, _mcp_payload(added_server=_ADDED_SERVER))
        second_command = ConfigReloadService(ctx)

        assert _mcp_record(ctx, "added_server").change == "added"
        assert any(
            record.server_key == "added_server"
            for record in second_command._pending_state().pending_mcp_records()
        )

    def test_the_same_pending_change_is_not_recorded_twice(self) -> None:
        ctx = _reload_ctx()
        payload = _mcp_payload(added_server=_ADDED_SERVER)

        _reload(ctx, payload)
        _reload(ctx, payload)

        records = [
            record
            for record in _pending(ctx).pending_mcp_records()
            if record.server_key == "added_server"
        ]
        assert len(records) == 1

    def test_a_field_the_payload_no_longer_changes_stops_being_pending(self) -> None:
        """The pending view is the last complete classification, not a history (AC-4).

        The first payload changed `url`; the second payload keeps `url` at the live
        value and changes `call_timeout_sec` instead.  The second reload classifies the
        whole candidate, so `url` stops being pending and only the field the config
        file still redefines is shown.
        """
        ctx = _reload_ctx()
        first = {
            **MIN_MCP_SERVERS,
            _SERVER_KEY: {
                **MIN_MCP_SERVERS[_SERVER_KEY],
                "url": "http://mcp.local:9001",
            },
        }
        second = {
            **MIN_MCP_SERVERS,
            _SERVER_KEY: {**MIN_MCP_SERVERS[_SERVER_KEY], "call_timeout_sec": 12.0},
        }

        _reload(ctx, {"mcp_servers": first})
        assert _mcp_record(ctx, _SERVER_KEY).field_paths == (
            f"mcp_servers/{_SERVER_KEY}.url",
        )

        _reload(ctx, {"mcp_servers": second})

        record = _mcp_record(ctx, _SERVER_KEY)
        assert record.change == "changed"
        assert record.field_paths == (f"mcp_servers/{_SERVER_KEY}.call_timeout_sec",)

    def test_several_changed_fields_of_one_server_are_one_record(self) -> None:
        """One server with two changed fields yields one record naming both, in registry order."""
        ctx = _reload_ctx()
        payload = {
            **MIN_MCP_SERVERS,
            _SERVER_KEY: {
                **MIN_MCP_SERVERS[_SERVER_KEY],
                "url": "http://mcp.local:9001",
                "call_timeout_sec": 12.0,
            },
        }

        _reload(ctx, {"mcp_servers": payload})

        record = _mcp_record(ctx, _SERVER_KEY)
        assert record.field_paths == (
            f"mcp_servers/{_SERVER_KEY}.url",
            f"mcp_servers/{_SERVER_KEY}.call_timeout_sec",
        )

    def test_a_fresh_state_is_empty(self) -> None:
        """A restart builds a new process, so the pending view starts empty."""
        state = PendingConfigState()

        assert state.pending_mcp_records() == ()
        assert state.pending_startup_only() == ()
        assert state.allow_reload() is True


class TestDegradedReloadGuard:
    """REQ-012, AC-5: a reload that degraded refuses the next reload, across commands."""

    def _degrade(self, ctx: Any, monkeypatch: pytest.MonkeyPatch) -> None:
        from agent.services import config_reload as reload_module
        from agent.services.config_reload_transaction import PreparedStep
        from agent.services.config_service_sync import ServiceSyncer

        def _apply_that_cannot_undo(_ctx: Any, candidate: Any) -> UndoToken:
            """Mirror apply_validated_section, with a restore that always fails."""
            setattr(_ctx.cfg, candidate.section_path, candidate.section)

            def restore() -> None:
                raise RuntimeError("restore failed")

            return UndoToken(
                service=candidate.section_path,
                field_paths=candidate.field_paths,
                restore=restore,
            )

        def _step_that_fails(self: ServiceSyncer) -> PreparedStep:
            def apply() -> UndoToken:
                raise RuntimeError("commit step failed")

            return PreparedStep(
                service="runtime_tools",
                field_paths=("tool.max_tool_turns",),
                apply=apply,
            )

        monkeypatch.setattr(
            reload_module, "apply_validated_section", _apply_that_cannot_undo
        )
        monkeypatch.setattr(ServiceSyncer, "prepare_runtime_tools", _step_that_fails)

        with pytest.raises(ConfigReloadRollbackError):
            _reload(ctx, {"max_tool_turns": 9})

    def test_record_degraded_makes_allow_reload_false(self) -> None:
        state = PendingConfigState()
        assert state.allow_reload() is True

        state.record_degraded(("conversation",))

        assert state.allow_reload() is False
        assert state.degraded_services() == ("conversation",)

    def test_the_next_command_is_refused_and_changes_nothing(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        ctx = _reload_ctx()
        self._degrade(ctx, monkeypatch)

        degraded_cfg = ctx.cfg
        degraded_tool = ctx.cfg.tool
        assert _pending(ctx).allow_reload() is False

        with pytest.raises(ConfigReloadRollbackError) as exc:
            _reload(ctx, {"max_tool_turns": 11})

        assert ctx.cfg is degraded_cfg
        assert ctx.cfg.tool is degraded_tool
        assert exc.value.service == "tool"

    def test_a_refused_reload_records_no_pending_change(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        ctx = _reload_ctx()
        self._degrade(ctx, monkeypatch)
        before = _pending(ctx).pending_mcp_records()

        with pytest.raises(ConfigReloadRollbackError):
            _reload(ctx, _mcp_payload(added_server=_ADDED_SERVER))

        assert _pending(ctx).pending_mcp_records() == before


class TestPendingStateIsNotConfiguration:
    """REQ-011: the pending view names fields; it is not a second source of values."""

    def test_a_pending_record_stores_no_value(self) -> None:
        state = PendingConfigState()

        state.set_startup_only(["context_char_limit"])

        assert state.pending_startup_only() == ("context_char_limit",)
        assert "1234" not in repr(state)

    def test_the_reload_request_shape_is_still_validated_at_construction(self) -> None:
        from agent.services.exceptions import ConfigReloadValidationError

        with pytest.raises(ConfigReloadValidationError):
            ConfigReloadRequest(mcp_servers="fixture_server")
