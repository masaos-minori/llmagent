## Goal

Describe the vector operation in the ADR as orphan-row removal through the renamed method, where the file currently calls it a rebuild (`rebuild_vec`) (REQ-007: name matches behavior).

## Scope
**Release unit**: R6-rag-vector-contract (Phase 6)

- In scope: the startup-classification item at `docs/10_adr/adr_02_06_005_rag-source-derived-index-relationships.md:80`, which names the vector operation as a rebuild through `rebuild_vec`.
- Out of scope: the sanctioned-path statement at `:72` and the repair line at `:156`; both name the FTS command, which is not renamed.

## Assumptions

- The ADR's rule is unchanged: direct INSERT/UPDATE into `chunks_fts` is prohibited outside the schema triggers and the sanctioned maintenance operations. Only the name of the sanctioned operation changes for the vector side.
- The vector path is not a rebuild; the ADR text must describe it as removing orphan `chunks_vec` rows, consistent with `docs/21_rag/rag_05_07-rag-index-consistency-checks.md` (row 29).

## Design decisions

- The ADR names the sanctioned path as the service method, so the text must name `RagMaintenanceService` and the renamed method `prune_orphan_vectors()` (row 22) rather than only the slash command.

## Alternatives considered

- Keeping the old name in the ADR as a historical note — rejected: `tools/check_docs_quality.py` flags the name against the corrected rule (row 35), and the ADR is read as current guidance.

## Implementation
### Target file
`docs/10_adr/adr_02_06_005_rag-source-derived-index-relationships.md`

### Procedure
1. At `:80`, name the operation as removing orphan `chunks_vec` rows through `RagMaintenanceService.prune_orphan_vectors()` (row 22); the FTS items at `:72` and `:156` keep their names.
2. Keep the prohibition on direct writes to `chunks_fts` unchanged.

### Method

- Keep the ADR's numbered-list style; no new rule is added.

### Details

- The rule is enforced by `tools/check_chunks_fts_invariant.py`, which whitelists `scripts/agent/services/rag_maintenance_service.py` by path (`:36-41`); the checker is not changed by the rename, so the ADR's parenthetical reference to it stays valid.
- Line 80 names the operation as `rebuild_vec`; it becomes the renamed method (row 22), which is where the "rebuild vec" wording is corrected to orphan-row removal.

### Companion test files

- None. This is a documentation row; its validation is the docs checkers.

## Compatibility considerations

- Same release unit as the code rename and the doc-quality rule. The checker is unchanged, so the ADR's reference to its sanctioned paths stays valid.

## Security considerations

- N/A: documentation.

## Rollback considerations

- N/A: revert the Phase 6 commit.

## Validation plan

| Target | Strategy | Command | Expected outcome |
|---|---|---|---|
| This document | Checkers | `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py docs/10_adr/adr_02_06_005_rag-source-derived-index-relationships.md` | No finding |
| Same rule | Checker (regression) | `uv run python tools/check_chunks_fts_invariant.py` | No finding; the checker whitelists the service file by path, so the rename does not affect it |

## Completion criteria

- The ADR names the method that is actually sanctioned, and the vector operation is described as orphan removal.

## Out of Scope

- The service implementation, the FTS ADR (row 34), the FTS command name at `:156`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the startup-classification item at `:80` to name the renamed method | Pending | — | — | Phase 6 |
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
- **Related target files**: `docs/10_adr/adr_02_06_005_rag-source-derived-index-relationships.md`
