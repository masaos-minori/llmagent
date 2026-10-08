## Goal
Compare the Bearer token in `_is_authorized()` in constant time. (REQ-001 of the Plan).

## Scope
- Only `scripts/mcp_servers/server.py`; no other file is modified by this procedure.

## Assumptions
- User decisions (2026-10-08): add a new inbound `auth_token` for the rag-pipeline server and keep `rag_auth_token` as the outbound token; the external RAG service accepts `Authorization: Bearer`.

## Design decisions
- Single expression change in `_is_authorized()`.

## Alternatives considered
- Reusing `rag_auth_token` for the inbound check: rejected by the user decision above.

## Implementation
### Target file
scripts/mcp_servers/server.py

### Procedure
1. Import `hmac` if absent.
2. Replace the `==` comparison with `hmac.compare_digest` on encoded bytes.
3. Keep the empty-token accept-all behavior unchanged.

### Method
Single expression change in `_is_authorized()`.

### Details
Both operands are encoded with UTF-8 before comparison so non-ASCII input does not raise TypeError.

## Compatibility considerations
- Behavior is identical for valid and invalid tokens.

## Security considerations
- Removes a timing side channel on the token compare.

## Rollback considerations
- Revert the commit.

## Validation plan
- `uv run pytest tests/mcp_servers -q --timeout=60`; ruff; mypy; bandit.

## Completion criteria
- The described change is in place and the validation commands pass (REQ-001).

## Out of scope
- Any file other than `scripts/mcp_servers/server.py`.

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
- **Related target files**: scripts/mcp_servers/server.py