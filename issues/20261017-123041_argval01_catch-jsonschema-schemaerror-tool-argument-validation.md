# Catch jsonschema.SchemaError in tool argument type validation

## Priority
Medium

## Summary
`_check_type_validation()` in `scripts/agent/tool_arg_validator.py` only catches
`jsonschema.ValidationError`. A structurally invalid MCP input schema raises
`jsonschema.SchemaError` instead, which propagates uncaught. Make type validation
robust against both error kinds so a malformed server schema is reported as a
validation failure rather than crashing the execution path.

## Background
Tool arguments are validated against each MCP server's declared `input_schema`
before execution. The type-check step delegates to `jsonschema.validate()` inside
`_check_type_validation()`. Per `docs/23_agent/agent_06_01_...execution.md` Known
Limitations, structurally invalid schemas from MCP servers may raise
`jsonschema.SchemaError`, which that function does not catch.

## Problem
`_check_type_validation()` wraps only `jsonschema.ValidationError`:

```python
try:
    jsonschema.validate(instance=args, schema=input_schema)
except jsonschema.ValidationError as e:   # SchemaError is NOT caught here
    return ValidationResult(success=False, reason=...)
return ValidationResult(success=True)
```

`jsonschema.SchemaError` (raised when the schema itself is malformed, e.g. invalid
JSON Schema syntax/keywords) is a distinct exception hierarchy from
`ValidationError`. When an MCP server ships a broken schema, `validate()` raises
`SchemaError`, which escapes `_check_type_validation()` and the surrounding
validation call chain, turning a recoverable "bad schema" condition into an
unhandled exception in the tool execution path.

## Reason for Change
A broken or malicious MCP server can therefore crash the tool execution path by
shipping a malformed schema, rather than being rejected like any other type
mismatch. This is a defense-in-depth and reliability gap: schema validity is a
precondition that should fail closed with a reported validation error, not an
uncaught exception.

## Implementation Intent
Wrap the `jsonschema.validate()` call in `_check_type_validation()` to also catch
`jsonschema.SchemaError` (and, defensively, the base `jsonschema.exceptions.JSONSchemaError`)
and convert them to a `ValidationResult(success=False, ...)` with a clear reason.
Keep the existing `ValidationError` handling unchanged. Do not alter the
required-fields, extra-fields, or custom-validator steps.

## Target Files or Areas
- `scripts/agent/tool_arg_validator.py` (`_check_type_validation`, lines ~184-195)
- Related: `scripts/agent/services/tool_validation.py` (caller chain, to confirm the exception currently propagates)

## Required Changes
- Catch `jsonschema.SchemaError` in addition to `jsonschema.ValidationError` in
  `_check_type_validation()` and return a failed `ValidationResult`.
- Use a distinct reason string for schema errors (e.g. "Invalid input schema for
  {tool_name}: {e.message}") so operators can tell it apart from a value type
  mismatch.
- Add a unit test that feeds a deliberately malformed schema and asserts the
  validation returns `success=False` instead of raising.

## Constraints
- Do not change the success/failure semantics for valid schemas or ordinary value
  mismatches.
- Do not broaden the catch to bare `Exception` — only the jsonschema error
  hierarchy.
- Preserve the existing `ValidationError` message format for backward compatibility
  with any log parsing or tests.

## Acceptance Criteria
- A malformed `input_schema` causes `_check_type_validation()` to return
  `success=False` rather than raising.
- A valid schema and an ordinary type mismatch keep their current behavior.
- A new unit test covers the `SchemaError` path and asserts no exception escapes.

## Testing Expectations
- Unit test for `_check_type_validation()` with a malformed schema (asserts failed
  result, no raise).
- Regression tests for the existing valid-schema and type-mismatch cases.
- Confirm no caller relies on `SchemaError` propagating (grep the validation call
  chain).

## Documentation Impact
Update the Known Limitations bullet in
`docs/23_agent/agent_06_01_...execution.md` to reflect that structurally invalid
schemas are now handled, or move the item to a resolved note.

## Out of Scope
- Changing how valid schemas are validated.
- Adding new validation steps beyond type checking.
- Modifying the JSON Schema library version.

## Dependencies
- N/A: none

## Unresolved Questions
- Whether callers of the validation call chain already have a try/except that
  swallows `SchemaError`; if so, the observable impact is smaller than the doc
  implies. Confirm by tracing the caller before deciding severity.
- Whether `SchemaError` should be surfaced to the user as a tool error message or
  logged server-side only.

## AI Implementation Instruction
Do NOT change the `ValidationError` branch or any other validation step. Only add
a `except jsonschema.SchemaError` (and defensively
`jsonschema.exceptions.JSONSchemaError`) branch to `_check_type_validation()` in
`scripts/agent/tool_arg_validator.py` that returns a failed `ValidationResult`
with a schema-specific reason. Add one unit test for the malformed-schema path.
Confirm the exception does not escape via the caller chain first; if a caller
already handles it, note that in the PR but still close the gap defensively.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261017-123041
- **Related target files**: `scripts/agent/tool_arg_validator.py`
