## Goal
Describe the HTTP delegation failure by cause in the RAG error-handling reference and point to ADR-010 (REQ-006).

## Scope
**Release unit**: N/A: not part of a release unit
Edits the row "Failure when setting `rag_query_service_url`" in `docs/21_rag/rag_05_04-error-handling-reference.md`.

## Assumptions
- Depends on the ADR-010 table (seq 01).

## Design decisions
- Reference the ADR-010 table rather than copying it (single source).

## Alternatives considered
N/A: one-row change

## Implementation
### Target file
`docs/21_rag/rag_05_04-error-handling-reference.md`

### Procedure
1. Replace the single "Fallback to in-process pipeline" outcome with cause-based outcomes: fallback for availability failures, fail closed for 401/403, empty result for parse failure.
2. Add a pointer to the ADR-010 decision table.

### Method
Documentation edit of one table row.

### Details
- Keep the table column structure.

## Compatibility considerations
Documentation only.

## Security considerations
N/A: documentation-only change; no secret, permission, or input-handling behavior changes

## Rollback considerations
N/A: revert the commit

## Validation plan
- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`, `check_docs_japanese.py`: no findings
- `uv run python tools/check_docs_consistency.py --domain rag`: no findings

## Completion criteria
- The row describes outcomes by cause and references ADR-010.

## Out of Scope
- Other rows of the reference.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit the document as described in Implementation > Procedure | Pending | — | — |  |
| 2 | Run the documentation checkers named in the Validation plan | Pending | — | — |  |

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
- **Requirement ID**: `REQ-006` (RAG error reference by cause)
- **Source issue**: issues/20261107-050701_adrrag001_rag-fallback-failure-policy.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261108-091446_adrrag001_rag-fallback-failure-policy.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261108-111044
- **Related target files**: `docs/21_rag/rag_05_04-error-handling-reference.md`
