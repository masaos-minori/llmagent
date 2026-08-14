"""
tests/agent/test_tool_preparation.py
Unit tests for tool_preparation.py: the fail-closed preparation phase run before approval.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

from agent.config_builders import build_agent_config
from agent.config_dataclasses import AgentConfig
from agent.tool_preparation import PreparedToolCall, prepare_tool_calls
from shared.tool_spec import ToolSpec


def _cfg(**overrides: Any) -> AgentConfig:
    defaults: dict[str, Any] = {
        "context_char_limit": 8000,
        "context_compress_turns": 4,
        "tool_cache_ttl": 300,
        "top_k_search": 20,
        "top_k_rerank": 15,
        "rag_top_k": 5,
        "use_mqe": True,
        "use_search": True,
        "use_rrf": True,
        "use_rerank": True,
        "llm_max_retries": 3,
        "llm_retry_base_delay": 1.0,
        "rag_min_score": 0.0,
        "max_chunks_per_doc": 2,
        "use_two_stage_fetch": False,
        "two_stage_max_docs": 2,
        "serial_tool_calls": False,
        "use_semantic_cache": False,
        "semantic_cache_threshold": 0.92,
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
            "_dummy": {"transport": "http", "url": "http://127.0.0.1:9999"}
        },
    }
    defaults.update(overrides)
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
        runtime_tool.input_schema = {}
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
