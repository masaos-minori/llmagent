## Goal

Make `SearchDocsMetadata.query_preview` carry the hashed query identifier instead of the first 80 raw characters of the query, so no raw query text reaches a persisted or returned value (REQ-005, AC-5).

## Scope
**Release unit**: query-boundary-characterization-tests (Plan step 3 cites this row; the unit covers Phases 1, 2, 3, 4)

## Assumptions
- No companion: `tests/mcp_servers/test_mdq_audit.py` is named by this row but is a target row of plan 001 (`implementations/20261127-213547_15_tests_mcp_servers_test_mdq_audit.py.md`), so it cannot also be a companion of this document.
- The field type stays `str`; only the value written by `scripts/mcp_servers/mdq/search.py` (seq 01) changes.
- The request model keeps `path_prefix`, `heading_prefix`, `mode`, and `limit` unchanged, which `tests/mcp_servers/mdq/test_mdq_search_modes.py` (seq 07) pins.
- The hashed identifier and the hashing convention come from plan 001 (`scripts/mcp_servers/audit.py`); this document defines none.
- Execution-order dependency on plan 001: its procedures are still Pending, so the Step 3c gated marker is written on each pending row of this document. `tools/plan_dependency_order.py` reports this plan Ready on 20261127 because plan 001's generation cycle completed; the marker records the substantive dependency, not tool readiness.

## Design decisions
- The model holds the identifier, not the raw text, so a consumer cannot recover the query from metadata.
- The field name stays, so the response shape is unchanged.

## Alternatives considered
- Remove the field — rejected: the plan keeps the metadata field and changes only its content; removal would break the response shape the tests pin.

## Implementation
### Target file
`scripts/mcp_servers/mdq/mdq_models.py`

### Procedure
- Keep `query_preview: str` (line 324) as the field, and document in the model that its value is the hashed identifier.
- Do not change any other field of `SearchDocsMetadata` or `SearchDocsRequest`.

### Method
- The value is produced by the shared hashing helper in `scripts/mcp_servers/audit.py` (plan 001), called from `scripts/mcp_servers/mdq/search.py` (seq 01).

### Details
- The 80-character truncation is removed with the raw value, so no prefix of the query survives.

## Compatibility considerations
- `tests/mcp_servers/test_mdq_audit.py` asserts the absence of raw query text in persisted records; it is run unchanged and is the guard for this change.
- `tests/mcp_servers/mdq/test_mdq_model_usage.py` is run unchanged.

## Security considerations
- No raw query text may appear in the response or in a persisted record (AC-5).

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/mcp_servers/test_mdq_audit.py tests/mcp_servers/mdq/test_mdq_model_usage.py tests/mcp_servers/mdq/test_search.py`
- Full sequence per `rules/toolchain.md`, including `PYTHONPATH=scripts uv run lint-imports`.

## Completion criteria
- `query_preview` carries the hashed identifier.
- No raw query text is reachable from the metadata.

## Out of Scope
- The hashing helper and the audit target (plan 001).
- The query construction (seq 01).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Gated: plans/20261127-160114_mdqmcp001_mdq-server-boundary.md phase all - the closed error-code vocabulary and the single audit-emission boundary this plan's classification and metrics must match are defined there | Depends on plan 001 procedures, which are still Pending |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | Gated: plans/20261127-160114_mdqmcp001_mdq-server-boundary.md phase all - the closed error-code vocabulary and the single audit-emission boundary this plan's classification and metrics must match are defined there | No test change; the existing assertions stay compatible |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | Gated: plans/20261127-160114_mdqmcp001_mdq-server-boundary.md phase all - the closed error-code vocabulary and the single audit-emission boundary this plan's classification and metrics must match are defined there | Documentation is a separate row (seq 11) |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Requirement ID**: REQ-005 (no raw query text in returned or persisted values)
- **Workflow phase**: plan-to-implementation-procedure
- **Source issue**: `issues/done/20261119-142124_mdqmcp002_mdq-search-query-boundary.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261127-161505_mdqmcp002_mdq-search-query-boundary.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-220630
- **Related target files**: `scripts/mcp_servers/mdq/mdq_models.py`
