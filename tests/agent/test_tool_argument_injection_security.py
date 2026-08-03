"""tests/test_tool_argument_injection_security.py

Guard tests for tool argument injection prevention.

These tests document current behavior to establish a baseline before
any future refactoring of the tool runner layer.
"""

from __future__ import annotations

from agent.tool_arg_validator import (
    ValidationResult,
    register_custom_validator,
    validate_tool_arguments,
)


class TestUnexpectedFieldRejection:
    """Verify unexpected field injection is rejected."""

    def test_extra_field_rejected_by_default(self) -> None:
        """When allow_extra_fields=False (default), extra fields are rejected."""
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"],
        }
        result = validate_tool_arguments(
            "test_tool",
            {"name": "test", "__meta": "injected"},
            schema,
        )
        assert result.success is False
        assert "Extra fields not allowed" in result.reason

    def test_extra_field_allowed_when_flag_set(self) -> None:
        """When allow_extra_fields=True, extra fields pass through."""
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"],
        }
        result = validate_tool_arguments(
            "test_tool",
            {"name": "test", "__meta": "injected"},
            schema,
            allow_extra_fields=True,
        )
        assert result.success is True

    def test_no_schema_allows_any_field(self) -> None:
        """Without a schema, all fields are accepted regardless of allow_extra_fields."""
        result = validate_tool_arguments(
            "test_tool",
            {"name": "test", "__meta": "injected"},
            {},
        )
        assert result.success is True

    def test_no_properties_key_allows_any_field(self) -> None:
        """Schema without 'properties' key allows any field even with allow_extra_fields=False."""
        schema = {"type": "object", "required": ["name"]}
        result = validate_tool_arguments(
            "test_tool",
            {"name": "test", "__meta": "injected"},
            schema,
        )
        assert result.success is True

    def test_multiple_extra_fields_all_reported(self) -> None:
        """Multiple extra fields are reported together."""
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"],
        }
        result = validate_tool_arguments(
            "test_tool",
            {"name": "test", "__meta": "injected", "_secret": "leaked"},
            schema,
        )
        assert result.success is False
        assert "__meta" in result.reason
        assert "_secret" in result.reason

    def test_malicious_meta_field_rejected(self) -> None:
        """Known malicious meta fields are rejected by default."""
        schema = {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        }
        result = validate_tool_arguments(
            "search",
            {"query": "test", "__ignore_instructions": "true"},
            schema,
        )
        assert result.success is False
        assert "__ignore_instructions" in result.reason


class TestSchemaValidationCatchesViolations:
    """Verify schema validation catches violations."""

    def test_missing_required_field_rejected(self) -> None:
        """Missing required field is caught by validation."""
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"],
        }
        result = validate_tool_arguments("test_tool", {}, schema)
        assert result.success is False
        assert "Missing required fields" in result.reason

    def test_type_mismatch_rejected(self) -> None:
        """Type mismatch is caught by jsonschema validation."""
        schema = {
            "type": "object",
            "properties": {"count": {"type": "integer"}},
            "required": ["count"],
        }
        result = validate_tool_arguments(
            "test_tool", {"count": "not_an_integer"}, schema
        )
        assert result.success is False
        assert "Type mismatch" in result.reason

    def test_nested_object_type_violation(self) -> None:
        """Nested object type violation is caught."""
        schema = {
            "type": "object",
            "properties": {
                "config": {
                    "type": "object",
                    "properties": {"debug": {"type": "boolean"}},
                    "required": ["debug"],
                }
            },
            "required": ["config"],
        }
        result = validate_tool_arguments(
            "test_tool", {"config": {"debug": "yes"}}, schema
        )
        assert result.success is False
        assert "Type mismatch" in result.reason

    def test_array_item_type_violation(self) -> None:
        """Array item type violation is caught."""
        schema = {
            "type": "object",
            "properties": {
                "items": {
                    "type": "array",
                    "items": {"type": "integer"},
                }
            },
            "required": ["items"],
        }
        result = validate_tool_arguments("test_tool", {"items": [1, "two", 3]}, schema)
        assert result.success is False
        assert "Type mismatch" in result.reason

    def test_null_value_for_non_nullable_field(self) -> None:
        """Null value for non-nullable string field is rejected."""
        schema = {
            "type": "object",
            "properties": {"value": {"type": "string"}},
            "required": ["value"],
        }
        result = validate_tool_arguments("set_value", {"value": None}, schema)
        assert result.success is False
        assert "Type mismatch" in result.reason

    def test_validation_short_circuits_on_first_error(self) -> None:
        """Validation stops at the first error (short-circuit)."""
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"],
        }
        # Missing required + extra field — only one error returned
        result = validate_tool_arguments("test_tool", {"extra": "field"}, schema)
        assert result.success is False
        assert len(result.reason.split("\n")) == 1

    def test_validation_order_required_then_extra_then_type(self) -> None:
        """Validation order: required → extra → type."""
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"],
        }
        # Wrong type for existing field — should report type mismatch since required check passes
        result = validate_tool_arguments("test_tool", {"name": 123}, schema)
        assert result.success is False
        assert "Type mismatch" in result.reason

    def test_custom_validator_catches_business_rule_violation(self) -> None:
        """Custom validator catches business rule violations beyond schema checks."""
        from agent.tool_arg_validator import _CUSTOM_VALIDATORS

        saved = dict(_CUSTOM_VALIDATORS)
        _CUSTOM_VALIDATORS.clear()

        try:

            @register_custom_validator("custom_tool")
            def custom_validator(args: dict) -> ValidationResult:
                return ValidationResult(success=False, reason="business rule violated")

            schema = {
                "type": "object",
                "properties": {"count": {"type": "integer"}},
                "required": ["count"],
            }
            result = validate_tool_arguments("custom_tool", {"count": 1}, schema)
            assert result.success is False
            assert result.reason == "business rule violated"
        finally:
            _CUSTOM_VALIDATORS.clear()
            _CUSTOM_VALIDATORS.update(saved)

    def test_hook_not_called_when_earlier_checks_fail(self) -> None:
        """Custom hooks must not run when required/extra/type checks already failed."""
        from agent.tool_arg_validator import _CUSTOM_VALIDATORS

        calls: list[dict] = []
        saved = dict(_CUSTOM_VALIDATORS)
        _CUSTOM_VALIDATORS.clear()

        try:

            @register_custom_validator("hooked_tool")
            def _validator(args: dict) -> ValidationResult:
                calls.append(args)
                return ValidationResult(success=True)

            schema = {
                "type": "object",
                "properties": {"count": {"type": "integer"}},
                "required": ["count"],
            }
            result = validate_tool_arguments("hooked_tool", {}, schema)
            assert result.success is False
            assert calls == []
        finally:
            _CUSTOM_VALIDATORS.clear()
            _CUSTOM_VALIDATORS.update(saved)


class TestWhitelistFilteringEnforced:
    """Verify whitelist filtering enforces strict field lists."""

    def test_schema_properties_as_whitelist(self) -> None:
        """Schema properties act as a whitelist when allow_extra_fields=False."""
        schema = {
            "type": "object",
            "properties": {"allowed_field": {"type": "string"}},
            "required": [],
        }
        result = validate_tool_arguments(
            "test_tool",
            {"allowed_field": "ok", "blocked_field": "no"},
            schema,
        )
        assert result.success is False
        assert "blocked_field" in result.reason

    def test_only_whitelisted_fields_pass_through(self) -> None:
        """Only whitelisted fields pass through validation."""
        schema = {
            "type": "object",
            "properties": {"a": {"type": "string"}, "b": {"type": "integer"}},
            "required": [],
        }
        result = validate_tool_arguments("test_tool", {"a": "hello", "b": 42}, schema)
        assert result.success is True

    def test_empty_properties_allows_any_field(self) -> None:
        """Empty properties means no whitelist to enforce — any field passes."""
        schema = {"type": "object", "properties": {}, "required": []}
        result = validate_tool_arguments("test_tool", {"any_field": "value"}, schema)
        assert result.success is True
