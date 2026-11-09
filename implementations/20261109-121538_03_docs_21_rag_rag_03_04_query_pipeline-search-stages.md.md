## Goal
Describe the independent retrieval legs and the combined `fts_errors` meaning in the search-stage document (`REQ-007`), replacing the statement that an embedding or DB error returns empty.

## Scope
**Release unit**: N/A: not part of a release unit

- Modifies only `docs/21_rag/rag_03_04_query_pipeline-search-stages.md`, in the SearchStage section (not the MQE paragraph that ragrev007 edits).

## Assumptions
- Execution order: Plan Phase 3, after the code and test procedures; the text must describe the behavior as implemented.
- Overlap judgment (Plan Assumptions): `plans/20261108-165229_ragrev007_mqe-queries-uncapped-duplicated.md` edits the MQE paragraph of the same file; the two edits are in different paragraphs and are compatible.
- `docs/21_rag/rag_04_dto-models-types.md` and `rag_03_03_query_pipeline-context-and-diagnostics.md` stay accurate under the combined-counter choice and are not edited.

## Design decisions
- Describe intent and failure behavior only (independent legs, which counter counts what, when the stage reports fallback); no implementation-location mapping, no function names beyond those already used in the section, and no counts of anything (`skills/DESIGN.md` Docs content policy).
- Write in English only (`tools/check_docs_japanese.py`).

## Alternatives considered
N/A: single-section documentation change.

## Implementation
### Target file
`docs/21_rag/rag_03_04_query_pipeline-search-stages.md`

### Procedure
1. In the SearchStage bullets, replace the statement that each query adds KNN and BM25 results and "returns empty if embedding or DB error occurs" with: the vector leg runs only when an embedding is available and the BM25 leg always runs, so an embedding failure or a vector-search error does not suppress the BM25 hits.
2. Rewrite the "Error handling" note: errors raised by the vector or BM25 retrieval, including packing failures, are caught per leg and are never propagated; `fts_errors` counts failed retrieval legs (vector or BM25), once per failed leg per query; `embed_failed` counts embedding failures; the diagnostics report `degraded` when either counter is positive; the stage status is `fallback` only when no leg returned any hit.
3. Adjust the bullet about the search log so it names retrieval-leg errors (`fts_errors`) rather than "FTS errors".

### Method
- Keep the existing note that a failure in one query does not stop the remaining queries and that embedding failures are swallowed individually and reflected in the diagnostics counters.
- Do not edit the MQE paragraph (ragrev007) or any other section.

### Details
- After editing, confirm the sentence about `fts_errors` still matches the log text `search degraded: %d FTS/vec errors` documented behavior; do not quote the log string in the document.
- Run the documentation checkers named in the Validation plan.

## Compatibility considerations
N/A: documentation only.

## Security considerations
N/A: documentation only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py`, `uv run python tools/check_docs_content_policy.py --strict`, `uv run python tools/check_docs_consistency.py --domain rag`, `uv run python tools/check_docs_japanese.py`.

## Completion criteria
- The SearchStage section states independent legs, the combined `fts_errors` meaning, and that the stage reports `fallback` only when no leg returned hits; the old "returns empty if embedding or DB error occurs" statement is gone.
- All five documentation checkers pass.

## Out of Scope
- The MQE paragraph and other sections, other RAG documents, and any code or test change.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the SearchStage bullets and the error-handling note | Pending | — | — | |
| 2 | Run the documentation checkers named in `routing.md` Tools | Pending | — | — | |

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
- **Requirement ID**: `REQ-007` (search-stage doc describes independent legs and the combined counter)
- **Source issue**: issues/20261108-131007_ragrev004_search-bm25-coupling.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261108-164823_ragrev004_search-bm25-coupling.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261109-121538
- **Related target files**: `docs/21_rag/rag_03_04_query_pipeline-search-stages.md`
