"""tests/test_tool_arg_validator.py

Unit tests for tool_arg_validator.py: schema-based argument validation.
"""

from __future__ import annotations

import pytest
from agent.tool_arg_validator import (
    _CUSTOM_VALIDATORS,
    ValidationResult,
    register_custom_validator,
    validate_tool_arguments,
)


class TestValidationResult:
    def test_success_defaults_reason_to_empty(self) -> None:
        v = ValidationResult(success=True)
        assert v.success is True
        assert v.reason == ""

    def test_failure_contains_reason(self) -> None:
        v = ValidationResult(success=False, reason="missing fields")
        assert v.success is False
        assert v.reason == "missing fields"

    def test_frozen_dataclass_cannot_be_modified(self) -> None:
        v = ValidationResult(success=True)
        with pytest.raises(Exception):
            v.success = False


class TestValidateToolArgumentsEmptySchema:
    def test_none_schema_skips_validation(self) -> None:
        result = validate_tool_arguments("read_file", {"path": "/tmp/f"}, {})
        assert result.success is True

    def test_empty_dict_schema_skips_validation(self) -> None:
        result = validate_tool_arguments("read_file", {"path": "/tmp/f"}, {})
        assert result.success is True

    def test_missing_required_with_empty_schema(self) -> None:
        schema: dict = {}
        result = validate_tool_arguments("read_file", {}, schema)
        assert result.success is True


class TestValidateToolArgumentsRequiredFields:
    def test_all_required_fields_present(self) -> None:
        schema = {
            "type": "object",
            "required": ["path", "mode"],
            "properties": {
                "path": {"type": "string"},
                "mode": {"type": "string"},
            },
        }
        result = validate_tool_arguments(
            "read_file", {"path": "/tmp/f", "mode": "r"}, schema
        )
        assert result.success is True

    def test_missing_one_required_field(self) -> None:
        schema = {
            "type": "object",
            "required": ["path", "mode"],
            "properties": {
                "path": {"type": "string"},
                "mode": {"type": "string"},
            },
        }
        result = validate_tool_arguments("read_file", {"path": "/tmp/f"}, schema)
        assert result.success is False
        assert "Missing required fields" in result.reason

    def test_missing_all_required_fields(self) -> None:
        schema = {
            "type": "object",
            "required": ["path", "mode"],
            "properties": {
                "path": {"type": "string"},
                "mode": {"type": "string"},
            },
        }
        result = validate_tool_arguments("read_file", {}, schema)
        assert result.success is False
        assert "path" in result.reason
        assert "mode" in result.reason

    def test_no_required_array_rejects_extra_fields(self) -> None:
        schema = {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
            },
        }
        result = validate_tool_arguments("read_file", {"extra": "field"}, schema)
        assert result.success is False
        assert "extra" in result.reason


class TestValidateToolArgumentsExtraFields:
    def test_no_extra_fields_allowed_by_default(self) -> None:
        schema = {
            "type": "object",
            "required": ["path"],
            "properties": {
                "path": {"type": "string"},
            },
        }
        result = validate_tool_arguments(
            "read_file",
            {"path": "/tmp/f", "extra": "malicious"},
            schema,
        )
        assert result.success is False
        assert "extra" in result.reason

    def test_extra_fields_allowed_when_flag_set(self) -> None:
        schema = {
            "type": "object",
            "required": ["path"],
            "properties": {
                "path": {"type": "string"},
            },
        }
        result = validate_tool_arguments(
            "read_file",
            {"path": "/tmp/f", "extra": "allowed"},
            schema,
            allow_extra_fields=True,
        )
        assert result.success is True

    def test_multiple_extra_fields_detected(self) -> None:
        schema = {
            "type": "object",
            "required": ["path"],
            "properties": {
                "path": {"type": "string"},
            },
        }
        result = validate_tool_arguments(
            "read_file",
            {"path": "/tmp/f", "a": 1, "b": 2},
            schema,
        )
        assert result.success is False
        assert "a" in result.reason
        assert "b" in result.reason

    def test_properties_absent_allows_extra(self) -> None:
        schema = {
            "type": "object",
            "required": ["path"],
        }
        result = validate_tool_arguments(
            "read_file",
            {"path": "/tmp/f", "extra": "field"},
            schema,
        )
        assert result.success is True


class TestValidateToolArgumentsTypeValidation:
    def test_correct_types_pass(self) -> None:
        schema = {
            "type": "object",
            "required": ["count", "name"],
            "properties": {
                "count": {"type": "integer"},
                "name": {"type": "string"},
            },
        }
        result = validate_tool_arguments(
            "create_item", {"count": 5, "name": "foo"}, schema
        )
        assert result.success is True

    def test_wrong_type_rejected(self) -> None:
        schema = {
            "type": "object",
            "required": ["count"],
            "properties": {
                "count": {"type": "integer"},
            },
        }
        result = validate_tool_arguments("create_item", {"count": "not_an_int"}, schema)
        assert result.success is False
        assert "Type mismatch" in result.reason

    def test_string_given_where_integer_expected(self) -> None:
        schema = {
            "type": "object",
            "required": ["limit"],
            "properties": {
                "limit": {"type": "integer"},
            },
        }
        result = validate_tool_arguments("search_items", {"limit": "10"}, schema)
        assert result.success is False

    def test_boolean_given_where_integer_expected(self) -> None:
        schema = {
            "type": "object",
            "required": ["flag"],
            "properties": {
                "flag": {"type": "integer"},
            },
        }
        result = validate_tool_arguments("toggle", {"flag": True}, schema)
        assert result.success is False

    def test_nested_object_validated(self) -> None:
        schema = {
            "type": "object",
            "required": ["config"],
            "properties": {
                "config": {
                    "type": "object",
                    "required": ["timeout"],
                    "properties": {
                        "timeout": {"type": "integer"},
                    },
                },
            },
        }
        result = validate_tool_arguments(
            "run_task", {"config": {"timeout": "fast"}}, schema
        )
        assert result.success is False
        assert "Type mismatch" in result.reason

    def test_array_type_validated(self) -> None:
        schema = {
            "type": "object",
            "required": ["items"],
            "properties": {
                "items": {"type": "array", "items": {"type": "string"}},
            },
        }
        result = validate_tool_arguments("batch_process", {"items": [1, 2, 3]}, schema)
        assert result.success is False
        assert "Type mismatch" in result.reason

    def test_null_value_for_non_nullable_field(self) -> None:
        schema = {
            "type": "object",
            "required": ["value"],
            "properties": {
                "value": {"type": "string"},
            },
        }
        result = validate_tool_arguments("set_value", {"value": None}, schema)
        assert result.success is False
        assert "Type mismatch" in result.reason


class TestCustomValidatorHooks:
    """Tests for register_custom_validator / _run_custom_validator wiring."""

    _SCHEMA = {
        "type": "object",
        "required": ["count"],
        "properties": {"count": {"type": "integer"}},
    }

    @pytest.fixture(autouse=True)
    def _isolate_registry(self):
        """Snapshot and restore the module-level registry so tests don't leak hooks."""
        saved = dict(_CUSTOM_VALIDATORS)
        _CUSTOM_VALIDATORS.clear()
        yield
        _CUSTOM_VALIDATORS.clear()
        _CUSTOM_VALIDATORS.update(saved)

    def test_no_hook_registered_is_noop(self) -> None:
        result = validate_tool_arguments("unhooked_tool", {"count": 1}, self._SCHEMA)
        assert result.success is True

    def test_registered_hook_passes(self) -> None:
        @register_custom_validator("hooked_tool")
        def _validator(args: dict) -> ValidationResult:
            return ValidationResult(success=True)

        result = validate_tool_arguments("hooked_tool", {"count": 1}, self._SCHEMA)
        assert result.success is True

    def test_registered_hook_fails(self) -> None:
        @register_custom_validator("hooked_tool")
        def _validator(args: dict) -> ValidationResult:
            return ValidationResult(success=False, reason="business rule violated")

        result = validate_tool_arguments("hooked_tool", {"count": 1}, self._SCHEMA)
        assert result.success is False
        assert result.reason == "business rule violated"

    def test_hook_raising_exception_is_converted_not_propagated(self) -> None:
        @register_custom_validator("hooked_tool")
        def _validator(args: dict) -> ValidationResult:
            raise RuntimeError("boom")

        result = validate_tool_arguments("hooked_tool", {"count": 1}, self._SCHEMA)
        assert result.success is False
        assert "Custom validation error for hooked_tool" in result.reason
        assert "boom" in result.reason

    def test_hook_not_called_when_earlier_checks_fail(self) -> None:
        """Custom hooks must not run when required/extra/type checks already failed."""
        calls: list[dict] = []

        @register_custom_validator("hooked_tool")
        def _validator(args: dict) -> ValidationResult:
            calls.append(args)
            return ValidationResult(success=True)

        result = validate_tool_arguments("hooked_tool", {}, self._SCHEMA)
        assert result.success is False
        assert calls == []

    def test_hook_skipped_when_schema_empty(self) -> None:
        """Custom hooks are not invoked when input_schema is empty (lenient fallback)."""
        calls: list[dict] = []

        @register_custom_validator("hooked_tool")
        def _validator(args: dict) -> ValidationResult:
            calls.append(args)
            return ValidationResult(success=True)

        result = validate_tool_arguments("hooked_tool", {"count": 1}, {})
        assert result.success is True
        assert calls == []
