## Goal

Correct `docs/03_rag_03_06_query_pipeline-helpers-and-cache.md`'s mis-categorization of `fetch_full_document()` as a `RagRepository` "Public Method" and expand its correct "Module-level Standalone Wrappers" entry into a full contract description (REQ-001, REQ-002).

## Scope

- Remove `fetch_full_document`'s entry from the "Public Methods" bullet list (line 85) — it is not a `RagRepository` method
- Expand its entry under "Module-level Standalone Wrappers" (line 92) into a full contract description covering parameters (`chunk_id`, `db`, `window`), `window` semantics (`None` = full document, `N` = ±N chunk-index range), return format (ordered by `chunk_index` ascending) and ordering guarantee, and the not-found case (`chunk_id` not found → `[]`)

## Assumptions

- `fetch_full_document()`'s docstring (`repository.py:270-276`) is the authoritative, current contract — confirmed consistent with `tests/rag/test_fetch_order.py`'s existing assertions
- No other documentation file mis-categorizes `fetch_full_document` as a `RagRepository` method (only this one "Public Methods" list was found doing so)
- The two mentions here sit in two deliberately distinct sub-lists within one coherent section (`### 7.1 RagRepository`), not duplicated top-level sections

## Design decisions

1. Remove the mis-categorized "Public Methods" entry rather than also expanding it in place — keeping a mis-categorized entry, even if expanded, would still mislead a reader about how to call the function (`repo.fetch_full_document(...)` would not work; it must be called as `fetch_full_document(...)`, imported directly)
2. Expand the "Module-level Standalone Wrappers" entry in place rather than adding a new sub-section — this list is already the correct location and format for a standalone function's contract, consistent with how its sibling entries (`vector_search`, `fts_search`, `deduplicate_chunks`, `cosine_sim`) are listed there

## Alternatives considered

1. Creating a new, separate document for helper functions — rejected because the Issue's Recommended Action already identifies `docs/03_rag_03_06_query_pipeline-helpers-and-cache.md` as the correct existing destination
2. Also correcting `deduplicate_chunks`/`cosine_sim`'s identical mis-categorization in the same "Public Methods" list — rejected because they are related but separate defects this Issue did not raise; tracked as UNK-01 for a follow-on issue

## Implementation

### Target file

`docs/03_rag_03_06_query_pipeline-helpers-and-cache.md`

### Procedure

1. Confirm the docstring and RagRepository's method list are unchanged
2. Remove `fetch_full_document`'s entry from the "Public Methods" list
3. Expand the "Module-level Standalone Wrappers" entry to document parameters, `window` semantics, ordering guarantee, and not-found behavior

### Method

Phase 1: Preparation — confirm evidence line numbers
- Re-read `repository.py:121-249` (`RagRepository` class) and `repository.py:265-306` (`fetch_full_document()`) to confirm the class's actual method list and the function's current docstring before editing (REQ-001, REQ-002; `docs/03_rag_03_06_query_pipeline-helpers-and-cache.md`)

Phase 2: Core Logic — correct and expand
- Remove `fetch_full_document`'s entry from the "Public Methods" list (REQ-002; `docs/03_rag_03_06_query_pipeline-helpers-and-cache.md`)
- Expand the "Module-level Standalone Wrappers" entry to document parameters, `window` semantics, ordering guarantee, and not-found behavior (REQ-001; `docs/03_rag_03_06_query_pipeline-helpers-and-cache.md`)

### Details

**Phase 1:** Verify via read/grep that:
- `RagRepository` at `repository.py:121-249` defines only two instance methods:
  - `vector_search(self, embedding, top_k)` at line 167
  - `fts_search(self, query, top_k)` at line 191
- `fetch_full_document()` at `repository.py:265-308` is a module-level function (not a class method) with docstring stating:
  - Parameters: `chunk_id: int`, `db: SQLiteHelper`, `window: int | None = None`
  - `window=None`: return all chunks from the same document (full expansion)
  - `window=N`: return chunks within N positions of chunk_id (±N window)
  - Results ordered by `chunk_index` ascending (document reading order)
  - Returns empty list when `chunk_id` is not found (valid not-found result)
- Tests at `tests/rag/test_fetch_order.py:85-131` cover: full document fetch, not-found case, multiple window values, boundary conditions

**Phase 2:** Make the following changes:

1. **Remove line 85** from "Public Methods" section:
   ```markdown
   - `fetch_full_document(chunk_id, db, window=None)` $\rightarrow$ Fetches chunks for the same document in ascending order of `chunk_index`; `window=N` $\rightarrow$ $\pm N$.
   ```

2. **Expand line 92** in "Module-level Standalone Wrappers" section:
   
   Replace:
   ```markdown
   - `fetch_full_document(chunk_id, db, window=None)` $\rightarrow$ Fetches chunks for the same document in ascending order of `chunk_index`; `window=N` $\rightarrow$ $\pm N$
   ```
   
   With:
   ```markdown
   - `fetch_full_document(chunk_id, db, window=None)` $\rightarrow$ Retrieve surrounding chunks for a given chunk_id from the same document. Parameters: `chunk_id` (int, required), `db` (SQLiteHelper, required), `window` (int or None, optional). When `window=None`, returns all chunks from the same document (full expansion); when `window=N`, returns chunks within N positions of chunk_id (±N window range). Results are ordered by `chunk_index` ascending (document reading order). Returns an empty list `[]` when `chunk_id` is not found (valid not-found result, not an error).
   ```

## Compatibility considerations

This is a documentation-only correction/expansion. No backward compatibility concerns.

## Security considerations

No security impact — documentation correction/expansion only.

## Rollback considerations

Simple revert: restore the original "Public Methods" entry and the terse "Module-level Standalone Wrappers" entry. The underlying code remains unchanged.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| docs/03_rag_03_06_query_pipeline-helpers-and-cache.md | Manual — cross-check documented claims against docstring and existing tests | Manual inspection | Every claim traceable to code or an existing test |

## Completion criteria

- [ ] `fetch_full_document`'s "Public Methods" list entry is removed (REQ-002)
- [ ] The "Module-level Standalone Wrappers" entry documents: `chunk_id`, `db`, `window` parameters; `window=None` vs. `window=N` semantics; ascending `chunk_index` ordering; and the `chunk_id`-not-found → `[]` behavior (REQ-001)
- [ ] No other content in the "Public Methods"/"Module-level Standalone Wrappers" lists is altered (REQ-002)

## Out of scope

- Correcting `deduplicate_chunks`/`cosine_sim`'s identical mis-categorization in the same "Public Methods" list (see Unknowns — a related but separate defect this Issue did not raise)
- Creating a new, separate document for helper functions (the Issue's Recommended Action already identifies `docs/03_rag_03_06_query_pipeline-helpers-and-cache.md` as the correct existing destination)
- Modifying `fetch_full_document()`'s implementation

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: Confirm docstring and RagRepository's method list | Completed | — | — | |
| 2 | Phase 2: Remove mis-categorized entry | Completed | — | — | |
| 3 | Phase 2: Expand Module-level entry | Completed | — | — | |
| 4 | Verification: manual review | Completed | — | — | |

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
- **Requirement ID**: REQ-001, REQ-002
- **Source issue**: issues/20260913-183009_missing_fetch_full_document_documentation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260913-204344_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260913-234740
- **Related target files**: docs/03_rag_03_06_query_pipeline-helpers-and-cache.md
