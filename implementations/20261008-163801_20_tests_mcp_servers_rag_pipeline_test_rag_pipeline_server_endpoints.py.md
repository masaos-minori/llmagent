## Goal
Adapt endpoint tests to the new inbound auth and add 401/200 cases. (REQ-001 of the Plan).

## Scope
- Only `tests/mcp_servers/rag_pipeline/test_rag_pipeline_server_endpoints.py`; no other file is modified by this procedure.

## Assumptions
- User decisions (2026-10-08): add a new inbound `auth_token` for the rag-pipeline server and keep `rag_auth_token` as the outbound token; the external RAG service accepts `Authorization: Bearer`.

## Design decisions
- Write the new 401 tests first; they fail before the middleware is attached.

## Alternatives considered
- Reusing `rag_auth_token` for the inbound check: rejected by the user decision above.

## Implementation
### Target file
tests/mcp_servers/rag_pipeline/test_rag_pipeline_server_endpoints.py

### Procedure
1. Build the TestClient with  before any monkeypatch of .
2. Add tests: missing header -> 401, wrong token -> 401, correct token -> success.

### Method
Write the new 401 tests first; they fail before the middleware is attached.

### Details
tests/conftest.py sets MCP_RAG_PIPELINE_AUTH_TOKEN to test-token, so the token is non-empty in tests.

## Compatibility considerations
- Test-only change.

## Security considerations
- Verifies fail-closed behavior for missing and wrong tokens.

## Rollback considerations
- Revert the commit.

## Validation plan
- uv run pytest tests/mcp_servers/rag_pipeline -q --timeout=60.

## Completion criteria
- The described change is in place and the validation commands pass (REQ-001).

## Out of scope
- Any file other than `tests/mcp_servers/rag_pipeline/test_rag_pipeline_server_endpoints.py`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Write or update tests first (Validation plan) | Completed | 20261008-165853 | 20261008-165853 |  |
| 2 | Implement the change in Implementation > Procedure | Completed | 20261008-165853 | 20261008-165853 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261008-165853 | 20261008-165853 |  |

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
- **Requirement ID**: REQ-001
- **Source issue**: issues/20261007-153933_ragauth01_add-rag-http-delegation-authentication-and-fail-closed-responses.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261008-095953_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261008-163801
- **Related target files**: tests/mcp_servers/rag_pipeline/test_rag_pipeline_server_endpoints.py