"""tests/test_tool_loop_guard.py
Unit tests for agent/tool_loop_guard.py — ToolLoopGuard.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import orjson
from agent.config_builders import build_agent_config
from agent.config_dataclasses import AgentConfig
from agent.tool_loop_guard import ToolLoopGuard, TurnLoopState


def _cfg(**overrides: dict) -> AgentConfig:
    defaults: dict = {
        "context_char_limit": 8000,
        "context_compress_turns": 4,
        "tool_cache_ttl": 300,
        "llm_max_retries": 3,
        "llm_retry_base_delay": 1.0,
        "use_two_stage_fetch": False,
        "two_stage_max_docs": 2,
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
        "tool_dedup_max_repeats": 3,
        "tool_cycle_detect_window": 2,
        "tool_error_retry_max": 1,
        "tool_error_max_consecutive": 3,
        "mcp_servers": {
            "_dummy": {"transport": "http", "url": "http://127.0.0.1:9999"}
        },
    }
    defaults.update(overrides)
    return build_agent_config(defaults)


def _make_ctx(cfg: AgentConfig | None = None) -> MagicMock:
    ctx = MagicMock()
    ctx.cfg = cfg or _cfg()
    ctx.conv = MagicMock()
    ctx.conv.history = []
    return ctx


def _state() -> TurnLoopState:
    return TurnLoopState()


def _msg(*tool_names: str) -> dict:
    return {
        "tool_calls": [
            {"function": {"name": name, "arguments": "{}"}} for name in tool_names
        ]
    }


class TestCheckCycle:
    def test_window_zero_disabled(self) -> None:
        cfg = _cfg(tool_cycle_detect_window=0)
        ctx = _make_ctx(cfg)
        guard = ToolLoopGuard(ctx)
        assert guard.check_cycle([], _msg("read_text_file")) is None
        assert len(ctx.conv.history) == 0

    def test_no_cycle_returns_none(self) -> None:
        ctx = _make_ctx()
        guard = ToolLoopGuard(ctx)
        fingerprints: list[str] = ["aaa", "bbb"]
        msg = _msg("read_text_file")
        result = guard.check_cycle(fingerprints, msg)
        assert result is None
        assert len(fingerprints) == 3
        assert len(ctx.conv.history) == 0

    def test_cycle_detected_stores_in_diagnostic_only(self) -> None:
        """Cycle detection must store hint in diagnostics; history must not be modified."""
        ctx = _make_ctx()
        guard = ToolLoopGuard(ctx)
        msg = _msg("write_file")
        fingerprints: list[str] = []
        guard.check_cycle(fingerprints, msg)
        guard.check_cycle(fingerprints, msg)
        result = guard.check_cycle(fingerprints, msg)
        assert result is not None
        assert "Cyclic" in result
        assert len(ctx.conv.history) == 0
        ctx.diagnostics.save.assert_called_once()
        call_args = ctx.diagnostics.save.call_args
        assert call_args[0][1] == "guard_hint"

    def test_cycle_below_threshold_returns_none(self) -> None:
        cfg = _cfg(tool_cycle_detect_window=3)
        ctx = _make_ctx(cfg)
        guard = ToolLoopGuard(ctx)
        msg = _msg("read_text_file")
        fingerprints: list[str] = ["fp1", "fp1"]
        assert guard.check_cycle(fingerprints, msg) is None


class TestCheckDedup:
    def test_window_zero_disabled_by_default(self) -> None:
        ctx = _make_ctx()
        guard = ToolLoopGuard(ctx)
        seen: dict[str, int] = {}
        assert guard.check_dedup(seen, _msg("tool_a", "tool_a")) is None

    def test_first_call_not_blocked(self) -> None:
        ctx = _make_ctx()
        guard = ToolLoopGuard(ctx)
        seen: dict[str, int] = {}
        result = guard.check_dedup(seen, _msg("write_file"))
        assert result is None

    def test_repeat_calls_blocked_at_threshold(self) -> None:
        cfg = _cfg(tool_dedup_max_repeats=2)
        ctx = _make_ctx(cfg)
        guard = ToolLoopGuard(ctx)
        seen: dict[str, int] = {}
        msg = _msg("write_file")
        guard.check_dedup(seen, msg)
        result = guard.check_dedup(seen, msg)
        assert result is not None
        assert "Repeated" in result

    def test_hint_stored_in_diagnostic_on_block(self) -> None:
        """Dedup guard must store hint in diagnostics; history must not be modified."""
        cfg = _cfg(tool_dedup_max_repeats=2)
        ctx = _make_ctx(cfg)
        guard = ToolLoopGuard(ctx)
        seen: dict[str, int] = {}
        guard.check_dedup(seen, _msg("write_file"))
        result = guard.check_dedup(seen, _msg("write_file"))
        assert result is not None
        assert len(ctx.conv.history) == 0
        ctx.diagnostics.save.assert_called_once()
        call_args = ctx.diagnostics.save.call_args
        assert call_args[0][1] == "guard_hint"


class TestCheckRetry:
    def test_retry_max_zero_disabled(self) -> None:
        cfg = _cfg(tool_error_retry_max=0)
        ctx = _make_ctx(cfg)
        guard = ToolLoopGuard(ctx)
        assert guard.check_retry(set(), _msg("write_file")) is None

    def test_not_in_failed_set_returns_none(self) -> None:
        ctx = _make_ctx()
        guard = ToolLoopGuard(ctx)
        result = guard.check_retry(set(), _msg("write_file"))
        assert result is None

    def test_retry_of_failed_call_blocked(self) -> None:
        from shared.tool_executor_helpers import tool_hash_key

        ctx = _make_ctx()
        guard = ToolLoopGuard(ctx)
        failed: set[str] = {tool_hash_key("write_file", {})}
        result = guard.check_retry(failed, _msg("write_file"))
        assert result is not None
        assert "Repeated failed" in result

    def test_invalid_json_args_handles_gracefully(self) -> None:
        ctx = _make_ctx()
        guard = ToolLoopGuard(ctx)
        msg = {
            "tool_calls": [
                {
                    "function": {
                        "name": "write_file",
                        "arguments": "not valid json",
                    }
                }
            ]
        }
        result = guard.check_retry(set(), msg)
        assert result is None

    def test_failed_call_tracking_no_collision_across_tools(self) -> None:
        """Verify that failed-call tracking does not collide across different tools."""
        from shared.tool_executor_helpers import tool_hash_key

        ctx = _make_ctx()
        guard = ToolLoopGuard(ctx)

        # Track failure for write_file only (empty args matching _msg pattern)
        failed_calls: set[str] = {tool_hash_key("write_file", {})}

        # read_file with identical empty args should NOT be blocked
        msg_read = _msg("read_file")
        result_read = guard.check_retry(failed_calls, msg_read)
        assert result_read is None

        # write_file with identical empty args SHOULD be blocked
        msg_write = _msg("write_file")
        result_write = guard.check_retry(failed_calls, msg_write)
        assert result_write is not None
        assert "Repeated failed" in result_write


class TestCheckAll:
    def test_runs_in_order_and_stops_on_first_hit(self) -> None:
        ctx = _make_ctx()
        guard = ToolLoopGuard(ctx)
        state = _state()
        msg = _msg("write_file")
        result = guard.check_all(
            state.seen_calls, state.round_fingerprints, state.failed_calls, msg
        )
        assert result is None

    def test_cycle_checked_before_dedup(self) -> None:
        ctx = _make_ctx()
        guard = ToolLoopGuard(ctx)
        state = _state()
        msg = _msg("write_file")
        guard.check_all(
            state.seen_calls, state.round_fingerprints, state.failed_calls, msg
        )
        guard.check_all(
            state.seen_calls, state.round_fingerprints, state.failed_calls, msg
        )
        r3 = guard.check_all(
            state.seen_calls, state.round_fingerprints, state.failed_calls, msg
        )
        assert r3 is not None
        assert "Cyclic" in r3


class TestUpdateErrors:
    def test_all_failed_increments(self) -> None:
        result = ToolLoopGuard.update_errors(0, 3, 3)
        assert result == 1

    def test_partial_failure_maintains_count(self) -> None:
        result = ToolLoopGuard.update_errors(5, 1, 3)
        assert result == 5

    def test_zero_tool_calls_no_increment(self) -> None:
        result = ToolLoopGuard.update_errors(0, 0, 0)
        assert result == 1

    def test_no_errors_resets_even_with_prior_errors(self) -> None:
        result = ToolLoopGuard.update_errors(2, 0, 3)
        assert result == 0


class TestCheckErrorLimit:
    def test_limit_zero_disabled(self) -> None:
        cfg = _cfg(tool_error_max_consecutive=0)
        ctx = _make_ctx(cfg)
        guard = ToolLoopGuard(ctx)
        assert guard.check_error_limit(10) is None

    def test_below_limit_returns_none(self) -> None:
        ctx = _make_ctx()
        guard = ToolLoopGuard(ctx)
        assert guard.check_error_limit(2) is None

    def test_at_limit_returns_exit_message(self) -> None:
        ctx = _make_ctx()
        guard = ToolLoopGuard(ctx)
        result = guard.check_error_limit(3)
        assert result is not None
        assert "consecutive" in result.lower()

    def test_above_limit_also_triggers(self) -> None:
        ctx = _make_ctx()
        guard = ToolLoopGuard(ctx)
        assert guard.check_error_limit(5) is not None


class TestCanonicalKeyConsistency:
    def test_same_args_different_json_order_produce_same_key(self) -> None:
        """check_dedup and check_retry agree even when JSON key order differs."""
        key1 = ToolLoopGuard._canonical_key(
            "write_file", '{"path": "a", "content": "b"}'
        )
        key2 = ToolLoopGuard._canonical_key(
            "write_file", '{"content": "b", "path": "a"}'
        )
        assert key1 == key2

    def test_different_args_produce_different_key(self) -> None:
        key1 = ToolLoopGuard._canonical_key("write_file", '{"path": "a"}')
        key2 = ToolLoopGuard._canonical_key("write_file", '{"path": "b"}')
        assert key1 != key2

    def test_invalid_json_falls_back_to_empty_dict(self) -> None:
        from shared.tool_executor_helpers import tool_hash_key

        key = ToolLoopGuard._canonical_key("write_file", "INVALID_JSON")
        expected = tool_hash_key("write_file", {})
        assert key == expected


class TestUpdateErrorsPartialFailure:
    def test_all_failed_increments(self) -> None:
        assert ToolLoopGuard.update_errors(2, 3, 3) == 3

    def test_all_succeeded_resets(self) -> None:
        assert ToolLoopGuard.update_errors(2, 0, 3) == 0

    def test_partial_failure_maintains_count(self) -> None:
        assert ToolLoopGuard.update_errors(2, 1, 3) == 2


class TestCheckRetryHint:
    def test_check_retry_diagnostics_uses_retry_hint(self) -> None:
        """check_retry stores RETRY_HINT (not DEDUP_HINT) in diagnostics."""
        from agent.tool_loop_guard import RETRY_HINT, ToolLoopGuard

        ctx = _make_ctx()
        ctx.diagnostics = MagicMock()
        saved = []
        ctx.diagnostics.save = lambda *a: saved.append(orjson.loads(a[2]))

        from shared.tool_executor_helpers import tool_hash_key

        key = tool_hash_key("write_file", {"path": "a"})
        failed_calls = {key}
        message: dict = {
            "role": "assistant",
            "tool_calls": [
                {"function": {"name": "write_file", "arguments": '{"path":"a"}'}}
            ],
        }
        guard = ToolLoopGuard(ctx)
        result = guard.check_retry(failed_calls, message)
        assert result is not None
        assert any(d.get("hint") == RETRY_HINT for d in saved)
