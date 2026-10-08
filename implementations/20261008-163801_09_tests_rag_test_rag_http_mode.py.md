## Goal
Update stubs to `CallRagResult`. (REQ-002, REQ-004 of the Plan).

## Scope
- Only `tests/rag/test_rag_http_mode.py`; no other file is modified by this procedure.

## Assumptions
- User decisions (2026-10-08): add a new inbound `auth_token` for the rag-pipeline server and keep `rag_auth_token` as the outbound token; the external RAG service accepts `Authorization: Bearer`.

## Design decisions
- Mapping: `("", 200, x)` is empty; `(None, 503, x)` is transient_failure.

## Alternatives considered
- Reusing `rag_auth_token` for the inbound check: rejected by the user decision above.

## Implementation
### Target file
tests/rag/test_rag_http_mode.py

### Procedure
1. Replace each 3-tuple stub return with a `CallRagResult` of the matching kind.

### Method
Mapping: `("", 200, x)` is empty; `(None, 503, x)` is transient_failure.

### Details
Keep assertions otherwise unchanged.

## Compatibility considerations
- Test-only change.

## Security considerations
- None.

## Rollback considerations
- Revert the commit.

## Validation plan
- `uv run pytest tests/rag/test_rag_http_mode.py -q --timeout=60`.

## Completion criteria
- The described change is in place and the validation commands pass (REQ-002, REQ-004).

## Out of scope
- Any file other than `tests/rag/test_rag_http_mode.py`.

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
- **Requirement ID**: REQ-002, REQ-004
- **Source issue**: issues/20261007-153933_ragauth01_add-rag-http-delegation-authentication-and-fail-closed-responses.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261008-095953_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261008-163801
- **Related target files**: tests/rag/test_rag_http_mode.py