## Goal
Update unpacking and add Bearer, is_error, and 401/403 assertions. (REQ-002, REQ-005 of the Plan).

## Scope
- Only `tests/rag/test_rag_pipeline_service.py`; no other file is modified by this procedure.

## Assumptions
- User decisions (2026-10-08): add a new inbound `auth_token` for the rag-pipeline server and keep `rag_auth_token` as the outbound token; the external RAG service accepts `Authorization: Bearer`.

## Design decisions
- Write the new tests first.

## Alternatives considered
- Reusing `rag_auth_token` for the inbound check: rejected by the user decision above.

## Implementation
### Target file
tests/rag/test_rag_pipeline_service.py

### Procedure
1. Replace `result, status, _ = await call_rag_service(...)` with attribute access on `CallRagResult`.
2. Assert `Authorization: Bearer <token>` and no `X-RAG-Token` header.
3. Add tests for `is_error` true and for 401/403 without retry.

### Method
Write the new tests first.

### Details
Use the existing httpx mock transport.

## Compatibility considerations
- Test-only change.

## Security considerations
- Verifies the token is not sent when empty.

## Rollback considerations
- Revert the commit.

## Validation plan
- `uv run pytest tests/rag/test_rag_pipeline_service.py -q --timeout=60`.

## Completion criteria
- The described change is in place and the validation commands pass (REQ-002, REQ-005).

## Out of scope
- Any file other than `tests/rag/test_rag_pipeline_service.py`.

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
- **Requirement ID**: REQ-002, REQ-005
- **Source issue**: issues/20261007-153933_ragauth01_add-rag-http-delegation-authentication-and-fail-closed-responses.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261008-095953_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261008-163801
- **Related target files**: tests/rag/test_rag_pipeline_service.py