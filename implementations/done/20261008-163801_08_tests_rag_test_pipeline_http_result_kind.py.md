## Goal
Update stubs to `CallRagResult` and add an auth-error fail-closed case. (REQ-003, REQ-004 of the Plan).

## Scope
- Only `tests/rag/test_pipeline_http_result_kind.py`; no other file is modified by this procedure.

## Assumptions
- User decisions (2026-10-08): add a new inbound `auth_token` for the rag-pipeline server and keep `rag_auth_token` as the outbound token; the external RAG service accepts `Authorization: Bearer`.

## Design decisions
- Write the new test first and confirm it fails against the old code.

## Alternatives considered
- Reusing `rag_auth_token` for the inbound check: rejected by the user decision above.

## Implementation
### Target file
tests/rag/test_pipeline_http_result_kind.py

### Procedure
1. Replace each 3-tuple stub return with a `CallRagResult`.
2. Add a test that kind auth_error raises `RagPipelineError` and sets `http_result_kind` to auth_error.

### Method
Write the new test first and confirm it fails against the old code.

### Details
Assert the in-process pipeline is not entered.

## Compatibility considerations
- Test-only change.

## Security considerations
- None.

## Rollback considerations
- Revert the commit.

## Validation plan
- `uv run pytest tests/rag/test_pipeline_http_result_kind.py -q --timeout=60`.

## Completion criteria
- The described change is in place and the validation commands pass (REQ-003, REQ-004).

## Out of scope
- Any file other than `tests/rag/test_pipeline_http_result_kind.py`.

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
- **Requirement ID**: REQ-003, REQ-004
- **Source issue**: issues/20261007-153933_ragauth01_add-rag-http-delegation-authentication-and-fail-closed-responses.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261008-095953_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261008-163801
- **Related target files**: tests/rag/test_pipeline_http_result_kind.py