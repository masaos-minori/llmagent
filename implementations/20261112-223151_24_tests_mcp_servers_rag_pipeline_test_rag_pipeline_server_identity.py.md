## Goal

Delete the rag-pipeline MCP server identity-view test module (`REQ-003`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- `tests/mcp_servers/rag_pipeline/test_rag_pipeline_server_identity.py` tests
  `_identity_payload` and imports `SCHEMA_VERSION`; both are removed by seq 04.

## Design decisions
- Delete the test module outright; no replacement.

## Alternatives considered
N/A: removal is the decided Option B; the module tests a removed identity view.

## Implementation
### Target file
`tests/mcp_servers/rag_pipeline/test_rag_pipeline_server_identity.py`
### Procedure
- Delete `tests/mcp_servers/rag_pipeline/test_rag_pipeline_server_identity.py` via
  `git rm`.
### Method
Single file deletion; confirm no remaining reference to `_identity_payload` or
`SCHEMA_VERSION`.
### Details
- The server function and `SCHEMA_VERSION` are removed by seq 04; delete together so no test
  imports a removed symbol.

## Compatibility considerations
N/A: test-only; the identity view is removed by the sibling code document (seq 04).

## Security considerations
N/A: no security-relevant behavior change.

## Rollback considerations
Revert the commit: restore the file from the prior commit.

## Validation plan
- `rg -n "corpus_identity|_identity_payload" scripts/mcp_tests tests` returns nothing.
- `uv run pytest tests/mcp_servers/rag_pipeline` passes.

## Completion criteria
The identity-view test module is gone; no test references the removed symbols.

## Out of Scope
The server identity view (`REQ-003`, seq 04) and the endpoint-test trim (seq 25).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: `REQ-003`
- **Source issue**: issues/20261110-170753_rmcompat003_rag-corpus-identity-decision.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261112-120011_rmcompat003_rag-corpus-identity-decision.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261112-223151
- **Related target files**: `tests/mcp_servers/rag_pipeline/test_rag_pipeline_server_identity.py`
