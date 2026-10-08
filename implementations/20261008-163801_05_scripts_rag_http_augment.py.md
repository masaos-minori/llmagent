## Goal
Classify the new result type and surface auth errors. (REQ-003, REQ-004 of the Plan).

## Scope
- Only `scripts/rag/http_augment.py`; no other file is modified by this procedure.

## Assumptions
- User decisions (2026-10-08): add a new inbound `auth_token` for the rag-pipeline server and keep `rag_auth_token` as the outbound token; the external RAG service accepts `Authorization: Bearer`.

## Design decisions
- Extend `HttpAugmentResult` to carry the kind if needed.

## Alternatives considered
- Reusing `rag_auth_token` for the inbound check: rejected by the user decision above.

## Implementation
### Target file
scripts/rag/http_augment.py

### Procedure
1. Replace the 3-tuple unpack with `CallRagResult` handling.
2. Map kind to `HttpResultKind` (including `auth_error`).
3. Replace the `assert` with an explicit `TypeError`.
4. Keep the warning log for 401/403.

### Method
Extend `HttpAugmentResult` to carry the kind if needed.

### Details
`python -O` must not change behavior.

## Compatibility considerations
- `HttpAugmentResult` fields remain compatible.

## Security considerations
- Auth failures are no longer converted to an in-process fallback result.

## Rollback considerations
- Revert the commit.

## Validation plan
- `uv run pytest tests/rag -q --timeout=60 -k http`.

## Completion criteria
- The described change is in place and the validation commands pass (REQ-003, REQ-004).

## Out of scope
- Any file other than `scripts/rag/http_augment.py`.

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
- **Related target files**: scripts/rag/http_augment.py