## Goal

Document the exit-status contract and the `ChunkRunResult` failure aggregate in `docs/21_rag/rag_05_04-error-handling-reference.md` alongside the existing continue-to-next-file policy (`REQ-003`, `REQ-006`, `REQ-007`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The file currently documents the continue-to-next-file policy in the `## ChunkSplitter` table (lines ~36–39): Sudachi tokenization error → abort the file, `ERROR` with traceback, continue to next file; file-level failure → continue; existing chunks → skip unless `--force`; size-rule discard → not an error. This is the source of truth for the continue policy (the plan's note confirms `rag_05_04` governs it, not `adr_02_06_009_rag-fts5-text-separation.md` INV-05, which actually governs content preservation).
- The file has standard front matter (`title`/`area`/`tags`/`related:`) and `## ` section headings; any added section must conform to the doc-quality gates (front matter intact, related-doc heading present).
- The `ChunkRunResult` aggregate (`processed`/`skipped`/`failed` counts + per-file reasons) and the `main()` non-zero-on-failure exit are introduced by row 1 (`chunk_splitter.py`).
- Do NOT reword `adr_02_06_009_rag-fts5-text-separation.md` INV-05 (ADR-preservation rule); the continue-policy citation stays with `rag_05_04`.

## Design decisions
- Add a short `## Chunk-Stage Exit Status` (or `## Exit Status`) section stating: the chunk stage returns a non-zero process exit code when one or more source files fail, and `0` when only legitimate skips occurred; `run_all` exposes the `processed`/`skipped`/`failed` aggregate; each failure maps to an `IngestionFailureReason` (`STORAGE_FAILED` for write/publish `OSError`, `PARSE_FAILED` for `ChunkFormatError`, `VALIDATION_FAILED` for `PipelineValidationError`, `UNEXPECTED_FAILURE` for `TokenizationError` and others).
- Cross-link the new section to the existing continue-to-next-file table so readers see both the per-file policy and the run-level exit contract together.

## Alternatives considered
- Adding a new top-level section vs. extending the existing `## ChunkSplitter` table: a dedicated section keeps the exit-status contract scannable and avoids overloading the error table; chosen.

## Implementation
### Target file
`docs/21_rag/rag_05_04-error-handling-reference.md`

### Procedure
1. Verify the current filename is the canonical one (confirm it is listed in `docs/00_index.md` before editing, per the plan's Documentation Impact caveat).
2. After the `## ChunkSplitter` table (or in an appropriate position under the ingestion section), add the `## Chunk-Stage Exit Status` section describing the non-zero-on-failure exit contract and the `ChunkRunResult` aggregate with the exception-class → reason mapping.
3. Reference the existing continue-to-next-file policy in the new section so the two read as one contract.

### Method
- Match the surrounding heading hierarchy (`## ` level) and prose style. Keep it concise (a few bullets).
- Preserve front matter; do not remove or reorder existing sections.

### Details
- After editing, run the applicable docs checkers (`rules/toolchain.md`) — front-matter and related-doc heading gates — before considering the row done.
- Do not touch `adr_02_06_009_rag-fts5-text-separation.md`.

## Compatibility considerations
- Pure documentation addition; no code impact.
- Coordinate with `ragcrv010` (chunking docs) and `ragcrv005` so doc updates describe one consistent design, per the plan.

## Security considerations
N/A: documentation only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- Doc review: the exit-status contract and failure aggregate are present and cross-linked to the continue policy (`REQ-007`).
- Docs checkers (`rules/toolchain.md`) pass: front matter intact, related-doc heading present.

## Completion criteria
- `rag_05_04-error-handling-reference.md` documents the non-zero-on-failure exit contract and the `ChunkRunResult` aggregate alongside the continue-to-next-file policy; docs checkers pass.

## Out of Scope
- Introducing `ChunkRunResult`/`run_all` in code — row 1.
- The execution-guide doc — row 4.
- Rewriting `adr_02_06_009_rag-fts5-text-separation.md` INV-05.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261120-002119 | 20261120-002119 |  |
| 2 | Add or update tests per Validation plan | N/A | — | — | N/A: documentation-only procedure, no tests |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261120-002119 | 20261120-002119 | check_docs_quality.py (No issues); rag_05_04 canonical (referenced by 6+ docs; not in 00_index - pre-existing, out of scope) |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261120-002119 | 20261120-002119 |  |

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
- **Requirement ID**: `REQ-003` (exit-status contract), `REQ-007` (documentation)
- **Source issue**: `issues/20261119-112019_ragcrv007_chunk-failure-exit-reporting.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261119-191233_ragcrv007_chunk-failure-exit-reporting.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261119-201415
- **Related target files**: `docs/21_rag/rag_05_04-error-handling-reference.md`