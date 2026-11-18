## Goal

Apply the approved DT-02 decision (Option A, 2026-11-18): `_check_extra_fields()` must fail closed
for schemas without `properties` (REQ-008), with `RuntimeTool.allow_extra_fields` as the only
per-tool escape hatch (REQ-004).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- No shipped MCP tool schema lacks `properties` (all are built by `_input_schema(PydanticModel)`),
  so this change cannot alter behavior of any current tool; it closes a latent permissive default.
- `RuntimeTool.allow_extra_fields` (`scripts/shared/runtime_tool.py`) remains the sanctioned escape
  hatch and is untouched.

## Design decisions
- Fail closed: when a schema defines no `properties`, extra fields are rejected (previously the
  check was skipped). `ValidationResult(success=False, reason=...)` follows the existing shape of
  the required-fields failure path.
- The single assertion set is rewritten, not duplicated: the companion test is rewritten in the
  same commit so the suite never documents both policies (Plan Assumptions).

## Alternatives considered
- Keep the lenient default (DT-02 Option B) and require explicit registration (Option C) — both
  rejected by the maintainer decision.

## Implementation
### Target file
`scripts/agent/tool_arg_validator.py`
### Procedure
1. In `_check_extra_fields()` (`:166-184`), replace the "no `properties` → skip" branch with a
   rejection branch that reports the schema is missing `properties` and cannot validate extra fields.
2. Update the function docstring to state the fail-closed contract and name
   `RuntimeTool.allow_extra_fields` as the escape hatch.
### Method
One branch change plus docstring; the `properties`-present path is unchanged.
### Details
- The rejection `reason` must name the tool (mirror the `Missing required fields for {tool_name}` idiom)
  so the log identifies which schema needs a fix.
- Argument validation runs before the approval gate (`scripts/agent/tool_preparation.py`), so the blast
  radius stays inside the validation step.

### Companion test files
- `tests/agent/test_tool_arg_validator.py`
  - Procedure: rewrite `test_properties_absent_allows_extra` (`:172`) to assert rejection for a schema
    without `properties`; keep it a single assertion set (rename it to match the new contract).
  - Validation: `uv run pytest tests/agent/test_tool_arg_validator.py -q` passes with exactly one
    assertion set for schemas without `properties`.
- `tests/agent/test_tool_argument_injection_security.py`
  - Procedure: rewrite `test_no_properties_key_allows_any_field` (`:62`) and
    `test_empty_properties_allows_any_field` (`:284`) to assert rejection — these pinned assertions
    were found during execution-cycle verification (2026-11-19); the original "single assertion set"
    claim missed this file. Same commit as the code change.
  - Validation: `uv run pytest tests/agent/test_tool_argument_injection_security.py -q` contains no
    assertion accepting the lenient default.

## Compatibility considerations
- Only future schemas are affected (none shipped lacks `properties`); no MCP server change is needed.

## Security considerations
Turns a fail-open default into fail-closed; no new attack surface.

## Rollback considerations
N/A: revert the commit (code and companion test land together).

## Validation plan
- `uv run pytest tests/agent/test_tool_arg_validator.py -q`
- Lint/type check per `rules/toolchain.md`.

## Completion criteria
- A schema without `properties` rejects extra fields; `allow_extra_fields` tools still pass;
  the suite contains exactly one assertion set for the no-`properties` case.

## Out of Scope
`scripts/shared/runtime_tool.py` (Reference file), registration-time schema enforcement
(rejected DT-02 Option C).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the fail-closed branch per Procedure/Method/Details | Completed | 20261119-072416 | 20261119-072416 | Rejection branch + docstring; empty-args no-properties call still passes |
| 2 | Rewrite the pinned assertion in the companion test in the same commit | Completed | 20261119-072416 | 20261119-072416 | 3 pinned assertions rewritten: test_tool_arg_validator.py:172 plus test_tool_argument_injection_security.py:62 and :284 (found in verification; procedure corrected) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261119-072416 | 20261119-072416 | ruff format/check + mypy pass; 152 tests pass incl. test_tool_runner.py blast-radius check |

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
- **Requirement ID**: `REQ-008` (fail-closed validation default), `REQ-004` (DT-02 decision)
- **Source issue**: `issues/20261117-123003_adrchk003_agent-approval-policy.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261118-224457_adrchk003_agent-approval-policy.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-233456
- **Related target files**: `scripts/agent/tool_arg_validator.py`, `tests/agent/test_tool_arg_validator.py`
