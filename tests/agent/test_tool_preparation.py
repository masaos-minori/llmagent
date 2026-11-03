"""
tests/agent/test_tool_preparation.py
Unit tests for tool_preparation.py: the fail-closed preparation phase run before approval.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

from agent.config_builders import build_agent_config
from agent.config_dataclasses import AgentConfig
from agent.tool_preparation import PreparedToolCall, prepare_tool_calls
from shared.tool_spec import ToolSpec


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
        "tool_definitions": [],
        "tool_safety_tiers": {},
        "approval_risk_rules": {},
        "approval_protected_paths": [],
        "approval_github_allowed_repos": [],
        "approval_high_risk_branches": [],
        "approval_shell_safe_prefixes": [],
        "approval_resource_keys": {"path_keys": [], "branch_keys": []},
        "allowed_root": "",
        "tool_results_turn_max_chars": 0,
        "embed_url": "http://127.0.0.1:9999",
        "mcp_servers": {
            "_dummy": {
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
    def test_unregistered_name_rejected_despite_matching_tool_definitions_entry(
        self,
    ) -> None:
        """The core regression test: an unregistered tool name must be rejected even
        when a stale ctx.cfg.tool.tool_definitions entry matches it by name — proving
        tool_definitions is never consulted as a fallback."""
        ctx = _make_ctx(_cfg(tool_definitions=[{"function": {"name": "stale_tool"}}]))
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
