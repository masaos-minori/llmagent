## Goal

Make the recovery document's repair guidance name the job commands and the renamed RAG vector command (REQ-007: name matches behavior; REQ-009: guidance names registered commands; REQ-010: documentation reflects the implementation).

## Scope
**Release unit**: R6-rag-vector-contract (Phase 6); the job-command guidance is R7-docs-generated (Phase 7)

- In scope: the repair sentence at `docs/41_db/db_07_api_and_operations-recovery-and-reference.md:74`.

## Assumptions

- The document's statement that the logical-verification stage only recommends repair and never performs it stays true; the change is the name it recommends.

## Design decisions

- N/A: the change is descriptive.

## Alternatives considered

- N/A: a half-applied rename fails `tools/check_docs_quality.py` with the rule in `config/doc_quality_rules.json` (row 35).

## Implementation
### Target file
`docs/41_db/db_07_api_and_operations-recovery-and-reference.md`

### Procedure
1. Replace `/session rag-rebuild-vec` in the sentence at `:74` with the renamed form and describe it as removing orphan `chunks_vec` rows.
2. Add the job-command reference (`/jobs status <id>`) to the same guidance, since the operator needs the job record to see whether a run was verified.
3. Keep `/session rag-rebuild-fts` unchanged.

### Method

- N/A: single-sentence change.

### Details

- N/A.

### Companion test files

- None. This is a documentation row; its validation is the docs checkers.

## Compatibility considerations

- Part of the same release unit as `scripts/db/rag_consistency.py` (row 20) and `config/doc_quality_rules.json` (row 35); the checkers run over both.

## Security considerations

- N/A: documentation.

## Rollback considerations

- N/A: revert the Phase 6 commit.

## Validation plan

| Target | Strategy | Command | Expected outcome |
|---|---|---|---|
| This document | Checkers | `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py docs/41_db/db_07_api_and_operations-recovery-and-reference.md` | No finding |

## Completion criteria

- The recovery document names only registered commands, and the vector guidance names the prune operation.

## Out of Scope

- The code that produces the guidance, the other documents that name the command.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the repair guidance sentence | Pending | — | — | Phase 6, Phase 7 |
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
- **Requirement ID**: REQ-007 (name matching behavior), REQ-009 (guidance names registered commands), REQ-010 (documentation reflects the implementation)
- **Source issue**: issues/20261119-145301_cliplc003_maintenance-job-framework.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-001800_cliplc003_maintenance-job-framework.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261124-122732
- **Related target files**: `docs/41_db/db_07_api_and_operations-recovery-and-reference.md`
