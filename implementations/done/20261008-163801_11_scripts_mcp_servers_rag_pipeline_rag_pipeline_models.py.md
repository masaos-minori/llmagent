## Goal
Add the inbound `auth_token` field. (REQ-001 of the Plan).

## Scope
- Only `scripts/mcp_servers/rag_pipeline/rag_pipeline_models.py`; no other file is modified by this procedure.

## Assumptions
- User decisions (2026-10-08): add a new inbound `auth_token` for the rag-pipeline server and keep `rag_auth_token` as the outbound token; the external RAG service accepts `Authorization: Bearer`.

## Design decisions
- Same style as `rag_auth_token`.

## Alternatives considered
- Reusing `rag_auth_token` for the inbound check: rejected by the user decision above.

## Implementation
### Target file
scripts/mcp_servers/rag_pipeline/rag_pipeline_models.py

### Procedure
1. Add `auth_token: str = ""` to `RagPipelineConfig`.
2. Read `auth_token` in `from_dict`.

### Method
Same style as `rag_auth_token`.

### Details
Do not rename or remove `rag_auth_token`.

## Compatibility considerations
- Default empty keeps existing configs loading.

## Security considerations
- The field holds a secret; do not include it in repr or logs if the class already masks `rag_auth_token`.

## Rollback considerations
- Revert the commit.

## Validation plan
- `uv run pytest tests/mcp_servers/rag_pipeline -q --timeout=60`; mypy.

## Completion criteria
- The described change is in place and the validation commands pass (REQ-001).

## Out of scope
- Any file other than `scripts/mcp_servers/rag_pipeline/rag_pipeline_models.py`.

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
- **Related target files**: scripts/mcp_servers/rag_pipeline/rag_pipeline_models.py