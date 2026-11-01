# Tool validation fails open empty schema

## Priority
Low

## Summary
`validate_tool_arguments()` skips every check (required fields, extra fields, jsonschema type validation, the custom-validator hook) and returns success when a tool's `input_schema` is missing or empty. The branch is documented as lenient mode, and registration-time validation (`validate_tool_schema_v2`) is a hard gate at MCP discovery, so an empty-schema tool cannot reach `RuntimeToolRegistry` through discovery; this is a structural fail-open kept as defense in depth. Change the branch to fail closed and remove the documented lenient mode.

## Background
Found during an adversarial code review (`python-code-review` skill) of the REPL's tool-execution/approval-gating subsystem (`scripts/agent/tool_arg_validator.py`), cross-referenced against this project's own stated rule ("fail-fast for unknown tool names, tiers, or metadata — never fail-open").

## Problem
`scripts/agent/tool_arg_validator.py::validate_tool_arguments()`:
```python
if not input_schema:
    logger.debug("No input schema for %s; skipping validation", tool_name)
    return ValidationResult(success=True)
```
The module's own docstring states this module exists to "prevent argument injection attacks," yet a falsy `input_schema` (missing or `{}`) bypasses required-field checks, extra-field checks, jsonschema type validation, and the registered custom validator hook, returning `ValidationResult(success=True)` instead of rejecting.

## Reason for Change
The branch contradicts the project's fail-fast policy. `validate_tool_schema_v2` rejects a missing or empty `inputSchema` and is a hard gate in `mcp_tool_discovery_fetch.py` (it returns an error string, not only a warning), so this is defense in depth only. Empty-schema runtime tools can come only from `build_runtime_tool` called without a schema (mostly tests), which defaults a missing schema to `{}`. Zero-argument tools are not affected because their schema is a non-empty dict such as `{"type": "object", "properties": {}}`.

## Implementation Intent
Change the `if not input_schema` branch to return a rejection (`ValidationResult(success=False, ...)`) rather than lenient acceptance, consistent with `shared/resource_scope.py::validate_tool_schema_v2()`'s "reject rather than silently accept" stance for the same data. Confirm first whether any legitimate tool is expected to have no schema at all (e.g. a zero-argument tool) — if so, that case needs an explicit, narrow allowance (e.g. an empty but present `{"type": "object", "properties": {}}` schema) distinct from a missing/malformed schema.

## Target Files or Areas
- `scripts/agent/tool_arg_validator.py` (`validate_tool_arguments()`, module docstring "lenient mode" sentence)
- `scripts/shared/runtime_tool.py` (`build_runtime_tool`, default schema `{}`)
- `tests/` that build tools without a schema (fail-closed will break them)

## Required Changes
- Replace the `return ValidationResult(success=True)` branch for a missing or empty schema with a rejection; keep a well-formed empty-properties schema accepted.
- Update the module docstring sentence that describes lenient mode.
- Update tests that build runtime tools without a schema.
- Add tests: missing `input_schema` is rejected; `{}` is rejected; a well-formed zero-argument schema is accepted.

## Constraints
- Do not change behavior for a tool with a well-formed, non-empty schema.
- Do not weaken the existing jsonschema/custom-validator checks that already run when a schema is present.

## Acceptance Criteria
- A tool call targeting a tool whose `input_schema` is missing or `{}` is rejected by `validate_tool_arguments()`, not silently accepted.
- A legitimate zero-argument tool (if one exists with a well-formed empty-properties schema) is unaffected.

## Testing Expectations
Unit tests: (1) missing `input_schema` → rejection; (2) `input_schema = {}` → rejection; (3) a well-formed zero-argument schema (if applicable) → acceptance. Run `tests/agent/test_tool_arg_validator.py` after the change.

## Documentation Impact
N/A: no operator-facing documentation describes this specific fail-open branch today.

## Out of Scope
- `shared/resource_scope.py::validate_tool_schema_v2()`'s own registration-time gating logic, beyond confirming its advisory-vs-hard-gate status.
- Any change to the jsonschema validation logic that already runs for a present schema.

## Dependencies
N/A: none.

## Unresolved Questions
N/A: none. `validate_tool_schema_v2` is a hard gate at discovery (`Explicit in code`), so the severity is Low.

## AI Implementation Instruction
Change the fail-open branch to fail closed and update the docstring and the tests that rely on it; do not touch the jsonschema or custom-validator logic for present schemas. Add the tests described above before considering this done.

## Traceability
- **Workflow phase**: python-code-review -> issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261003-180328
- **Related target files**: scripts/agent/tool_arg_validator.py, scripts/agent/services/mcp_tool_discovery.py, shared/resource_scope.py
