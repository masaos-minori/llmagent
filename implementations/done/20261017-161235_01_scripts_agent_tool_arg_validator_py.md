# Implementation Procedure — `scripts/agent/tool_arg_validator.py`

## Goal

Make `_check_type_validation()` robust against malformed MCP input schemas by catching
`jsonschema.SchemaError` in addition to `jsonschema.ValidationError`, returning a failed
`ValidationResult` with a schema-specific reason instead of crashing the tool execution
path (`REQ-001`, `REQ-002`).

## Scope

Modify only `scripts/agent/tool_arg_validator.py`. Add an `except jsonschema.SchemaError`
branch to `_check_type_validation()` after the existing `ValidationError` branch. Do NOT
touch the `ValidationError` branch, required-fields/extra-fields/custom-validator steps, or
any other file.

## Assumptions

- `_check_type_validation(tool_name, args, input_schema)` is at lines 184–195 and currently
  catches only `jsonschema.ValidationError`.
- `jsonschema` is imported at module level (line 33).
- `ValidationResult(success=False, reason=...)` is the established failure shape.

## Adversarial verification findings (plan discrepancies)

- **The plan's "defensive `jsonschema.exceptions.JSONSchemaError`" does not exist.** This
  repo's `jsonschema` version exposes only `ValidationError` and `SchemaError`, which are
  **sibling** classes both subclassing the private `_Error` → `Exception`. There is no
  public `JSONSchemaError` base. Therefore the defensive base-class catch cannot be written
  as stated and MUST be dropped.
- Because `ValidationError` and `SchemaError` are siblings (neither a subclass of the
  other), their relative except-clause order does not affect correctness. Place the new
  `SchemaError` branch after the existing `ValidationError` branch. A defensive base catch
  is unnecessary: `SchemaError` already covers malformed-schema cases and there is no public
  broader class than `_Error`/`Exception` to guard against.
- `SchemaError` exposes a `.message` attribute (verified), so `{e.message}` is usable in the
  reason string.

## Design decisions

- Catch `SchemaError` only (not a bare `Exception`) — matches the plan's out-of-scope
  prohibition on broadening the catch and keeps fail-closed behavior.
- Use a distinct reason string so operators can tell a malformed schema apart from a value
  type mismatch (`REQ-002`).
- Preserve the existing `ValidationError` message format verbatim (`REQ-002`).

## Alternatives considered

- Wrapping in a broad `except Exception`: rejected — explicitly out of scope and would mask
  unrelated bugs.
- Relying on the outer caller to catch: rejected — `validate_tool_arguments()` does not wrap
  `_check_type_validation()` in try/except (confirmed in `scripts/agent/services/tool_validation.py`), so the fix belongs here.

## Implementation

### Target file

`scripts/agent/tool_arg_validator.py`

### Procedure

1. Open `_check_type_validation()` (lines 184–195).
2. After the existing `except jsonschema.ValidationError as e: ... return ...` block, add:
   ```python
   except jsonschema.SchemaError as e:
       return ValidationResult(
           success=False,
           reason=f"Invalid input schema for {tool_name}: {e.message}",
       )
   ```
3. Verify the `ValidationError` branch is unchanged (same message format).
4. Do NOT add any `JSONSchemaError` clause (class does not exist).

### Method

Edit the function body inline; keep the `ValidationError` branch first, then the new
`SchemaError` branch. Re-run the affected unit tests.

### Details

- `tool_name` is already a parameter of `_check_type_validation`; reuse it in the reason.
- Do not log or return the raw schema contents (may contain sensitive data).

## Compatibility considerations

Adding a branch changes only the exception-handling surface; valid schemas and ordinary
type mismatches keep their current behavior (`REQ-004`). No caller relies on `SchemaError`
propagating (confirmed none does).

## Security considerations

Fail closed: a malformed schema now yields `success=False` rather than an unhandled
exception that could crash the tool execution path (defense-in-depth gap closed).

## Rollback considerations

Revert the commit to `scripts/agent/tool_arg_validator.py`.

## Validation plan

- Unit: feed a deliberately malformed schema (e.g. `{"type": "invalid-type-token"}` or a
  schema with an illegal keyword) and assert `_check_type_validation()` returns
  `success=False` with the schema-specific reason and raises nothing.
- Regression: a valid schema returns `success=True`; an ordinary type mismatch returns the
  unchanged `ValidationError` reason format.
- Command: `uv run pytest tests/agent/test_tool_arg_validator.py -q`.
- Lint/type: `uv run ruff check scripts/agent/tool_arg_validator.py` and
  `uv run mypy scripts/agent/tool_arg_validator.py` clean.

## Completion criteria

`_check_type_validation()` returns `success=False` for a malformed schema without raising,
the `SchemaError` reason is distinct from the `ValidationError` reason, and existing
valid-schema/type-mismatch behavior is unchanged.

## Out of scope

The `ValidationError` branch, other validation steps, the test file (separate row), and
any JSON Schema library version change.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `except jsonschema.SchemaError` to `_check_type_validation()` | Completed | 20261018-100916 | 20261018-100916 | drop non-existent JSONSchemaError (verification finding) |
| 2 | Add or update tests per Validation plan | Completed | 20261018-100916 | 20261018-100916 | N/A: test file is a separate row |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261018-100916 | 20261018-100916 | stale_detector findings were false positives (jsonschema.SchemaError is a valid library exception; _Error/JSONSchemaError are prose mentions in the findings section); ruff clean, mypy clean, 27 tests pass, malformed-schema returns success=False |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261018-100916 | 20261018-100916 | N/A: doc is a separate row |

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
- **Requirement ID**: `REQ-001` (catch `SchemaError`, return failed result), `REQ-002`
  (distinct schema-specific reason; preserve `ValidationError` format)
- **Source issue**: `issues/20261017-123041_argval01_catch-jsonschema-schemaerror-tool-argument-validation.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261017-140719_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261017-161235
- **Related target files**: `scripts/agent/tool_arg_validator.py`