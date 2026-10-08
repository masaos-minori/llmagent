## Goal
Propagate the auth-error signal from `HttpAugment.run()`. (REQ-003 of the Plan).

## Scope
- Only `scripts/rag/augment.py`; no other file is modified by this procedure.

## Assumptions
- User decisions (2026-10-08): add a new inbound `auth_token` for the rag-pipeline server and keep `rag_auth_token` as the outbound token; the external RAG service accepts `Authorization: Bearer`.

## Design decisions
- Diagnostics are recorded before raising so the caller can still copy them.

## Alternatives considered
- Reusing `rag_auth_token` for the inbound check: rejected by the user decision above.

## Implementation
### Target file
scripts/rag/augment.py

### Procedure
1. After updating `search_diagnostics`, raise `RagPipelineError` when the result kind is auth_error.
2. Keep the other kinds returning `result.result`.

### Method
Diagnostics are recorded before raising so the caller can still copy them.

### Details
`RagPipelineError` is defined in `scripts/rag/exceptions.py`.

## Compatibility considerations
- Only the auth-error path changes.

## Security considerations
- Fail closed instead of widening to local data.

## Rollback considerations
- Revert the commit.

## Validation plan
- `uv run pytest tests/rag/test_augment_refiner.py tests/rag/test_augment_integration.py -q --timeout=60`.

## Completion criteria
- The described change is in place and the validation commands pass (REQ-003).

## Out of scope
- Any file other than `scripts/rag/augment.py`.

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
- **Requirement ID**: REQ-003
- **Source issue**: issues/20261007-153933_ragauth01_add-rag-http-delegation-authentication-and-fail-closed-responses.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261008-095953_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261008-163801
- **Related target files**: scripts/rag/augment.py