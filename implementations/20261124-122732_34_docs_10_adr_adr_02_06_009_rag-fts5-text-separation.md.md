## Goal

Describe the FTS rebuild as the implementation now performs it: a run recorded as a job whose result is verified after the insert (REQ-004: success only after the postcondition).

## Scope
**Release unit**: R6-rag-vector-contract (Phase 6)

- In scope: the FTS rebuild description at `docs/10_adr/adr_02_06_009_rag-fts5-text-separation.md:148`.

## Assumptions

- What the rebuild regenerates is unchanged: it rebuilds `chunks_fts` from the stored `content` and `normalized_content` and does not recompute normalization. This row does not change that statement.
- The FTS command name stays `/session rag-rebuild-fts`; the rename applies only to the vector operation.

## Design decisions

- The ADR gains one sentence about the postcondition, because the requirement makes the verified result part of what the operation is; the rest of the text is left as it is.

## Alternatives considered

- Leaving the ADR unchanged — rejected: the plan lists this file as a target because the requirement changes the outcome contract the ADR describes; an ADR that omits it would contradict the chapter documents.

## Implementation
### Target file
`docs/10_adr/adr_02_06_009_rag-fts5-text-separation.md`

### Procedure
1. At `:148`, name the operation through the service method that performs it (`RagMaintenanceService.rebuild_fts()`, row 22) and state that the run is recorded as a job and reports success only after the FTS row count is re-measured against `chunks`.
2. The file names no vector operation, so nothing changes for the rename; the FTS command name at `:148` stays `/session rag-rebuild-fts`.

### Method

- Keep the ADR style: one statement of the mechanism, no implementation detail.

### Details

- N/A: no other section of the file changes.

### Companion test files

- None. This is a documentation row; its validation is the docs checkers.

## Compatibility considerations

- The postcondition itself is implemented in row 22 (Phase 4, R4) and asserted by `tests/rag/test_fts_sync.py` (row 52); this row is cited by the plan's Phase 6 checklist, so its wording must be written after the Phase 4 change lands and must not describe behavior that is not yet implemented.

## Security considerations

- N/A: documentation.

## Rollback considerations

- N/A: revert the Phase 6 commit.

## Validation plan

| Target | Strategy | Command | Expected outcome |
|---|---|---|---|
| This document | Checkers | `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py docs/10_adr/adr_02_06_009_rag-fts5-text-separation.md` | No finding |

## Completion criteria

- The ADR describes the FTS rebuild as a recorded, verified run and names only registered commands.

## Out of Scope

- The service implementation, the ADR for the derived-index relationships (row 33).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the FTS rebuild description at `:148` to state the recorded run and the verified result | Pending | — | — | Phase 6 (text follows the Phase 4 change) |
| 2 | Run the documentation checkers (`rules/tool-gates.md`) | Pending | — | — | |

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
- **Requirement ID**: REQ-004 (verified result before the success line)
- **Source issue**: issues/20261119-145301_cliplc003_maintenance-job-framework.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-001800_cliplc003_maintenance-job-framework.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261124-122732
- **Related target files**: `docs/10_adr/adr_02_06_009_rag-fts5-text-separation.md`
