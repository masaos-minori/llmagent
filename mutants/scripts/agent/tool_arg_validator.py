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


from mutmut.mutation.trampoline import wrap_in_trampoline as _mutmut_mutated, MutantDict


@dataclass(frozen=True)
class ValidationResult:
    """Result of validating tool call arguments against an MCP input schema.

    Attributes:
        success: True when all checks passed.
        reason: Human-readable explanation (empty string on success).
    """

    success: bool
    reason: str = ""
mutants_x_validate_tool_arguments__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x_validate_tool_arguments__mutmut)
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


def x_validate_tool_arguments__mutmut_orig(
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


def x_validate_tool_arguments__mutmut_1(
    tool_name: str,
    args: dict,
    input_schema: dict,
    allow_extra_fields: bool = True,
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


def x_validate_tool_arguments__mutmut_2(
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
    if input_schema:
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


def x_validate_tool_arguments__mutmut_3(
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
        logger.debug(None, tool_name)
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


def x_validate_tool_arguments__mutmut_4(
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
        logger.debug("No input schema for %s; skipping validation", None)
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


def x_validate_tool_arguments__mutmut_5(
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
        logger.debug(tool_name)
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


def x_validate_tool_arguments__mutmut_6(
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
        logger.debug("No input schema for %s; skipping validation", )
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


def x_validate_tool_arguments__mutmut_7(
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
        logger.debug("XXNo input schema for %s; skipping validationXX", tool_name)
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


def x_validate_tool_arguments__mutmut_8(
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
        logger.debug("no input schema for %s; skipping validation", tool_name)
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


def x_validate_tool_arguments__mutmut_9(
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
        logger.debug("NO INPUT SCHEMA FOR %S; SKIPPING VALIDATION", tool_name)
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


def x_validate_tool_arguments__mutmut_10(
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
        return ValidationResult(success=None)

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


def x_validate_tool_arguments__mutmut_11(
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
        return ValidationResult(success=False)

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


def x_validate_tool_arguments__mutmut_12(
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

    result = None
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


def x_validate_tool_arguments__mutmut_13(
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

    result = _check_required_fields(None, args, input_schema)
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


def x_validate_tool_arguments__mutmut_14(
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

    result = _check_required_fields(tool_name, None, input_schema)
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


def x_validate_tool_arguments__mutmut_15(
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

    result = _check_required_fields(tool_name, args, None)
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


def x_validate_tool_arguments__mutmut_16(
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

    result = _check_required_fields(args, input_schema)
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


def x_validate_tool_arguments__mutmut_17(
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

    result = _check_required_fields(tool_name, input_schema)
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


def x_validate_tool_arguments__mutmut_18(
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

    result = _check_required_fields(tool_name, args, )
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


def x_validate_tool_arguments__mutmut_19(
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
    if result.success:
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


def x_validate_tool_arguments__mutmut_20(
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

    if allow_extra_fields:
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


def x_validate_tool_arguments__mutmut_21(
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
        result = None
        if not result.success:
            return result

    result = _check_type_validation(tool_name, args, input_schema)
    if not result.success:
        return result

    result = _run_custom_validator(tool_name, args)
    if not result.success:
        return result

    return ValidationResult(success=True)


def x_validate_tool_arguments__mutmut_22(
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
        result = _check_extra_fields(None, args, input_schema)
        if not result.success:
            return result

    result = _check_type_validation(tool_name, args, input_schema)
    if not result.success:
        return result

    result = _run_custom_validator(tool_name, args)
    if not result.success:
        return result

    return ValidationResult(success=True)


def x_validate_tool_arguments__mutmut_23(
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
        result = _check_extra_fields(tool_name, None, input_schema)
        if not result.success:
            return result

    result = _check_type_validation(tool_name, args, input_schema)
    if not result.success:
        return result

    result = _run_custom_validator(tool_name, args)
    if not result.success:
        return result

    return ValidationResult(success=True)


def x_validate_tool_arguments__mutmut_24(
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
        result = _check_extra_fields(tool_name, args, None)
        if not result.success:
            return result

    result = _check_type_validation(tool_name, args, input_schema)
    if not result.success:
        return result

    result = _run_custom_validator(tool_name, args)
    if not result.success:
        return result

    return ValidationResult(success=True)


def x_validate_tool_arguments__mutmut_25(
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
        result = _check_extra_fields(args, input_schema)
        if not result.success:
            return result

    result = _check_type_validation(tool_name, args, input_schema)
    if not result.success:
        return result

    result = _run_custom_validator(tool_name, args)
    if not result.success:
        return result

    return ValidationResult(success=True)


def x_validate_tool_arguments__mutmut_26(
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
        result = _check_extra_fields(tool_name, input_schema)
        if not result.success:
            return result

    result = _check_type_validation(tool_name, args, input_schema)
    if not result.success:
        return result

    result = _run_custom_validator(tool_name, args)
    if not result.success:
        return result

    return ValidationResult(success=True)


def x_validate_tool_arguments__mutmut_27(
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
        result = _check_extra_fields(tool_name, args, )
        if not result.success:
            return result

    result = _check_type_validation(tool_name, args, input_schema)
    if not result.success:
        return result

    result = _run_custom_validator(tool_name, args)
    if not result.success:
        return result

    return ValidationResult(success=True)


def x_validate_tool_arguments__mutmut_28(
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
        if result.success:
            return result

    result = _check_type_validation(tool_name, args, input_schema)
    if not result.success:
        return result

    result = _run_custom_validator(tool_name, args)
    if not result.success:
        return result

    return ValidationResult(success=True)


def x_validate_tool_arguments__mutmut_29(
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

    result = None
    if not result.success:
        return result

    result = _run_custom_validator(tool_name, args)
    if not result.success:
        return result

    return ValidationResult(success=True)


def x_validate_tool_arguments__mutmut_30(
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

    result = _check_type_validation(None, args, input_schema)
    if not result.success:
        return result

    result = _run_custom_validator(tool_name, args)
    if not result.success:
        return result

    return ValidationResult(success=True)


def x_validate_tool_arguments__mutmut_31(
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

    result = _check_type_validation(tool_name, None, input_schema)
    if not result.success:
        return result

    result = _run_custom_validator(tool_name, args)
    if not result.success:
        return result

    return ValidationResult(success=True)


def x_validate_tool_arguments__mutmut_32(
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

    result = _check_type_validation(tool_name, args, None)
    if not result.success:
        return result

    result = _run_custom_validator(tool_name, args)
    if not result.success:
        return result

    return ValidationResult(success=True)


def x_validate_tool_arguments__mutmut_33(
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

    result = _check_type_validation(args, input_schema)
    if not result.success:
        return result

    result = _run_custom_validator(tool_name, args)
    if not result.success:
        return result

    return ValidationResult(success=True)


def x_validate_tool_arguments__mutmut_34(
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

    result = _check_type_validation(tool_name, input_schema)
    if not result.success:
        return result

    result = _run_custom_validator(tool_name, args)
    if not result.success:
        return result

    return ValidationResult(success=True)


def x_validate_tool_arguments__mutmut_35(
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

    result = _check_type_validation(tool_name, args, )
    if not result.success:
        return result

    result = _run_custom_validator(tool_name, args)
    if not result.success:
        return result

    return ValidationResult(success=True)


def x_validate_tool_arguments__mutmut_36(
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
    if result.success:
        return result

    result = _run_custom_validator(tool_name, args)
    if not result.success:
        return result

    return ValidationResult(success=True)


def x_validate_tool_arguments__mutmut_37(
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

    result = None
    if not result.success:
        return result

    return ValidationResult(success=True)


def x_validate_tool_arguments__mutmut_38(
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

    result = _run_custom_validator(None, args)
    if not result.success:
        return result

    return ValidationResult(success=True)


def x_validate_tool_arguments__mutmut_39(
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

    result = _run_custom_validator(tool_name, None)
    if not result.success:
        return result

    return ValidationResult(success=True)


def x_validate_tool_arguments__mutmut_40(
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

    result = _run_custom_validator(args)
    if not result.success:
        return result

    return ValidationResult(success=True)


def x_validate_tool_arguments__mutmut_41(
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

    result = _run_custom_validator(tool_name, )
    if not result.success:
        return result

    return ValidationResult(success=True)


def x_validate_tool_arguments__mutmut_42(
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
    if result.success:
        return result

    return ValidationResult(success=True)


def x_validate_tool_arguments__mutmut_43(
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

    return ValidationResult(success=None)


def x_validate_tool_arguments__mutmut_44(
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

    return ValidationResult(success=False)

mutants_x_validate_tool_arguments__mutmut['_mutmut_orig'] = x_validate_tool_arguments__mutmut_orig # type: ignore # mutmut generated
mutants_x_validate_tool_arguments__mutmut['x_validate_tool_arguments__mutmut_1'] = x_validate_tool_arguments__mutmut_1 # type: ignore # mutmut generated
mutants_x_validate_tool_arguments__mutmut['x_validate_tool_arguments__mutmut_2'] = x_validate_tool_arguments__mutmut_2 # type: ignore # mutmut generated
mutants_x_validate_tool_arguments__mutmut['x_validate_tool_arguments__mutmut_3'] = x_validate_tool_arguments__mutmut_3 # type: ignore # mutmut generated
mutants_x_validate_tool_arguments__mutmut['x_validate_tool_arguments__mutmut_4'] = x_validate_tool_arguments__mutmut_4 # type: ignore # mutmut generated
mutants_x_validate_tool_arguments__mutmut['x_validate_tool_arguments__mutmut_5'] = x_validate_tool_arguments__mutmut_5 # type: ignore # mutmut generated
mutants_x_validate_tool_arguments__mutmut['x_validate_tool_arguments__mutmut_6'] = x_validate_tool_arguments__mutmut_6 # type: ignore # mutmut generated
mutants_x_validate_tool_arguments__mutmut['x_validate_tool_arguments__mutmut_7'] = x_validate_tool_arguments__mutmut_7 # type: ignore # mutmut generated
mutants_x_validate_tool_arguments__mutmut['x_validate_tool_arguments__mutmut_8'] = x_validate_tool_arguments__mutmut_8 # type: ignore # mutmut generated
mutants_x_validate_tool_arguments__mutmut['x_validate_tool_arguments__mutmut_9'] = x_validate_tool_arguments__mutmut_9 # type: ignore # mutmut generated
mutants_x_validate_tool_arguments__mutmut['x_validate_tool_arguments__mutmut_10'] = x_validate_tool_arguments__mutmut_10 # type: ignore # mutmut generated
mutants_x_validate_tool_arguments__mutmut['x_validate_tool_arguments__mutmut_11'] = x_validate_tool_arguments__mutmut_11 # type: ignore # mutmut generated
mutants_x_validate_tool_arguments__mutmut['x_validate_tool_arguments__mutmut_12'] = x_validate_tool_arguments__mutmut_12 # type: ignore # mutmut generated
mutants_x_validate_tool_arguments__mutmut['x_validate_tool_arguments__mutmut_13'] = x_validate_tool_arguments__mutmut_13 # type: ignore # mutmut generated
mutants_x_validate_tool_arguments__mutmut['x_validate_tool_arguments__mutmut_14'] = x_validate_tool_arguments__mutmut_14 # type: ignore # mutmut generated
mutants_x_validate_tool_arguments__mutmut['x_validate_tool_arguments__mutmut_15'] = x_validate_tool_arguments__mutmut_15 # type: ignore # mutmut generated
mutants_x_validate_tool_arguments__mutmut['x_validate_tool_arguments__mutmut_16'] = x_validate_tool_arguments__mutmut_16 # type: ignore # mutmut generated
mutants_x_validate_tool_arguments__mutmut['x_validate_tool_arguments__mutmut_17'] = x_validate_tool_arguments__mutmut_17 # type: ignore # mutmut generated
mutants_x_validate_tool_arguments__mutmut['x_validate_tool_arguments__mutmut_18'] = x_validate_tool_arguments__mutmut_18 # type: ignore # mutmut generated
mutants_x_validate_tool_arguments__mutmut['x_validate_tool_arguments__mutmut_19'] = x_validate_tool_arguments__mutmut_19 # type: ignore # mutmut generated
mutants_x_validate_tool_arguments__mutmut['x_validate_tool_arguments__mutmut_20'] = x_validate_tool_arguments__mutmut_20 # type: ignore # mutmut generated
mutants_x_validate_tool_arguments__mutmut['x_validate_tool_arguments__mutmut_21'] = x_validate_tool_arguments__mutmut_21 # type: ignore # mutmut generated
mutants_x_validate_tool_arguments__mutmut['x_validate_tool_arguments__mutmut_22'] = x_validate_tool_arguments__mutmut_22 # type: ignore # mutmut generated
mutants_x_validate_tool_arguments__mutmut['x_validate_tool_arguments__mutmut_23'] = x_validate_tool_arguments__mutmut_23 # type: ignore # mutmut generated
mutants_x_validate_tool_arguments__mutmut['x_validate_tool_arguments__mutmut_24'] = x_validate_tool_arguments__mutmut_24 # type: ignore # mutmut generated
mutants_x_validate_tool_arguments__mutmut['x_validate_tool_arguments__mutmut_25'] = x_validate_tool_arguments__mutmut_25 # type: ignore # mutmut generated
mutants_x_validate_tool_arguments__mutmut['x_validate_tool_arguments__mutmut_26'] = x_validate_tool_arguments__mutmut_26 # type: ignore # mutmut generated
mutants_x_validate_tool_arguments__mutmut['x_validate_tool_arguments__mutmut_27'] = x_validate_tool_arguments__mutmut_27 # type: ignore # mutmut generated
mutants_x_validate_tool_arguments__mutmut['x_validate_tool_arguments__mutmut_28'] = x_validate_tool_arguments__mutmut_28 # type: ignore # mutmut generated
mutants_x_validate_tool_arguments__mutmut['x_validate_tool_arguments__mutmut_29'] = x_validate_tool_arguments__mutmut_29 # type: ignore # mutmut generated
mutants_x_validate_tool_arguments__mutmut['x_validate_tool_arguments__mutmut_30'] = x_validate_tool_arguments__mutmut_30 # type: ignore # mutmut generated
mutants_x_validate_tool_arguments__mutmut['x_validate_tool_arguments__mutmut_31'] = x_validate_tool_arguments__mutmut_31 # type: ignore # mutmut generated
mutants_x_validate_tool_arguments__mutmut['x_validate_tool_arguments__mutmut_32'] = x_validate_tool_arguments__mutmut_32 # type: ignore # mutmut generated
mutants_x_validate_tool_arguments__mutmut['x_validate_tool_arguments__mutmut_33'] = x_validate_tool_arguments__mutmut_33 # type: ignore # mutmut generated
mutants_x_validate_tool_arguments__mutmut['x_validate_tool_arguments__mutmut_34'] = x_validate_tool_arguments__mutmut_34 # type: ignore # mutmut generated
mutants_x_validate_tool_arguments__mutmut['x_validate_tool_arguments__mutmut_35'] = x_validate_tool_arguments__mutmut_35 # type: ignore # mutmut generated
mutants_x_validate_tool_arguments__mutmut['x_validate_tool_arguments__mutmut_36'] = x_validate_tool_arguments__mutmut_36 # type: ignore # mutmut generated
mutants_x_validate_tool_arguments__mutmut['x_validate_tool_arguments__mutmut_37'] = x_validate_tool_arguments__mutmut_37 # type: ignore # mutmut generated
mutants_x_validate_tool_arguments__mutmut['x_validate_tool_arguments__mutmut_38'] = x_validate_tool_arguments__mutmut_38 # type: ignore # mutmut generated
mutants_x_validate_tool_arguments__mutmut['x_validate_tool_arguments__mutmut_39'] = x_validate_tool_arguments__mutmut_39 # type: ignore # mutmut generated
mutants_x_validate_tool_arguments__mutmut['x_validate_tool_arguments__mutmut_40'] = x_validate_tool_arguments__mutmut_40 # type: ignore # mutmut generated
mutants_x_validate_tool_arguments__mutmut['x_validate_tool_arguments__mutmut_41'] = x_validate_tool_arguments__mutmut_41 # type: ignore # mutmut generated
mutants_x_validate_tool_arguments__mutmut['x_validate_tool_arguments__mutmut_42'] = x_validate_tool_arguments__mutmut_42 # type: ignore # mutmut generated
mutants_x_validate_tool_arguments__mutmut['x_validate_tool_arguments__mutmut_43'] = x_validate_tool_arguments__mutmut_43 # type: ignore # mutmut generated
mutants_x_validate_tool_arguments__mutmut['x_validate_tool_arguments__mutmut_44'] = x_validate_tool_arguments__mutmut_44 # type: ignore # mutmut generated
mutants_x_register_custom_validator__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x_register_custom_validator__mutmut)
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


def x_register_custom_validator__mutmut_orig(
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


def x_register_custom_validator__mutmut_1(
    tool_name: str,
) -> Callable[[CustomValidator], CustomValidator]:
    """Decorator that registers a custom validation hook for tool_name.

    The registered hook runs after the built-in required/extra-field/type checks
    pass, and must return a `ValidationResult` (never raise for expected validation
    failures — see `_run_custom_validator` for exception handling).
    """

    def decorator(fn: CustomValidator) -> CustomValidator:
        """Register this hook under the given tool name."""
        _CUSTOM_VALIDATORS[tool_name] = None
        return fn

    return decorator

mutants_x_register_custom_validator__mutmut['_mutmut_orig'] = x_register_custom_validator__mutmut_orig # type: ignore # mutmut generated
mutants_x_register_custom_validator__mutmut['x_register_custom_validator__mutmut_1'] = x_register_custom_validator__mutmut_1 # type: ignore # mutmut generated
mutants_x__run_custom_validator__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x__run_custom_validator__mutmut)
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
    except Exception as exc:  # noqa: BLE001 — hooks are arbitrary registered callables and must never crash execute_one_tool_call()
        # Broad catch is intentional: hooks are arbitrary registered callables and
        # must never crash execute_one_tool_call(); any failure becomes a normal
        # ValidationResult failure instead of propagating.
        logger.error("Custom validator raised for %s: %s", tool_name, exc)
        return ValidationResult(
            success=False,
            reason=f"Custom validation error for {tool_name}: {exc}",
        )


def x__run_custom_validator__mutmut_orig(tool_name: str, args: dict) -> ValidationResult:
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
    except Exception as exc:  # noqa: BLE001 — hooks are arbitrary registered callables and must never crash execute_one_tool_call()
        # Broad catch is intentional: hooks are arbitrary registered callables and
        # must never crash execute_one_tool_call(); any failure becomes a normal
        # ValidationResult failure instead of propagating.
        logger.error("Custom validator raised for %s: %s", tool_name, exc)
        return ValidationResult(
            success=False,
            reason=f"Custom validation error for {tool_name}: {exc}",
        )


def x__run_custom_validator__mutmut_1(tool_name: str, args: dict) -> ValidationResult:
    """Run the registered custom validation hook for tool_name, if any.

    Returns success when no hook is registered. Any exception raised by the hook
    is caught and converted into a failed ValidationResult so a custom hook can
    never crash the calling tool-execution pipeline.
    """
    hook = None
    if hook is None:
        return ValidationResult(success=True)

    try:
        return hook(args)
    except Exception as exc:  # noqa: BLE001 — hooks are arbitrary registered callables and must never crash execute_one_tool_call()
        # Broad catch is intentional: hooks are arbitrary registered callables and
        # must never crash execute_one_tool_call(); any failure becomes a normal
        # ValidationResult failure instead of propagating.
        logger.error("Custom validator raised for %s: %s", tool_name, exc)
        return ValidationResult(
            success=False,
            reason=f"Custom validation error for {tool_name}: {exc}",
        )


def x__run_custom_validator__mutmut_2(tool_name: str, args: dict) -> ValidationResult:
    """Run the registered custom validation hook for tool_name, if any.

    Returns success when no hook is registered. Any exception raised by the hook
    is caught and converted into a failed ValidationResult so a custom hook can
    never crash the calling tool-execution pipeline.
    """
    hook = _CUSTOM_VALIDATORS.get(None)
    if hook is None:
        return ValidationResult(success=True)

    try:
        return hook(args)
    except Exception as exc:  # noqa: BLE001 — hooks are arbitrary registered callables and must never crash execute_one_tool_call()
        # Broad catch is intentional: hooks are arbitrary registered callables and
        # must never crash execute_one_tool_call(); any failure becomes a normal
        # ValidationResult failure instead of propagating.
        logger.error("Custom validator raised for %s: %s", tool_name, exc)
        return ValidationResult(
            success=False,
            reason=f"Custom validation error for {tool_name}: {exc}",
        )


def x__run_custom_validator__mutmut_3(tool_name: str, args: dict) -> ValidationResult:
    """Run the registered custom validation hook for tool_name, if any.

    Returns success when no hook is registered. Any exception raised by the hook
    is caught and converted into a failed ValidationResult so a custom hook can
    never crash the calling tool-execution pipeline.
    """
    hook = _CUSTOM_VALIDATORS.get(tool_name)
    if hook is not None:
        return ValidationResult(success=True)

    try:
        return hook(args)
    except Exception as exc:  # noqa: BLE001 — hooks are arbitrary registered callables and must never crash execute_one_tool_call()
        # Broad catch is intentional: hooks are arbitrary registered callables and
        # must never crash execute_one_tool_call(); any failure becomes a normal
        # ValidationResult failure instead of propagating.
        logger.error("Custom validator raised for %s: %s", tool_name, exc)
        return ValidationResult(
            success=False,
            reason=f"Custom validation error for {tool_name}: {exc}",
        )


def x__run_custom_validator__mutmut_4(tool_name: str, args: dict) -> ValidationResult:
    """Run the registered custom validation hook for tool_name, if any.

    Returns success when no hook is registered. Any exception raised by the hook
    is caught and converted into a failed ValidationResult so a custom hook can
    never crash the calling tool-execution pipeline.
    """
    hook = _CUSTOM_VALIDATORS.get(tool_name)
    if hook is None:
        return ValidationResult(success=None)

    try:
        return hook(args)
    except Exception as exc:  # noqa: BLE001 — hooks are arbitrary registered callables and must never crash execute_one_tool_call()
        # Broad catch is intentional: hooks are arbitrary registered callables and
        # must never crash execute_one_tool_call(); any failure becomes a normal
        # ValidationResult failure instead of propagating.
        logger.error("Custom validator raised for %s: %s", tool_name, exc)
        return ValidationResult(
            success=False,
            reason=f"Custom validation error for {tool_name}: {exc}",
        )


def x__run_custom_validator__mutmut_5(tool_name: str, args: dict) -> ValidationResult:
    """Run the registered custom validation hook for tool_name, if any.

    Returns success when no hook is registered. Any exception raised by the hook
    is caught and converted into a failed ValidationResult so a custom hook can
    never crash the calling tool-execution pipeline.
    """
    hook = _CUSTOM_VALIDATORS.get(tool_name)
    if hook is None:
        return ValidationResult(success=False)

    try:
        return hook(args)
    except Exception as exc:  # noqa: BLE001 — hooks are arbitrary registered callables and must never crash execute_one_tool_call()
        # Broad catch is intentional: hooks are arbitrary registered callables and
        # must never crash execute_one_tool_call(); any failure becomes a normal
        # ValidationResult failure instead of propagating.
        logger.error("Custom validator raised for %s: %s", tool_name, exc)
        return ValidationResult(
            success=False,
            reason=f"Custom validation error for {tool_name}: {exc}",
        )


def x__run_custom_validator__mutmut_6(tool_name: str, args: dict) -> ValidationResult:
    """Run the registered custom validation hook for tool_name, if any.

    Returns success when no hook is registered. Any exception raised by the hook
    is caught and converted into a failed ValidationResult so a custom hook can
    never crash the calling tool-execution pipeline.
    """
    hook = _CUSTOM_VALIDATORS.get(tool_name)
    if hook is None:
        return ValidationResult(success=True)

    try:
        return hook(None)
    except Exception as exc:  # noqa: BLE001 — hooks are arbitrary registered callables and must never crash execute_one_tool_call()
        # Broad catch is intentional: hooks are arbitrary registered callables and
        # must never crash execute_one_tool_call(); any failure becomes a normal
        # ValidationResult failure instead of propagating.
        logger.error("Custom validator raised for %s: %s", tool_name, exc)
        return ValidationResult(
            success=False,
            reason=f"Custom validation error for {tool_name}: {exc}",
        )


def x__run_custom_validator__mutmut_7(tool_name: str, args: dict) -> ValidationResult:
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
    except Exception as exc:  # noqa: BLE001 — hooks are arbitrary registered callables and must never crash execute_one_tool_call()
        # Broad catch is intentional: hooks are arbitrary registered callables and
        # must never crash execute_one_tool_call(); any failure becomes a normal
        # ValidationResult failure instead of propagating.
        logger.error(None, tool_name, exc)
        return ValidationResult(
            success=False,
            reason=f"Custom validation error for {tool_name}: {exc}",
        )


def x__run_custom_validator__mutmut_8(tool_name: str, args: dict) -> ValidationResult:
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
    except Exception as exc:  # noqa: BLE001 — hooks are arbitrary registered callables and must never crash execute_one_tool_call()
        # Broad catch is intentional: hooks are arbitrary registered callables and
        # must never crash execute_one_tool_call(); any failure becomes a normal
        # ValidationResult failure instead of propagating.
        logger.error("Custom validator raised for %s: %s", None, exc)
        return ValidationResult(
            success=False,
            reason=f"Custom validation error for {tool_name}: {exc}",
        )


def x__run_custom_validator__mutmut_9(tool_name: str, args: dict) -> ValidationResult:
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
    except Exception as exc:  # noqa: BLE001 — hooks are arbitrary registered callables and must never crash execute_one_tool_call()
        # Broad catch is intentional: hooks are arbitrary registered callables and
        # must never crash execute_one_tool_call(); any failure becomes a normal
        # ValidationResult failure instead of propagating.
        logger.error("Custom validator raised for %s: %s", tool_name, None)
        return ValidationResult(
            success=False,
            reason=f"Custom validation error for {tool_name}: {exc}",
        )


def x__run_custom_validator__mutmut_10(tool_name: str, args: dict) -> ValidationResult:
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
    except Exception as exc:  # noqa: BLE001 — hooks are arbitrary registered callables and must never crash execute_one_tool_call()
        # Broad catch is intentional: hooks are arbitrary registered callables and
        # must never crash execute_one_tool_call(); any failure becomes a normal
        # ValidationResult failure instead of propagating.
        logger.error(tool_name, exc)
        return ValidationResult(
            success=False,
            reason=f"Custom validation error for {tool_name}: {exc}",
        )


def x__run_custom_validator__mutmut_11(tool_name: str, args: dict) -> ValidationResult:
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
    except Exception as exc:  # noqa: BLE001 — hooks are arbitrary registered callables and must never crash execute_one_tool_call()
        # Broad catch is intentional: hooks are arbitrary registered callables and
        # must never crash execute_one_tool_call(); any failure becomes a normal
        # ValidationResult failure instead of propagating.
        logger.error("Custom validator raised for %s: %s", exc)
        return ValidationResult(
            success=False,
            reason=f"Custom validation error for {tool_name}: {exc}",
        )


def x__run_custom_validator__mutmut_12(tool_name: str, args: dict) -> ValidationResult:
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
    except Exception as exc:  # noqa: BLE001 — hooks are arbitrary registered callables and must never crash execute_one_tool_call()
        # Broad catch is intentional: hooks are arbitrary registered callables and
        # must never crash execute_one_tool_call(); any failure becomes a normal
        # ValidationResult failure instead of propagating.
        logger.error("Custom validator raised for %s: %s", tool_name, )
        return ValidationResult(
            success=False,
            reason=f"Custom validation error for {tool_name}: {exc}",
        )


def x__run_custom_validator__mutmut_13(tool_name: str, args: dict) -> ValidationResult:
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
    except Exception as exc:  # noqa: BLE001 — hooks are arbitrary registered callables and must never crash execute_one_tool_call()
        # Broad catch is intentional: hooks are arbitrary registered callables and
        # must never crash execute_one_tool_call(); any failure becomes a normal
        # ValidationResult failure instead of propagating.
        logger.error("XXCustom validator raised for %s: %sXX", tool_name, exc)
        return ValidationResult(
            success=False,
            reason=f"Custom validation error for {tool_name}: {exc}",
        )


def x__run_custom_validator__mutmut_14(tool_name: str, args: dict) -> ValidationResult:
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
    except Exception as exc:  # noqa: BLE001 — hooks are arbitrary registered callables and must never crash execute_one_tool_call()
        # Broad catch is intentional: hooks are arbitrary registered callables and
        # must never crash execute_one_tool_call(); any failure becomes a normal
        # ValidationResult failure instead of propagating.
        logger.error("custom validator raised for %s: %s", tool_name, exc)
        return ValidationResult(
            success=False,
            reason=f"Custom validation error for {tool_name}: {exc}",
        )


def x__run_custom_validator__mutmut_15(tool_name: str, args: dict) -> ValidationResult:
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
    except Exception as exc:  # noqa: BLE001 — hooks are arbitrary registered callables and must never crash execute_one_tool_call()
        # Broad catch is intentional: hooks are arbitrary registered callables and
        # must never crash execute_one_tool_call(); any failure becomes a normal
        # ValidationResult failure instead of propagating.
        logger.error("CUSTOM VALIDATOR RAISED FOR %S: %S", tool_name, exc)
        return ValidationResult(
            success=False,
            reason=f"Custom validation error for {tool_name}: {exc}",
        )


def x__run_custom_validator__mutmut_16(tool_name: str, args: dict) -> ValidationResult:
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
    except Exception as exc:  # noqa: BLE001 — hooks are arbitrary registered callables and must never crash execute_one_tool_call()
        # Broad catch is intentional: hooks are arbitrary registered callables and
        # must never crash execute_one_tool_call(); any failure becomes a normal
        # ValidationResult failure instead of propagating.
        logger.error("Custom validator raised for %s: %s", tool_name, exc)
        return ValidationResult(
            success=None,
            reason=f"Custom validation error for {tool_name}: {exc}",
        )


def x__run_custom_validator__mutmut_17(tool_name: str, args: dict) -> ValidationResult:
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
    except Exception as exc:  # noqa: BLE001 — hooks are arbitrary registered callables and must never crash execute_one_tool_call()
        # Broad catch is intentional: hooks are arbitrary registered callables and
        # must never crash execute_one_tool_call(); any failure becomes a normal
        # ValidationResult failure instead of propagating.
        logger.error("Custom validator raised for %s: %s", tool_name, exc)
        return ValidationResult(
            success=False,
            reason=None,
        )


def x__run_custom_validator__mutmut_18(tool_name: str, args: dict) -> ValidationResult:
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
    except Exception as exc:  # noqa: BLE001 — hooks are arbitrary registered callables and must never crash execute_one_tool_call()
        # Broad catch is intentional: hooks are arbitrary registered callables and
        # must never crash execute_one_tool_call(); any failure becomes a normal
        # ValidationResult failure instead of propagating.
        logger.error("Custom validator raised for %s: %s", tool_name, exc)
        return ValidationResult(
            reason=f"Custom validation error for {tool_name}: {exc}",
        )


def x__run_custom_validator__mutmut_19(tool_name: str, args: dict) -> ValidationResult:
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
    except Exception as exc:  # noqa: BLE001 — hooks are arbitrary registered callables and must never crash execute_one_tool_call()
        # Broad catch is intentional: hooks are arbitrary registered callables and
        # must never crash execute_one_tool_call(); any failure becomes a normal
        # ValidationResult failure instead of propagating.
        logger.error("Custom validator raised for %s: %s", tool_name, exc)
        return ValidationResult(
            success=False,
            )


def x__run_custom_validator__mutmut_20(tool_name: str, args: dict) -> ValidationResult:
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
    except Exception as exc:  # noqa: BLE001 — hooks are arbitrary registered callables and must never crash execute_one_tool_call()
        # Broad catch is intentional: hooks are arbitrary registered callables and
        # must never crash execute_one_tool_call(); any failure becomes a normal
        # ValidationResult failure instead of propagating.
        logger.error("Custom validator raised for %s: %s", tool_name, exc)
        return ValidationResult(
            success=True,
            reason=f"Custom validation error for {tool_name}: {exc}",
        )

mutants_x__run_custom_validator__mutmut['_mutmut_orig'] = x__run_custom_validator__mutmut_orig # type: ignore # mutmut generated
mutants_x__run_custom_validator__mutmut['x__run_custom_validator__mutmut_1'] = x__run_custom_validator__mutmut_1 # type: ignore # mutmut generated
mutants_x__run_custom_validator__mutmut['x__run_custom_validator__mutmut_2'] = x__run_custom_validator__mutmut_2 # type: ignore # mutmut generated
mutants_x__run_custom_validator__mutmut['x__run_custom_validator__mutmut_3'] = x__run_custom_validator__mutmut_3 # type: ignore # mutmut generated
mutants_x__run_custom_validator__mutmut['x__run_custom_validator__mutmut_4'] = x__run_custom_validator__mutmut_4 # type: ignore # mutmut generated
mutants_x__run_custom_validator__mutmut['x__run_custom_validator__mutmut_5'] = x__run_custom_validator__mutmut_5 # type: ignore # mutmut generated
mutants_x__run_custom_validator__mutmut['x__run_custom_validator__mutmut_6'] = x__run_custom_validator__mutmut_6 # type: ignore # mutmut generated
mutants_x__run_custom_validator__mutmut['x__run_custom_validator__mutmut_7'] = x__run_custom_validator__mutmut_7 # type: ignore # mutmut generated
mutants_x__run_custom_validator__mutmut['x__run_custom_validator__mutmut_8'] = x__run_custom_validator__mutmut_8 # type: ignore # mutmut generated
mutants_x__run_custom_validator__mutmut['x__run_custom_validator__mutmut_9'] = x__run_custom_validator__mutmut_9 # type: ignore # mutmut generated
mutants_x__run_custom_validator__mutmut['x__run_custom_validator__mutmut_10'] = x__run_custom_validator__mutmut_10 # type: ignore # mutmut generated
mutants_x__run_custom_validator__mutmut['x__run_custom_validator__mutmut_11'] = x__run_custom_validator__mutmut_11 # type: ignore # mutmut generated
mutants_x__run_custom_validator__mutmut['x__run_custom_validator__mutmut_12'] = x__run_custom_validator__mutmut_12 # type: ignore # mutmut generated
mutants_x__run_custom_validator__mutmut['x__run_custom_validator__mutmut_13'] = x__run_custom_validator__mutmut_13 # type: ignore # mutmut generated
mutants_x__run_custom_validator__mutmut['x__run_custom_validator__mutmut_14'] = x__run_custom_validator__mutmut_14 # type: ignore # mutmut generated
mutants_x__run_custom_validator__mutmut['x__run_custom_validator__mutmut_15'] = x__run_custom_validator__mutmut_15 # type: ignore # mutmut generated
mutants_x__run_custom_validator__mutmut['x__run_custom_validator__mutmut_16'] = x__run_custom_validator__mutmut_16 # type: ignore # mutmut generated
mutants_x__run_custom_validator__mutmut['x__run_custom_validator__mutmut_17'] = x__run_custom_validator__mutmut_17 # type: ignore # mutmut generated
mutants_x__run_custom_validator__mutmut['x__run_custom_validator__mutmut_18'] = x__run_custom_validator__mutmut_18 # type: ignore # mutmut generated
mutants_x__run_custom_validator__mutmut['x__run_custom_validator__mutmut_19'] = x__run_custom_validator__mutmut_19 # type: ignore # mutmut generated
mutants_x__run_custom_validator__mutmut['x__run_custom_validator__mutmut_20'] = x__run_custom_validator__mutmut_20 # type: ignore # mutmut generated
mutants_x__check_required_fields__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x__check_required_fields__mutmut)
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


def x__check_required_fields__mutmut_orig(
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


def x__check_required_fields__mutmut_1(
    tool_name: str, args: dict, input_schema: dict
) -> ValidationResult:
    """Check that all required fields are present in args."""
    required = None
    if not required or not isinstance(required, list):
        return ValidationResult(success=True)

    missing = [field for field in required if field not in args]
    if missing:
        return ValidationResult(
            success=False,
            reason=f"Missing required fields for {tool_name}: {missing}",
        )
    return ValidationResult(success=True)


def x__check_required_fields__mutmut_2(
    tool_name: str, args: dict, input_schema: dict
) -> ValidationResult:
    """Check that all required fields are present in args."""
    required = input_schema.get(None)
    if not required or not isinstance(required, list):
        return ValidationResult(success=True)

    missing = [field for field in required if field not in args]
    if missing:
        return ValidationResult(
            success=False,
            reason=f"Missing required fields for {tool_name}: {missing}",
        )
    return ValidationResult(success=True)


def x__check_required_fields__mutmut_3(
    tool_name: str, args: dict, input_schema: dict
) -> ValidationResult:
    """Check that all required fields are present in args."""
    required = input_schema.get("XXrequiredXX")
    if not required or not isinstance(required, list):
        return ValidationResult(success=True)

    missing = [field for field in required if field not in args]
    if missing:
        return ValidationResult(
            success=False,
            reason=f"Missing required fields for {tool_name}: {missing}",
        )
    return ValidationResult(success=True)


def x__check_required_fields__mutmut_4(
    tool_name: str, args: dict, input_schema: dict
) -> ValidationResult:
    """Check that all required fields are present in args."""
    required = input_schema.get("REQUIRED")
    if not required or not isinstance(required, list):
        return ValidationResult(success=True)

    missing = [field for field in required if field not in args]
    if missing:
        return ValidationResult(
            success=False,
            reason=f"Missing required fields for {tool_name}: {missing}",
        )
    return ValidationResult(success=True)


def x__check_required_fields__mutmut_5(
    tool_name: str, args: dict, input_schema: dict
) -> ValidationResult:
    """Check that all required fields are present in args."""
    required = input_schema.get("required")
    if not required and not isinstance(required, list):
        return ValidationResult(success=True)

    missing = [field for field in required if field not in args]
    if missing:
        return ValidationResult(
            success=False,
            reason=f"Missing required fields for {tool_name}: {missing}",
        )
    return ValidationResult(success=True)


def x__check_required_fields__mutmut_6(
    tool_name: str, args: dict, input_schema: dict
) -> ValidationResult:
    """Check that all required fields are present in args."""
    required = input_schema.get("required")
    if required or not isinstance(required, list):
        return ValidationResult(success=True)

    missing = [field for field in required if field not in args]
    if missing:
        return ValidationResult(
            success=False,
            reason=f"Missing required fields for {tool_name}: {missing}",
        )
    return ValidationResult(success=True)


def x__check_required_fields__mutmut_7(
    tool_name: str, args: dict, input_schema: dict
) -> ValidationResult:
    """Check that all required fields are present in args."""
    required = input_schema.get("required")
    if not required or isinstance(required, list):
        return ValidationResult(success=True)

    missing = [field for field in required if field not in args]
    if missing:
        return ValidationResult(
            success=False,
            reason=f"Missing required fields for {tool_name}: {missing}",
        )
    return ValidationResult(success=True)


def x__check_required_fields__mutmut_8(
    tool_name: str, args: dict, input_schema: dict
) -> ValidationResult:
    """Check that all required fields are present in args."""
    required = input_schema.get("required")
    if not required or not isinstance(required, list):
        return ValidationResult(success=None)

    missing = [field for field in required if field not in args]
    if missing:
        return ValidationResult(
            success=False,
            reason=f"Missing required fields for {tool_name}: {missing}",
        )
    return ValidationResult(success=True)


def x__check_required_fields__mutmut_9(
    tool_name: str, args: dict, input_schema: dict
) -> ValidationResult:
    """Check that all required fields are present in args."""
    required = input_schema.get("required")
    if not required or not isinstance(required, list):
        return ValidationResult(success=False)

    missing = [field for field in required if field not in args]
    if missing:
        return ValidationResult(
            success=False,
            reason=f"Missing required fields for {tool_name}: {missing}",
        )
    return ValidationResult(success=True)


def x__check_required_fields__mutmut_10(
    tool_name: str, args: dict, input_schema: dict
) -> ValidationResult:
    """Check that all required fields are present in args."""
    required = input_schema.get("required")
    if not required or not isinstance(required, list):
        return ValidationResult(success=True)

    missing = None
    if missing:
        return ValidationResult(
            success=False,
            reason=f"Missing required fields for {tool_name}: {missing}",
        )
    return ValidationResult(success=True)


def x__check_required_fields__mutmut_11(
    tool_name: str, args: dict, input_schema: dict
) -> ValidationResult:
    """Check that all required fields are present in args."""
    required = input_schema.get("required")
    if not required or not isinstance(required, list):
        return ValidationResult(success=True)

    missing = [field for field in required if field in args]
    if missing:
        return ValidationResult(
            success=False,
            reason=f"Missing required fields for {tool_name}: {missing}",
        )
    return ValidationResult(success=True)


def x__check_required_fields__mutmut_12(
    tool_name: str, args: dict, input_schema: dict
) -> ValidationResult:
    """Check that all required fields are present in args."""
    required = input_schema.get("required")
    if not required or not isinstance(required, list):
        return ValidationResult(success=True)

    missing = [field for field in required if field not in args]
    if missing:
        return ValidationResult(
            success=None,
            reason=f"Missing required fields for {tool_name}: {missing}",
        )
    return ValidationResult(success=True)


def x__check_required_fields__mutmut_13(
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
            reason=None,
        )
    return ValidationResult(success=True)


def x__check_required_fields__mutmut_14(
    tool_name: str, args: dict, input_schema: dict
) -> ValidationResult:
    """Check that all required fields are present in args."""
    required = input_schema.get("required")
    if not required or not isinstance(required, list):
        return ValidationResult(success=True)

    missing = [field for field in required if field not in args]
    if missing:
        return ValidationResult(
            reason=f"Missing required fields for {tool_name}: {missing}",
        )
    return ValidationResult(success=True)


def x__check_required_fields__mutmut_15(
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
            )
    return ValidationResult(success=True)


def x__check_required_fields__mutmut_16(
    tool_name: str, args: dict, input_schema: dict
) -> ValidationResult:
    """Check that all required fields are present in args."""
    required = input_schema.get("required")
    if not required or not isinstance(required, list):
        return ValidationResult(success=True)

    missing = [field for field in required if field not in args]
    if missing:
        return ValidationResult(
            success=True,
            reason=f"Missing required fields for {tool_name}: {missing}",
        )
    return ValidationResult(success=True)


def x__check_required_fields__mutmut_17(
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
    return ValidationResult(success=None)


def x__check_required_fields__mutmut_18(
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
    return ValidationResult(success=False)

mutants_x__check_required_fields__mutmut['_mutmut_orig'] = x__check_required_fields__mutmut_orig # type: ignore # mutmut generated
mutants_x__check_required_fields__mutmut['x__check_required_fields__mutmut_1'] = x__check_required_fields__mutmut_1 # type: ignore # mutmut generated
mutants_x__check_required_fields__mutmut['x__check_required_fields__mutmut_2'] = x__check_required_fields__mutmut_2 # type: ignore # mutmut generated
mutants_x__check_required_fields__mutmut['x__check_required_fields__mutmut_3'] = x__check_required_fields__mutmut_3 # type: ignore # mutmut generated
mutants_x__check_required_fields__mutmut['x__check_required_fields__mutmut_4'] = x__check_required_fields__mutmut_4 # type: ignore # mutmut generated
mutants_x__check_required_fields__mutmut['x__check_required_fields__mutmut_5'] = x__check_required_fields__mutmut_5 # type: ignore # mutmut generated
mutants_x__check_required_fields__mutmut['x__check_required_fields__mutmut_6'] = x__check_required_fields__mutmut_6 # type: ignore # mutmut generated
mutants_x__check_required_fields__mutmut['x__check_required_fields__mutmut_7'] = x__check_required_fields__mutmut_7 # type: ignore # mutmut generated
mutants_x__check_required_fields__mutmut['x__check_required_fields__mutmut_8'] = x__check_required_fields__mutmut_8 # type: ignore # mutmut generated
mutants_x__check_required_fields__mutmut['x__check_required_fields__mutmut_9'] = x__check_required_fields__mutmut_9 # type: ignore # mutmut generated
mutants_x__check_required_fields__mutmut['x__check_required_fields__mutmut_10'] = x__check_required_fields__mutmut_10 # type: ignore # mutmut generated
mutants_x__check_required_fields__mutmut['x__check_required_fields__mutmut_11'] = x__check_required_fields__mutmut_11 # type: ignore # mutmut generated
mutants_x__check_required_fields__mutmut['x__check_required_fields__mutmut_12'] = x__check_required_fields__mutmut_12 # type: ignore # mutmut generated
mutants_x__check_required_fields__mutmut['x__check_required_fields__mutmut_13'] = x__check_required_fields__mutmut_13 # type: ignore # mutmut generated
mutants_x__check_required_fields__mutmut['x__check_required_fields__mutmut_14'] = x__check_required_fields__mutmut_14 # type: ignore # mutmut generated
mutants_x__check_required_fields__mutmut['x__check_required_fields__mutmut_15'] = x__check_required_fields__mutmut_15 # type: ignore # mutmut generated
mutants_x__check_required_fields__mutmut['x__check_required_fields__mutmut_16'] = x__check_required_fields__mutmut_16 # type: ignore # mutmut generated
mutants_x__check_required_fields__mutmut['x__check_required_fields__mutmut_17'] = x__check_required_fields__mutmut_17 # type: ignore # mutmut generated
mutants_x__check_required_fields__mutmut['x__check_required_fields__mutmut_18'] = x__check_required_fields__mutmut_18 # type: ignore # mutmut generated
mutants_x__check_extra_fields__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x__check_extra_fields__mutmut)
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


def x__check_extra_fields__mutmut_orig(
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


def x__check_extra_fields__mutmut_1(
    tool_name: str, args: dict, input_schema: dict
) -> ValidationResult:
    """Check that no extra fields are present beyond what the schema defines.

    When the schema has no 'properties' key, the extra field check is skipped
    (lenient fallback — we cannot determine which fields are allowed).
    """
    properties = None
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


def x__check_extra_fields__mutmut_2(
    tool_name: str, args: dict, input_schema: dict
) -> ValidationResult:
    """Check that no extra fields are present beyond what the schema defines.

    When the schema has no 'properties' key, the extra field check is skipped
    (lenient fallback — we cannot determine which fields are allowed).
    """
    properties = input_schema.get(None)
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


def x__check_extra_fields__mutmut_3(
    tool_name: str, args: dict, input_schema: dict
) -> ValidationResult:
    """Check that no extra fields are present beyond what the schema defines.

    When the schema has no 'properties' key, the extra field check is skipped
    (lenient fallback — we cannot determine which fields are allowed).
    """
    properties = input_schema.get("XXpropertiesXX")
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


def x__check_extra_fields__mutmut_4(
    tool_name: str, args: dict, input_schema: dict
) -> ValidationResult:
    """Check that no extra fields are present beyond what the schema defines.

    When the schema has no 'properties' key, the extra field check is skipped
    (lenient fallback — we cannot determine which fields are allowed).
    """
    properties = input_schema.get("PROPERTIES")
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


def x__check_extra_fields__mutmut_5(
    tool_name: str, args: dict, input_schema: dict
) -> ValidationResult:
    """Check that no extra fields are present beyond what the schema defines.

    When the schema has no 'properties' key, the extra field check is skipped
    (lenient fallback — we cannot determine which fields are allowed).
    """
    properties = input_schema.get("properties")
    if not properties and not isinstance(properties, dict):
        return ValidationResult(success=True)

    allowed_keys = set(properties.keys())
    extra_keys = set(args.keys()) - allowed_keys
    if extra_keys:
        return ValidationResult(
            success=False,
            reason=f"Extra fields not allowed for {tool_name}: {sorted(extra_keys)}",
        )
    return ValidationResult(success=True)


def x__check_extra_fields__mutmut_6(
    tool_name: str, args: dict, input_schema: dict
) -> ValidationResult:
    """Check that no extra fields are present beyond what the schema defines.

    When the schema has no 'properties' key, the extra field check is skipped
    (lenient fallback — we cannot determine which fields are allowed).
    """
    properties = input_schema.get("properties")
    if properties or not isinstance(properties, dict):
        return ValidationResult(success=True)

    allowed_keys = set(properties.keys())
    extra_keys = set(args.keys()) - allowed_keys
    if extra_keys:
        return ValidationResult(
            success=False,
            reason=f"Extra fields not allowed for {tool_name}: {sorted(extra_keys)}",
        )
    return ValidationResult(success=True)


def x__check_extra_fields__mutmut_7(
    tool_name: str, args: dict, input_schema: dict
) -> ValidationResult:
    """Check that no extra fields are present beyond what the schema defines.

    When the schema has no 'properties' key, the extra field check is skipped
    (lenient fallback — we cannot determine which fields are allowed).
    """
    properties = input_schema.get("properties")
    if not properties or isinstance(properties, dict):
        return ValidationResult(success=True)

    allowed_keys = set(properties.keys())
    extra_keys = set(args.keys()) - allowed_keys
    if extra_keys:
        return ValidationResult(
            success=False,
            reason=f"Extra fields not allowed for {tool_name}: {sorted(extra_keys)}",
        )
    return ValidationResult(success=True)


def x__check_extra_fields__mutmut_8(
    tool_name: str, args: dict, input_schema: dict
) -> ValidationResult:
    """Check that no extra fields are present beyond what the schema defines.

    When the schema has no 'properties' key, the extra field check is skipped
    (lenient fallback — we cannot determine which fields are allowed).
    """
    properties = input_schema.get("properties")
    if not properties or not isinstance(properties, dict):
        return ValidationResult(success=None)

    allowed_keys = set(properties.keys())
    extra_keys = set(args.keys()) - allowed_keys
    if extra_keys:
        return ValidationResult(
            success=False,
            reason=f"Extra fields not allowed for {tool_name}: {sorted(extra_keys)}",
        )
    return ValidationResult(success=True)


def x__check_extra_fields__mutmut_9(
    tool_name: str, args: dict, input_schema: dict
) -> ValidationResult:
    """Check that no extra fields are present beyond what the schema defines.

    When the schema has no 'properties' key, the extra field check is skipped
    (lenient fallback — we cannot determine which fields are allowed).
    """
    properties = input_schema.get("properties")
    if not properties or not isinstance(properties, dict):
        return ValidationResult(success=False)

    allowed_keys = set(properties.keys())
    extra_keys = set(args.keys()) - allowed_keys
    if extra_keys:
        return ValidationResult(
            success=False,
            reason=f"Extra fields not allowed for {tool_name}: {sorted(extra_keys)}",
        )
    return ValidationResult(success=True)


def x__check_extra_fields__mutmut_10(
    tool_name: str, args: dict, input_schema: dict
) -> ValidationResult:
    """Check that no extra fields are present beyond what the schema defines.

    When the schema has no 'properties' key, the extra field check is skipped
    (lenient fallback — we cannot determine which fields are allowed).
    """
    properties = input_schema.get("properties")
    if not properties or not isinstance(properties, dict):
        return ValidationResult(success=True)

    allowed_keys = None
    extra_keys = set(args.keys()) - allowed_keys
    if extra_keys:
        return ValidationResult(
            success=False,
            reason=f"Extra fields not allowed for {tool_name}: {sorted(extra_keys)}",
        )
    return ValidationResult(success=True)


def x__check_extra_fields__mutmut_11(
    tool_name: str, args: dict, input_schema: dict
) -> ValidationResult:
    """Check that no extra fields are present beyond what the schema defines.

    When the schema has no 'properties' key, the extra field check is skipped
    (lenient fallback — we cannot determine which fields are allowed).
    """
    properties = input_schema.get("properties")
    if not properties or not isinstance(properties, dict):
        return ValidationResult(success=True)

    allowed_keys = set(None)
    extra_keys = set(args.keys()) - allowed_keys
    if extra_keys:
        return ValidationResult(
            success=False,
            reason=f"Extra fields not allowed for {tool_name}: {sorted(extra_keys)}",
        )
    return ValidationResult(success=True)


def x__check_extra_fields__mutmut_12(
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
    extra_keys = None
    if extra_keys:
        return ValidationResult(
            success=False,
            reason=f"Extra fields not allowed for {tool_name}: {sorted(extra_keys)}",
        )
    return ValidationResult(success=True)


def x__check_extra_fields__mutmut_13(
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
    extra_keys = set(args.keys()) + allowed_keys
    if extra_keys:
        return ValidationResult(
            success=False,
            reason=f"Extra fields not allowed for {tool_name}: {sorted(extra_keys)}",
        )
    return ValidationResult(success=True)


def x__check_extra_fields__mutmut_14(
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
    extra_keys = set(None) - allowed_keys
    if extra_keys:
        return ValidationResult(
            success=False,
            reason=f"Extra fields not allowed for {tool_name}: {sorted(extra_keys)}",
        )
    return ValidationResult(success=True)


def x__check_extra_fields__mutmut_15(
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
            success=None,
            reason=f"Extra fields not allowed for {tool_name}: {sorted(extra_keys)}",
        )
    return ValidationResult(success=True)


def x__check_extra_fields__mutmut_16(
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
            reason=None,
        )
    return ValidationResult(success=True)


def x__check_extra_fields__mutmut_17(
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
            reason=f"Extra fields not allowed for {tool_name}: {sorted(extra_keys)}",
        )
    return ValidationResult(success=True)


def x__check_extra_fields__mutmut_18(
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
            )
    return ValidationResult(success=True)


def x__check_extra_fields__mutmut_19(
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
            success=True,
            reason=f"Extra fields not allowed for {tool_name}: {sorted(extra_keys)}",
        )
    return ValidationResult(success=True)


def x__check_extra_fields__mutmut_20(
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
            reason=f"Extra fields not allowed for {tool_name}: {sorted(None)}",
        )
    return ValidationResult(success=True)


def x__check_extra_fields__mutmut_21(
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
    return ValidationResult(success=None)


def x__check_extra_fields__mutmut_22(
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
    return ValidationResult(success=False)

mutants_x__check_extra_fields__mutmut['_mutmut_orig'] = x__check_extra_fields__mutmut_orig # type: ignore # mutmut generated
mutants_x__check_extra_fields__mutmut['x__check_extra_fields__mutmut_1'] = x__check_extra_fields__mutmut_1 # type: ignore # mutmut generated
mutants_x__check_extra_fields__mutmut['x__check_extra_fields__mutmut_2'] = x__check_extra_fields__mutmut_2 # type: ignore # mutmut generated
mutants_x__check_extra_fields__mutmut['x__check_extra_fields__mutmut_3'] = x__check_extra_fields__mutmut_3 # type: ignore # mutmut generated
mutants_x__check_extra_fields__mutmut['x__check_extra_fields__mutmut_4'] = x__check_extra_fields__mutmut_4 # type: ignore # mutmut generated
mutants_x__check_extra_fields__mutmut['x__check_extra_fields__mutmut_5'] = x__check_extra_fields__mutmut_5 # type: ignore # mutmut generated
mutants_x__check_extra_fields__mutmut['x__check_extra_fields__mutmut_6'] = x__check_extra_fields__mutmut_6 # type: ignore # mutmut generated
mutants_x__check_extra_fields__mutmut['x__check_extra_fields__mutmut_7'] = x__check_extra_fields__mutmut_7 # type: ignore # mutmut generated
mutants_x__check_extra_fields__mutmut['x__check_extra_fields__mutmut_8'] = x__check_extra_fields__mutmut_8 # type: ignore # mutmut generated
mutants_x__check_extra_fields__mutmut['x__check_extra_fields__mutmut_9'] = x__check_extra_fields__mutmut_9 # type: ignore # mutmut generated
mutants_x__check_extra_fields__mutmut['x__check_extra_fields__mutmut_10'] = x__check_extra_fields__mutmut_10 # type: ignore # mutmut generated
mutants_x__check_extra_fields__mutmut['x__check_extra_fields__mutmut_11'] = x__check_extra_fields__mutmut_11 # type: ignore # mutmut generated
mutants_x__check_extra_fields__mutmut['x__check_extra_fields__mutmut_12'] = x__check_extra_fields__mutmut_12 # type: ignore # mutmut generated
mutants_x__check_extra_fields__mutmut['x__check_extra_fields__mutmut_13'] = x__check_extra_fields__mutmut_13 # type: ignore # mutmut generated
mutants_x__check_extra_fields__mutmut['x__check_extra_fields__mutmut_14'] = x__check_extra_fields__mutmut_14 # type: ignore # mutmut generated
mutants_x__check_extra_fields__mutmut['x__check_extra_fields__mutmut_15'] = x__check_extra_fields__mutmut_15 # type: ignore # mutmut generated
mutants_x__check_extra_fields__mutmut['x__check_extra_fields__mutmut_16'] = x__check_extra_fields__mutmut_16 # type: ignore # mutmut generated
mutants_x__check_extra_fields__mutmut['x__check_extra_fields__mutmut_17'] = x__check_extra_fields__mutmut_17 # type: ignore # mutmut generated
mutants_x__check_extra_fields__mutmut['x__check_extra_fields__mutmut_18'] = x__check_extra_fields__mutmut_18 # type: ignore # mutmut generated
mutants_x__check_extra_fields__mutmut['x__check_extra_fields__mutmut_19'] = x__check_extra_fields__mutmut_19 # type: ignore # mutmut generated
mutants_x__check_extra_fields__mutmut['x__check_extra_fields__mutmut_20'] = x__check_extra_fields__mutmut_20 # type: ignore # mutmut generated
mutants_x__check_extra_fields__mutmut['x__check_extra_fields__mutmut_21'] = x__check_extra_fields__mutmut_21 # type: ignore # mutmut generated
mutants_x__check_extra_fields__mutmut['x__check_extra_fields__mutmut_22'] = x__check_extra_fields__mutmut_22 # type: ignore # mutmut generated
mutants_x__check_type_validation__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x__check_type_validation__mutmut)
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


def x__check_type_validation__mutmut_orig(
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


def x__check_type_validation__mutmut_1(
    tool_name: str, args: dict, input_schema: dict
) -> ValidationResult:
    """Validate arg values against declared types using jsonschema."""
    try:
        jsonschema.validate(instance=None, schema=input_schema)
    except jsonschema.ValidationError as e:
        return ValidationResult(
            success=False,
            reason=f"Type mismatch for {tool_name}: {e.message}",
        )
    return ValidationResult(success=True)


def x__check_type_validation__mutmut_2(
    tool_name: str, args: dict, input_schema: dict
) -> ValidationResult:
    """Validate arg values against declared types using jsonschema."""
    try:
        jsonschema.validate(instance=args, schema=None)
    except jsonschema.ValidationError as e:
        return ValidationResult(
            success=False,
            reason=f"Type mismatch for {tool_name}: {e.message}",
        )
    return ValidationResult(success=True)


def x__check_type_validation__mutmut_3(
    tool_name: str, args: dict, input_schema: dict
) -> ValidationResult:
    """Validate arg values against declared types using jsonschema."""
    try:
        jsonschema.validate(schema=input_schema)
    except jsonschema.ValidationError as e:
        return ValidationResult(
            success=False,
            reason=f"Type mismatch for {tool_name}: {e.message}",
        )
    return ValidationResult(success=True)


def x__check_type_validation__mutmut_4(
    tool_name: str, args: dict, input_schema: dict
) -> ValidationResult:
    """Validate arg values against declared types using jsonschema."""
    try:
        jsonschema.validate(instance=args, )
    except jsonschema.ValidationError as e:
        return ValidationResult(
            success=False,
            reason=f"Type mismatch for {tool_name}: {e.message}",
        )
    return ValidationResult(success=True)


def x__check_type_validation__mutmut_5(
    tool_name: str, args: dict, input_schema: dict
) -> ValidationResult:
    """Validate arg values against declared types using jsonschema."""
    try:
        jsonschema.validate(instance=args, schema=input_schema)
    except jsonschema.ValidationError as e:
        return ValidationResult(
            success=None,
            reason=f"Type mismatch for {tool_name}: {e.message}",
        )
    return ValidationResult(success=True)


def x__check_type_validation__mutmut_6(
    tool_name: str, args: dict, input_schema: dict
) -> ValidationResult:
    """Validate arg values against declared types using jsonschema."""
    try:
        jsonschema.validate(instance=args, schema=input_schema)
    except jsonschema.ValidationError as e:
        return ValidationResult(
            success=False,
            reason=None,
        )
    return ValidationResult(success=True)


def x__check_type_validation__mutmut_7(
    tool_name: str, args: dict, input_schema: dict
) -> ValidationResult:
    """Validate arg values against declared types using jsonschema."""
    try:
        jsonschema.validate(instance=args, schema=input_schema)
    except jsonschema.ValidationError as e:
        return ValidationResult(
            reason=f"Type mismatch for {tool_name}: {e.message}",
        )
    return ValidationResult(success=True)


def x__check_type_validation__mutmut_8(
    tool_name: str, args: dict, input_schema: dict
) -> ValidationResult:
    """Validate arg values against declared types using jsonschema."""
    try:
        jsonschema.validate(instance=args, schema=input_schema)
    except jsonschema.ValidationError as e:
        return ValidationResult(
            success=False,
            )
    return ValidationResult(success=True)


def x__check_type_validation__mutmut_9(
    tool_name: str, args: dict, input_schema: dict
) -> ValidationResult:
    """Validate arg values against declared types using jsonschema."""
    try:
        jsonschema.validate(instance=args, schema=input_schema)
    except jsonschema.ValidationError as e:
        return ValidationResult(
            success=True,
            reason=f"Type mismatch for {tool_name}: {e.message}",
        )
    return ValidationResult(success=True)


def x__check_type_validation__mutmut_10(
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
    return ValidationResult(success=None)


def x__check_type_validation__mutmut_11(
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
    return ValidationResult(success=False)

mutants_x__check_type_validation__mutmut['_mutmut_orig'] = x__check_type_validation__mutmut_orig # type: ignore # mutmut generated
mutants_x__check_type_validation__mutmut['x__check_type_validation__mutmut_1'] = x__check_type_validation__mutmut_1 # type: ignore # mutmut generated
mutants_x__check_type_validation__mutmut['x__check_type_validation__mutmut_2'] = x__check_type_validation__mutmut_2 # type: ignore # mutmut generated
mutants_x__check_type_validation__mutmut['x__check_type_validation__mutmut_3'] = x__check_type_validation__mutmut_3 # type: ignore # mutmut generated
mutants_x__check_type_validation__mutmut['x__check_type_validation__mutmut_4'] = x__check_type_validation__mutmut_4 # type: ignore # mutmut generated
mutants_x__check_type_validation__mutmut['x__check_type_validation__mutmut_5'] = x__check_type_validation__mutmut_5 # type: ignore # mutmut generated
mutants_x__check_type_validation__mutmut['x__check_type_validation__mutmut_6'] = x__check_type_validation__mutmut_6 # type: ignore # mutmut generated
mutants_x__check_type_validation__mutmut['x__check_type_validation__mutmut_7'] = x__check_type_validation__mutmut_7 # type: ignore # mutmut generated
mutants_x__check_type_validation__mutmut['x__check_type_validation__mutmut_8'] = x__check_type_validation__mutmut_8 # type: ignore # mutmut generated
mutants_x__check_type_validation__mutmut['x__check_type_validation__mutmut_9'] = x__check_type_validation__mutmut_9 # type: ignore # mutmut generated
mutants_x__check_type_validation__mutmut['x__check_type_validation__mutmut_10'] = x__check_type_validation__mutmut_10 # type: ignore # mutmut generated
mutants_x__check_type_validation__mutmut['x__check_type_validation__mutmut_11'] = x__check_type_validation__mutmut_11 # type: ignore # mutmut generated
