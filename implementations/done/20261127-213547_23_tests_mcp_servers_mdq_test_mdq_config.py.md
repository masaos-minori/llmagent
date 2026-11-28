## Goal

Replace the defaults-construction and boolean-coercion tests with strict-boolean and explicit-values expectations (REQ-007 strict configuration types).

## Scope
**Release unit**: boundary-characterization-tests (Plan step 1 cites this row; the unit covers Phases 1, 3, 4, 5, 6)

## Assumptions
- This row keeps its own document because it fails the companion condition (2): it is named by two code rows, `scripts/mcp_servers/mdq/mdq_models.py` (seq 06) and `scripts/mcp_servers/mdq/mdq_service.py` (seq 02).
- Plan Gap recorded by this pass: no `Implementation steps` entry cites this row; the row is covered by the plan's Tests section (REQ-007), not by a step.
- Written in Phase 1 before the production change; the replacement assertions fail first and pin the behavior being removed.

## Design decisions
- The construction test supplies explicit values for every key instead of relying on defaults.
- The boolean test asserts rejection of a non-boolean value rather than coercion.

## Alternatives considered
- N/A: the row is a test file.

## Implementation
### Target file
`tests/mcp_servers/mdq/test_mdq_config.py`

### Procedure
- Replace `test_all_defaults_construct_successfully` (line 20) with an explicit-values construction test.
- Replace `test_recognized_boolean_tokens_coerce` (line 88) with a strict-boolean rejection test.
- Keep the range and type rejection tests (`test_rejects_non_positive`, `test_rejects_non_list`) unchanged.

### Method
- The expectations follow `RULE_BOOL` and `ConfigFieldTypeError` in `scripts/shared/config_field_types.py`, whose error text names the field path only.
- Step 3b correction (20261128): `ConfigFieldTypeError` is a `ValueError` subclass, so a pydantic validator that applies the strict primitive has its error wrapped into `pydantic.ValidationError`. The assertion is on `ValidationError`, and the AC-6 assertion is on `errors()[0]["message"]`, because pydantic's error dict carries `input_value` separately and a plain "value not in the text" assertion would fail for the wrong reason.
- Step 3b correction (20261128): "keep the range and type rejection tests unchanged" cannot hold literally. Once seq 06 removes the defaults, `MdqConfig(**{field: bad_value})` fails because the other keys are missing, so those tests would pass for the wrong reason. They now build on one explicit payload helper (`_explicit()`) so the failure is the field under test; the assertions themselves are unchanged.
- Step 3b correction (20261128): the explicit payload supplies a non-empty `allowed_dirs`, so the construction test does not depend on a list-emptiness rule this row does not decide.

### Details
- `test_valid_config_constructs_service` (line 97) and `test_missing_config_file_falls_back_to_defaults` (line 129) change with seq 02 and seq 09: the fallback expectation becomes a failure expectation.
- Step 3b correction (20261128): both are left unchanged here. The failure expectation for a missing config file already lives in seq 09's companion (`tests/mcp_servers/mdq/test_mdq_config_error_degradation.py`), so restating it here would duplicate the assertion. `test_valid_config_constructs_service` supplies three keys and fails once the defaults are removed, and its mechanism (patching `ConfigLoader`) is replaced when seq 02 consumes the validated startup result. Recorded as a dependency on seq 02, not executed by this row.
- Step 3b correction (20261128): pydantic's `errors()` dict names the key `msg`, not `message` (`message` is the JSON form), so the AC-6 assertion reads `errors()[0]["msg"]`. Recorded 20261128 and applied.
- Step 3b correction (20261128): the dependency on seq 02 landed on 20261128. `test_valid_config_constructs_service` now supplies the startup result through the shared helper instead of patching `ConfigLoader`, and `test_missing_config_file_falls_back_to_defaults` is replaced by `test_missing_key_fails_construction`, which asserts that a result missing one declared key is a construction failure. The service no longer reads a configuration file, so a patched loader read cannot express the requirement.
- Step 3b correction (20261128): the two pinned disagreements are resolved. `test_construction_requires_every_key` and `test_recognized_boolean_tokens_are_rejected_not_coerced` pass now that seq 06 landed (20261128); they were the failing-first expectations recorded at Phase 1. The unchanged rejection assertions remain the behavior lock.

## Compatibility considerations
- N/A: test-only change.

## Security considerations
- The rejection test asserts that no configured value appears in the error text (AC-6).

## Rollback considerations
- N/A: revert the commit; the replaced assertions fail again.

## Validation plan
- `uv run pytest tests/mcp_servers/mdq/test_mdq_config.py`
- Full sequence per `rules/toolchain.md`.

## Completion criteria
- Non-boolean values are rejected.
- Construction requires explicit values for every key.
- Startup errors name field paths only.

## Out of Scope
- The model change (seq 06) and the configuration file content (seq 11).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261128 | 20261128 | `test_all_defaults_construct_successfully` replaced by `TestMdqConfigExplicitValues` (2 tests); `test_recognized_boolean_tokens_coerce` replaced by `test_recognized_boolean_tokens_are_rejected_not_coerced`; rejection tests rebuilt on the `_explicit()` payload helper (see Step 3b correction) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261128-093658 | 20261128-093658 | Targeted run 20261128: 2 failed as designed (implicit defaults, lax bool coercion), 34 passed as the behavior lock. ruff format/check Pass. Validation completes at the end of the release unit, after seq 06 lands end-of-unit gate 20261128 as recorded in seq 01's gates row; the two failing-first assertions pass after seq 06 landed |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Requirement ID**: REQ-007 (strict configuration types, explicit values)
- **Workflow phase**: plan-to-implementation-procedure
- **Source issue**: `issues/done/20261119-142123_mdqmcp001_mdq-server-boundary.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261127-160114_mdqmcp001_mdq-server-boundary.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-213547
- **Related target files**: `tests/mcp_servers/mdq/test_mdq_config.py`