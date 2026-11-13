## Goal

Remove the identity-wiring test class from the rag-pipeline server endpoint tests so the
suite no longer exercises the deleted `_identity_payload()` (`REQ-003`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- A test class patches `_identity_payload` and asserts the `corpus_identity` key on the
  response (~lines 209-227); both symbols are removed by seq 04.

## Design decisions
- Delete the identity-wiring test class; keep every other endpoint test unchanged.

## Alternatives considered
N/A: removal is the decided Option B; the class tests a removed view.

## Implementation
### Target file
`tests/mcp_servers/rag_pipeline/test_rag_pipeline_server_endpoints.py`
### Procedure
- Delete the whole `TestCorpusIdentityExposure` class (class definition at ~line 225, last
  assertion at ~line 301; re-read exact bounds before editing) that patches
  `_identity_payload` and asserts the `corpus_identity` key.
### Method
Class deletion; confirm no remaining reference to `_identity_payload` or `corpus_identity`.
### Details
- The server function and wire field are removed by seq 04; delete together so the module
  imports cleanly.

## Compatibility considerations
N/A: test-only; the identity view is removed by the sibling code document (seq 04).

## Security considerations
N/A: no security-relevant behavior change.

## Rollback considerations
Revert the commit.

## Validation plan
- `rg -n "corpus_identity|_identity_payload" scripts/mcp_servers tests/mcp_servers` returns
  nothing in the same cycle as seq 04, 05, and 24. Broader `corpus_identity` matches outside
  `mcp_servers` (`scripts/rag/corpus_identity.py`, its tests, the gate test) are removed by
  the release unit in phases 5-6 and are not this cycle's scope.
- `uv run pytest tests/mcp_servers/rag_pipeline` passes.

## Completion criteria
The identity-wiring class is gone; the endpoint tests pass without it.

## Out of Scope
The server identity view (`REQ-003`, seq 04) and the deleted identity-view test (seq 24).

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
- **Related target files**: `tests/mcp_servers/rag_pipeline/test_rag_pipeline_server_endpoints.py`