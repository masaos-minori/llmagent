## Goal

Apply the strict configuration type primitives to `MdqConfig` and remove the implicit production defaults so an explicit development or test path is the only source of defaults (REQ-007 strict configuration).

## Scope
**Release unit**: boundary-characterization-tests (Plan step 6 cites this row; the unit covers Phases 1, 3, 4, 5, 6)

## Assumptions
- `tests/mcp_servers/mdq/test_mdq_config.py` keeps its own document (seq 23) because it is named by two rows (this row and `scripts/mcp_servers/mdq/mdq_service.py`), so it fails the companion condition (2).
- UNK-04 (non-blocking): no mode flag or new configuration key is introduced; "explicit development or test mode" is satisfied by tests supplying explicit values, per the plan's default.
- The five keys that today come from pydantic defaults are stated explicitly in `config/mdq_mcp_server.toml` by seq 11, so production behavior is unchanged while the default path is removed.

## Design decisions
- `MdqConfig` uses `RULE_BOOL` and `ConfigFieldTypeError` from `scripts/shared/config_field_types.py`, whose error text names the field path and never echoes the configured value.
- Field defaults are removed from the model; a missing key is a validation failure, not a default.

## Alternatives considered
- Keep pydantic defaults and add a mode flag — rejected: no mode concept exists in `scripts/shared/config_loader.py`, and a new key would add a `deploy.sh` line and change the deployed configuration.

## Implementation
### Target file
`scripts/mcp_servers/mdq/mdq_models.py`

### Procedure
- Remove the pydantic field defaults in `MdqConfig` (lines 96-120), including `enable_grep: bool = True` (line 118).
- Replace the plain `bool` annotation with the strict primitive so non-boolean values are rejected.
- Keep `db_path` out of the model, as the current docstring states.

### Method
- The strict primitives raise `ConfigFieldTypeError` naming the field path only; the model does not catch it.
- The numeric constraints (`gt=0`, `ge=0`) stay as they are.

### Details
- `test_recognized_boolean_tokens_coerce` (line 88) asserts the coercion behavior being removed, so it is replaced by a rejection test in seq 23.
- `test_all_defaults_construct_successfully` (line 20) is replaced by an explicit-values construction test.

## Compatibility considerations
- Startup for a deployed configuration that relies on the removed defaults fails; seq 11 adds the keys with the same values before the change is validated.

## Security considerations
- Error text must name field paths only, never values, paths, or secrets (AC-6).

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/mcp_servers/mdq/test_mdq_config.py tests/mcp_servers/mdq/test_mdq_config_error_degradation.py`
- Full sequence per `rules/toolchain.md`.

## Completion criteria
- Non-boolean values are rejected.
- No field of `MdqConfig` has an implicit default.
- Startup errors name field paths only.

## Out of Scope
- The loader that produces the validated result (seq 09) and the configuration file content (seq 11).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | Covered by seq 23, which is not a companion of this row |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | Documentation is a separate row (seq 27) |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Requirement ID**: REQ-007 (strict configuration types, no implicit production defaults)
- **Workflow phase**: plan-to-implementation-procedure
- **Source issue**: `issues/done/20261119-142123_mdqmcp001_mdq-server-boundary.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261127-160114_mdqmcp001_mdq-server-boundary.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-213547
- **Related target files**: `scripts/mcp_servers/mdq/mdq_models.py`
