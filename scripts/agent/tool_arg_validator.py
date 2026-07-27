"""scripts/agent/tool_arg_validator.py

Schema-based validation for LLM-generated tool call arguments before they reach MCP servers.

Rejects tool calls that contain unexpected or invalid fields according to the MCP tool
definition's inputSchema, preventing argument injection attacks.

Validation location: execute_one_tool_call() after orjson.loads(), before calling executor.

Custom validation hooks:
    Tool-specific validation rules stricter than the generic schema checks can be
    registered per tool name via the `register_custom_validator` decorator. A
    registered hook runs only after the required-field, extra-field, and type checks
    have already passed, and must return a `ValidationResult` rather than raising.

    Usage:
        @register_custom_validator("my_tool")
        def _validate_my_tool(args: dict) -> ValidationResult:
            if args.get("count", 0) > 100:
                return ValidationResult(success=False, reason="count must be <= 100")
            return ValidationResult(success=True)

    `validate_tool_arguments()` looks up and runs the registered hook (if any) for
    the given tool name; tools without a registered hook are unaffected.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass

import jsonschema

logger = logging.getLogger(__name__)

CustomValidator = Callable[[dict], "ValidationResult"]
_CUSTOM_VALIDATORS: dict[str, CustomValidator] = {}


@dataclass(frozen=True)
class ValidationResult:
    """Result of validating tool call arguments against an MCP input schema.

    Attributes:
        success: True when all checks passed.
        reason: Human-readable explanation (empty string on success).
    """

    success: bool
    reason: str = ""


def validate_tool_arguments(
    tool_name: str,
    args: dict,
    input_schema: dict,
    allow_extra_fields: bool = False,
) -> ValidationResult:
    """Validate tool call arguments against the MCP tool's input schema.

    Checks performed (in order):
        1. Required fields present
        2. Extra fields rejected (unless allow_extra_fields=True)
        3. Type validation via jsonschema

    When the schema is missing or malformed, falls back to lenient mode
    (accept all fields) to prevent blocking legitimate tool calls.

    Args:
        tool_name: Name of the tool being called.
        args: Parsed JSON arguments from the LLM.
        input_schema: MCP tool inputSchema dict.
        allow_extra_fields: If True, extra fields not defined in the schema are allowed.

    Returns:
        ValidationResult indicating pass or failure with reason.
    """
    if not input_schema:
        logger.debug("No input schema for %s; skipping validation", tool_name)
        return ValidationResult(success=True)

    result = _check_required_fields(tool_name, args, input_schema)
    if not result.success:
        return result

    if not allow_extra_fields:
        result = _check_extra_fields(tool_name, args, input_schema)
        if not result.success:
            return result

    result = _check_type_validation(tool_name, args, input_schema)
    if not result.success:
        return result

    result = _run_custom_validator(tool_name, args)
    if not result.success:
        return result

    return ValidationResult(success=True)


def register_custom_validator(
    tool_name: str,
) -> Callable[[CustomValidator], CustomValidator]:
    """Decorator that registers a custom validation hook for tool_name.

    The registered hook runs after the built-in required/extra-field/type checks
    pass, and must return a `ValidationResult` (never raise for expected validation
    failures — see `_run_custom_validator` for exception handling).
    """

    def decorator(fn: CustomValidator) -> CustomValidator:
        """Register this hook under the given tool name."""
        _CUSTOM_VALIDATORS[tool_name] = fn
        return fn

    return decorator


def _run_custom_validator(tool_name: str, args: dict) -> ValidationResult:
    """Run the registered custom validation hook for tool_name, if any.

    Returns success when no hook is registered. Any exception raised by the hook
    is caught and converted into a failed ValidationResult so a custom hook can
    never crash the calling tool-execution pipeline.
    """
    hook = _CUSTOM_VALIDATORS.get(tool_name)
    if hook is None:
        return ValidationResult(success=True)

    try:
        return hook(args)
    except Exception as exc:
        # Broad catch is intentional: hooks are arbitrary registered callables and
        # must never crash execute_one_tool_call(); any failure becomes a normal
        # ValidationResult failure instead of propagating.
        logger.error("Custom validator raised for %s: %s", tool_name, exc)
        return ValidationResult(
            success=False,
            reason=f"Custom validation error for {tool_name}: {exc}",
        )


def _check_required_fields(
    tool_name: str, args: dict, input_schema: dict
) -> ValidationResult:
    """Check that all required fields are present in args."""
    required = input_schema.get("required")
    if not required or not isinstance(required, list):
        return ValidationResult(success=True)

    missing = [field for field in required if field not in args]
    if missing:
        return ValidationResult(
            success=False,
            reason=f"Missing required fields for {tool_name}: {missing}",
        )
    return ValidationResult(success=True)


def _check_extra_fields(
    tool_name: str, args: dict, input_schema: dict
) -> ValidationResult:
    """Check that no extra fields are present beyond what the schema defines.

    When the schema has no 'properties' key, the extra field check is skipped
    (lenient fallback — we cannot determine which fields are allowed).
    """
    properties = input_schema.get("properties")
    if not properties or not isinstance(properties, dict):
        return ValidationResult(success=True)

    allowed_keys = set(properties.keys())
    extra_keys = set(args.keys()) - allowed_keys
    if extra_keys:
        return ValidationResult(
            success=False,
            reason=f"Extra fields not allowed for {tool_name}: {sorted(extra_keys)}",
        )
    return ValidationResult(success=True)


def _check_type_validation(
    tool_name: str, args: dict, input_schema: dict
) -> ValidationResult:
    """Validate arg values against declared types using jsonschema."""
    try:
        jsonschema.validate(instance=args, schema=input_schema)
    except jsonschema.ValidationError as e:
        return ValidationResult(
            success=False,
            reason=f"Type mismatch for {tool_name}: {e.message}",
        )
    return ValidationResult(success=True)
