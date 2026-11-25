"""tests/agent/services/test_config_reload_transaction.py

Rollback contract for `ReloadTransaction` (REQ-005, REQ-006, REQ-007, REQ-012; AC-3, AC-5).

Every case drives the transaction through `PreparedStep` objects and asserts the
order of apply and restore calls, so the reverse-order guarantee is visible rather
than inferred.  No case asserts message wording; row 38 owns the CLI text.
"""

from __future__ import annotations

from typing import Any, cast
from unittest.mock import MagicMock

import httpx
import pytest
from agent.history import HistoryManager
from agent.history_selection_policy import HistorySelectionPolicy
from agent.services.config_reload_transaction import (
    CommitPhase,
    PreparedStep,
    ReloadStage,
    ReloadTransaction,
)
from agent.services.exceptions import (
    ConfigReloadCommitError,
    ConfigReloadRollbackError,
    ConfigReloadValidationError,
)
from agent.services.models import ConfigReloadRequest
from shared.config_field_types import ConfigFieldTypeError
from shared.config_undo import ServiceSnapshot, UndoToken
from shared.llm_hot_config import LlmHotConfigHandler
from shared.runtime_tool_registry import RuntimeToolRegistry

from tests.agent._config_test_defaults import reload_candidate, reload_fixture_ctx
from tests.shared.runtime_tool_factory import build_fixture_runtime_tool

# The commit order the transaction enforces, and the service name each phase owns.
_COMMIT_ORDER: tuple[tuple[CommitPhase, str], ...] = (
    (CommitPhase.SECTIONS, "tool"),
    (CommitPhase.CONVERSATION, "conversation"),
    (CommitPhase.RUNTIME_TOOLS, "runtime_tools"),
    (CommitPhase.HISTORY, "history"),
    (CommitPhase.LLM_CONFIG, "llm"),
)


@pytest.fixture(autouse=True)
def prompt_source_env(tmp_path: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    """Point the prompt reader at a temporary source for every test (row 15).

    The reload path reads prompt content through ``agent.prompt_source``; tests
    must not depend on the committed ``registry/manifests/prompt_source.toml``.
    """
    manifest_dir = tmp_path / "manifests"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    (manifest_dir / "prompt_source.toml").write_text(
        'default = "fixture default prompt"\n', encoding="utf-8"
    )
    monkeypatch.setenv("LLMAGENT_REGISTRY_DIR", str(tmp_path))


class _RecordedService:
    """Minimal live service that records every apply and restore into one shared log.

    Attributes:
        log: Shared list every service writes to, so one assertion shows the global
            order of apply and restore calls.
        restore_fails: Makes this service's restore raise, which is how the
            `degraded` path is produced.
    """

    def __init__(
        self,
        name: str,
        log: list[str],
        *,
        value: int = 0,
        restore_fails: bool = False,
    ) -> None:
        self.name = name
        self.log = log
        self.value = value
        self._restore_fails = restore_fails

    def snapshot(self) -> ServiceSnapshot:
        """Capture the one value a step of this service changes."""
        return ServiceSnapshot(service=self.name, values={"value": self.value})

    def restore(self, snapshot: ServiceSnapshot) -> None:
        """Write the captured value back; raises when this is the failing service."""
        self.log.append(f"restore:{self.name}")
        if self._restore_fails:
            raise RuntimeError(f"{self.name} restore failed")
        self.value = snapshot.values["value"]

    def step(self, new_value: int, *, fail: bool = False) -> PreparedStep:
        """Return the prepared step that writes ``new_value`` into this service."""
        snapshot = self.snapshot()
        field_path = f"{self.name}.value"

        def apply() -> UndoToken:
            if fail:
                raise RuntimeError(f"{self.name} commit step failed")
            self.log.append(f"apply:{self.name}")
            self.value = new_value
            return UndoToken(
                service=self.name,
                field_paths=(field_path,),
                restore=lambda: self.restore(snapshot),
            )

        return PreparedStep(service=self.name, field_paths=(field_path,), apply=apply)


def _build_transaction(
    failure_index: int | None, *, failing_restore_index: int | None = None
) -> tuple[ReloadTransaction, list[_RecordedService], list[str]]:
    """Build one transaction whose steps cover every commit phase.

    Steps are registered in reverse commit order, so a passing test also proves the
    transaction commits by phase, not by registration order.
    """
    log: list[str] = []
    services = [
        _RecordedService(
            name,
            log,
            value=index,
            restore_fails=index == failing_restore_index,
        )
        for index, (_phase, name) in enumerate(_COMMIT_ORDER)
    ]
    txn = ReloadTransaction()
    for index in range(len(_COMMIT_ORDER) - 1, -1, -1):
        txn.add_step(
            _COMMIT_ORDER[index][0],
            services[index].step(100 + index, fail=index == failure_index),
        )
    return txn, services, log


def _make_llm_instance() -> Any:
    """Return an object carrying the private attributes `LlmHotConfigHandler` writes."""

    class _LLM:
        def __init__(self) -> None:
            for attr, _kwarg in LlmHotConfigHandler.HOT_CONFIG_FIELDS:
                setattr(self, attr, None)

    return _LLM()


def _make_history_manager() -> HistoryManager:
    """Build a HistoryManager with the fixture limits the reload path reports."""
    return HistoryManager(
        http=MagicMock(spec=httpx.AsyncClient),
        llm_url="http://localhost:8002/v1/chat/completions",
        char_limit=1000,
        compress_turns=2,
        compress_temperature=0.1,
        compress_max_tokens=200,
        protect_turns=0,
        token_limit=0,
    )


class TestCommitOrder:
    def test_commit_runs_the_phases_in_the_declared_order(self) -> None:
        txn, _services, log = _build_transaction(failure_index=None)

        assert txn.commit() is ReloadStage.COMMITTED
        assert log == [f"apply:{name}" for _phase, name in _COMMIT_ORDER]

    def test_applied_names_are_recorded_in_commit_order(self) -> None:
        txn, _services, _log = _build_transaction(failure_index=None)
        txn.commit()

        assert txn.applied == [name for _phase, name in _COMMIT_ORDER]

    def test_a_transaction_with_no_step_stays_prepared(self) -> None:
        """Nothing changed, so nothing was committed (REQ-005)."""
        txn = ReloadTransaction()

        assert txn.commit() is ReloadStage.PREPARED
        assert txn.applied == []


class TestCommitFailureRollback:
    """AC-3: a commit failure at any applied step undoes every step applied before it."""

    @pytest.mark.parametrize("failure_index", range(len(_COMMIT_ORDER)))
    def test_failure_at_any_step_restores_the_applied_steps_in_reverse_order(
        self, failure_index: int
    ) -> None:
        applied_names = [name for _phase, name in _COMMIT_ORDER[:failure_index]]
        txn, _services, log = _build_transaction(failure_index=failure_index)

        with pytest.raises(ConfigReloadCommitError):
            txn.commit()

        assert log == [f"apply:{name}" for name in applied_names] + [
            f"restore:{name}" for name in reversed(applied_names)
        ]
        assert txn.stage is ReloadStage.ROLLED_BACK
        assert txn.degraded_services == ()

    @pytest.mark.parametrize("failure_index", range(len(_COMMIT_ORDER)))
    def test_rolled_back_values_are_the_pre_commit_values(
        self, failure_index: int
    ) -> None:
        txn, services, _log = _build_transaction(failure_index=failure_index)

        with pytest.raises(ConfigReloadCommitError):
            txn.commit()

        for index, service in enumerate(services):
            assert service.value == index, service.name

    def test_a_step_after_the_failure_is_never_applied(self) -> None:
        txn, _services, log = _build_transaction(failure_index=1)

        with pytest.raises(ConfigReloadCommitError):
            txn.commit()

        assert "apply:runtime_tools" not in log
        assert "apply:history" not in log
        assert "apply:llm" not in log

    def test_commit_error_names_the_failing_step_field_not_its_value(self) -> None:
        txn, _services, _log = _build_transaction(failure_index=2)

        with pytest.raises(ConfigReloadCommitError) as exc:
            txn.commit()

        assert exc.value.field_path == "runtime_tools.value"


class TestDegradedRollback:
    """REQ-012: a failing restore does not abandon the remaining restores."""

    def test_rollback_continues_past_a_failing_restore(self) -> None:
        txn, services, log = _build_transaction(
            failure_index=4, failing_restore_index=1
        )

        with pytest.raises(ConfigReloadRollbackError):
            txn.commit()

        applied_names = [name for _phase, name in _COMMIT_ORDER[:4]]
        assert log == [f"apply:{name}" for name in applied_names] + [
            f"restore:{name}" for name in reversed(applied_names)
        ]
        # The service whose restore failed keeps the applied value; the others are back.
        assert services[1].value == 101
        for index in (0, 2, 3):
            assert services[index].value == index, services[index].name

    def test_degraded_stage_names_the_services_left_inconsistent(self) -> None:
        txn, _services, _log = _build_transaction(
            failure_index=4, failing_restore_index=1
        )

        with pytest.raises(ConfigReloadRollbackError) as exc:
            txn.commit()

        assert txn.stage is ReloadStage.DEGRADED
        assert txn.degraded_services == ("conversation",)
        assert exc.value.service == "conversation"

    def test_a_degraded_transaction_refuses_another_step(self) -> None:
        txn, _services, _log = _build_transaction(
            failure_index=4, failing_restore_index=1
        )
        with pytest.raises(ConfigReloadRollbackError):
            txn.commit()

        with pytest.raises(ConfigReloadRollbackError):
            txn.add_step(CommitPhase.LLM_CONFIG, _RecordedService("llm", []).step(1))
        with pytest.raises(ConfigReloadRollbackError):
            txn.commit()

        assert txn.stage is ReloadStage.DEGRADED


class TestReloadServiceDegradedGuard:
    """REQ-012: a reload that degraded refuses the next reload instead of stacking on it."""

    def _degrade_first_reload(self, monkeypatch: pytest.MonkeyPatch) -> tuple[Any, Any]:
        from agent.services import config_reload as reload_module
        from agent.services.config_service_sync import ServiceSyncer

        ctx = reload_fixture_ctx()
        svc = reload_module.ConfigReloadService(ctx)

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
        return svc, ctx

    def test_first_reload_reports_the_rollback_failure(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        svc, ctx = self._degrade_first_reload(monkeypatch)
        before = ctx.cfg.tool

        with pytest.raises(ConfigReloadRollbackError):
            svc.apply_config_dict({"max_tool_turns": 9})

        assert ctx.cfg.tool is not before

    def test_the_next_reload_is_refused_and_changes_nothing(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        svc, ctx = self._degrade_first_reload(monkeypatch)
        with pytest.raises(ConfigReloadRollbackError):
            svc.apply_config_dict({"max_tool_turns": 9})

        degraded_cfg = ctx.cfg
        degraded_tool = ctx.cfg.tool
        before_prompt = ctx.conv.system_prompt_content

        with pytest.raises(ConfigReloadRollbackError) as exc:
            svc.apply_config_dict({"max_tool_turns": 11})

        assert ctx.cfg is degraded_cfg
        assert ctx.cfg.tool is degraded_tool
        assert ctx.conv.system_prompt_content == before_prompt
        assert exc.value.service == "tool"


class TestSectionIdentity:
    """Restored section values land on the same section objects the services hold."""

    def test_restore_puts_the_previous_section_object_back_into_the_same_cfg(
        self,
    ) -> None:
        from agent.services.config_section_reload import (
            apply_validated_section,
            prepare_validated_section,
        )

        ctx = reload_fixture_ctx()
        prepared = prepare_validated_section(
            ctx, "tool", reload_candidate(ctx, max_tool_turns=9).tool
        )
        assert prepared is not None
        before = ctx.cfg
        before_tool = ctx.cfg.tool

        token = apply_validated_section(ctx, prepared)
        assert ctx.cfg is before
        assert ctx.cfg.tool is not before_tool
        assert ctx.cfg.tool.max_tool_turns == 9

        token.restore()
        assert ctx.cfg is before
        assert ctx.cfg.tool is before_tool
        assert ctx.cfg.tool.max_tool_turns == 5

    def test_the_token_names_the_field_paths_the_section_candidate_changed(
        self,
    ) -> None:
        from agent.services.config_section_reload import (
            apply_validated_section,
            prepare_validated_section,
        )

        ctx = reload_fixture_ctx()
        prepared = prepare_validated_section(
            ctx, "tool", reload_candidate(ctx, max_tool_turns=9).tool
        )
        assert prepared is not None

        token = apply_validated_section(ctx, prepared)

        assert token.service == "tool"
        assert token.field_paths == ("tool.max_tool_turns",)


class TestLiveServiceRestorePairs:
    """The live services restore through their own snapshot and restore pair."""

    def test_llm_restore_writes_the_pre_commit_values_into_the_same_instance(
        self,
    ) -> None:
        instance = _make_llm_instance()
        LlmHotConfigHandler.apply_config(instance, temperature=0.5, max_tokens=100)
        snapshot = LlmHotConfigHandler.snapshot(instance)
        txn = ReloadTransaction()

        def apply() -> UndoToken:
            LlmHotConfigHandler.apply_config(instance, temperature=0.9, max_tokens=200)
            return UndoToken(
                service="llm",
                field_paths=("llm_temperature", "llm_max_tokens"),
                restore=lambda: LlmHotConfigHandler.restore(instance, snapshot),
            )

        txn.add_step(
            CommitPhase.LLM_CONFIG,
            PreparedStep("llm", ("llm_temperature", "llm_max_tokens"), apply),
        )
        txn.commit()
        assert instance._temperature == 0.9
        assert instance._max_tokens == 200

        assert txn.rollback() == ()
        assert instance._temperature == 0.5
        assert instance._max_tokens == 100

    def test_apply_one_returns_the_token_that_undoes_only_its_own_field(self) -> None:
        instance = _make_llm_instance()
        LlmHotConfigHandler.apply_config(instance, temperature=0.5, max_tokens=100)

        token = LlmHotConfigHandler.apply_one(instance, "_temperature", 0.9)
        assert instance._max_tokens == 100

        token.restore()
        assert instance._temperature == 0.5
        assert instance._max_tokens == 100

    def test_runtime_tools_restore_reattaches_the_original_tool_objects(self) -> None:
        tools = {
            "read_file": build_fixture_runtime_tool(
                name="read_file",
                server_key="fs",
                description="Read a file",
                input_schema={"type": "object"},
                status="active",
                is_write=False,
                agent_safety_tier=cast("Any", "READ_ONLY"),
                enabled_for_llm=True,
            )
        }
        registry = RuntimeToolRegistry(tools=tools, allowed_servers=frozenset({"fs"}))
        original = registry.get("read_file")
        snapshot = registry.snapshot_policy()
        txn = ReloadTransaction()

        def apply() -> UndoToken:
            registry.apply_policy(
                allowed_tools=[],
                tool_policy_mode="explicit_allowlist",
                disabled_tools=(),
            )
            return UndoToken(
                service="runtime_tools",
                field_paths=("allowed_tools",),
                restore=lambda: registry.restore_policy(snapshot),
            )

        txn.add_step(
            CommitPhase.RUNTIME_TOOLS,
            PreparedStep("runtime_tools", ("allowed_tools",), apply),
        )
        txn.commit()
        assert registry.get("read_file") is not original
        assert registry.get("read_file").enabled_for_llm is False

        assert txn.rollback() == ()
        assert registry.get("read_file") is original
        assert registry.get("read_file").enabled_for_llm is True

    def test_history_restore_puts_back_the_limits_and_rebuilds_the_policy(self) -> None:
        manager = _make_history_manager()
        before = manager.snapshot_config()
        txn = ReloadTransaction()

        def apply() -> UndoToken:
            manager.apply_config(char_limit=500, compress_turns=9, token_limit=10)
            return UndoToken(
                service="history",
                field_paths=("context_char_limit", "context_compress_turns"),
                restore=lambda: manager.restore_config(before),
            )

        txn.add_step(
            CommitPhase.HISTORY,
            PreparedStep(
                "history", ("context_char_limit", "context_compress_turns"), apply
            ),
        )
        txn.commit()
        assert manager.compress_turns == 9

        assert txn.rollback() == ()
        restored = manager.snapshot_config()
        assert restored.values["char_limit"] == 1000
        assert restored.values["compress_turns"] == 2
        assert manager.compress_turns == 2
        # The derived policy is a new object built from the restored value, not the
        # one the failed commit left behind.
        policy = restored.values["selection_policy"]
        assert isinstance(policy, HistorySelectionPolicy)
        assert policy is not before.values["selection_policy"]
        assert policy._compress_turns == 2

    def test_history_restore_leaves_the_compression_counters_alone(self) -> None:
        manager = _make_history_manager()
        before = manager.snapshot_config()
        manager.stat_compress_count = 3
        manager.stat_fallback_truncate_count = 2

        manager.apply_config(char_limit=500, compress_turns=9, token_limit=10)
        manager.restore_config(before)

        assert manager.stat_compress_count == 3
        assert manager.stat_fallback_truncate_count == 2


class TestOutcomeStage:
    """REQ-005: the outcome reports the stage the reload ended in."""

    def _ctx_without_live_services(self) -> Any:
        ctx = reload_fixture_ctx()
        ctx.services_required.llm = None
        ctx.services_required.runtime_tools = None
        return ctx

    def test_no_change_reports_prepared(self) -> None:
        from agent.services.config_reload import ConfigReloadService

        outcome = ConfigReloadService(
            self._ctx_without_live_services()
        ).apply_config_dict({})

        assert outcome.applied == []
        assert outcome.stage is ReloadStage.PREPARED

    def test_an_applied_change_reports_committed(self) -> None:
        from agent.services.config_reload import ConfigReloadService

        outcome = ConfigReloadService(
            self._ctx_without_live_services()
        ).apply_config_dict({"max_tool_turns": 9})

        assert "tool" in outcome.applied
        assert outcome.stage is ReloadStage.COMMITTED

    def test_the_conversation_step_is_not_reported_as_an_applied_section(self) -> None:
        from agent.services.config_reload import ConfigReloadService

        ctx = self._ctx_without_live_services()
        ctx.conv.system_prompt_content = "a stale prompt"

        outcome = ConfigReloadService(ctx).apply_config_dict({})

        assert outcome.applied == []
        assert outcome.stage is ReloadStage.COMMITTED
        assert ctx.conv.system_prompt_content != "a stale prompt"

    def test_a_rejected_payload_mutates_nothing(self) -> None:
        from agent.services.config_reload import ConfigReloadService

        ctx = self._ctx_without_live_services()
        before = ctx.cfg

        with pytest.raises(ConfigFieldTypeError):
            ConfigReloadService(ctx).apply_config_dict({"max_tool_turns": "many"})

        assert ctx.cfg is before


class TestMcpPathIsNotACommitStep:
    """REQ-007: the irreversible MCP path never enters the transaction."""

    def test_an_added_server_is_reported_as_pending_without_a_live_mcp_change(
        self,
    ) -> None:
        from agent.services.config_reload import ConfigReloadService

        ctx = reload_fixture_ctx()
        payload = {
            "mcp_servers": {
                "fixture_server": {
                    "transport": "http",
                    "url": "http://mcp.local:8100",
                    "cmd": ["/opt/llm/bin/fixture_server"],
                },
                "added_server": {
                    "transport": "http",
                    "url": "http://mcp.local:8101",
                    "cmd": ["/opt/llm/bin/added_server"],
                },
            }
        }
        before_mcp = ctx.cfg.mcp

        outcome = ConfigReloadService(ctx).apply_config_dict(payload)

        assert ctx.cfg.mcp is before_mcp
        assert any("added_server" in item for item in outcome.needs_restart)
        ctx.services_required.lifecycle.cleanup_server_resources.assert_not_called()

    def test_a_pending_only_reload_registers_no_commit_step(self) -> None:
        from agent.services.config_reload import ConfigReloadService

        ctx = reload_fixture_ctx()
        ctx.services_required.llm = None
        ctx.services_required.runtime_tools = None

        outcome = ConfigReloadService(ctx).apply_config_dict(
            {"context_char_limit": 1234}
        )

        assert outcome.stage is ReloadStage.PREPARED
        assert outcome.applied == []
        assert "context_char_limit" in outcome.startup_only


class TestConfigReloadRequestShape:
    """REQ-005: a request cannot carry a payload of the wrong shape."""

    @pytest.mark.parametrize(
        "section", ["mcp_servers", "approval", "llm", "rag_tool", "sse"]
    )
    def test_a_scalar_payload_is_rejected_by_the_request(self, section: str) -> None:
        with pytest.raises(ConfigReloadValidationError):
            ConfigReloadRequest(**{section: 5})

    def test_a_non_list_masked_fields_is_rejected_by_the_request(self) -> None:
        with pytest.raises(ConfigReloadValidationError):
            ConfigReloadRequest(masked_fields="api_key")

    def test_a_valid_section_payload_is_accepted(self) -> None:
        req = ConfigReloadRequest(llm={"llm_temperature": 0.4})

        assert req.llm == {"llm_temperature": 0.4}
