"""
tests/test_ephemeral_filtering_security.py

Characterization tests for ephemeral message filtering hardening.
Verifies current behavior of message_schema.validate_message().
"""

from __future__ import annotations

from agent.message_schema import (
    TRUSTED_SOURCES,
    get_allowed_ephemeral_keys,
    is_trusted_source,
    validate_message,
)

# ── Fake ephemeral key injection — message with fake _ephemeral key filtered out ──


class TestFakeEphemeralKeyInjection:
    """Verify message with fake _ephemeral key is filtered out."""

    def test_untrusted_source_with_ephemeral_key_rejected(self) -> None:
        """Untrusted source cannot inject _ephemeral key."""
        result = validate_message({"role": "user", "content": "hi", "_ephemeral": True})
        assert result.success is False
        assert "Ephemeral keys not allowed" in result.reason

    def test_untrusted_source_with_memory_injected_key_rejected(self) -> None:
        """Untrusted source cannot inject _memory_injected key."""
        result = validate_message(
            {"role": "user", "content": "hi", "_memory_injected": True}
        )
        assert result.success is False
        assert "Ephemeral keys not allowed" in result.reason

    def test_untrusted_source_with_skill_ephemeral_key_rejected(self) -> None:
        """Untrusted source cannot inject _skill_ephemeral key."""
        result = validate_message(
            {"role": "user", "content": "hi", "_skill_ephemeral": True}
        )
        assert result.success is False
        assert "Ephemeral keys not allowed" in result.reason

    def test_unknown_role_with_ephemeral_key_rejected(self) -> None:
        """Unknown role with ephemeral key is rejected before ephemeral check."""
        result = validate_message(
            {"role": "unknown", "content": "hi", "_ephemeral": True}
        )
        assert result.success is False
        assert "Unknown role" in result.reason

    def test_no_source_field_with_ephemeral_key_rejected(self) -> None:
        """No source field means ephemeral keys are rejected."""
        result = validate_message({"role": "user", "content": "hi", "_ephemeral": True})
        assert result.success is False
        assert "Ephemeral keys not allowed" in result.reason

    def test_empty_source_field_with_ephemeral_key_rejected(self) -> None:
        """Empty source field means ephemeral keys are rejected."""
        result = validate_message(
            {"role": "user", "content": "hi", "_ephemeral": True, "source": ""}
        )
        assert result.success is False
        assert "Ephemeral keys not allowed" in result.reason

    def test_non_ephemeral_extra_key_without_source_rejected(self) -> None:
        """Non-ephemeral extra key without trusted source is rejected."""
        result = validate_message(
            {"role": "user", "content": "hi", "custom_key": "value"}
        )
        assert result.success is False
        assert "Unexpected keys" in result.reason

    def test_multiple_ephemeral_keys_from_untrusted_source_rejected(self) -> None:
        """Multiple ephemeral keys from untrusted source are all rejected."""
        result = validate_message(
            {
                "role": "user",
                "content": "hi",
                "_ephemeral": True,
                "_memory_injected": True,
            }
        )
        assert result.success is False
        assert "Ephemeral keys not allowed" in result.reason

    def test_fake_ephemeral_key_on_assistant_rejected(self) -> None:
        """Assistant message with fake _ephemeral key is rejected."""
        result = validate_message(
            {"role": "assistant", "content": "hi", "_ephemeral": True}
        )
        assert result.success is False
        assert "Ephemeral keys not allowed" in result.reason

    def test_fake_ephemeral_key_on_tool_rejected(self) -> None:
        """Tool message with fake _ephemeral key is rejected."""
        result = validate_message(
            {
                "role": "tool",
                "content": "done",
                "tool_call_id": "123",
                "_ephemeral": True,
            }
        )
        assert result.success is False
        assert "Ephemeral keys not allowed" in result.reason


# ── Message structure validation — malformed messages caught by validation ──


class TestMessageStructureValidation:
    """Verify malformed messages caught by validation."""

    def test_missing_role_rejected(self) -> None:
        """Message without role field is rejected."""
        result = validate_message({"content": "hi"})
        assert result.success is False
        assert "Missing 'role'" in result.reason

    def test_missing_content_rejected(self) -> None:
        """Message without content field is rejected."""
        result = validate_message({"role": "user"})
        assert result.success is False
        assert "Missing 'content'" in result.reason

    def test_both_missing_rejected(self) -> None:
        """Message missing both role and content is rejected."""
        result = validate_message({})
        assert result.success is False
        assert "Missing 'role'" in result.reason

    def test_none_role_rejected(self) -> None:
        """None as role is rejected."""
        result = validate_message({"role": None, "content": "hi"})
        assert result.success is False
        assert "Unknown role" in result.reason

    def test_empty_role_rejected(self) -> None:
        """Empty string as role is rejected."""
        result = validate_message({"role": "", "content": "hi"})
        assert result.success is False
        assert "Unknown role" in result.reason

    def test_valid_user_message_accepted(self) -> None:
        """Valid user message passes validation."""
        result = validate_message({"role": "user", "content": "hello"})
        assert result.success is True
        assert result.reason == ""

    def test_valid_system_message_accepted(self) -> None:
        """Valid system message passes validation."""
        result = validate_message({"role": "system", "content": "instructions"})
        assert result.success is True
        assert result.reason == ""

    def test_valid_assistant_message_accepted(self) -> None:
        """Valid assistant message passes validation."""
        result = validate_message({"role": "assistant", "content": "response"})
        assert result.success is True
        assert result.reason == ""

    def test_valid_assistant_with_tool_calls_accepted(self) -> None:
        """Valid assistant message with tool_calls passes validation."""
        result = validate_message(
            {
                "role": "assistant",
                "content": "calling tools",
                "tool_calls": [
                    {"id": "1", "type": "function", "function": {"name": "test"}}
                ],
            }
        )
        assert result.success is True
        assert result.reason == ""

    def test_valid_tool_message_accepted(self) -> None:
        """Valid tool message passes validation."""
        result = validate_message(
            {
                "role": "tool",
                "content": "result",
                "tool_call_id": "123",
            }
        )
        assert result.success is True
        assert result.reason == ""

    def test_system_with_priority_accepted(self) -> None:
        """System message with priority field passes validation."""
        result = validate_message(
            {"role": "system", "content": "instructions", "priority": "high"}
        )
        assert result.success is True
        assert result.reason == ""

    def test_user_with_unknown_extra_key_rejected(self) -> None:
        """User message with unknown extra key is rejected."""
        result = validate_message({"role": "user", "content": "hi", "unknown": "field"})
        assert result.success is False
        assert "Unexpected keys" in result.reason

    def test_assistant_with_unknown_extra_key_rejected(self) -> None:
        """Assistant message with unknown extra key is rejected."""
        result = validate_message(
            {"role": "assistant", "content": "hi", "unknown": "field"}
        )
        assert result.success is False
        assert "Unexpected keys" in result.reason

    def test_tool_with_unknown_extra_key_rejected(self) -> None:
        """Tool message with unknown extra key is rejected."""
        result = validate_message(
            {"role": "tool", "content": "hi", "tool_call_id": "1", "unknown": "field"}
        )
        assert result.success is False
        assert "Unexpected keys" in result.reason

    def test_system_with_unknown_extra_key_rejected(self) -> None:
        """System message with unknown extra key is rejected."""
        result = validate_message(
            {"role": "system", "content": "hi", "unknown": "field"}
        )
        assert result.success is False
        assert "Unexpected keys" in result.reason


# ── Ephemeral-only-from-trusted-sources — rejection from non-command handlers ──


class TestEphemeralOnlyFromTrustedSources:
    """Verify ephemeral messages from non-command handlers are rejected."""

    def test_cmd_handler_can_use_ephemeral(self) -> None:
        """cmd_handler can inject _ephemeral key."""
        result = validate_message(
            {
                "role": "user",
                "content": "hi",
                "_ephemeral": True,
                "source": "cmd_handler",
            }
        )
        assert result.success is True
        assert result.reason == ""

    def test_cmd_handler_cannot_use_memory_injected(self) -> None:
        """cmd_handler cannot inject _memory_injected key."""
        result = validate_message(
            {
                "role": "user",
                "content": "hi",
                "_memory_injected": True,
                "source": "cmd_handler",
            }
        )
        assert result.success is False
        assert "Unauthorized ephemeral keys" in result.reason

    def test_cmd_handler_cannot_use_skill_ephemeral(self) -> None:
        """cmd_handler cannot inject _skill_ephemeral key."""
        result = validate_message(
            {
                "role": "user",
                "content": "hi",
                "_skill_ephemeral": True,
                "source": "cmd_handler",
            }
        )
        assert result.success is False
        assert "Unauthorized ephemeral keys" in result.reason

    def test_memory_injection_can_use_memory_injected(self) -> None:
        """memory_injection can inject _memory_injected key."""
        result = validate_message(
            {
                "role": "system",
                "content": "injected",
                "_memory_injected": True,
                "source": "memory_injection",
            }
        )
        assert result.success is True
        assert result.reason == ""

    def test_memory_injection_cannot_use_ephemeral(self) -> None:
        """memory_injection cannot inject _ephemeral key."""
        result = validate_message(
            {
                "role": "system",
                "content": "injected",
                "_ephemeral": True,
                "source": "memory_injection",
            }
        )
        assert result.success is False
        assert "Unauthorized ephemeral keys" in result.reason

    def test_memory_injection_cannot_use_skill_ephemeral(self) -> None:
        """memory_injection cannot inject _skill_ephemeral key."""
        result = validate_message(
            {
                "role": "system",
                "content": "injected",
                "_skill_ephemeral": True,
                "source": "memory_injection",
            }
        )
        assert result.success is False
        assert "Unauthorized ephemeral keys" in result.reason

    def test_skill_mixin_can_use_skill_ephemeral(self) -> None:
        """skill_mixin can inject _skill_ephemeral key."""
        result = validate_message(
            {
                "role": "system",
                "content": "skill hint",
                "_skill_ephemeral": True,
                "source": "skill_mixin",
            }
        )
        assert result.success is True
        assert result.reason == ""

    def test_skill_mixin_cannot_use_ephemeral(self) -> None:
        """skill_mixin cannot inject _ephemeral key."""
        result = validate_message(
            {
                "role": "system",
                "content": "skill hint",
                "_ephemeral": True,
                "source": "skill_mixin",
            }
        )
        assert result.success is False
        assert "Unauthorized ephemeral keys" in result.reason

    def test_skill_mixin_cannot_use_memory_injected(self) -> None:
        """skill_mixin cannot inject _memory_injected key."""
        result = validate_message(
            {
                "role": "system",
                "content": "skill hint",
                "_memory_injected": True,
                "source": "skill_mixin",
            }
        )
        assert result.success is False
        assert "Unauthorized ephemeral keys" in result.reason

    def test_multiple_ephemeral_keys_from_trusted_source_partial_failure(self) -> None:
        """Trusted source with multiple ephemeral keys of mixed authorization fails."""
        result = validate_message(
            {
                "role": "system",
                "content": "hint",
                "_skill_ephemeral": True,
                "_ephemeral": True,
                "source": "skill_mixin",
            }
        )
        assert result.success is False
        assert "Unauthorized ephemeral keys" in result.reason

    def test_is_trusted_source_returns_true_for_known_sources(self) -> None:
        """is_trusted_source returns True for known sources."""
        assert is_trusted_source("cmd_handler") is True
        assert is_trusted_source("memory_injection") is True
        assert is_trusted_source("skill_mixin") is True

    def test_is_trusted_source_returns_false_for_unknown_sources(self) -> None:
        """is_trusted_source returns False for unknown sources."""
        assert is_trusted_source("unknown") is False
        assert is_trusted_source("") is False
        assert is_trusted_source("llm_response") is False

    def test_get_allowed_ephemeral_keys_returns_correct_set(self) -> None:
        """get_allowed_ephemeral_keys returns correct ephemeral keys per source."""
        assert get_allowed_ephemeral_keys("cmd_handler") == {"_ephemeral"}
        assert get_allowed_ephemeral_keys("memory_injection") == {"_memory_injected"}
        assert get_allowed_ephemeral_keys("skill_mixin") == {"_skill_ephemeral"}

    def test_get_allowed_ephemeral_keys_returns_empty_for_unknown(self) -> None:
        """get_allowed_ephemeral_keys returns empty set for unknown source."""
        assert get_allowed_ephemeral_keys("unknown") == set()

    def test_trusted_sources_dict_has_expected_entries(self) -> None:
        """TRUSTED_SOURCES dict has expected entries."""
        assert set(TRUSTED_SOURCES.keys()) == {
            "cmd_handler",
            "memory_injection",
            "skill_mixin",
        }
        assert TRUSTED_SOURCES["cmd_handler"] == {"_ephemeral"}
        assert TRUSTED_SOURCES["memory_injection"] == {"_memory_injected"}
        assert TRUSTED_SOURCES["skill_mixin"] == {"_skill_ephemeral"}


# ── Filtering preserves persistent messages — without ephemeral keys preserved ──


class TestFilteringPreservesPersistentMessages:
    """Verify messages without ephemeral keys are preserved."""

    def test_plain_user_message_preserved(self) -> None:
        """Plain user message without ephemeral keys is preserved."""
        result = validate_message({"role": "user", "content": "hello"})
        assert result.success is True
        assert result.reason == ""

    def test_plain_system_message_preserved(self) -> None:
        """Plain system message without ephemeral keys is preserved."""
        result = validate_message({"role": "system", "content": "instructions"})
        assert result.success is True
        assert result.reason == ""

    def test_plain_assistant_message_preserved(self) -> None:
        """Plain assistant message without ephemeral keys is preserved."""
        result = validate_message({"role": "assistant", "content": "response"})
        assert result.success is True
        assert result.reason == ""

    def test_plain_tool_message_preserved(self) -> None:
        """Plain tool message without ephemeral keys is preserved."""
        result = validate_message(
            {"role": "tool", "content": "result", "tool_call_id": "123"}
        )
        assert result.success is True
        assert result.reason == ""

    def test_user_with_tool_calls_not_accepted(self) -> None:
        """User message with tool_calls field is rejected (not allowed for user role)."""
        result = validate_message({"role": "user", "content": "hi", "tool_calls": []})
        assert result.success is False
        assert "Unexpected keys" in result.reason

    def test_assistant_without_tool_calls_accepted(self) -> None:
        """Assistant message without tool_calls is accepted."""
        result = validate_message({"role": "assistant", "content": "simple response"})
        assert result.success is True
        assert result.reason == ""
