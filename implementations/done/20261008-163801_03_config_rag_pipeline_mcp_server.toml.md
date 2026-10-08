## Goal
Declare the inbound `auth_token` for the rag-pipeline server. (REQ-001 of the Plan).

## Scope
- Only `config/rag_pipeline_mcp_server.toml`; no other file is modified by this procedure.

## Assumptions
- User decisions (2026-10-08): add a new inbound `auth_token` for the rag-pipeline server and keep `rag_auth_token` as the outbound token; the external RAG service accepts `Authorization: Bearer`.

## Design decisions
- Same form as the other `config/*_mcp_server.toml` files.

## Alternatives considered
- Reusing `rag_auth_token` for the inbound check: rejected by the user decision above.

## Implementation
### Target file
config/rag_pipeline_mcp_server.toml

### Procedure
1. Add `auth_token = "${ENV:MCP_RAG_PIPELINE_AUTH_TOKEN}"` with a comment that it is the inbound token.
2. Keep `rag_auth_token` untouched (outbound token for the external RAG service).

### Method
Same form as the other `config/*_mcp_server.toml` files.

### Details
User decision 2026-10-08: separate inbound and outbound tokens.

## Compatibility considerations
- The key is new; absent env var must fail loudly per the env-expansion rule.

## Security considerations
- The secret is read from the environment, never stored in the file.

## Rollback considerations
- Revert the commit.

## Validation plan
- Config load test and `tests/mcp_servers/rag_pipeline/test_rag_pipeline_removed_config_keys_rejected.py`.

## Completion criteria
- The described change is in place and the validation commands pass (REQ-001).

## Out of scope
- Any file other than `config/rag_pipeline_mcp_server.toml`.

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
- **Related target files**: config/rag_pipeline_mcp_server.toml