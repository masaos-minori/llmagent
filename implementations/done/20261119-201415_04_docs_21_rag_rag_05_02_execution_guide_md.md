## Goal

State what a non-zero chunk-stage exit means for the following ingester stage in `docs/21_rag/rag_05_02-execution-guide.md` (`REQ-003`, `REQ-007`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The guide shows the three pipeline stages running as separate commands (e.g. `uv run python scripts/rag/ingestion/chunk_splitter.py` for the chunk stage, then `uv run python scripts/rag/ingestion/ingester.py` for the ingester stage; lines ~40 and ~50). Because they are separate manual/scripted commands, a non-zero chunk-stage exit does not itself stop the ingester stage from running.
- `deploy/setup_services.sh` documents the chunk stage as a separate manual command, so a non-zero exit does not break the following stages (Reference Files).
- The guide has standard front matter and `## ` section headings; any added text must conform to the doc-quality gates.
- The non-zero exit is introduced by row 1 (`chunk_splitter.py`): `main()` returns `1` when `run_all().failed > 0` else `0`, propagated via `sys.exit(main())`.

## Design decisions
- Add a concise note near the chunk-stage command (and/or in a warnings/post-ingestion note) stating: a non-zero exit of `chunk_splitter.py` means one or more source files failed (see the `ChunkRunResult` aggregate / exit-status contract in `rag_05_04`); because the stages run as separate commands, the ingester stage still runs on whatever chunks were produced — it does not auto-abort, so an operator should inspect the exit code / log before proceeding.

## Alternatives considered
- A new dedicated subsection vs. a parenthetical note by the command: a short explicit note by the chunk command maximizes discoverability; chosen.

## Implementation
### Target file
`docs/21_rag/rag_05_02-execution-guide.md`

### Procedure
1. Verify the current filename is the canonical one (confirm it is listed in `docs/00_index.md` before editing, per the plan's Documentation Impact caveat).
2. Locate the chunk-stage command block (`uv run python scripts/rag/ingestion/chunk_splitter.py[ --force]`) and add the exit-status note adjacent to it.
3. Cross-link to `rag_05_04-error-handling-reference.md` for the full exit-status contract and failure aggregate.

### Method
- Match the surrounding heading hierarchy and prose style. Keep it concise (one or two sentences / a bullet).
- Preserve front matter; do not remove or reorder existing sections.

### Details
- After editing, run the applicable docs checkers (`rules/toolchain.md`) — front-matter and related-doc heading gates — before considering the row done.

## Compatibility considerations
- Pure documentation addition; no code impact.
- Coordinate with `ragcrv010` (chunking docs) and `ragcrv005` so doc updates describe one consistent design, per the plan.

## Security considerations
N/A: documentation only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- Doc review: the non-zero-chunk-stage-exits meaning for the ingester stage is documented (`REQ-007`).
- Docs checkers (`rules/toolchain.md`) pass: front matter intact, related-doc heading present.

## Completion criteria
- `rag_05_02-execution-guide.md` states what a non-zero chunk-stage exit means for the following ingester stage; docs checkers pass.

## Out of Scope
- Introducing `ChunkRunResult`/`run_all` in code — row 1.
- The error-handling reference doc — row 3.
- Rewriting `adr_02_06_009_rag-fts5-text-separation.md`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261120-002326 | 20261120-002326 |  |
| 2 | Add or update tests per Validation plan | N/A | — | — | N/A: documentation-only procedure, no tests |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261120-002326 | 20261120-002326 | check_docs_quality.py (No issues) |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261120-002326 | 20261120-002326 |  |

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
- **Related target files**: `docs/21_rag/rag_05_02-execution-guide.md`