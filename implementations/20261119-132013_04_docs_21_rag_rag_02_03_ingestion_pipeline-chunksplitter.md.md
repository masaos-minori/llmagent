## Goal

State exactly what an English chunk's stored `content` and `normalized_content` contain,
and the `min_chunk` discard measurement basis, so the doc matches the restored invariant
(`REQ-005`, `REQ-007`).

## Scope
**Release unit**: english-content-stopword-loss

## Assumptions

- The sibling `chunk_english.py` procedure restores the unfiltered original as English
  `content`; the sibling `chunk_splitter.py` procedure confirms English
  `normalized_content` is `NULL` (Shape B). This doc records both.

## Design decisions

- `N/A: documentation-only; no design decision is made here. The doc records the locked
  Shape B behavior and the preserved `min_chunk` basis.`

## Alternatives considered

- `N/A: none. The doc states the current (post-fix) behavior; it does not change it.`

## Implementation
### Target file
`docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md`

### Procedure
Update the English-language paragraph(s) that describe stopword handling so they state:

1. **`content`**: the **original** crawled English text region — every word retained,
   including stopwords. English `content` is NOT the stopword-stripped projection.
2. **`normalized_content`**: `NULL` for English (Shape B, filtering dropped); English
   behaves like code/markdown under ADR-009 INV-04. FTS5 indexes the original `content`
   via `COALESCE(normalized_content, content)`.
3. **`min_chunk` basis**: a chunk is discarded when its length is below `min_chunk`,
   measured on the **post-filter (stopword-stripped) string** — the same basis the code
   uses. This basis is preserved even though the stored `content` is now unfiltered.

Remove or correct any sentence that implies the stored English `content` is the
stopword-stripped text.

### Method

Locate the English paragraph near the doc's English/Japanese comparison (currently the
passages discussing `en_stopwords` as the discard threshold and the English
`content`/`normalized_content` summary) and rewrite those sentences to the three points
above. Keep the Japanese paragraph and all other sections unchanged. Do not alter the
configuration-reference cross-link.

### Details

- Docs-only change. No code, symbols, or imports are affected.
- `docs/21_rag/rag_05_01-configuration-reference.md` is out of scope here (the Plan lists
  it as a separate consideration, not a modification target).

## Compatibility considerations

- `N/A: documentation-only; no runtime or API impact. The doc records the post-fix
  behavior.`

## Security considerations

`N/A: documentation-only.`

## Rollback considerations

Revert the commit that edits the doc.

## Validation plan

- Read-back: confirm the English paragraph states `content` is the original text,
  `normalized_content` is `NULL`, and the `min_chunk` basis is the post-filter length.
- `tools/check_workitem_structure.py` / doc linter per `routing.md` Tools "When to run
  which tool".

## Completion criteria

- The doc explicitly states English `content` retains every word, English
  `normalized_content` is `NULL`, and the `min_chunk` discard is measured on the
  post-filter length.
- No implication remains that stored English `content` is stopword-stripped.

## Out of Scope

- `docs/21_rag/rag_05_01-configuration-reference.md` (`en_stopwords` effects) — a
  separate Plan consideration, not a modification target here.
- Production code (`chunk_english.py`, `chunk_splitter.py`) — covered by sibling
  procedures.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the doc per Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Run the documentation checkers (`rules/toolchain.md`, `routing.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-005` (`min_chunk` basis documented), `REQ-007` (doc states
  English `content`/`normalized_content`)
- **Source issue**: `issues/20261119-112014_ragcrv002_english-content-stopword-loss.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261119-123746_ragcrv002_english-content-stopword-loss.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261119-132013
- **Related target files**: `docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md`
