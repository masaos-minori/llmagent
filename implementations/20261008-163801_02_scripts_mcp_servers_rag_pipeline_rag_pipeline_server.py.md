## Goal
Enforce inbound Bearer auth on the rag-pipeline server. (REQ-001 of the Plan).

## Scope
- Only `scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py`; no other file is modified by this procedure.

## Assumptions
- User decisions (2026-10-08): add a new inbound `auth_token` for the rag-pipeline server and keep `rag_auth_token` as the outbound token; the external RAG service accepts `Authorization: Bearer`.

## Design decisions
- Mirror `scripts/mcp_servers/web_search/web_search_server.py:67`.

## Alternatives considered
- Reusing `rag_auth_token` for the inbound check: rejected by the user decision above.

## Implementation
### Target file
scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py

### Procedure
1. Import `attach_auth_middleware` (and the `_FastAPIApp` cast type as the other servers do).
2. Call `attach_auth_middleware(cast(_FastAPIApp, app), _cfg.auth_token or "")` at module scope right after `app = FastAPI(...)`.

### Method
Mirror `scripts/mcp_servers/web_search/web_search_server.py:67`.

### Details
The token comes from `RagPipelineConfig.auth_token` (not the outbound `rag_auth_token`). An empty token keeps accept-all; the TOML supplies a non-empty value.

## Compatibility considerations
- Deployments must set `MCP_RAG_PIPELINE_AUTH_TOKEN`; the agent already sends it via `config/agent.toml`.

## Security considerations
- Closes MCP-005: endpoints were reachable without a token.

## Rollback considerations
- Revert the commit.

## Validation plan
- `uv run pytest tests/mcp_servers/rag_pipeline -q --timeout=60`; add a test that a missing or wrong Bearer returns 401 and a correct one succeeds (in the existing endpoint test module, if it is already a target; otherwise record a Needs-confirmation work item).

## Completion criteria
- The described change is in place and the validation commands pass (REQ-001).

## Out of scope
- Any file other than `scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py`.

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
- **Related target files**: scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py