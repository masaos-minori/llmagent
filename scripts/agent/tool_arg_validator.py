"""scripts/agent/tool_arg_validator.py

Schema-based validation for LLM-generated tool call arguments before they reach MCP servers.

Rejects tool calls that contain unexpected or invalid fields according to the MCP tool
definition's inputSchema, preventing argument injection attacks.

Validation location: execute_one_tool_call() after orjson.loads(), before calling executor.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import jsonschema

logger = logging.getLogger(__name__)


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

    return ValidationResult(success=True)


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
