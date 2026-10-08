## Goal
Make `call_rag_service()` send `Authorization: Bearer` and return a tagged result. (REQ-002, REQ-004, REQ-005 of the Plan).

## Scope
- Only `scripts/rag/pipeline_service.py`; no other file is modified by this procedure.

## Assumptions
- User decisions (2026-10-08): add a new inbound `auth_token` for the rag-pipeline server and keep `rag_auth_token` as the outbound token; the external RAG service accepts `Authorization: Bearer`.

## Design decisions
- Keep the retry loop and backoff; only the return values change.

## Alternatives considered
- Reusing `rag_auth_token` for the inbound check: rejected by the user decision above.

## Implementation
### Target file
scripts/rag/pipeline_service.py

### Procedure
1. Add `@dataclass(frozen=True) class CallRagResult` with `kind` (success, empty, auth_error, transient_failure), `result`, `status_code`, `latency_ms`.
2. Replace the `X-RAG-Token` header with `Authorization: Bearer <token>` only when the token is non-empty.
3. Return `auth_error` on 401/403 with no retry; `transient_failure` after retries are exhausted, on other <500 statuses, and when the body has `is_error` true.
4. Move the literal `10.0` to `_REQUEST_TIMEOUT_SECONDS`.
5. Update the docstring (return contract, header).

### Method
Keep the retry loop and backoff; only the return values change.

### Details
Callers that unpack a 3-tuple break; all callers are in the Plan's target files.

## Compatibility considerations
- Return type changes (internal API; confirmed no external callers).

## Security considerations
- The token is sent only in the Authorization header and is never logged.

## Rollback considerations
- Revert the commit.

## Validation plan
- `uv run pytest tests/rag/test_rag_pipeline_service.py -q --timeout=60`; ruff; mypy; bandit.

## Completion criteria
- The described change is in place and the validation commands pass (REQ-002, REQ-004, REQ-005).

## Out of scope
- Any file other than `scripts/rag/pipeline_service.py`.

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
- **Requirement ID**: REQ-002, REQ-004, REQ-005
- **Source issue**: issues/20261007-153933_ragauth01_add-rag-http-delegation-authentication-and-fail-closed-responses.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261008-095953_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261008-163801
- **Related target files**: scripts/rag/pipeline_service.py