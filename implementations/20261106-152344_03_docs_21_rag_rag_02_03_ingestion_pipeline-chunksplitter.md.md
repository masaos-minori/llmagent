## Goal

Update `docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md` to describe the
language-aware Markdown chunking behavior introduced by `raging007` (`REQ-005`,
`AC-4`): the "Japanese content" paragraph no longer documents a Sudachi bypass, and
the oversized-section fallback names the language-appropriate chunker.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The behavior change is implemented by the companion `chunk_splitter.py` procedure
  document before this doc is updated.
- No other doc references the old bypass paragraph (source Plan Step 3 scan).

## Design decisions
- Edit only the two locations the Plan identifies: the oversized-section fallback
  sentence and the "Japanese content" paragraph. Leave the rest of the section
  untouched to avoid unrelated rewrites.

## Alternatives considered
- Rewriting the entire 3.1.4 section or the content-type table: rejected — out of
  scope for `REQ-005`; only the bypass description and fallback wording change.

## Implementation
### Target file
- `docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md`

### Procedure
1. Rewrite the oversized-section fallback sentence in section 3.1.4 to name the
   language-appropriate chunker (ja -> `_chunk_japanese`, non-ja -> `_chunk_english`).
2. Replace the "Japanese content" paragraph so it states that Japanese Markdown
   sections follow Japanese chunking semantics with non-empty `normalized_content`,
   and remove the statement that ja Markdown bypasses Sudachi normalization.

### Method
- In section **3.1.4 Markdown Heading Chunking Behavior**, change the "Oversized"
  bullet so it says the section is split by the language-appropriate chunker
  (`_chunk_japanese` for `lang == "ja"`, else `_chunk_english`) rather than an
  English-only sentence split.
- Replace the "**Japanese content:**" paragraph with prose stating that when
  `lang == "ja"`, both in-section and oversized Markdown sections carry
  `normalized_content` produced by the ja path (Sudachi normalized form), and that
  non-ja Markdown still emits empty `normalized_content`. Keep the FTS5 `COALESCE`
  note accurate for the non-ja case.

### Details
- Verify the updated text against the implemented behavior in the companion
  `chunk_splitter.py` procedure before updating — do not describe behavior that is
  not yet implemented.
- Do not alter parameter tables, configuration references, or other sections.

## Compatibility considerations
N/A: documentation-only change describing already-implemented behavior.

## Security considerations
N/A: documentation-only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- Review of the updated paragraphs confirms they match the implemented
  language-aware behavior (`AC-4`); the old bypass paragraph no longer exists.

## Completion criteria
- Section 3.1.4 describes language-aware Markdown chunking with per-language
  oversized fallback and ja `normalized_content`; the bypass statement is removed.

## Out of Scope
- Any other section of this doc; any other documentation file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Run the documentation checkers in `routing.md` Tools "When to run which tool" | Pending | — | — | REQ-005 |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | N/A at plan creation | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-005`
- **Source issue**: `issues/20261106-073538_raging007_markdown-japanese-chunk-bypass.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261106-103229_raging007_markdown-japanese-chunk-bypass.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261106-152344
- **Related target files**: `docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md`
