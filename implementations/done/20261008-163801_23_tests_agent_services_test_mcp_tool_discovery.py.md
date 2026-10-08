## Goal
Keep the parametrized /v1/tools tests passing under rag-pipeline inbound auth. (REQ-001 of the Plan).

## Scope
- Only `tests/agent/services/test_mcp_tool_discovery.py`; no other file is modified by this procedure.

## Assumptions
- User decisions (2026-10-08): add a new inbound `auth_token` for the rag-pipeline server and keep `rag_auth_token` as the outbound token; the external RAG service accepts `Authorization: Bearer`.

## Design decisions
- Other servers keep an empty test token, so they receive no header.

## Alternatives considered
- Reusing `rag_auth_token` for the inbound check: rejected by the user decision above.

## Implementation
### Target file
tests/agent/services/test_mcp_tool_discovery.py

### Procedure
1. Add a helper that returns the Authorization: Bearer header from the module's _cfg.auth_token when it is non-empty.
2. Pass that header to both TestClient constructions.

### Method
Other servers keep an empty test token, so they receive no header.

### Details
Only the header is added; assertions are unchanged.

## Compatibility considerations
- Test-only change.

## Security considerations
- None.

## Rollback considerations
- Revert the commit.

## Validation plan
- uv run pytest tests/agent/services/test_mcp_tool_discovery.py -q --timeout=60.

## Completion criteria
- The described change is in place and the validation commands pass (REQ-001).

## Out of scope
- Any file other than `tests/agent/services/test_mcp_tool_discovery.py`.

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
- **Related target files**: tests/agent/services/test_mcp_tool_discovery.py