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

### Details
- `test_valid_config_constructs_service` (line 97) and `test_missing_config_file_falls_back_to_defaults` (line 129) change with seq 02 and seq 09: the fallback expectation becomes a failure expectation.

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
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
