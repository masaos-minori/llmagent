## Goal

Delete the rag-pipeline MCP server's identity view so the server and its response model no
longer produce or declare `corpus_identity` (`REQ-003`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- `_identity_payload()` reads the local identity through a short-lived read-only connection
  and imports `SCHEMA_VERSION` and `compute_local_identity` lazily; deleting the function
  removes those lazy imports too.
- `SCHEMA_VERSION` is also removed from `pipeline.py` (seq 02), so no importer survives.
- `RagDebugResponse` subclasses `RagRunResponse`, so removing the field from the parent
  removes it from both.

## Design decisions
- Delete `_identity_payload()` and its three call sites (`rag_run_pipeline`,
  `rag_debug_pipeline`, `/health`); delete the `corpus_identity` field from
  `RagRunResponse`.
- Do not keep an alias or a stubbed empty field: the responses simply stop carrying the
  key.

## Alternatives considered
N/A: removal is the decided Option B; a present-but-empty field would keep dead wire state.

## Implementation
### Target file
`scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py`
### Procedure
- Delete the `_identity_payload()` function definition.
- Delete `result.corpus_identity = _identity_payload()` from `rag_run_pipeline`.
- Delete `result.corpus_identity = _identity_payload()` from `rag_debug_pipeline`.
- Delete `details["corpus_identity"] = _identity_payload()` from the `/health` handler.
- Do not edit `rag_pipeline_models.py` here: the `corpus_identity` field deletion (lines
  259-262) is owned by the sibling document (seq 05). Run seq 04 and seq 05 in the same
  cycle so the validation `rg` below returns nothing only after both are applied.
### Method
Four deletions in the server; confirm no remaining reference to `_identity_payload` or
`corpus_identity` in the server file.
### Details
- The `/health` handler still builds `details` for `make_health_response`; keep everything
  else in that dict.

## Compatibility considerations
The `corpus_identity` wire field was documented as additive; removing it is intended and
recorded in the ADR. External readers are unknown (`UNK-03`).

## Security considerations
N/A: no security-relevant behavior change.

## Rollback considerations
Revert the commit.

## Validation plan
- `rg -n "corpus_identity|_identity_payload" scripts/mcp_servers` returns nothing (after the
  seq 05 model removal is also applied in the same cycle).
- `uv run pytest tests/mcp_servers/rag_pipeline` passes only after the companion test rows
  are handled in the same cycle: delete `tests/mcp_servers/rag_pipeline/test_rag_pipeline_server_identity.py`
  (seq 24) and strip `corpus_identity` assertions from `test_rag_pipeline_server_endpoints.py`
  (seq 25).

## Completion criteria
No `_identity_payload` or `corpus_identity` remains in the server or model; the endpoint
tests pass without the identity wiring.

## Out of Scope
The pipeline diagnostics identity (`REQ-002`, seq 02) and the deleted identity-view test
(`tests/mcp_servers/rag_pipeline/test_rag_pipeline_server_identity.py`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261113-100607 | 20261113-100819 |  |
| 2 | Add or update tests per Validation plan | Completed | — | 20261113-100819 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261113-100819 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261113-100819 |  |

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
- **Related target files**: `scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py`, `scripts/mcp_servers/rag_pipeline/rag_pipeline_models.py`