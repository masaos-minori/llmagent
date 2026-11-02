<!-- workitem: {"id": "20261102-192710", "generated_at": "2026-11-02T19:27:10Z", "schema_hash": "488513b688446992", "schema_version": 1, "source": "plans/20261101-142029_toolarg001_tool-validation-fails-open-empty-schema.md", "target_file": "scripts/agent/tool_arg_validator.py", "target_kind": "source", "seq": 1} -->

## Goal

Make `validate_tool_arguments()` reject a call whose `input_schema` is missing or
`{}` (REQ-001: fail closed on missing/empty schema) instead of returning success,
and remove the "lenient mode" docstring paragraph (REQ-002: docstring states the
rejection). Companion test file carries the unit tests (REQ-003).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- The rule stays exactly "missing or empty": keep the existing `if not input_schema`
  truthiness test. Non-dict truthy test doubles (e.g. a `MagicMock` schema attribute)
  keep their current behavior — an `isinstance` tightening is not in the Plan
  (Plan Assumptions; falsifiable via `tests/agent/test_tool_loop_guard_wiring.py` in AC-4).
- A well-formed zero-argument schema `{"type": "object", "properties": {}}` is truthy
  and takes the normal path, so it stays accepted without a special allowance
  (Plan Assumptions; existing `test_empty_properties_allows_any_field` in
  `tests/agent/test_tool_argument_injection_security.py` shows the shape is accepted).
- Rejection happens here, not in `build_runtime_tool()` (Plan UNK-01, owner decision
  not taken; the `{}` default stays unchanged).
- Fallout pin migration (deviation, precedent: healthcascade001's 400-behavior pins):
  `tests/agent/test_tool_argument_injection_security.py::test_no_schema_allows_any_field`
  pinned the old lenient outcome but the file is not a Plan target row; it was renamed
  to `test_no_schema_rejects_any_field` asserting the new rejection contract. No other
  behavior in that file changed (its `test_no_properties_key_allows_any_field` and
  `test_empty_properties_allows_any_field` use non-empty schemas and stay valid).
- Execution order: land the fixture migrations of procedures seq 03-06 (Plan Phase 1)
  before this change; otherwise 34 stub-based tests fail (Plan Design evidence).

## Design decisions

- Keep the early-return shape (log + failed `ValidationResult`): replacing one early
  return with another does not change cyclomatic complexity (radon B(7) baseline).
- Log at warning, not debug: a reachable falsy branch now means a registry
  construction bug. The reason string must name the tool so the answered tool
  message is actionable (Plan Design).

## Alternatives considered

- `not isinstance(input_schema, dict) or not input_schema` (mirroring
  `validate_tool_schema_v2`): rejected — it would also reject `MagicMock` schemas used
  by other test doubles, with no production benefit (the registry always holds a dict).
- Rejecting in `build_runtime_tool()`: rejected — out of the Issue's Required Changes
  and breaks `tests/shared/` real-registry fixtures that never reach the validator.

## Implementation
### Target file
`scripts/agent/tool_arg_validator.py`

### Procedure
Replace the falsy-schema success branch in `validate_tool_arguments()` with a failed
`ValidationResult` plus a warning log, and reword the docstring's lenient-mode
paragraph (REQ-001, REQ-002).

### Method
- In the `if not input_schema:` block: change `logger.debug(...)` to a `logger.warning`
  naming the tool and the missing schema, and return
  `ValidationResult(success=False, reason=...)` where the reason names the tool and
  contains the words "input schema" (AC-1).
- Docstring: delete the paragraph "When the schema is missing or malformed, falls back
  to lenient mode (accept all fields) to prevent blocking legitimate tool calls." and
  state that a missing or empty schema is rejected. Keep the first docstring line
  unchanged so the generated API reference stays in sync (AC-2).

### Details
- Current behavior (verified 20261102): the branch logs "No input schema for %s;
  skipping validation" at debug and returns `ValidationResult(success=True)`; the
  docstring paragraph says "falls back to lenient mode".
- Both `None` and `{}` are falsy and reach this branch; `allow_extra_fields` and any
  registered custom validator cannot change the outcome because the rejection
  precedes both checks (REQ-001).
- The only production caller, `scripts/agent/tool_preparation._prepare_one`, already
  maps a failed result to `_reject(..., "schema", validation.reason)` — no caller
  change is needed.

### Companion test files
- `tests/agent/test_tool_arg_validator.py`
  - Procedure: in `TestValidateToolArgumentsEmptySchema`, flip the three lenient tests
    to assert rejection: rename `test_none_schema_skips_validation` to
    `test_none_schema_rejected` (new), `test_empty_dict_schema_skips_validation` to
    `test_empty_dict_schema_rejected` (new), `test_missing_required_with_empty_schema` to
    `test_missing_required_with_empty_schema_rejected` (new) (each asserts `success is False`
    and a reason naming the tool and "input schema"); add
    `test_empty_schema_rejected_with_allow_extra_fields` (new) (same rejection with
    `allow_extra_fields=True`) and `test_zero_argument_schema_accepted` (new)
    (`{"type": "object", "properties": {}}` with empty args succeeds) (REQ-003).
  - Pin migration found at execution (Step 3a, 20261102):
    `test_hook_skipped_when_schema_empty` also pinned the lenient outcome; renamed to
    `test_hook_not_reached_when_schema_empty` asserting rejection and no hook call
    (the rejection precedes the hook lookup).
  - Validation: `uv run pytest tests/agent/test_tool_arg_validator.py tests/agent/test_tool_argument_injection_security.py` — all pass.

## Compatibility considerations

Behavior changes only for a falsy schema: the `validate_tool_arguments()` signature,
`ValidationResult`, and the check/hook ordering are unchanged. First docstring line
unchanged, so `docs/23_agent/agent_13_reference-api-generated.md` and
`registry/manifests/agent_api.yaml` stay in sync (AC-2).

## Security considerations

Closes the structural fail-open branch in the argument-injection gate, aligning it
with the project fail-fast policy and the discovery gate's stance; independent of the
discovery gate going forward (Plan Reason for Change).

## Rollback considerations

N/A: revert the commit.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| This file (unit, via companion) | Unit | `uv run pytest tests/agent/test_tool_arg_validator.py tests/agent/test_tool_argument_injection_security.py` | All pass, flipped and new cases green (AC-1, AC-3) |
| Changed `scripts/` lines | Lint/type/arch/security | `uv run ruff format`, `uv run ruff check`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus`, `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml -ll` | Clean |
| Generated reference | Docs sync | `uv run python tools/generate_reference_table.py --check`, `uv run python tools/check_module_size.py`, `uv run python tools/check_docstrings.py` | Clean; generated API reference unchanged (AC-2) |
| Changed lines | Coverage | `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` (sequence in `rules/toolchain.md` section 7) | At least 90% |

## Completion criteria

- `validate_tool_arguments("t", {...}, {})` and `validate_tool_arguments("t", {...}, None)`
  return `success=False`; the reason contains the tool name and "input schema"; the
  result is identical with `allow_extra_fields=True` (AC-1).
- The docstring no longer contains "lenient mode" and states the rejection; the first
  line is unchanged (AC-2).
- Companion and injection-security test files pass (AC-3).

## Out of Scope

- The jsonschema, required-field, extra-field and custom-validator logic for a
  non-empty schema (Issue Constraint).
- The separate lenient fallback in `_check_extra_fields()` for a non-empty schema
  without `properties` (Plan Out-of-Scope).
- `scripts/shared/runtime_tool.py` `build_runtime_tool()` `{}` default (Plan UNK-01),
  `scripts/shared/resource_scope.py` `validate_tool_schema_v2()` and the discovery
  gate in `scripts/agent/services/mcp_tool_discovery_fetch.py`.
- No `docs/*.md` change (Plan Documentation Impact: N/A).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace the falsy-schema success branch (warning + failed `ValidationResult`) and reword the docstring paragraph (REQ-001, REQ-002) | Completed | 2026-11-02 | 2026-11-02 | Plan Phase 2; start only after the fixture migrations of procedures seq 03-06 (Plan Phase 1) have landed |
| 2 | Flip the three lenient tests and add the `None`, `allow_extra_fields=True` and zero-argument cases in the companion file (REQ-003) | Completed | 2026-11-02 | 2026-11-02 | TDD order: companion tests written first (red), then the validator change; companion hook pin renamed; injection-file pin migrated as fallout (see Assumptions) |
| 3 | Run the validation sequence (`rules/toolchain.md`) incl. the docs-sync checkers above | Completed | 2026-11-02 | 2026-11-02 | Batch full-suite run passed: 11369 passed / 8 skipped; diff-cover 100%; ruff/mypy/lint-imports/bandit -ll/docs-sync checkers clean |

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
- **Requirement ID**: `REQ-001` (reject missing/empty schema), `REQ-002` (docstring), `REQ-003` (companion unit tests)
- **Source issue**: issues/20261003-180328_toolarg001_tool-validation-fails-open-empty-schema.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261101-142029_toolarg001_tool-validation-fails-open-empty-schema.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261102-192710
- **Related target files**: scripts/agent/tool_arg_validator.py, `tests/agent/test_tool_arg_validator.py`
