## Goal

Move the MDQ handler path from per-key argument extraction to whole-mapping validation through the request model, and make the `get_chunk` audit detail read the truncation state from metadata (`REQ-001` validation parity, `REQ-004` `get_chunk` metadata).

## Scope
**Release unit**: N/A: not part of a release unit

- The 7 dispatch handlers (`_handle_search_docs` 223, `_handle_get_chunk` 240, `_handle_outline` 251, `_handle_index_paths` 262, `_handle_refresh_index` 270, `_handle_stats` 281, `_handle_grep_docs` 287) validate the argument mapping through the model.
- `_build_call_tool_audit_detail()` (341) reads the `get_chunk` truncation state from metadata.
- `_handle_get_chunk` returns text plus metadata, matching the service shape changed by row 04.

## Assumptions

- A validation failure is reported as `MdqValidationError`, which already has an exception handler (`mdq_server.py:139`) and is in the `call_tool` catch set (417-418), so the wire behavior stays HTTP 200 with `is_error=True` and the audit `error_type` remains `MdqValidationError`.
- A `pydantic.ValidationError` must be converted inside the handler, not left to escape: the audit record's `error_type` is `type(exc).__name__` (422), so an unconverted error would change the reported error kind and break the error-taxonomy expectation.
- The audit detail format for `get_chunk` keeps the `truncated=true` part, so `tests/mcp_servers/mdq/test_mdq_exception_handlers.py::TestGetChunkTruncationAuditDetail` still passes with the state sourced from metadata.
- That test file's module docstring says `get_chunk` is "the one tool whose truncation flag is not carried via structured metadata"; the wording becomes inaccurate after this row. The file is not a target row, so no modification is instructed here; the caveat is recorded in the Plan's Assumptions.
- Metadata is passed from handler to audit through `_mdq_metadata_var` (196-206, lifecycle documented in its comment block); this row keeps that mechanism.

## Design decisions

- Validate with `Model.model_validate(args)` and build nothing else, so the same object the schema is generated from is the object that enforces the contract (`REQ-001`).
- Keep display wording in the tool output unchanged; only the source of the audit state moves from text matching to metadata.

## Alternatives considered

- Validate through `scripts/agent/tool_arg_validator.py::validate_tool_arguments()` inside the server: rejected, that path is the Agent side and works on a JSON Schema with jsonschema; the direct path should use the model, and the parity test (row 12) compares the two rather than merging them.

## Implementation
### Target file
`scripts/mcp_servers/mdq/mdq_server.py`

### Procedure
1. Replace the field-by-field model construction in each handler with `model_validate(args)`.
2. Wrap the validation call so a `pydantic.ValidationError` is re-raised as `MdqValidationError` with the field name in the message.
3. `_handle_get_chunk` unpacks the service's text-and-metadata result and sets `_mdq_metadata_var`.
4. In `_build_call_tool_audit_detail()`, read the `get_chunk` truncation state from `r.metadata` instead of `"[Truncated" in r.output`.

### Method

- Handlers keep returning `str` for the wire response; metadata is published through the ContextVar that `_dispatch_mdq_tool()` reads after dispatch (323-335).
- The `get_chunk` branch (360) becomes the same style as the `search_docs` and `grep_docs` branches, which already read `r.metadata`.

### Details

- Read the metadata keys defined by row 01: `truncated`, `truncation_char_count`, `char_count`, `refresh_in_progress`, `index_generation`.
- The detail parts for `get_chunk` keep `truncated=true` only when the metadata says the read was truncated; the non-truncated case emits no truncation part, which is what the existing test asserts.

## Compatibility considerations

- Callers that pass fields the model does not declare now get a validation error instead of a silent drop; this is the deliberate characterization change recorded in the Plan's Risks.
- `tests/mcp_servers/mdq/test_mdq_get_chunk_behavior.py` (row 08) is the test that flips; the exception-handler and error-taxonomy tests are verification dependencies only.

## Security considerations

- Unknown-field rejection closes the divergence between the Agent path and the direct path; no new trust boundary is introduced. Path authorization in the service layer is unchanged.

## Rollback considerations

- N/A: revert the commit; no stored state depends on the handler shape.

## Validation plan

- `uv run pytest tests/mcp_servers/mdq/test_mdq_error_taxonomy.py tests/mcp_servers/mdq/test_mdq_exception_handlers.py`
- `uv run pytest tests/mcp_servers/mdq/test_mdq_validation_parity.py`
- `uv run ruff check scripts/mcp_servers/mdq/mdq_server.py && uv run mypy scripts/mcp_servers/mdq/mdq_server.py`
- Full sequence per `rules/toolchain.md`.

## Completion criteria

- An unknown or removed field is an error on the direct path, the same decision the Agent path makes (`AC-1`).
- The `get_chunk` audit detail is built from metadata, so a change to the display wording cannot change the reported state (`AC-4`, `AC-5`).

## Out of Scope

- The service read paths that fill the metadata (`scripts/mcp_servers/mdq/mdq_service.py`, row 04).
- The metadata shapes themselves (`scripts/mcp_servers/mdq/mdq_models.py`, row 01).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Plan Phase 2 and Phase 4 |
| 2 | Add or update tests per Validation plan | Pending | — | — | Assertions live in rows 08, 12 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | Row 14 states the contract in the mdq doc |

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
- **Requirement ID**: REQ-001 (whole-mapping validation through the model), REQ-004 (`get_chunk` metadata read by the audit detail)
- **Source issue**: `issues/20261119-142130_mdqmcp008_mdq-schema-scope-consistency.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261127-184702_mdqmcp008_mdq-schema-scope-consistency.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261128-084218
- **Related target files**: `scripts/mcp_servers/mdq/mdq_server.py`
