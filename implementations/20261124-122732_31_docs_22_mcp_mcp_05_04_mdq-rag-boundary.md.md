## Goal

Name the renamed RAG vector command at the MDQ/RAG boundary (REQ-007: name matches behavior).

## Scope
**Release unit**: R6-rag-vector-contract (Phase 6)

- In scope: the admin-bypass item at `docs/22_mcp/mcp_05_04_mdq-rag-boundary.md:78`.

## Assumptions

- The boundary itself is unchanged: these commands access `rag.sqlite` directly through `RagMaintenanceService` and are not part of normal operation.

## Design decisions

- N/A: single-name change; the boundary statement stays as written.

## Alternatives considered

- N/A: a half-applied rename fails `tools/check_docs_quality.py` with the rule in `config/doc_quality_rules.json` (row 35).

## Implementation
### Target file
`docs/22_mcp/mcp_05_04_mdq-rag-boundary.md`

### Procedure
1. Replace `/session rag-rebuild-vec` at `:78` with the renamed form.
2. Keep `/session rag-consistency` and `/session rag-rebuild-fts` unchanged.

### Method

- N/A: single-line change.

### Details

- N/A.

### Companion test files

- None. This is a documentation row; its validation is the docs checkers.

## Compatibility considerations

- Same release unit as the code rename and the doc-quality rule.

## Security considerations

- N/A: documentation; the trust boundary text itself is in `docs/91_security/security_01_architecture-and-trust-boundaries.md` (row 28).

## Rollback considerations

- N/A: revert the Phase 6 commit.

## Validation plan

| Target | Strategy | Command | Expected outcome |
|---|---|---|---|
| This document | Checkers | `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py docs/22_mcp/mcp_05_04_mdq-rag-boundary.md` | No finding |

## Completion criteria

- The boundary document names only the registered command.

## Out of Scope

- The service implementation, the enforcement text (row 32), the other documents that name the command.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the command name | Pending | — | — | Phase 6 |
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
- **Requirement ID**: REQ-007 (name matching behavior)
- **Source issue**: issues/20261119-145301_cliplc003_maintenance-job-framework.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-001800_cliplc003_maintenance-job-framework.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261124-122732
- **Related target files**: `docs/22_mcp/mcp_05_04_mdq-rag-boundary.md`
