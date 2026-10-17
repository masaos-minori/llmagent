# Implementation Procedure — `tests/agent/test_tool_arg_validator.py`

## Goal

Add a unit test for the malformed-schema path and regression coverage for the existing
valid-schema / type-mismatch cases (`REQ-003`, `REQ-004`).

## Scope

Modify only `tests/agent/test_tool_arg_validator.py`. Append a test asserting that a
deliberately malformed schema makes `_check_type_validation()` return `success=False`
without raising, plus regression assertions for valid schema and ordinary type mismatch.
Depends on the code change in `scripts/agent/tool_arg_validator.py` (this plan's row 1).

## Assumptions

- The existing test file imports `ValidationResult` and `_check_type_validation` (or the
  module under test); append new test functions rather than rewriting fixtures.
- Row 1 adds the `SchemaError` catch, so `_check_type_validation()` will now return
  `success=False` for a malformed schema.

## Design decisions

- Construct a malformed schema that deterministically raises `jsonschema.SchemaError` (a
  schema with an illegal keyword/token), not a `ValidationError` (which a bad *instance*
  raises) — verify which one a given dict produces before asserting.
- Keep regression tests for the valid-schema and type-mismatch cases intact.

## Alternatives considered

- Reusing an existing malformed-instance schema: rejected — that raises `ValidationError`,
  not `SchemaError`; the test must target the schema-malformed path specifically.

## Implementation

### Target file

`tests/agent/test_tool_arg_validator.py`

### Procedure

1. Add a test that calls `_check_type_validation()` with a malformed schema and asserts
   `result.success is False` and that no exception escapes; optionally assert the reason
   contains the schema-specific marker (`"Invalid input schema"`).
2. Add a regression test that a valid schema returns `success=True`.
3. Add a regression test that an ordinary type mismatch returns the unchanged
   `ValidationError` reason format.
4. Confirm the malformed-schema fixture actually triggers `SchemaError` (not
   `ValidationError`) by inspecting the raised exception type during development.

### Method

Append test functions to the existing file; reuse existing helpers/fixtures.

### Details

- If the exact malformed schema that raises `SchemaError` is environment-dependent, pin it
  to a concrete illegal keyword known to raise `SchemaError` in this `jsonschema` version.

## Compatibility considerations

N/A: test-only change.

## Security considerations

Do not assert on or leak raw schema contents beyond the documented reason marker.

## Rollback considerations

Revert the commit to the test file.

## Validation plan

- Run the agent validator tests; all pass.
- Command: `uv run pytest tests/agent/test_tool_arg_validator.py -q`.

## Completion criteria

A malformed-schema test asserts `success=False` with no escape; valid-schema and
type-mismatch regressions pass.

## Out of scope

`scripts/agent/tool_arg_validator.py` (separate row).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the test changes in test_tool_arg_validator.py | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-003` (malformed-schema test, no raise), `REQ-004` (regression)
- **Source issue**: `issues/20261017-123041_argval01_catch-jsonschema-schemaerror-tool-argument-validation.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261017-140719_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261017-161235
- **Related target files**: `tests/agent/test_tool_arg_validator.py`
