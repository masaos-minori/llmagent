## Goal
Do not fall back after an auth error and drop the `assert`. (REQ-003 of the Plan).

## Scope
- Only `scripts/rag/pipeline.py`; no other file is modified by this procedure.

## Assumptions
- User decisions (2026-10-08): add a new inbound `auth_token` for the rag-pipeline server and keep `rag_auth_token` as the outbound token; the external RAG service accepts `Authorization: Bearer`.

## Design decisions
- The exception propagates to the MCP service layer.

## Alternatives considered
- Reusing `rag_auth_token` for the inbound check: rejected by the user decision above.

## Implementation
### Target file
scripts/rag/pipeline.py

### Procedure
1. Wrap the HTTP stage in try/finally so diagnostics and stage results are copied even when `RagPipelineError` is raised.
2. Remove the `assert result is None or result == ""` after the HTTP stage.
3. Update the docstring fallback chain.

### Method
The exception propagates to the MCP service layer.

### Details
Behavior for success, empty, and transient failure is unchanged.

## Compatibility considerations
- Callers of `augment()` can now see `RagPipelineError` on 401/403.

## Security considerations
- RAG-001: no local fallback on 401/403.

## Rollback considerations
- Revert the commit.

## Validation plan
- `uv run pytest tests/rag -q --timeout=60`.

## Completion criteria
- The described change is in place and the validation commands pass (REQ-003).

## Out of scope
- Any file other than `scripts/rag/pipeline.py`.

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
- **Related target files**: scripts/rag/pipeline.py