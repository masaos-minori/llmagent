## Goal

Expand the "### 3.1.4 Markdown Heading Chunking Behavior" subsection in
`docs/03_rag_02_03_ingestion_pipeline-chunksplitter.md` to document the fallback
trigger condition, the sequential per-section combination model, the metadata-during-fallback
behavior, and the undersized-section edge case, per REQ-001, REQ-002, REQ-003.

## Scope

- Expand exactly one existing subsection within
  `docs/03_rag_02_03_ingestion_pipeline-chunksplitter.md`
- Document four specific findings derived from `_chunk_markdown_by_heading()`'s
  implementation: trigger condition, combination model, metadata behavior, edge case
- Out-of-scope: changing `_chunk_markdown_by_heading()`'s actual implementation;
  correcting duplicate-section structure (addressed by sibling Plan
  `plans/20260913-202903_plan.md`); addressing the separate question covered by
  sibling Plan `plans/20260913-210434_plan.md`

## Assumptions

- `_chunk_markdown_by_heading()`'s current implementation remains the authoritative
  behavior (confirmed this cycle)
- The Plan's frozen `Implementation Target Files` section accurately reflects scope

## Design decisions

- State the metadata-during-fallback finding as "no distinguishing field exists"
  rather than inventing a distinction — this is the accurate, confirmed behavior
- Include the undersized-section drop as the answer to the Issue's "known edge cases"
  request — this is the one edge case surfaced with a concrete, confirmable mechanism
  (the `min_chunk` guard)

## Alternatives considered

- Adding a new subsection for each of the four findings: rejected in favor of expanding
  the existing subsection to keep related information together
- Using prose-only description vs. structured list: structured list preferred for
  readability of distinct behavioral facts

## Implementation

### Target file

`docs/03_rag_02_03_ingestion_pipeline-chunksplitter.md`

### Procedure

Append four paragraphs after the existing one-paragraph description in
"### 3.1.4 Markdown Heading Chunking Behavior":

1. Paragraph on the exact fallback trigger condition (`len(section) > md_snippet_max_chars`,
   default 600)
2. Paragraph on the sequential, per-section combination model (each section takes exactly
   one path — whole-section or fallback-split, never both)
3. Paragraph on the metadata-during-fallback finding (fallback-split chunks carry no
   distinguishing metadata from whole-section chunks; all tagged `"text"`)
4. Paragraph on the undersized-section edge case (sections shorter than `min_chunk` are
   silently dropped, producing no chunk)

### Method

1. Read the current content of "### 3.1.4 Markdown Heading Chunking Behavior"
   subsection to identify the insertion point (after the existing one-paragraph
   description, before the next heading)
2. Append the four paragraphs in order, maintaining consistency with the existing
   documentation style (prose descriptions, evidence references where applicable)
3. Use `N/A: {short reason}` format for any section that does not apply

### Details

**Paragraph 1 — Fallback trigger:**
State that when a heading-delimited section exceeds `md_snippet_max_chars` characters
(default 600), the section is split using sentence-boundary splitting via
`_chunk_english()`. Cite the trigger condition explicitly: `len(section) > md_snippet_max_chars`.

**Paragraph 2 — Combination model:**
State that the two strategies combine sequentially, per-section: the text is first split
into heading-delimited sections, then *each section independently* either passes through
as one chunk or is further split by `_chunk_english()`. The two strategies are not applied
in parallel or merged; each section takes exactly one path.

**Paragraph 3 — Metadata during fallback:**
State that no distinction is made between whole-section chunks and fallback-split chunks
at the metadata level. The caller tags every chunk returned by
`_chunk_markdown_by_heading()` with the literal `"text"` chunk-type marker, regardless
of whether that specific chunk came from a whole heading section or from a
`_chunk_english()`-split fragment of an oversized one. There is no metadata field
distinguishing "heading chunk" from "fallback-split chunk."

**Paragraph 4 — Undersized-section edge case:**
State that a section that fits within `md_snippet_max_chars` but is smaller than
`self._min_chunk` is silently dropped. The `append` only happens inside the inner check
(`if len(section) >= self._min_chunk:`); a too-small section produces no chunk at all,
not an error or warning.

## Compatibility considerations

This is a documentation-only change within an existing subsection. No code behavior changes.
No backward-compatibility concerns.

## Security considerations

N/A: documentation-only change.

## Rollback considerations

Revert the appended paragraphs to restore the original subsection content. No data loss
or side effects possible from reverting a documentation addition.

## Validation plan

| Target File | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| docs/03_rag_02_03_ingestion_pipeline-chunksplitter.md | Manual — cross-check expanded subsection against `chunk_splitter.py` | Manual inspection | Every claim traceable to a specific code line |

## Completion criteria

- [ ] Paragraph 1 states the exact trigger condition (`len(section) > md_snippet_max_chars`)
- [ ] Paragraph 2 states each section takes exactly one path (whole-section or fallback-split),
      sequentially per section, never both
- [ ] Paragraph 3 states fallback-split chunks carry the same `"text"` chunk-type marker as
      whole-section chunks, with no distinguishing field
- [ ] Paragraph 4 states sections smaller than `min_chunk` are silently dropped, producing no chunk
- [ ] Each added paragraph traces to a specific `chunk_splitter.py` line number

## Out of scope

- Changing `_chunk_markdown_by_heading()`'s actual implementation
- Correcting this file's duplicate-section structure (`## 3.`/`## 3a.`/`## 3b.`)
- Addressing the unrelated question about why the `.md` extension always triggers heading
  chunking

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: documentation-only change |
| 3 | Run the validation sequence (rules/toolchain.md) | Pending | — | — | N/A: documentation-only change |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: documentation-only change |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003
- **Source issue**: issues/20260913-183034_missing_chunksplitter_markdown_heading_fallback.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260913-213534_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260914-104912
- **Related target files**: docs/03_rag_02_03_ingestion_pipeline-chunksplitter.md
