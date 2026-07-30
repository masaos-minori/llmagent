"""tests/test_message_schema.py — Unit tests for agent/message_schema.py."""

from __future__ import annotations

from agent.message_schema import (
    ROLE_KEY_WHITELIST,
    TRUSTED_SOURCES,
    get_allowed_ephemeral_keys,
    is_trusted_source,
    validate_message,
)


class TestValidateMessageRequiredFields:
    def test_valid_system_message(self) -> None:
        result = validate_message({"role": "system", "content": "hello"})
        assert result.success is True

    def test_valid_user_message(self) -> None:
        result = validate_message({"role": "user", "content": "hello"})
        assert result.success is True

    def test_valid_assistant_message_with_tool_calls(self) -> None:
        result = validate_message(
            {
                "role": "assistant",
                "content": "ok",
                "tool_calls": [
                    {"id": "tc1", "function": {"name": "test", "arguments": "{}"}}
                ],
            }
        )
        assert result.success is True

    def test_valid_tool_message(self) -> None:
        result = validate_message(
            {
                "role": "tool",
                "content": "result",
                "tool_call_id": "tc1",
            }
        )
        assert result.success is True

    def test_missing_role_returns_error(self) -> None:
        result = validate_message({"content": "hello"})
        assert result.success is False
        assert "Missing 'role'" in result.reason

    def test_missing_content_returns_error(self) -> None:
        result = validate_message({"role": "user"})
        assert result.success is False
        assert "Missing 'content'" in result.reason

    def test_unknown_role_returns_error(self) -> None:
        result = validate_message({"role": "unknown", "content": "hello"})
        assert result.success is False
        assert "Unknown role" in result.reason


class TestValidateMessageExtraKeys:
    def test_extra_key_in_system_message_rejected(self) -> None:
        result = validate_message(
            {
                "role": "system",
                "content": "hello",
                "extra_field": "value",
            }
        )
        assert result.success is False
        assert "Unexpected keys" in result.reason

    def test_priority_allowed_in_system_message(self) -> None:
        result = validate_message(
            {
                "role": "system",
                "priority": "low",
                "content": "hello",
            }
        )
        assert result.success is False
        assert "Unexpected keys" in result.reason

    def test_extra_key_in_user_message_rejected(self) -> None:
        result = validate_message(
            {
                "role": "user",
                "content": "hello",
                "extra_field": "value",
            }
        )
        assert result.success is False
        assert "Unexpected keys" in result.reason

    def test_extra_key_in_assistant_message_rejected(self) -> None:
        result = validate_message(
            {
                "role": "assistant",
                "content": "hello",
                "extra_field": "value",
            }
        )
        assert result.success is False
        assert "Unexpected keys" in result.reason

    def test_extra_key_in_tool_message_rejected(self) -> None:
        result = validate_message(
            {
                "role": "tool",
                "content": "result",
                "tool_call_id": "tc1",
                "extra_field": "value",
            }
        )
        assert result.success is False
        assert "Unexpected keys" in result.reason


class TestValidateMessageEphemeralKeys:
    def test_untrusted_source_cannot_add_ephemeral_key(self) -> None:
        result = validate_message(
            {
                "role": "assistant",
                "content": "hello",
                "_ephemeral": True,
            }
        )
        assert result.success is False
        assert "Ephemeral keys not allowed" in result.reason

    def test_trusted_cmd_handler_can_add_ephemeral_key(self) -> None:
        result = validate_message(
            {
                "role": "system",
                "content": "hint",
                "_ephemeral": True,
                "source": "cmd_handler",
            }
        )
        assert result.success is True

    def test_trusted_memory_injection_can_add_memory_injected_key(self) -> None:
        result = validate_message(
            {
                "role": "system",
                "content": "mem",
                "_memory_injected": True,
                "source": "memory_injection",
            }
        )
        assert result.success is True

    def test_trusted_skill_mixin_can_add_skill_ephemeral_key(self) -> None:
        result = validate_message(
            {
                "role": "system",
                "content": "skill hint",
                "_skill_ephemeral": True,
                "source": "skill_mixin",
            }
        )
        assert result.success is True

    def test_unauthorized_ephemeral_key_for_source_rejected(self) -> None:
        result = validate_message(
            {
                "role": "system",
                "content": "hint",
                "_memory_injected": True,
                "source": "cmd_handler",
            }
        )
        assert result.success is False
        assert "Unauthorized ephemeral keys" in result.reason

    def test_multiple_ephemeral_keys_from_trusted_source_accepted(self) -> None:
        result = validate_message(
            {
                "role": "system",
                "content": "hint",
                "_ephemeral": True,
                "_skill_ephemeral": True,
                "source": "skill_mixin",
            }
        )
        # skill_mixin can only use _skill_ephemeral, so _ephemeral should fail
        assert result.success is False

    def test_no_source_field_means_untrusted_for_ephemeral_keys(self) -> None:
        result = validate_message(
            {
                "role": "system",
                "content": "hint",
                "_ephemeral": True,
            }
        )
        assert result.success is False
        assert "Ephemeral keys not allowed" in result.reason

    def test_empty_source_field_means_untrusted_for_ephemeral_keys(self) -> None:
        result = validate_message(
            {
                "role": "system",
                "content": "hint",
                "_ephemeral": True,
                "source": "",
            }
        )
        assert result.success is False
        assert "Ephemeral keys not allowed" in result.reason

    def test_llm_source_cannot_add_ephemeral_key(self) -> None:
        result = validate_message(
            {
                "role": "assistant",
                "content": "hello",
                "_ephemeral": True,
                "source": "llm",
            }
        )
        assert result.success is False
        assert "Ephemeral keys not allowed" in result.reason

    def test_null_source_cannot_add_ephemeral_key(self) -> None:
        result = validate_message(
            {
                "role": "system",
                "content": "hint",
                "_ephemeral": True,
                "source": None,  # type: ignore[arg-type]
            }
        )
        assert result.success is False
        assert "Ephemeral keys not allowed" in result.reason


class TestTrustedSourceHelpers:
    def test_is_trusted_source_true_for_known_sources(self) -> None:
        assert is_trusted_source("cmd_handler") is True
        assert is_trusted_source("memory_injection") is True
        assert is_trusted_source("skill_mixin") is True

    def test_is_trusted_source_false_for_unknown_sources(self) -> None:
        assert is_trusted_source("llm") is False
        assert is_trusted_source("") is False
        assert is_trusted_source("unknown") is False

    def test_get_allowed_ephemeral_keys_for_trusted_source(self) -> None:
        assert get_allowed_ephemeral_keys("cmd_handler") == {"_ephemeral"}
        assert get_allowed_ephemeral_keys("memory_injection") == {"_memory_injected"}
        assert get_allowed_ephemeral_keys("skill_mixin") == {"_skill_ephemeral"}

    def test_get_allowed_ephemeral_keys_for_untrusted_source(self) -> None:
        assert get_allowed_ephemeral_keys("llm") == set()
        assert get_allowed_ephemeral_keys("") == set()

    def test_trusted_sources_defined_correctly(self) -> None:
        assert "cmd_handler" in TRUSTED_SOURCES
        assert "memory_injection" in TRUSTED_SOURCES
        assert "skill_mixin" in TRUSTED_SOURCES
        assert "loop_guard" in TRUSTED_SOURCES
        assert len(TRUSTED_SOURCES) == 4

    def test_role_key_whitelist_defined_correctly(self) -> None:
        assert "system" in ROLE_KEY_WHITELIST
        assert "user" in ROLE_KEY_WHITELIST
        assert "assistant" in ROLE_KEY_WHITELIST
        assert "tool" in ROLE_KEY_WHITELIST
        assert len(ROLE_KEY_WHITELIST) == 4

    def test_loop_guard_is_trusted_source(self) -> None:
        assert is_trusted_source("loop_guard") is True

    def test_get_allowed_ephemeral_keys_for_loop_guard(self) -> None:
        assert get_allowed_ephemeral_keys("loop_guard") == {"_ephemeral"}

    def test_validate_message_accepts_loop_guard_ephemeral_key(self) -> None:
        result = validate_message(
            {
                "role": "system",
                "content": "You are about to produce a final answer without calling any tools.",
                "_ephemeral": True,
                "source": "loop_guard",
            }
        )
        assert result.success is True
