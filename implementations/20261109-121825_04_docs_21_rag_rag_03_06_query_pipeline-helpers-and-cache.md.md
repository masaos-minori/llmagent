## Goal
Describe the OR matching rule and the tokenization boundary, and correct the two doc/code mismatches in the "Japanese FTS5 Tokenization" paragraph (`REQ-006`).

## Scope
**Release unit**: N/A: not part of a release unit

- Modifies only `docs/21_rag/rag_03_06_query_pipeline-helpers-and-cache.md`, in the paragraph that follows the `RagRepository` description. `docs/21_rag/rag_03_04_query_pipeline-search-stages.md` is edited by the ragrev004 Plan, not here.

## Assumptions
- Execution order: Plan Phase 3, after the code and test procedures; the text must describe the behavior as implemented.
- No overlap with another Plan on this file was reported by `tools/check_plan_target_overlaps.py`.

## Design decisions
- Describe intent and failure behavior only (matching rule, tokenization boundary, what an empty query does, what truncation does); no regex literal and no implementation-location mapping (`skills/DESIGN.md` Docs content policy). Name `_MAX_FTS_TOKENS` only as the paragraph already does.
- Write in English only (`tools/check_docs_japanese.py`).

## Alternatives considered
N/A: single-paragraph documentation change.

## Implementation
### Target file
`docs/21_rag/rag_03_06_query_pipeline-helpers-and-cache.md`

### Procedure
1. Rewrite the sentence on English queries: non-Japanese text is tokenized into runs of letters and digits of any script (accented Latin, Cyrillic, and Hangul included); an underscore or punctuation separates tokens, matching how the index tokenizer splits text.
2. Add the matching rule: every token is double-quoted and the tokens are combined with OR, so a chunk matching a subset of the terms is returned and ranked by BM25 (more and rarer matched terms rank higher); operator words in the user text are literals.
3. Correct truncation: tokens beyond the limit are dropped and the construction is logged at info level (original and used token counts, with a truncated flag) on every call.
4. Correct the empty case: when no valid token remains, the builder returns an empty string and the search returns no hits without running a query (replace the `'""'` statement).
5. Keep the sentence that the limit is a heuristic without recorded rationale.

### Method
- Keep the Japanese token description (Sudachi part-of-speech categories) as it is; the matching rule applies to both branches.
- Do not edit the `RagRepository` paragraph above it or the "Sudachi Lazy Loading" paragraph below it.

### Details
- After editing, check that no statement implies all terms must match, and that the word "silently" no longer describes truncation.
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
- The paragraph states the OR rule, the Unicode tokenization boundary, the real empty-query behavior, and logged truncation; the `'""'` and "silently truncated" statements are gone.
- All five documentation checkers pass.

## Out of Scope
- Other RAG documents (including the search-stage document owned by ragrev004), any code or test change.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the "Japanese FTS5 Tokenization" paragraph | Pending | — | — | |
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
- **Requirement ID**: `REQ-006` (docs state the matching rule, tokenization boundary, and the two corrections)
- **Source issue**: issues/20261108-131008_ragrev005_fts-query-and-semantics.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261108-164946_ragrev005_fts-query-and-semantics.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261109-121825
- **Related target files**: `docs/21_rag/rag_03_06_query_pipeline-helpers-and-cache.md`
