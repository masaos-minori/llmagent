"""
tests/agent/test_tool_preparation.py
Unit tests for tool_preparation.py: the fail-closed preparation phase run before approval.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from agent.config_builders import build_agent_config
from agent.config_dataclasses import AgentConfig
from agent.tool_preparation import (
    PreparedToolCall,
    ReplayDirective,
    _canonical_args_hash,
    new_execution_context,
    prepare_tool_calls,
)
from shared.tool_spec import ToolSpec
from shared.transport_dto import ToolExecutionContext

from tests.agent._config_test_defaults import (
    PERMISSIVE_ALLOWED_ROOT,
    SHIPPED_DB_PATH_KEYS,
)


def _cfg(**overrides: Any) -> AgentConfig:
    """Build an AgentConfig for tool_preparation.py unit tests.

    This intentionally bypasses ProductionConfigValidator (patched below):
    these tests construct a deliberately empty allowed_tools/tool_safety_tiers/
    approval_risk_rules config, which is a different concern from whether the
    resulting config would be accepted as production-ready.
    """
    defaults: dict[str, Any] = {
        "context_char_limit": 8000,
        "context_compress_turns": 4,
        "llm_retry_base_delay": 1.0,
        "serial_tool_calls": False,
        "tool_result_max_llm_chars": 4000,
        "masked_fields": [],
        "allowed_tools": [],
        "tool_safety_tiers": {},
        "approval_risk_rules": {},
        "approval_protected_paths": [],
        "approval_github_allowed_repos": [],
        "approval_high_risk_branches": [],
        "approval_shell_safe_prefixes": [],
        "approval_resource_keys": {"path_keys": [], "branch_keys": []},
        "allowed_root": PERMISSIVE_ALLOWED_ROOT,
        # build_agent_config() resolves the typed DB configuration from the mapping, so the fixture supplies the mirrored path keys.
        **SHIPPED_DB_PATH_KEYS,
        "tool_results_turn_max_chars": 0,
        "memory_embed_url": "http://127.0.0.1:9999",
        "mcp_servers": {
            "dummy": {
                "transport": "http",
                "url": "http://127.0.0.1:9999",
                "auth_token": "test-token",
            }
        },
    }
    defaults.update(overrides)
    with patch("agent.config_builders.ProductionConfigValidator") as mock_validator:
        mock_validator.return_value.validate.return_value.errors = []
        mock_validator.return_value.validate.return_value.warnings = []
        return build_agent_config(defaults)


def _make_ctx(cfg: AgentConfig | None = None) -> MagicMock:
    ctx = MagicMock()
    ctx.cfg = cfg or _cfg()
    ctx.services_required.runtime_tools = None
    return ctx


def _tc(name: str, args_str: str, call_id: str = "call_1") -> dict:
    return {"id": call_id, "function": {"name": name, "arguments": args_str}}


class TestPrepareToolCallsConfigurationErrors:
    def test_registry_none_rejects_with_configuration_kind(self) -> None:
        """A None RuntimeToolRegistry is a defensive configuration-kind rejection."""
        ctx = _make_ctx()
        ctx.services_required.runtime_tools = None

        prepared, failures = prepare_tool_calls(
            ctx, [_tc("read_text_file", '{"path": "/tmp/f"}')]
        )

        assert prepared == []
        assert len(failures) == 1
        tc_id, name, args, text, is_error, llm_text = failures[0]
        assert is_error is True
        assert "configuration" in text or "RuntimeToolRegistry" in text
        assert text == llm_text


class TestPrepareToolCallsUnknownTool:
    def test_unregistered_name_rejected(
        self,
    ) -> None:
        """The core regression test: an unregistered tool name must be rejected by
        the fail-closed preparation path — the RuntimeToolRegistry is the sole
        authority and never falls back to any static config."""
        ctx = _make_ctx(_cfg())
        ctx.services_required.runtime_tools = MagicMock()
        ctx.services_required.runtime_tools.get.side_effect = KeyError("stale_tool")

        prepared, failures = prepare_tool_calls(ctx, [_tc("stale_tool", "{}")])

        assert prepared == []
        assert len(failures) == 1
        tc_id, name, args, text, is_error, llm_text = failures[0]
        assert name == "stale_tool"
        assert is_error is True
        ctx.services_required.runtime_tools.tool_spec_for_call.assert_not_called()


class TestPrepareToolCallsMalformedJson:
    def test_malformed_json_rejected_with_validation_kind(self) -> None:
        ctx = _make_ctx()
        ctx.services_required.runtime_tools = MagicMock()

        prepared, failures = prepare_tool_calls(
            ctx, [_tc("read_text_file", "{not valid json")]
        )

        assert prepared == []
        assert len(failures) == 1
        tc_id, name, args, text, is_error, llm_text = failures[0]
        assert is_error is True
        assert "Invalid JSON" in text

    def test_non_dict_decoded_value_rejected(self) -> None:
        ctx = _make_ctx()
        ctx.services_required.runtime_tools = MagicMock()

        prepared, failures = prepare_tool_calls(
            ctx, [_tc("read_text_file", "[1, 2, 3]")]
        )

        assert prepared == []
        assert len(failures) == 1
        tc_id, name, args, text, is_error, llm_text = failures[0]
        assert is_error is True
        assert "must decode to a JSON object" in text


class TestPrepareToolCallsSchemaViolation:
    def test_schema_violation_rejected_with_schema_kind(self) -> None:
        ctx = _make_ctx()
        runtime_tool = MagicMock()
        runtime_tool.input_schema = {
            "type": "object",
            "required": ["path"],
            "properties": {"path": {"type": "string"}},
        }
        runtime_tool.allow_extra_fields = False
        ctx.services_required.runtime_tools = MagicMock()
        ctx.services_required.runtime_tools.get.return_value = runtime_tool

        prepared, failures = prepare_tool_calls(
            ctx, [_tc("read_text_file", '{"unexpected": "field"}')]
        )

        assert prepared == []
        assert len(failures) == 1
        tc_id, name, args, text, is_error, llm_text = failures[0]
        assert is_error is True
        assert "unexpected" in text or "path" in text

    def test_empty_schema_rejected_with_schema_kind(self) -> None:
        """A registry tool whose input_schema is empty is rejected fail-closed with
        the schema kind naming the tool and the missing schema."""
        ctx = _make_ctx()
        runtime_tool = MagicMock()
        runtime_tool.input_schema = {}
        runtime_tool.allow_extra_fields = True
        ctx.services_required.runtime_tools = MagicMock()
        ctx.services_required.runtime_tools.get.return_value = runtime_tool

        prepared, failures = prepare_tool_calls(
            ctx, [_tc("read_text_file", '{"path": "/tmp/f"}')]
        )

        assert prepared == []
        assert len(failures) == 1
        tc_id, name, args, text, is_error, llm_text = failures[0]
        assert is_error is True
        assert "read_text_file" in text
        assert "input schema" in text


class TestPrepareToolCallsHappyPath:
    def test_valid_call_produces_prepared_tool_call(self) -> None:
        ctx = _make_ctx()
        runtime_tool = MagicMock()
        runtime_tool.input_schema = {
            "type": "object",
            "required": ["path"],
            "properties": {"path": {"type": "string"}},
        }
        runtime_tool.allow_extra_fields = False
        ctx.services_required.runtime_tools = MagicMock()
        ctx.services_required.runtime_tools.get.return_value = runtime_tool
        expected_spec = ToolSpec(
            call_id="call_1", name="read_text_file", args={"path": "/tmp/f"}
        )
        ctx.services_required.runtime_tools.tool_spec_for_call.return_value = (
            expected_spec
        )

        raw_call = _tc("read_text_file", '{"path": "/tmp/f"}', call_id="call_1")
        prepared, failures = prepare_tool_calls(ctx, [raw_call])

        assert failures == []
        assert len(prepared) == 1
        result = prepared[0]
        assert isinstance(result, PreparedToolCall)
        assert result.call_id == "call_1"
        assert result.name == "read_text_file"
        assert result.args == {"path": "/tmp/f"}
        assert result.spec is expected_spec
        assert result.original_call is raw_call


class TestPrepareToolCallsBatchOrdering:
    def _valid_registry(self) -> MagicMock:
        runtime_tool = MagicMock()
        runtime_tool.input_schema = {"type": "object", "properties": {}}
        runtime_tool.allow_extra_fields = True
        registry = MagicMock()

        def _get(name: str) -> MagicMock:
            if name == "unknown_tool":
                raise KeyError(name)
            return runtime_tool

        registry.get = MagicMock(side_effect=_get)
        registry.tool_spec_for_call = MagicMock(
            side_effect=lambda call_id, name, args: ToolSpec(
                call_id=call_id, name=name, args=args
            )
        )
        return registry

    def test_mixed_valid_invalid_batch_preserves_order(self) -> None:
        ctx = _make_ctx()
        ctx.services_required.runtime_tools = self._valid_registry()

        calls = [
            _tc("read_text_file", "{}", call_id="call_a"),
            _tc("unknown_tool", "{}", call_id="call_b"),
            _tc("write_text_file", "{}", call_id="call_c"),
        ]

        prepared, failures = prepare_tool_calls(ctx, calls)

        assert len(prepared) == 2
        assert [p.call_id for p in prepared] == ["call_a", "call_c"]
        assert len(failures) == 1
        assert failures[0][0] == "call_b"

    def test_approval_never_called_for_failed_prep_call(self) -> None:
        """A call that fails preparation cannot structurally reach the approval-gate
        call site, since only `prepared` (not `failures`) would ever be handed to it."""
        ctx = _make_ctx()
        ctx.services_required.runtime_tools = self._valid_registry()

        calls = [
            _tc("unknown_tool", "{}", call_id="call_bad"),
            _tc("read_text_file", "{}", call_id="call_good"),
        ]

        prepared, failures = prepare_tool_calls(ctx, calls)

        prepared_ids = [p.call_id for p in prepared]
        assert "call_bad" not in prepared_ids
        assert "call_good" in prepared_ids
        assert len(failures) == 1
        assert failures[0][0] == "call_bad"


class TestPrepareToolCallsDuplicateId:
    """REQ-001/AC-002: a call id appearing more than once in a batch is a preparation
    failure (`duplicate_id`) for every occurrence, before the approval gate.

    Asserted through the failure reason text: the flat failure tuple carries no
    `error_type` (the kind lives only in `_reject`'s internal `ToolCallResult`).
    """

    def _valid_registry(self) -> MagicMock:
        runtime_tool = MagicMock()
        runtime_tool.input_schema = {"type": "object", "properties": {}}
        runtime_tool.allow_extra_fields = True
        registry = MagicMock()
        registry.runtime_tool_stub = runtime_tool
        registry.get.return_value = runtime_tool
        registry.tool_spec_for_call = MagicMock(
            side_effect=lambda call_id, name, args: ToolSpec(
                call_id=call_id, name=name, args=args
            )
        )
        return registry

    def test_shared_id_rejects_both_occurrences(self) -> None:
        ctx = _make_ctx()
        ctx.services_required.runtime_tools = self._valid_registry()

        calls = [
            _tc("read_text_file", '{"path": "/tmp/a"}', call_id="call_dup"),
            _tc("read_text_file", '{"path": "/tmp/b"}', call_id="call_dup"),
        ]
        prepared, failures = prepare_tool_calls(ctx, calls)

        assert prepared == []
        assert len(failures) == 2
        for tc_id, name, args, text, is_error, llm_text in failures:
            assert tc_id == "call_dup"
            assert is_error is True
            assert text == (
                "duplicate tool call id 'call_dup' appears 2 times in this round"
            )
            assert text == llm_text

    def test_duplicate_pair_rejected_unique_call_survives(self) -> None:
        ctx = _make_ctx()
        ctx.services_required.runtime_tools = self._valid_registry()

        calls = [
            _tc("read_text_file", "{}", call_id="call_a"),
            _tc("read_text_file", "{}", call_id="call_dup"),
            _tc("write_text_file", "{}", call_id="call_dup"),
        ]
        prepared, failures = prepare_tool_calls(ctx, calls)

        assert [p.call_id for p in prepared] == ["call_a"]
        assert [f[0] for f in failures] == ["call_dup", "call_dup"]
        assert all("appears 2 times in this round" in f[3] for f in failures)

    def test_occurrence_rejected_for_other_reason_is_not_flagged_as_duplicate(
        self,
    ) -> None:
        """Counting is over `prepared` entries only (Plan D1): a prepared call sharing
        its id with an occurrence already rejected for another reason stays prepared —
        the misexecution hazard requires two same-id calls in `prepared`."""
        ctx = _make_ctx()
        registry = self._valid_registry()
        ctx.services_required.runtime_tools = registry

        def _get(name: str) -> MagicMock:
            if name == "broken_tool":
                raise KeyError(name)
            return registry.runtime_tool_stub

        registry.get = MagicMock(side_effect=_get)

        calls = [
            _tc("broken_tool", "{}", call_id="call_dup"),
            _tc("read_text_file", "{}", call_id="call_dup"),
        ]
        prepared, failures = prepare_tool_calls(ctx, calls)

        assert [p.call_id for p in prepared] == ["call_dup"]
        assert len(failures) == 1
        assert "unregistered tool" in failures[0][3]


class TestPrepareToolCallsLogicalIdentity:
    """REQ-001/REQ-002: uuid7 logical call id and execution context at preparation."""

    def _registry(self) -> MagicMock:
        runtime_tool = MagicMock()
        runtime_tool.input_schema = {"type": "object", "properties": {}}
        runtime_tool.allow_extra_fields = True
        registry = MagicMock()
        registry.get = MagicMock(return_value=runtime_tool)
        registry.tool_spec_for_call = MagicMock(
            side_effect=lambda call_id, name, args: ToolSpec(
                call_id=call_id, name=name, args=args
            )
        )
        return registry

    def _ctx(self) -> MagicMock:
        ctx = _make_ctx()
        ctx.services_required.runtime_tools = self._registry()
        return ctx

    def test_identical_args_get_distinct_logical_ids(self) -> None:
        """AC-1: two calls with identical tool+args must not share a logical id."""
        prepared, failures = prepare_tool_calls(
            self._ctx(),
            [
                _tc("read_text_file", '{"path": "/a"}', call_id="call_1"),
                _tc("read_text_file", '{"path": "/a"}', call_id="call_2"),
            ],
        )
        assert failures == []
        assert len(prepared) == 2
        ids = [p.context.call_id for p in prepared]
        assert ids[0] != ids[1]
        assert all(uuid.UUID(i).version == 7 for i in ids)

    def test_context_attached_with_canonical_args_hash(self) -> None:
        prepared, failures = prepare_tool_calls(
            self._ctx(), [_tc("write_text_file", '{"b": 2, "a": 1}', call_id="call_1")]
        )
        assert failures == []
        context = prepared[0].context
        assert isinstance(context, ToolExecutionContext)
        assert context.call_id != prepared[0].call_id  # logical id, not correlation id
        assert uuid.UUID(context.call_id).version == 7
        assert context.tool == "write_text_file"
        expected = hashlib.sha256(
            json.dumps({"b": 2, "a": 1}, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        assert context.args_hash == expected
        assert context.operation == "call_tool"

    def test_whitespace_in_id_rejected(self) -> None:
        prepared, failures = prepare_tool_calls(
            self._ctx(), [_tc("read_text_file", "{}", call_id="call 1")]
        )
        assert prepared == []
        assert "whitespace or control characters" in failures[0][3]

    def test_control_character_in_id_rejected(self) -> None:
        prepared, failures = prepare_tool_calls(
            self._ctx(), [_tc("read_text_file", "{}", call_id="call\n1")]
        )
        assert prepared == []
        assert "whitespace or control characters" in failures[0][3]

    def test_overlong_id_rejected(self) -> None:
        prepared, failures = prepare_tool_calls(
            self._ctx(), [_tc("read_text_file", "{}", call_id="x" * 300)]
        )
        assert prepared == []
        assert "exceeds 256 characters" in failures[0][3]

    def test_non_string_id_rejected(self) -> None:
        raw = _tc("read_text_file", "{}")
        raw["id"] = 123
        prepared, failures = prepare_tool_calls(self._ctx(), [raw])
        assert prepared == []
        assert "must be a string" in failures[0][3]

    def test_fallback_id_is_valid_uuid7(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """CI runs 3.13 where uuid.uuid7 is absent; the fallback must still compose
        an RFC 9562 version-7/variant-10 identifier."""
        import uuid as uuid_mod

        from agent.tool_preparation import _logical_call_id

        monkeypatch.setattr(uuid_mod, "uuid7", None, raising=False)
        value = _logical_call_id()
        parsed = uuid.UUID(value)
        assert parsed.version == 7
        assert parsed.variant == uuid.RFC_4122


class TestPrepareToolCallsExecutionMode:
    """mcpai005 REQ-001/REQ-009: the resolved execution mode on the prepared context."""

    def _registry(self, preview_capability: str) -> MagicMock:
        runtime_tool = MagicMock()
        runtime_tool.input_schema = {"type": "object", "properties": {}}
        runtime_tool.allow_extra_fields = True
        runtime_tool.preview_capability = preview_capability
        registry = MagicMock()
        registry.get = MagicMock(return_value=runtime_tool)
        registry.tool_spec_for_call = MagicMock(
            side_effect=lambda call_id, name, args: ToolSpec(
                call_id=call_id, name=name, args=args
            )
        )
        return registry

    def _ctx(self, preview_capability: str) -> MagicMock:
        ctx = _make_ctx()
        ctx.services_required.runtime_tools = self._registry(preview_capability)
        return ctx

    def test_preview_capable_tool_with_dry_run_prepares_as_preview(self) -> None:
        """AC-5: a dry-run call carries `preview`, so the runner records no state row."""
        prepared, failures = prepare_tool_calls(
            self._ctx("dry_run"),
            [_tc("write_text_file", '{"path": "/a", "dry_run": true}')],
        )
        assert failures == []
        assert prepared[0].context.execution_mode == "preview"

    def test_dry_run_false_on_a_preview_capable_tool_prepares_as_applied(self) -> None:
        prepared, failures = prepare_tool_calls(
            self._ctx("dry_run"),
            [_tc("write_text_file", '{"path": "/a", "dry_run": false}')],
        )
        assert failures == []
        assert prepared[0].context.execution_mode == "applied"

    def test_tool_without_preview_capability_prepares_as_applied(self) -> None:
        """`dry_run` on a non-capable tool is an ordinary argument, not a mode."""
        prepared, failures = prepare_tool_calls(
            self._ctx("none"),
            [_tc("write_text_file", '{"path": "/a", "dry_run": true}')],
        )
        assert failures == []
        assert prepared[0].context.execution_mode == "applied"

    def test_non_boolean_dry_run_is_rejected_before_dispatch(self) -> None:
        """A malformed `dry_run` is a validation rejection that names the tool only."""
        prepared, failures = prepare_tool_calls(
            self._ctx("dry_run"),
            [_tc("write_text_file", '{"path": "/a", "dry_run": "true"}')],
        )
        assert prepared == []
        assert len(failures) == 1
        text = failures[0][3]
        assert "dry_run argument is of type str" in text
        assert "/a" not in text

    def test_new_execution_context_yields_distinct_ids_per_call(self) -> None:
        """The single construction site generates one uuid7 logical id per call."""
        first = new_execution_context("write_text_file", {"path": "/a"})
        second = new_execution_context("write_text_file", {"path": "/a"})
        assert first.call_id != second.call_id
        assert uuid.UUID(first.call_id).version == 7
        assert first.execution_mode == "applied"
        assert first.operation == "call_tool"
        assert first.args_hash == _canonical_args_hash({"path": "/a"})

    def test_replay_directive_id_is_kept_on_the_prepared_context(self) -> None:
        """The helper must not replace a matched replay directive's call id."""
        ctx = self._ctx("dry_run")
        directive = ReplayDirective(
            task_id=ctx.workflow.current_task_id,
            tool="write_text_file",
            args_hash=_canonical_args_hash({"path": "/a", "dry_run": True}),
            original_call_id="00000000-0000-7000-8000-000000000000",
            consumed=False,
        )
        ctx.turn.replay_directives = [directive]
        prepared, failures = prepare_tool_calls(
            ctx, [_tc("write_text_file", '{"path": "/a", "dry_run": true}')]
        )
        assert failures == []
        context = prepared[0].context
        assert context.call_id == directive.original_call_id
        assert context.execution_mode == "preview"


class TestPrepareToolCallsReplayDirective:
    """mcpai004 REQ-001/REQ-002/REQ-003: the one-time replay directive at preparation."""

    def _ctx(self, directives: list[ReplayDirective]) -> MagicMock:
        runtime_tool = MagicMock()
        runtime_tool.input_schema = {"type": "object", "properties": {}}
        runtime_tool.allow_extra_fields = True
        registry = MagicMock()
        registry.get = MagicMock(return_value=runtime_tool)
        registry.tool_spec_for_call = MagicMock(
            side_effect=lambda call_id, name, args: ToolSpec(
                call_id=call_id, name=name, args=args
            )
        )
        ctx = _make_ctx()
        ctx.services_required.runtime_tools = registry
        ctx.workflow.current_task_id = "task_1"
        ctx.turn.replay_directives = directives
        return ctx

    def _directive(
        self, tool: str, args: dict[str, Any], call_id: str
    ) -> ReplayDirective:
        return ReplayDirective(
            original_call_id=call_id,
            task_id="task_1",
            tool=tool,
            args_hash=_canonical_args_hash(args),
        )

    def _context(self, prepared: PreparedToolCall) -> ToolExecutionContext:
        """Narrow the optional execution context so the assertions read as the contract."""
        assert prepared.context is not None
        return prepared.context

    def test_matching_directive_reuses_the_original_id(self) -> None:
        """AC-001: a byte-identical reissue keeps the original logical call id, and the
        prepared context carries the same canonical hash the directive matched on."""
        args = {"path": "/a"}
        directive = self._directive(
            "read_text_file", args, "0199e2f3-0000-7000-8000-000000000001"
        )
        prepared, failures = prepare_tool_calls(
            self._ctx([directive]),
            [_tc("read_text_file", '{"path": "/a"}', call_id="call_1")],
        )
        assert failures == []
        context = self._context(prepared[0])
        assert context.call_id == directive.original_call_id
        assert context.args_hash == directive.args_hash
        assert directive.consumed

    def test_directive_is_consumed_once(self) -> None:
        """AC-002: the second identical call in the same batch gets a fresh id."""
        args = {"path": "/a"}
        directive = self._directive(
            "read_text_file", args, "0199e2f3-0000-7000-8000-000000000002"
        )
        prepared, failures = prepare_tool_calls(
            self._ctx([directive]),
            [
                _tc("read_text_file", '{"path": "/a"}', call_id="call_1"),
                _tc("read_text_file", '{"path": "/a"}', call_id="call_2"),
            ],
        )
        assert failures == []
        assert self._context(prepared[0]).call_id == directive.original_call_id
        second = self._context(prepared[1]).call_id
        assert second != directive.original_call_id
        assert uuid.UUID(second).version == 7

    def test_ambiguous_match_fails_closed_before_dispatch(self, caplog) -> None:
        """AC-002: several matching directives reject the call with the structured
        `ambiguity` kind, list the matching ids, and consume nothing."""
        args = {"path": "/a"}
        first = self._directive(
            "read_text_file", args, "0199e2f3-0000-7000-8000-000000000003"
        )
        second = self._directive(
            "read_text_file", args, "0199e2f3-0000-7000-8000-000000000004"
        )
        prepared, failures = prepare_tool_calls(
            self._ctx([first, second]),
            [_tc("read_text_file", '{"path": "/a"}', call_id="call_1")],
        )
        assert prepared == []
        assert len(failures) == 1
        assert failures[0][3].startswith(
            "2 replay directives match tool 'read_text_file'"
        )
        assert first.original_call_id in failures[0][3]
        assert second.original_call_id in failures[0][3]
        assert "kind=ambiguity" in caplog.text
        assert not first.consumed and not second.consumed

    def test_edited_arguments_do_not_match(self) -> None:
        """Plan Risk on edited arguments: a reissue with different args hashes
        differently, so no directive matches and the call proceeds as a new call."""
        directive = self._directive(
            "read_text_file", {"path": "/a"}, "0199e2f3-0000-7000-8000-000000000005"
        )
        prepared, failures = prepare_tool_calls(
            self._ctx([directive]),
            [_tc("read_text_file", '{"path": "/b"}', call_id="call_1")],
        )
        assert failures == []
        assert self._context(prepared[0]).call_id != directive.original_call_id
        assert not directive.consumed
